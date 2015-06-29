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

"""
WSGI middleware for QingCloud API.
"""

from oslo_config import cfg

import nova.api.qingcloud_openstack
from nova.api.qingcloud_openstack.compute import extensions
from nova.api.qingcloud_openstack.compute import flavors
from nova.api.qingcloud_openstack.compute import images
from nova.api.qingcloud_openstack.compute import volumes
from nova.api.qingcloud_openstack.compute import floating_ips
from nova.api.qingcloud_openstack.compute import servers
from nova.api.qingcloud_openstack.compute import versions

#allow_instance_snapshots_opt = cfg.BoolOpt('allow_instance_snapshots',
#        default=True,
#        help='Permit instance snapshot operations.')
#
CONF = cfg.CONF
#CONF.register_opt(allow_instance_snapshots_opt)


class APIRouter(nova.api.qingcloud_openstack.APIRouter):
    """Routes requests on the OpenStack API to the appropriate controller
    and method.
    """
    ExtensionManager = extensions.ExtensionManager

    def _setup_routes(self, mapper, ext_mgr, init_only):
        if init_only is None or 'versions' in init_only:
            self.resources['versions'] = versions.create_resource()
            mapper.connect("versions", "/",
                        controller=self.resources['versions'],
                        action='show',
                        conditions={"method": ['GET']})

        mapper.redirect("", "/")

        #if init_only is None or 'consoles' in init_only:
        #    self.resources['consoles'] = consoles.create_resource()
        #    mapper.resource("console", "consoles",
        #                controller=self.resources['consoles'],
        #                parent_resource=dict(member_name='server',
        #                collection_name='servers'))

        if init_only is None or 'consoles' in init_only or \
                'servers' in init_only:
            self.resources['servers'] = servers.create_resource(ext_mgr)
            mapper.resource("server", "servers",
                            controller=self.resources['servers'],
                            collection={'detail': 'GET'},
                            member={'action': 'POST'})

        #if init_only is None or 'ips' in init_only:
        #    self.resources['ips'] = ips.create_resource()
        #    mapper.resource("ip", "ips", controller=self.resources['ips'],
        #                    parent_resource=dict(member_name='server',
        #                                         collection_name='servers'))

        if init_only is None or 'images' in init_only:
            self.resources['images'] = images.create_resource()
            mapper.resource("image", "images",
                            controller=self.resources['images'],
                            collection={'detail': 'GET'})

        if init_only is None or 'volumes' in init_only:
            self.resources['volumes'] = volumes.create_resource()
            mapper.resource("volumes", "volumes",
                            controller=self.resources['volumes'],
                            collection={'detail': 'GET'})

        if init_only is None or 'os-floating-ips' in init_only:
            self.resources['os-floating-ips'] = floating_ips.create_resource()
            mapper.resource("os-floating-ips", "os-floating-ips",
                            controller=self.resources['os-floating-ips'],
                            collection={'detail': 'GET'})

        #if init_only is None or 'limits' in init_only:
        #    self.resources['limits'] = limits.create_resource()
        #    mapper.resource("limit", "limits",
        #                    controller=self.resources['limits'])

        if init_only is None or 'flavors' in init_only:
            self.resources['flavors'] = flavors.create_resource()
            mapper.resource("flavor", "flavors",
                            controller=self.resources['flavors'],
                            collection={'detail': 'GET'},
                            member={'action': 'POST'})

        #if init_only is None or 'image_metadata' in init_only:
        #    self.resources['image_metadata'] = image_metadata.create_resource()
        #    image_metadata_controller = self.resources['image_metadata']

        #    mapper.resource("image_meta", "metadata",
        #                    controller=image_metadata_controller,
        #                    parent_resource=dict(member_name='image',
        #                    collection_name='images'))

        #    mapper.connect("metadata",
        #                   "/{project_id}/images/{image_id}/metadata",
        #                   controller=image_metadata_controller,
        #                   action='update_all',
        #                   conditions={"method": ['PUT']})

        #if init_only is None or 'server_metadata' in init_only:
        #    self.resources['server_metadata'] = \
        #        server_metadata.create_resource()
        #    server_metadata_controller = self.resources['server_metadata']

        #    mapper.resource("server_meta", "metadata",
        #                    controller=server_metadata_controller,
        #                    parent_resource=dict(member_name='server',
        #                    collection_name='servers'))

        #    mapper.connect("metadata",
        #                   "/{project_id}/servers/{server_id}/metadata",
        #                   controller=server_metadata_controller,
        #                   action='update_all',
        #                   conditions={"method": ['PUT']})


#class APIRouterV21(nova.api.qingcloud_openstack.APIRouterV21):
#    """Routes requests on the OpenStack API to the appropriate controller
#    and method.
#    """
#    def __init__(self, init_only=None):
#        self._loaded_extension_info = plugins.LoadedExtensionInfo()
#        super(APIRouterV21, self).__init__(init_only)
#
#    def _register_extension(self, ext):
#        return self.loaded_extension_info.register_extension(ext.obj)
#
#    @property
#    def loaded_extension_info(self):
#        return self._loaded_extension_info
#
#
## NOTE(oomichi): Now v3 API tests use APIRouterV3. After moving all v3
## API extensions to v2.1 API, we can remove this class.
#class APIRouterV3(nova.api.qingcloud_openstack.APIRouterV21):
#    """Routes requests on the OpenStack API to the appropriate controller
#    and method.
#    """
#    def __init__(self, init_only=None):
#        self._loaded_extension_info = plugins.LoadedExtensionInfo()
#        super(APIRouterV3, self).__init__(init_only, v3mode=True)
#
#    def _register_extension(self, ext):
#        return self.loaded_extension_info.register_extension(ext.obj)
#
#    @property
#    def loaded_extension_info(self):
#        return self._loaded_extension_info
