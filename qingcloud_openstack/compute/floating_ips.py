# Copyright 2011 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import webob.exc

from nova.api.qingcloud_openstack import common
#from nova.api.qingcloud_openstack.compute.views import volumes as views_volumes
from nova.api.qingcloud_openstack import wsgi
from nova import exception
from nova.i18n import _
import nova.volume
import nova.utils
import qingcloud.iaas


conn = qingcloud.iaas.connect_to_zone(                                                               
    'gd1',
    'ABPWUVSJGOOZENGPOJSL',
    'fMsZTpw0CbXGqdsgwTv6BvdhRFUqpgCQgbdCKS6k'
)

SUPPORTED_FILTERS = {
    'name': 'name',
    'status': 'status',
    'changes-since': 'changes-since',
    'server': 'property-instance_uuid',
    'type': 'property-volume_type',
    'minRam': 'min_ram',
    'minDisk': 'min_disk',
}


class Controller(wsgi.Controller):
    """Base controller for retrieving/displaying volumes."""

    #_view_builder_class = views_volumes.ViewBuilder

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self._volume_api = nova.volume.API()

    def _get_filters(self, req):
        """Return a dictionary of query param filters from the request.

        :param req: the Request object coming from the wsgi layer
        :retval a dict of key/value filters
        """
        filters = {}
        for param in req.params:
            if param in SUPPORTED_FILTERS or param.startswith('property-'):
                # map filter name or carry through if property-*
                filter_name = SUPPORTED_FILTERS.get(param, param)
                filters[filter_name] = req.params.get(param)

        # ensure server filter is the instance uuid
        filter_name = 'property-instance_uuid'
        try:
            filters[filter_name] = filters[filter_name].rsplit('/', 1)[1]
        except (AttributeError, IndexError, KeyError):
            pass

        filter_name = 'status'
        if filter_name in filters:
            # The Image API expects us to use lowercase strings for status
            filters[filter_name] = filters[filter_name].lower()

        return filters

    def show(self, req, id):
        """Return detailed information about a specific volume.

        :param req: `wsgi.Request` object
        :param id: Image identifier
        """
        context = req.environ['nova.context']

        try:
            volume = self._volume_api.get(context, id)
        except (exception.NotFound, exception.InvalidImageRef):
            explanation = _("Image not found.")
            raise webob.exc.HTTPNotFound(explanation=explanation)

        req.cache_db_items('volumes', [volume], 'id')
        return self._view_builder.show(req, volume)

    def delete(self, req, id):
        """Delete an volume, if allowed.

        :param req: `wsgi.Request` object
        :param id: Image identifier (integer)
        """
        context = req.environ['nova.context']
        try:
            self._volume_api.delete(context, id)
        except exception.ImageNotFound:
            explanation = _("Image not found.")
            raise webob.exc.HTTPNotFound(explanation=explanation)
        except exception.ImageNotAuthorized:
            # The volume service raises this exception on delete if glanceclient
            # raises HTTPForbidden.
            explanation = _("You are not allowed to delete the volume.")
            raise webob.exc.HTTPForbidden(explanation=explanation)
        return webob.exc.HTTPNoContent()

    def index(self, req):
        """Return an index listing of volumes available to the request.

        :param req: `wsgi.Request` object

        """
        context = req.environ['nova.context']
        filters = self._get_filters(req)
        params = req.GET.copy()
        page_params = common.get_pagination_params(req)
        for key, val in page_params.iteritems():
            params[key] = val
        try:
            eip_list = conn.describe_eips(limit=50, status=["pending","available","associated","suspended"])
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        data = eip_list['eip_set']
        res = []
        for eip in data:
            res.append({
                'id': eip['eip_id'],
                'instance_id': eip['resource']['resource_id'],
                'status': eip['status'],
                'fixed_ip': '',
                'pool': "Elastic",
                'ip': eip['eip_addr']})
       

        return {'floating_ips': res}

    def detail(self, req):
        """Return a detailed index listing of volumes available to the request.

        :param req: `wsgi.Request` object.

        """
        context = req.environ['nova.context']
        filters = self._get_filters(req)
        params = req.GET.copy()
        page_params = common.get_pagination_params(req)
        for key, val in page_params.iteritems():
            params[key] = val
        try:
            volumes = conn.describe_volumes(limit=50)
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
	data = volumes['volume_set']
        res = [] 
        for volume in data:
            res.append({
                'status': volume['status'],
                'display_name': volume['volume_name'],
                'attachments': [],
                'display_description': volume['description'],
                'id': volume['volume_id'],
                'volume_type': u'lvmdriver-1',
                'snapshot_id': None,
                'size': volume['size'],
                'metadata': {},
                'created_at': volume['create_time'],
                'multiattach': 'false'})
        return {'volumes': res}
         


    def create(self, *args, **kwargs):
        try:
            eips = conn.allocate_eips(
                bandwidth=int(kwargs['body'].get('pool', 1)))
        except:
            raise webob.exc.HTTPMethodNotAllowed()
        return  {"floating_ip": {"instance_id": '', "ip": "", "fixed_ip": '', "id": eips['eips'][0], "pool": "Elastic"}}


def create_resource():
    return wsgi.Resource(Controller())
