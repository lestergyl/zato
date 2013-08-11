# -*- coding: utf-8 -*-

"""
Copyright (C) 2013 Dariusz Suchojad <dsuch at zato.io>

Licensed under LGPLv3, see LICENSE.txt for terms and conditions.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# anyjson
from anyjson import loads
from traceback import format_exc

# Zato
from zato.common import DEFAULT_DELIVERY_INSTANCE_LIST_BATCH_SIZE, DELIVERY_STATE, INVOCATION_TARGET, KVDB, ZatoException
from zato.server.service import AsIs
from zato.server.service.internal import AdminService, AdminSIO

class _DeliveryService(AdminService):
        
    def _validate_input_dict(self, *validation_info):
        """ Checks that input belongs is one of allowed values.
        """
        for key_name, key, source in validation_info:
            if not source.has(key):
                msg = 'Invalid {}:[{}]'.format(key_name, key)
                log_msg = '{} (attrs: {})'.format(msg, source.attrs)
                
                self.logger.warn(log_msg)
                raise ZatoException(self.cid, msg)

class GetList(_DeliveryService):
    """ For a given target type, returns a list of existing deliveries regardless of their states.
    """
    class SimpleIO(AdminSIO):
        request_elem = 'zato_pattern_delivery_get_list_request'
        response_elem = 'zato_pattern_delivery_get_list_response'
        input_required = ('cluster_id', 'target_type')
        output_required = ('name', 'last_updated_utc', 'target', 'target_type', 'short_def', 'total_count', 
            'in_progress_count', 'in_doubt_count', 'arch_success_count', 'arch_failed_count')
        
    def get_data(self, target_type):
        for name, base_target_info in self.delivery_store.get_by_target_type(target_type).items():
            base_target_info = loads(base_target_info)
            in_progress_count, in_doubt_count, arch_success_count, arch_failed_count = self.delivery_store.get_counts(name)

            yield {
                'name': name,
                'target':base_target_info['target'],
                'target_type': target_type,
                'last_updated_utc':base_target_info['last_updated_utc'],
                'short_def':'todo',
                'total_count':in_progress_count + in_doubt_count + arch_success_count + arch_failed_count,
                'in_progress_count':in_progress_count,
                'in_doubt_count':in_doubt_count,
                'arch_success_count':arch_success_count,
                'arch_failed_count':arch_failed_count
            }

    def handle(self):
        target_type = self.request.input.target_type
        self._validate_input_dict(('target_type', target_type, INVOCATION_TARGET))
            
        self.response.payload[:] = self.get_data(target_type)
        
class InDoubtGetInstanceList(_DeliveryService):
    """ For a given delivery name, return all instances that are in-doubt.
    """
    name = 'zato.pattern.delivery.in-doubt.get-instance-list'
    
    class SimpleIO(AdminSIO):
        request_elem = 'zato_pattern_delivery_in_doubt_get_instance_list_request'
        response_elem = 'zato_pattern_delivery_in_doubt_get_instance_list_response'
        input_required = ('name', 'target_type')
        input_optional = ('start', 'stop', 'batch_no', 'batch_size')
        output_required = ('name', 'target_type', AsIs('tx_id'), 'creation_time_utc', 'in_doubt_created_at_utc', 
            'source_count', 'target_count', 'retry_repeats', 'check_after', 'retry_seconds')
        
    def handle(self):
        try:
            batch_size = self.request.input.get('batch_size')
            batch_size = int(batch_size) or DEFAULT_DELIVERY_INSTANCE_LIST_BATCH_SIZE
        except(TypeError, ValueError), e:
            self.logger.debug('Invalid batch_size in:[%s], e:[%s]', batch_size, format_exc(e))
            batch_size = DEFAULT_DELIVERY_INSTANCE_LIST_BATCH_SIZE
            
        
            
        self.response.payload[:] = self.get_data(batch_size)
        
    def get_data(self, batch_size):
        for item in self.delivery_store.get_in_doubt_instance_list(
                self.request.input.name, self.request.input.get('start'), 
                self.request.input.get('stop'),batch_size):
            item['name'] = self.request.input.name
            item['target_type'] = self.request.input.target_type
            
            yield item