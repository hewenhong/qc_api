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
from nova.api.qingcloud_openstack import wsgi
from nova.api.qingcloud_openstack import qingcloud_api
from nova import exception


class Controller(wsgi.Controller):
    """Base controller for retrieving/displaying volumes."""

    #_view_builder_class = views_volumes.ViewBuilder

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self.conn = qingcloud_api.conn()

    def show(self, req, id):
        """Return detailed information about a specific volume.

        :param req: `wsgi.Request` object
        :param id: Image identifier
        """
        raise webob.exc.HTTPMethodNotAllowed()

    def delete(self, req, id):
        raise webob.exc.HTTPMethodNotAllowed()

    def index(self, req):
        """Return an index listing of volumes available to the request.

        :param req: `wsgi.Request` object

        """
        params = req.GET.copy()
        page_params = common.get_pagination_params(req)
        for key, val in page_params.iteritems():
            params[key] = val
        try:
            eip_list = self.conn.describe_eips(limit=50, status=["pending","available","associated","suspended"])
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
        try:
            volumes = self.conn.describe_volumes(limit=50)
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        res = []
        for volume in volumes['volume_set']:
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
            eips = self.conn.allocate_eips(
                bandwidth=int(kwargs['body'].get('pool', 1)))
        except:
            raise webob.exc.HTTPMethodNotAllowed()
        return  {"floating_ip": {"instance_id": '', "ip": "", "fixed_ip": '', "id": eips['eips'][0], "pool": "Elastic"}}


def create_resource():
    return wsgi.Resource(Controller())
