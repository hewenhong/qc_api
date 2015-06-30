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

"""Starter script for Nova QingCloud API."""

import sys

from oslo_config import cfg
from oslo_log import log as logging

from nova import config
from nova import objects
from nova.openstack.common.report import guru_meditation_report as gmr
from nova import service
from nova import utils
from nova import version


CONF = cfg.CONF
CONF.import_opt('enabled_ssl_apis', 'nova.service')


def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, "nova")
    utils.monkey_patch()
    objects.register_all()

    gmr.TextGuruMeditation.setup_autorun(version)

    should_use_ssl = 'qingcloud_openstack' in CONF.enabled_ssl_apis
    server = service.WSGIService('qingcloud_openstack', use_ssl=should_use_ssl,
                                 max_url_len=16384)
    service.serve(server, workers=server.workers)
    service.wait()
