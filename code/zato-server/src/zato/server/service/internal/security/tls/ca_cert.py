# -*- coding: utf-8 -*-

"""
Copyright (C) 2014 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# stdlib
import errno, os

# Zato
from zato.common.broker_message import SECURITY
from zato.common.odb.model import TLSCACert
from zato.common.odb.query import tls_ca_cert_list
from zato.common.util import get_tls_cert_full_path, get_tls_cert_info_from_payload, store_tls_ca_cert
from zato.server.service.internal import AdminService
from zato.server.service.meta import CreateEditMeta, DeleteMeta, GetListMeta

elem = 'security_tls_ca_cert'
model = TLSCACert
label = 'a TLS CA cert'
broker_message = SECURITY
broker_message_prefix = 'TLS_CA_CERT_'
list_func = tls_ca_cert_list
skip_input_params = ['info',]
output_optional_extra = ['info',]

def instance_hook(service, input, instance, attrs):

    instance.username = service.cid # Required by model
    instance.info = get_tls_cert_info_from_payload(input.value)

    with service.lock():
        full_path = store_tls_ca_cert(service.server.tls_dir, service.request.input.value)
        service.logger.info('CA certificate saved under `%s`', full_path)

def response_hook(service, input, instance, attrs, service_type):
    if service_type == 'create_edit':
        service.response.payload.info = instance.info

def delete_hook(service, input, instance, attrs):
    try:
        os.remove(get_tls_cert_full_path(service.server.tls_dir, instance.info))
    except OSError, e:
        if e.errno == errno.ENOENT:
            # It's ok - some other worker must have deleted it already
            pass
        else:
            raise

class GetList(AdminService):
    __metaclass__ = GetListMeta

class Delete(AdminService):
    __metaclass__ = DeleteMeta

class Create(AdminService):
    __metaclass__ = CreateEditMeta

class Edit(AdminService):
    __metaclass__ = CreateEditMeta