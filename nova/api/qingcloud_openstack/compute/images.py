# =========================================================================
# Copyright 2012-present Yunify, Inc.
# -------------------------------------------------------------------------
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this work except in compliance with the License.
# You may obtain a copy of the License in the LICENSE file, or at:
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =========================================================================

import webob.exc

from nova.api.qingcloud_openstack import common
from nova.api.qingcloud_openstack import wsgi
from nova.api.qingcloud_openstack import qingcloud_api
from nova import exception



class Controller(wsgi.Controller):
    """Base controller for retrieving/displaying images."""

    #_view_builder_class = views_images.ViewBuilder

    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self.conn = qingcloud_api.conn()

    def show(self, req, id):
        raise webob.exc.HTTPMethodNotAllowed()

    def delete(self, req, id):
        raise webob.exc.HTTPMethodNotAllowed()

    def index(self, req):
        """Return an index listing of images available to the request.

        :param req: `wsgi.Request` object

        """
        params = req.GET.copy()
        page_params = common.get_pagination_params(req)
        for key, val in page_params.iteritems():
            params[key] = val
        data = []

        try:
            images = self.conn.describe_images(
                provider="selected", status=["available"], **page_params)
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        for image in images['image_set']:
            data.append({
                'status': image.get('status', None),
                'name': image.get('image_id', None),
                'id': image.get('image_id', None)})
        return {'images': data}

        raise webob.exc.HTTPMethodNotAllowed()

    def detail(self, req):
        """Return a detailed index listing of images available to the request.

        :param req: `wsgi.Request` object.

        """
        page_params = common.get_pagination_params(req)
        data = []
        try:
            images = self.conn.describe_images(
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
