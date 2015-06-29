#!/usr/bin/env python
# encoding: utf-8
# Author: Vincent He <vincenthe@126.com>


import qingcloud.iaas
from nova.api.qingcloud_openstack import settings
import webob.exc

def conn():
    try:
        conn = qingcloud.iaas.connect_to_zone(
            settings.QINGCLOUD_AUTH.get('zone'),
            settings.QINGCLOUD_AUTH.get('access_key_id'),
            settings.QINGCLOUD_AUTH.get('secret_access_key')
        )
    except:
        raise webob.exc.HTTPMethodNotAllowed()
    return conn
