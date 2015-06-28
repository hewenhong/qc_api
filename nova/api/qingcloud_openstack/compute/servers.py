# Copyright 2010 OpenStack Foundation
# Copyright 2011 Piston Cloud Computing, Inc
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
import collections
import base64
import re
import sys

from oslo_config import cfg
from oslo_log import log as logging
import oslo_messaging as messaging
import six
from webob import exc
import qingcloud.iaas

from nova.api.qingcloud_openstack import common
from nova.api.qingcloud_openstack.compute.views import servers as views_servers
from nova.api.qingcloud_openstack import wsgi
#from nova import block_device
from nova import compute
from nova.compute import flavors
from nova import exception
from nova.i18n import _
#from nova import objects
#from nova import policy
from nova import utils

conn = qingcloud.iaas.connect_to_zone(
    'gd1',
    'ABPWUVSJGOOZENGPOJSL',
    'fMsZTpw0CbXGqdsgwTv6BvdhRFUqpgCQgbdCKS6k'
)

#server_opts = [
#    cfg.BoolOpt('enable_instance_password',
#                default=True,
#                help='Enables returning of the instance password by the'
#                     ' relevant server API calls such as create, rebuild'
#                     ' or rescue, If the hypervisor does not support'
#                     ' password injection then the password returned will'
#                     ' not be correct'),
#]
CONF = cfg.CONF
#CONF.register_opts(server_opts)
#CONF.import_opt('network_api_class', 'nova.network')
#CONF.import_opt('reclaim_instance_interval', 'nova.compute.manager')

LOG = logging.getLogger(__name__)

#CREATE_EXCEPTIONS = {
#    exception.InvalidMetadataSize: exc.HTTPRequestEntityTooLarge,
#    exception.ImageNotFound: exc.HTTPBadRequest,
#    exception.FlavorNotFound: exc.HTTPBadRequest,
#    exception.KeypairNotFound: exc.HTTPBadRequest,
#    exception.ConfigDriveInvalidValue: exc.HTTPBadRequest,
#    exception.ImageNotActive: exc.HTTPBadRequest,
#    exception.FlavorDiskTooSmall: exc.HTTPBadRequest,
#    exception.FlavorMemoryTooSmall: exc.HTTPBadRequest,
#    exception.NetworkNotFound: exc.HTTPBadRequest,
#    exception.PortNotFound: exc.HTTPBadRequest,
#    exception.FixedIpAlreadyInUse: exc.HTTPBadRequest,
#    exception.SecurityGroupNotFound: exc.HTTPBadRequest,
#    exception.InstanceUserDataTooLarge: exc.HTTPBadRequest,
#    exception.InstanceUserDataMalformed: exc.HTTPBadRequest,
#    exception.ImageNUMATopologyIncomplete: exc.HTTPBadRequest,
#    exception.ImageNUMATopologyForbidden: exc.HTTPBadRequest,
#    exception.ImageNUMATopologyAsymmetric: exc.HTTPBadRequest,
#    exception.ImageNUMATopologyCPUOutOfRange: exc.HTTPBadRequest,
#    exception.ImageNUMATopologyCPUDuplicates: exc.HTTPBadRequest,
#    exception.ImageNUMATopologyCPUsUnassigned: exc.HTTPBadRequest,
#    exception.ImageNUMATopologyMemoryOutOfRange: exc.HTTPBadRequest,
#    exception.PortInUse: exc.HTTPConflict,
#    exception.InstanceExists: exc.HTTPConflict,
#    exception.NoUniqueMatch: exc.HTTPConflict,
#    exception.Invalid: exc.HTTPBadRequest,
#}

#CREATE_EXCEPTIONS_MSGS = {
#    exception.ImageNotFound: _("Can not find requested image"),
#    exception.FlavorNotFound: _("Invalid flavorRef provided."),
#    exception.KeypairNotFound: _("Invalid key_name provided."),
#    exception.ConfigDriveInvalidValue: _("Invalid config_drive provided."),
#}


class Controller(wsgi.Controller):
    """The Server API base controller class Qingcloud for the OpenStack API."""

    _view_builder_class = views_servers.ViewBuilder

    def __init__(self, ext_mgr=None, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self.compute_api = compute.API()
        self.ext_mgr = ext_mgr

    def index(self, req):
        """Returns a list of server names and ids for a given user."""
        try:
            servers = self._get_servers(req, is_detail=False)
        except exception.Invalid as err:
            raise exc.HTTPBadRequest(explanation=err.format_message())
        return servers

    def detail(self, req):
        """Returns a list of server details for a given user."""
        try:
            servers = self._get_servers(req, is_detail=True)
        except exception.Invalid as err:
            raise exc.HTTPBadRequest(explanation=err.format_message())
        return servers

    def _get_servers(self, req, is_detail):
        """Returns a list of servers, based on any search options specified."""

        search_opts = {}
        search_opts.update(req.GET)

        context = req.environ['nova.context']
        remove_invalid_options(context, search_opts,
                self._get_server_search_options())
        search_filter_name = search_opts.get('name', None)
        #search_filter_id = search_opts.get('id', None)
        # By default, compute's get_all() will return deleted instances.
        # If an admin hasn't specified a 'deleted' search option, we need
        # to filter out deleted instances by setting the filter ourselves.
        # ... Unless 'changes-since' is specified, because 'changes-since'
        # should return recently deleted images according to the API spec.
        limit, marker = common.get_limit_and_marker(req)
        # Sorting by multiple keys and directions is conditionally enabled
        #if self.ext_mgr.is_loaded('os-server-sort-keys'):
        #    sort_keys, sort_dirs = common.get_sort_params(req.params)

        try:
            instance_list = conn.describe_instances(
                    limit=limit,
                    status=["pending","running","stopped","suspended"])
            data = instance_list['instance_set']
            res =[]
            for instance in xrange(instance_list.get('total_count', 0)):
                if search_filter_name == data[instance].get('instance_name') or \
                        search_filter_name == data[instance].get('instance_id'):
                    res = [{
                              "id": data[instance].get('instance_id'),
                              "name": data[instance].get('instance_id'),
                          }]
                    break
                else:
                    try:
                        eip_addr = collections.OrderedDict([(u'Elastic IP', [{'version': 4, 'addr': data[instance]['eip']['eip_addr']}])])
                    except:
                        eip_addr = ''
                    res.append({
                                "id": data[instance].get('instance_id'),
                                "name": data[instance].get('instance_name'),
                                "status": data[instance].get('status'),
                                "tenant_id": "",
                                "user_id": "",
                                "metadata": {},
                                "hostId": "",
                                "image": data[instance]['image']['image_id'],
                                "flavor": "",
                                "created": data[instance]['create_time'],
                                "updated": data[instance]['status_time'],
                                "addresses": eip_addr,
                                "accessIPv4": '',
                                "accessIPv6": '',
                                "links": ""
                            })

        except exception.MarkerNotFound:
            msg = _('marker [%s] not found') % marker
            raise exc.HTTPBadRequest(explanation=msg)

        return {'servers': res}

    #def _get_server(self, context, req, instance_uuid):
    #    """Utility function for looking up an instance by uuid."""
    #    instance = common.get_instance(self.compute_api, context,
    #                                   instance_uuid,
    #                                   expected_attrs=['flavor'])
    #    req.cache_db_instance(instance)
    #    return instance

    def _check_string_length(self, value, name, max_length=None):
        try:
            if isinstance(value, six.string_types):
                value = value.strip()
            utils.check_string_length(value, name, min_length=1,
                                      max_length=max_length)
        except exception.InvalidInput as e:
            raise exc.HTTPBadRequest(explanation=e.format_message())

    def _validate_server_name(self, value):
        self._check_string_length(value, 'Server name', max_length=255)

    def _decode_base64(self, data):
        data = re.sub(r'\s', '', data)
        if not self.B64_REGEX.match(data):
            return None
        try:
            return base64.b64decode(data)
        except TypeError:
            return None

    def show(self, req, id):
        """Returns server details by server id."""
        context = req.environ['nova.context']
        instance = self._get_server(context, req, id)
        return self._view_builder.show(req, instance)

    def _extract(self, server_dict, ext_name, key):
        if self.ext_mgr.is_loaded(ext_name):
            return server_dict.get(key)
        return None

    def _validate_user_data(self, user_data):
        if user_data and self._decode_base64(user_data) is None:
            expl = _('Userdata content cannot be decoded')
            raise exc.HTTPBadRequest(explanation=expl)
        return user_data

    @wsgi.response(202)
    def create(self, req, body):
        """Creates a new server for a given user."""
        #if not self.is_valid_body(body, 'server'):
        #    raise exc.HTTPUnprocessableEntity()

        context = req.environ['nova.context']
        server_dict = body['server']
        password = self._get_server_admin_password(server_dict)

        if 'name' not in server_dict:
            msg = _("Server name is not defined")
            raise exc.HTTPBadRequest(explanation=msg)

        name = server_dict['name']
        self._validate_server_name(name)
        name = name.strip()

        image_id = server_dict['imageRef']
        try:
           login_mode = 'keypair'
           key_name = server_dict['key_name']
        except:
           login_mode = 'passwd'
           login_passwd = password


        flavor_id = self._flavor_id_from_req_data(body)

        user_data = self._extract(server_dict, 'os-user-data', 'user_data')
        self._validate_user_data(user_data)

        try:
            _get_inst_type = flavors.get_flavor_by_flavor_id
            inst_type = _get_inst_type(flavor_id, ctxt=context,
                                       read_deleted="no")
            instances = conn.run_instances(
                         image_id=image_id,
                         cpu=inst_type.get('vcpus', None),
                         memory=inst_type.get('memory_mb', None),
                         instance_name=name,
                         login_mode=login_mode,
                         login_keypair=key_name,
                         )

            #(instances, resv_id) = self.compute_api.create(context,
            #            inst_type,
            #            image_uuid,
            #            display_name=name,
            #            display_description=name,
            #            key_name=key_name,
            #            metadata=server_dict.get('metadata', {}),
            #            access_ip_v4=access_ip_v4,
            #            access_ip_v6=access_ip_v6,
            #            injected_files=injected_files,
            #            admin_password=password,
            #            min_count=min_count,
            #            max_count=max_count,
            #            requested_networks=requested_networks,
            #            security_group=sg_names,
            #            user_data=user_data,
            #            availability_zone=availability_zone,
            #            config_drive=config_drive,
            #            block_device_mapping=block_device_mapping,
            #            auto_disk_config=auto_disk_config,
            #            scheduler_hints=scheduler_hints,
            #            legacy_bdm=legacy_bdm,
            #            check_server_group_quota=check_server_group_quota)
        except (exception.QuotaError,
                exception.PortLimitExceeded) as error:
            raise exc.HTTPForbidden(
                explanation=error.format_message(),
                headers={'Retry-After': 0})
        except messaging.RemoteError as err:
            msg = "%(err_type)s: %(err_msg)s" % {'err_type': err.exc_type,
                                                 'err_msg': err.value}
            raise exc.HTTPBadRequest(explanation=msg)
        except UnicodeDecodeError as error:
            msg = "UnicodeError: %s" % error
            raise exc.HTTPBadRequest(explanation=msg)
        except Exception as error:
            # The remaining cases can be handled in a standard fashion.
            self._handle_create_exception(*sys.exc_info())

        server = {'server': {
            'id': instances.get('instances')[0],
            'name': instances.get('instances')[0],
            'flavor':{'id': flavor_id}}}

        robj = wsgi.ResponseObject(server)
        return robj

    def _flavor_id_from_req_data(self, data):
        try:
            flavor_ref = data['server']['flavorRef']
        except (TypeError, KeyError):
            msg = _("Missing flavorRef attribute")
            raise exc.HTTPBadRequest(explanation=msg)
        try:
            return common.get_id_from_href(flavor_ref)
        except ValueError:
            msg = _("Invalid flavorRef provided.")
            raise exc.HTTPBadRequest(explanation=msg)

    def _get_server_admin_password(self, server):
        """Determine the admin password for a server on creation."""
        try:
            password = server['adminPass']
            self._validate_admin_password(password)
        except KeyError:
            password = utils.generate_password()
        except ValueError:
            raise exc.HTTPBadRequest(explanation=_("Invalid adminPass"))

        return password

    def _validate_admin_password(self, password):
        if not isinstance(password, six.string_types):
            raise ValueError()

    def _get_server_search_options(self):
        """Return server search options allowed by non-admin."""
        return ('reservation_id', 'name', 'status', 'image', 'flavor',
                'ip', 'changes-since', 'all_tenants')


def create_resource(ext_mgr):
    return wsgi.Resource(Controller(ext_mgr))


def remove_invalid_options(context, search_options, allowed_search_options):
    """Remove search options that are not valid for non-admin API/context."""
    if context.is_admin:
        # Allow all options
        return
    # Otherwise, strip out all unknown options
    unknown_options = [opt for opt in search_options
                        if opt not in allowed_search_options]
    LOG.debug("Removing options '%s' from query",
              ", ".join(unknown_options))
    for opt in unknown_options:
        search_options.pop(opt, None)
