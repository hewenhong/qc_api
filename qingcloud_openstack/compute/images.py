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
import qingcloud.iaas

from nova.api.qingcloud_openstack import common
from nova.api.qingcloud_openstack.compute.views import images as views_images
from nova.api.qingcloud_openstack import wsgi
from nova import exception
from nova.i18n import _
import nova.image
import nova.utils


SUPPORTED_FILTERS = {
    'name': 'name',
    'status': 'status',
    'changes-since': 'changes-since',
    'server': 'property-instance_uuid',
    'type': 'property-image_type',
    'minRam': 'min_ram',
    'minDisk': 'min_disk',
}

conn = qingcloud.iaas.connect_to_zone(
    'gd1',
    'ABPWUVSJGOOZENGPOJSL',
    'fMsZTpw0CbXGqdsgwTv6BvdhRFUqpgCQgbdCKS6k'
)

class Controller(wsgi.Controller):
    """Base controller for retrieving/displaying images."""

    _view_builder_class = views_images.ViewBuilder

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self._image_api = nova.image.API()

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
        raise webob.exc.HTTPMethodNotAllowed()

    def delete(self, req, id):
        raise webob.exc.HTTPMethodNotAllowed()

    def index(self, req):
        """Return an index listing of images available to the request.

        :param req: `wsgi.Request` object

        """
        page_params = common.get_pagination_params(req)
        data = []

        try:
            images = conn.describe_images(
                provider="selected", status=["available"], **page_params)
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        for image in images['image_set']:
            data.append({
                'status': image.get('status', None),
                'name': image.get('image_id', None),
                'id': image.get('image_id', None)})
        return {'images': data}

    def detail(self, req):
        """Return a detailed index listing of images available to the request.

        :param req: `wsgi.Request` object.

        """
        page_params = common.get_pagination_params(req)
        data = []
        try:
            images = conn.describe_images(
                provider="system", status=["pending","available","suspended"], **page_params)
            for image in images['image_set']:
                data.append({
                    'status': image.get('status', None),
                    'name': image.get('image_name', None),
                    'id': image.get('image_id', None)})

        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        return {'images': data}

    def create(self, *args, **kwargs):
        raise webob.exc.HTTPMethodNotAllowed()


def create_resource():
    return wsgi.Resource(Controller())
