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
import time
import json
from xlrelease.HttpRequest import HttpRequest

RECORD_FOUND_STATUS  = 200
RECORD_CREATED_STATUS  = 201
AUTH_ERROR_STATUS = 401

class AnsibleTowerClient(object):
    def __init__(self, httpConnection, username=None, password=None): 
        self.headers        = {"Accept": "application/json"}
        self.accessToken    = None
        self.refreshToken   = None
        self.httpConnection = httpConnection
        if username:
           self.httpConnection['username'] = username
        if password:
           self.httpConnection['password'] = password
        self.httpRequest = HttpRequest(self.httpConnection, username, password)

    @staticmethod
    def create_client(httpConnection, username=None, password=None):
        return AnsibleTowerClient(httpConnection, username, password)

    def launch(self, jobTemplate, content):
        tower_api_url =  '/api/v2/job_templates/%s/launch/' % jobTemplate
        retryCounter = 0
        success = False
        while(retryCounter < 5 and not success):
            response = self.httpRequest.post(tower_api_url, body=content, contentType='application/json', headers = self.headers)

            if response.getStatus() == RECORD_CREATED_STATUS:
                success = True
                return response.getResponse()
                break
            elif response.getStatus() == AUTH_ERROR_STATUS:
                retryCounter+=1
                time.sleep(60)
            else:
                self.throw_error(response)
            # End if
    # End launch

    def status(self, jobId):
        tower_api_url = '/api/v2/jobs/%s/' % jobId
        retryCounter = 0
        success = False
        print "Tower API URL = %s " % (tower_api_url)
        while(retryCounter < 5 and not success):
            response = self.httpRequest.get(tower_api_url, contentType='application/json', headers = self.headers)

            if response.getStatus() == RECORD_FOUND_STATUS:
                success = True
                return response
                break
            elif response.getStatus() == AUTH_ERROR_STATUS:
                retryCounter+=1
                time.sleep(60)
            else:
                print "find_record error %s" % (response)
                self.throw_error(response)
            # End if

    # End status

    def stdout(self, jobId):
        tower_api_url = '/api/v2/jobs/%s/stdout?format=json' % jobId
        retryCounter = 0
        success = False
        print "Tower API URL = %s " % (tower_api_url)
        while(retryCounter < 5 and not success):
            response = self.httpRequest.get(tower_api_url, contentType='application/json', headers = self.headers)

            if response.getStatus() == RECORD_FOUND_STATUS:
                success = True
                return response
                break
            elif response.getStatus() == AUTH_ERROR_STATUS:
                retryCounter+=1
                time.sleep(60)
            else:
                print "find_record error %s" % (response)
                self.throw_error(response)
                # End if

    # End status


    def throw_error(self, response):
        print "Error from Tower, HTTP Return: %s\n" % (response.getStatus())
        print "Detailed error: %s\n" % response.response
        sys.exit(1)

    # End throw_error

    def print_error(self, response):
        if type(response) is dict:
            outStr =   "| Status  | %s |\n" % ( response["status"] )
            outStr = "%s| Message | %s |\n" % ( outStr, response["error"]["message"] )
            outStr = "%s| Detail  | %s |\n" % ( outStr, response["error"]["detail"] )
            return outStr
        # End if
        return response
        #End  print_error