#
# This source file is part of the EdgeDB open source project.
#
# Copyright 2008-present MagicStack Inc. and the EdgeDB authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import textwrap

from ..common import quote_ident as qi
from ..common import quote_literal as ql

from . import base
from . import ddl


class Role(base.DBObject):
    def __init__(self, name, *, allow_login=False, password=None,
                 is_superuser=False, membership=None, metadata=None):
        super().__init__()
        self.name = name
        self.is_superuser = is_superuser
        self.allow_login = allow_login
        self.password = password
        self.membership = membership
        self.metadata = metadata

    def get_type(self):
        return 'ROLE'

    def get_id(self):
        return qi(self.name)


class RoleExists(base.Condition):
    def __init__(self, name):
        self.name = name

    def code(self, block: base.PLBlock) -> str:
        return textwrap.dedent(f'''\
            SELECT
                rolname
            FROM
                pg_catalog.pg_authid
            WHERE
                rolname = {ql(self.name)}
        ''')


class RoleCommand:

    def _render(self):
        superuser = 'SUPERUSER' if self.object.is_superuser else ''
        login = 'LOGIN' if self.object.allow_login else 'NOLOGIN'
        if self.object.password:
            password = f'PASSWORD {ql(self.object.password)}'
        else:
            password = f'PASSWORD NULL'

        return (
            f'ROLE {self.object.get_id()} '
            f'{superuser} {login} {password}'
        )


class CreateRole(ddl.CreateObject, RoleCommand):
    def __init__(
            self, role, *, conditions=None, neg_conditions=None, priority=0):
        super().__init__(
            role.name, conditions=conditions, neg_conditions=neg_conditions,
            priority=priority)
        self.object = role

    def code(self, block: base.PLBlock) -> str:
        if self.object.membership:
            roles = ', '.join(qi(m) for m in self.object.membership)
            membership = f'IN ROLE {roles}'
        else:
            membership = ''
        return f'CREATE {self._render()} {membership}'


class AlterRole(ddl.AlterObject, RoleCommand):
    def __init__(
            self, role, *, conditions=None, neg_conditions=None, priority=0):
        super().__init__(
            role.name, conditions=conditions, neg_conditions=neg_conditions,
            priority=priority)
        self.object = role

    def code(self, block: base.PLBlock) -> str:
        return f'ALTER {self._render()}'


class DropRole(ddl.SchemaObjectOperation):

    def code(self, block: base.PLBlock) -> str:
        return f'DROP ROLE {qi(self.name)}'


class AlterRoleAddMember(ddl.SchemaObjectOperation):

    def __init__(
            self, name, member, *, conditions=None,
            neg_conditions=None, priority=0):
        super().__init__(name, conditions=conditions,
                         neg_conditions=neg_conditions, priority=priority)
        self.member = member

    def code(self, block: base.PLBlock) -> str:
        return f'GRANT {qi(self.name)} TO {qi(self.member)}'


class AlterRoleDropMember(ddl.SchemaObjectOperation):

    def __init__(
            self, name, member, *, conditions=None,
            neg_conditions=None, priority=0):
        super().__init__(name, conditions=conditions,
                         neg_conditions=neg_conditions, priority=priority)
        self.member = member

    def code(self, block: base.PLBlock) -> str:
        return f'REVOKE {qi(self.name)} FROM {qi(self.member)}'