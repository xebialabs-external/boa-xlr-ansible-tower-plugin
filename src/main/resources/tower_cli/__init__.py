# Copyright 2015, Ansible, Inc.
# Luke Sneeringer <lsneeringer@ansible.com>
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

from __future__ import absolute_import, unicode_literals

import importlib

from src.main.resources.tower_cli import constants

__version__ = constants.VERSION


def get_resource(name):
    """Return an instance of the requested Resource class.

    Since all of the resource classes are named `Resource`, this provides
    a slightly cleaner interface for using these classes via. importing rather
    than through the CLI.
    """
    module = importlib.import_module('tower_cli.resources.%s' % name)
    return module.Resource()