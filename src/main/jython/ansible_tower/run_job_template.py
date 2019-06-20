#
# Copyright 2019 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import time
import json
import sys
import ast
from xlrelease.HttpRequest import HttpRequest
from ansible_tower.AnsibleTowerClient import AnsibleTowerClient

#

# Launches a job and monitors its progress using the Tower CLI

# Set up a loop for the job monitor process

# If the job monitor process fails because stdout can't be found or

# the 'Invalid Tower authentication credential' error

# we check the actual status of the job, if its still running, we restart monitoring

# otherwise we gracefully exit

#
#Get global variables.
ansiblePluginRetryCounter = 5
ansiblePluginAuthErrorRetryInterval = 60
ansiblePluginJobStatusCheckInterval = 10
global_vars = configurationApi.globalVariables
for var in global_vars:
    if var.key == "global.ansiblePluginJobStatusCheckInterval":
        ansiblePluginJobStatusCheckInterval = var.value
    if var.key == "global.ansiblePluginRetryCounter":
        ansiblePluginRetryCounter = var.value
    if var.key == "global.ansiblePluginAuthErrorRetryInterval":
        ansiblePluginAuthErrorRetryInterval = var.value

if tower_server is None:
    print "No server provided."
    sys.exit(1)


tower_serverUrl = tower_server['url']


# Construct the payload.

contentRaw = {}

extraVarsDict = {}
for data in extraVars:
    if data.startswith('{'):
        tmpData = ast.literal_eval(data)
        extraVarsDict.update(tmpData)
    else:
        i = data.split(': ')
        if len(i)>1:
            extraVarsDict[i[0]] = i[1]

extraVarsDict['taskPassword'] = taskPassword
extraVarsDict['taskPasswordToken'] = taskPasswordToken

if credential:
    contentRaw['credential'] = credential

if inventory:
    contentRaw['inventory'] = inventory

contentRaw['extra_vars'] = extraVarsDict

content = json.dumps(contentRaw)

#print "Sending payload %s" % content


towerClient = AnsibleTowerClient.create_client(tower_server, username, password)
tower_serverLaunchResponse = towerClient.launch(jobTemplate, content,ansiblePluginRetryCounter,ansiblePluginAuthErrorRetryInterval)

jobId = ''


if tower_serverLaunchResponse is not None:
    print("\n")
    try:
        data = json.loads(tower_serverLaunchResponse)
        print "Tower job launch response is %s" %  data
        jobId = data["id"]
        print "Started %s in Tower." % (jobId)
    except ValueError, e:
        print "Tower job launch response is not a valid json %s" % tower_serverLaunchResponse
    except KeyError, e:
        print "Tower job launch response is not a valid json %s" % tower_serverLaunchResponse

else:
    print "Failed to start job in tower"
    sys.exit(1)

print("\n")

jobStatus = ''
execution_node = ''
isJobFailed = False
isJobPending = True

while(isJobPending):
    #We need to detect when the job status is in any mode other than 'pending'

    #In pending mode, the execution_node value is not yet populated, so we

    #need to wait unitl the execution_node value is populated.

    # Add a 3 second sleep between the status check calls to reduce tower server load.

    time.sleep(ansiblePluginJobStatusCheckInterval)

    if(execution_node == ""):
        tower_serverStatusResponse = towerClient.status(jobId,ansiblePluginRetryCounter,ansiblePluginAuthErrorRetryInterval)

    else:
        print "Found Tower job execution_node = %s" % execution_node
        print("\n")
        if execution_node == "localhost" or isDMZ:
            #Revert the execution_node back to the supplied cli_tower_host value (can be blank)
            print "Revert the execution_node back to the supplied cli_tower_host value (can be blank)"
            print("\n")
            cli_tower_host = tower_server['url'].split("//")[1]
            execution_node = cli_tower_host
            print "cli_tower_host is %s " % cli_tower_host

        tower_serverAPIStatusUrl = 'https://' + execution_node
        towerClient = AnsibleTowerClient.create_client({'url':tower_serverAPIStatusUrl}, tower_server['username'], tower_server['password'])
        tower_serverStatusResponse = towerClient.status(jobId,ansiblePluginRetryCounter,ansiblePluginAuthErrorRetryInterval)


    if tower_serverStatusResponse is not None:
        print("\n")
        try:
            data = json.loads(tower_serverStatusResponse.getResponse())
            jobStatus = data["status"]
            isJobFailed = data["failed"]
            execution_node = data["execution_node"]
            print "Status for Job %s in Tower is %s." % (jobId,jobStatus)
        except ValueError, e:
            print "Tower job status response is not a valid json %s" % tower_serverStatusResponse.response
        except KeyError, e:
            print "Tower job status response is not a valid json %s" % tower_serverStatusResponse.response
    else:
        print "Failed to get status from tower"
        sys.exit(1)

    if isJobFailed or jobStatus == 'successful':
        isJobPending = False
        break



print("\n")


# 3. We need to monitor against the 'execution_node', since this is where Tower stores the

# stdout content (other nodes in the load balancer will not be able to respond with the stdout)

#The execution_node only populates into the job api data once the job status is running (not pending)

# If we have an execution_node, we can start monitoring against that execution node where the

#stdout will be present.

if not execution_node == "":
#Check if execution_node is 'localhost'.  This occurs when the job is executing on the legacy Tower instances,

#since they don't have scaled nodes, Tower records the execution_node as 'localhost'.

#In this case, we don't need to use the -h option to specify the specific execution_node

    if execution_node == "localhost" or isDMZ:
    #Revert the execution_node back to the supplied cli_tower_host value (can be blank)
        print "Revert the execution_node back to the supplied cli_tower_host value (can be blank)"
        print("\n")
        cli_tower_host = tower_server['url'].split("//")[1]
        execution_node = cli_tower_host
        print "cli_tower_host is %s " % cli_tower_host
    else:
        print "Found Tower job execution_node = %s" % execution_node
        print("\n")

        # We start up monitoring using the specific execution_node (scaled) or the cli_tower_host value (legacy)

    tower_serverAPIStdOutUrl = 'https://' + execution_node

    towerClient = AnsibleTowerClient.create_client({'url':tower_serverAPIStdOutUrl}, tower_server['username'], tower_server['password'])
    tower_serverAPIStdOutResponse = towerClient.stdout(jobId,ansiblePluginRetryCounter,ansiblePluginAuthErrorRetryInterval)

    if tower_serverAPIStdOutResponse is not None:
        print("\n")
        try:
            data = json.loads(tower_serverAPIStdOutResponse.getResponse())
            stdout = data["content"]

            print "Stdout log from Tower is %s." % stdout

        except ValueError, e:
            print "Tower stdout response error %s" % tower_serverAPIStdOutResponse.response
        except KeyError, e:
            print "Tower stdout response error %s" % tower_serverAPIStdOutResponse.response
    else:
        print "Failed to get stdout from tower"
        sys.exit(1)

print("\n")

print("* [Job %s Link](%s/#/jobs/%s)" % (jobId, tower_server['url'], jobId))

if stopOnFailure and isJobFailed:
    print("\n")
    raise Exception("Failed with status %s" % jobStatus)