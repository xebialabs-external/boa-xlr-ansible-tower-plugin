#
# Copyright 2019 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#


import sys
import urllib
import com.xhaus.jyson.JysonCodec as json
from xlrelease.HttpRequest import HttpRequest

AT_RESULT_STATUS       = 200
RECORD_CREATED_STATUS  = 201

class AnsibleTowerClient(object):
    def __init__(self, httpConnection, username=None, password=None): 
        self.headers        = {}
        self.accessToken    = None
        self.refreshToken   = None
        self.httpConnection = httpConnection
        #self.useOAuth = httpConnection['useOAuth']
        if username:
           self.httpConnection['username'] = username
        if password:
           self.httpConnection['password'] = password
        self.httpRequest = HttpRequest(self.httpConnection, username, password)
        #self.sysparms = 'sysparm_display_value=%s&sysparm_input_display_value=%s' % (self.httpConnection['sysparmDisplayValue'], self.httpConnection['sysparmInputDisplayValue'])

    @staticmethod
    def create_client(httpConnection, username=None, password=None):
        return AnsibleTowerClient(httpConnection, username, password)

    def launch(self, table_name, content):
        if self.useOAuth :self.issue_token()
        servicenow_api_url = '/api/now/v1/table/%s?%s' % (table_name, self.sysparms)
        response = self.httpRequest.post(servicenow_api_url, body=content, contentType='application/json', headers = self.headers)
        if self.useOAuth :self.revoke_token()

        if response.getStatus() == RECORD_CREATED_STATUS:
            data = json.loads(response.getResponse())
            return data['result']
        else:
            self.throw_error(response)
            # End if