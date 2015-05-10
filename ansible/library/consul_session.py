#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2015 Chavez <chavez@somewhere-cool.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import json
import string

from collections import OrderedDict


DOCUMENTATION = '''
---
module: consul_session
version_added: "1.9"
author: Chavez
short_description: Interact with Consul Sessions API
description:
   - Use Consul Sessions API in your playbooks and roles
options:
  action:
    description:
      - API session action [create, destroy, info, node, list, renew]
    required: true
  behavior:
    description:
      - Controls when the session is invalidated [release, delete]
    require: false
  checks:
    description:
      - List of associated health checks comma separated "foo,bar,baz"
    required: false
  dc:
    desription:
      - The datacenter to use
    required: false
    default: dc1
  host:
    description:
      - Consul host
    required: true
    default: 127.0.0.1
  lock_delay:
    description:
      - Time to delay the lock of the session
    require: false
  node:
    description:
      - Node name to set on create
    required: false
  port:
    description:
      - Consul API port
    required: true
  session:
    description:
      - Consul session to interact with
    require: false
  ttl:
    description:
      - Session TTL
    required: false
  version:
    description:
      - Consul API version
    required: true
    default: v1

# informational: requirements for nodes
requirements: [ urllib, urllib2 ]
'''

EXAMPLES = '''
# Session create
- consul_session: action=create

# Session destroy
- consul_session: action=destroy session="some-valid-session"

# Get session info
- consul_session: action=info session="some-valid-session"

# Renew session
- consul_session: action=renew session="some-valid-session"

# List sessions
- consul_session: action=list

# List sessions
- consul_session: action=list
  register: all_sessions

# All sessions for a node
- consul_session: action=node node="node-foo"
'''

#
# Module execution.
#


class ConsulSession(object):

    ALLOWED_ACTIONS = ['create', 'destroy', 'info', 'node', 'list', 'renew']
    CREATE, DESTROY, INFO, NODE, LIST, RENEW = ALLOWED_ACTIONS

    PUT_ACTIONS = [CREATE, DESTROY, RENEW]
    GET_ACTIONS = [INFO, NODE, LIST]

    DEFAULT_CHECKS = ['serfHealth']

    def __init__(self, module):
        """Takes an AnsibleModule object to set up Consul Session interaction"""
        self.module = module
        self.action = string.lower(module.params.get('action', ''))
        self.behavior = module.params.get('behavior', 'release')
        self.checks = module.params.get('checks', self.DEFAULT_CHECKS[0])
        self.dc = module.params.get('dc', 'dc1')
        self.host = module.params.get('host', '127.0.0.1')
        self.lock_delay = module.params.get('lock_delay', '15s')
        self.node = module.params.get('node', '')
        self.port = module.params.get('port', 8500)
        self.session = module.params.get('session', '')
        self.ttl = module.params.get('ttl', '15s')
        self.version = module.params.get('version', 'v1')
        self.params = OrderedDict({})
        self.checks = str(self.checks).split(',')
        self._build_url()

    def run_cmd(self):
        self.validate()
        self._make_api_call()

    def validate(self):
        # Check action is allowed
        if not self.action or self.action not in self.ALLOWED_ACTIONS:
            self.module.fail_json(msg='Action is required and must be one of %r' % self.ALLOWED_ACTIONS)
        # Validate action being used
        # ie self._validate_create(), self._validate_destroy(), self._validate_info()
        getattr(self, "_validate_%s" % self.action)

    def _build_url(self):
        self.api_url = "http://%s:%s/%s/session/%s" % (self.host, self.port, self.version, self.action)
        if self.action in [self.DESTROY, self.INFO, self.RENEW] and self.session:
            self.api_url += '/%s' % self.session
        if self.action == self.NODE:
            self.api_url += '/%s' % self.node

    def _validate_create(self):
        pass

    def _validate_destroy(self):
        if not self.session:
            module.fail_json(msg="Destroy requires a session")

    def _validate_info(self):
        if not self.session:
            module.fail_json(msg="Info requires a session")

    def _validate_renew(self):
        if not self.session:
            module.fail_json(msg="Renew requires a session")

    def _validate_node(self):
        pass

    def _validate_list(self):
        pass

    def _make_api_call(self):
        req = self._setup_request()

        try:
            opener = urllib2.build_opener(urllib2.HTTPHandler)
            response = opener.open(req)
        except urllib2.URLError, e:
            self.module.fail_json(msg="API call (%s) failed: %s" % (self.api_url, str(e)))

        response_body = response.read()
        self._handle_response(response, response_body)

    def _add_create_params(self):
        valid_params = {
            "lock_delay": "LockDelay",
            "name": "Name",
            "node": "Node",
            "checks": "Checks",
            "behavior": "Behavior",
            "ttl": "TTL"
        }
        for param, name in valid_params.iteritems():
            if hasattr(self, param) and getattr(self, param):
                self.params[name] = getattr(self, param)
        # Ensure the default checks exist
        if self.DEFAULT_CHECKS[0] not in self.params['Checks']:
            self.params['Checks'] += self.DEFAULT_CHECKS
        self.params['Checks'] = filter(None, self.params['Checks'])

    def _setup_request(self):
        # Add dc param if not the default
        if self.dc != 'dc1':
            self.api_url = self.api_url + '?dc=%s' % self.dc
        # Add params for CREATE
        # Will set self.params dictionary to be encoded
        if self.action == self.CREATE:
            self._add_create_params()

        req = urllib2.Request(url=self.api_url)
        if self.action in self.PUT_ACTIONS:
            args = {'url': self.api_url}
            if self.params:
                args['data'] = json.dumps(self.params)
            req = urllib2.Request(**args)

        # Set correct HTTP method
        req.get_method = lambda: self._http_verb_for_action()

        return req

    def _http_verb_for_action(self):
        if self.action in self.PUT_ACTIONS:
            return 'PUT'
        return 'GET'

    def _handle_response(self, response, response_body):
        code = response.getcode()
        if code != 200:
            self.module.fail_json(msg="Failed with code %i for session %s with response %s" % (code, self.action, response_body))
        else:
            try:
                parsed_response = json.loads(response_body)
            except:
                parsed_response = ''
            self.module.exit_json(changed=True, succeeded=True, value=parsed_response)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True),
            behavior=dict(required=False, default='release'),
            checks=dict(required=False, default=ConsulSession.DEFAULT_CHECKS[0]),
            dc=dict(required=False, default='dc1'),
            host=dict(required=False, default='127.0.0.1'),
            lock_delay=dict(require=False, default='15s'),
            node=dict(required=False),
            port=dict(require=False, default=8500),
            session=dict(require=False),
            ttl=dict(required=False, default='15s'),
            version=dict(required=False, default='v1'),
        ),
        supports_check_mode=True
    )

    # If we're in check mode, just exit pretending like we succeeded
    if module.check_mode:
        module.exit_json(changed=False)

    consul_session = ConsulSession(module)
    consul_session.run_cmd()


# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.urls import *

main()
