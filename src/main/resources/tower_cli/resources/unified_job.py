# Copyright 2017, Ansible by Red Hat
# Alan Rominger <arominge@redhat.com>
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

from src.main.resources.tower_cli import models


class Resource(models.Resource):
    """A resource for unified jobs."""
    cli_help = 'Combined model of projects, job templates, and others.'
    endpoint = '/unified_jobs/'
    internal = True

    name = models.Field(required=False, display=True, col_width=24)
    type = models.Field(required=False, display=True, col_width=14)
    status = models.Field(required=False, display=True, col_width=10)
    created = models.Field(required=False, display=True, col_width=24)
    elapsed = models.Field(required=False, display=True, col_width=7)
