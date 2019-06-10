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


#

# Launches a job and monitors its progress using the Tower CLI

# Set up a loop for the job monitor process

# If the job monitor process fails because stdout can't be found or

# the 'Invalid Tower authentication credential' error

# we check the actual status of the job, if its still running, we restart monitoring

# otherwise we gracefully exit

#

if tower_server is None:
    print "No server provided."
    sys.exit(1)


tower_serverUrl = tower_server['url']

credentials = CredentialsFallback(tower_server, username, password).getCredentials()

# Construct the payload.

content = {}

extraVarData = json.dumps(extraVars)
extraVarJson = json.loads(extraVarData)

extraVarJson['taskPassword'] = taskPassword
extraVarJson['taskPasswordToken'] = taskPasswordToken

if credential:
    content['credential'] = credential

if inventory:
    content['inventory'] = inventory

content ['extra_vars'] = extraVarJson

print "Sending payload %s" % content

if jobTemplateId is None or jobTemplateId == "" and jobTemplate is not None:
    tower_serverAPIGetTemplateUrl = tower_serverUrl + '/api/v2/system_job_templates/'
    tower_serverAPIGetTemplateResponse = XLRequest(tower_serverAPIGetTemplateUrl, 'GET', content, credentials['username'], credentials['password'], 'application/json').send()
    if tower_serverAPIGetTemplateResponse is not None:
        try:
            data = json.loads(tower_serverAPIGetTemplateResponse.read())
            print "Tower job templates response is %s" % data
            for result in data["results"]:
                if result["name"]== jobTemplate:
                    jobTemplateId = result["id"]
                    print "Found Job template ID %s for Job Template name %s in Tower." % (result["id"], jobTemplate)
        except ValueError, e:
            print "Tower get job templates response is not a valid json %s" % tower_serverAPIGetTemplateResponse.read()

    else:
        print "Failed to get job templates in tower"
        tower_serverAPIGetTemplateResponse.errorDump()
        sys.exit(1)



tower_serverAPILaunchUrl = tower_serverUrl + '/api/v2/job_templates/%s/launch/' % jobTemplateId

tower_serverLaunchResponse = XLRequest(tower_serverAPILaunchUrl, 'POST', content, credentials['username'], credentials['password'], 'application/json').send()

jobId = ''


if tower_serverLaunchResponse is not None:
    try:
        data = json.loads(tower_serverLaunchResponse.read())
        print "Tower job launch response is %s" % data
        jobId = data["id"]
        print "Started %s in Tower." % (jobId)
    except ValueError, e:
        print "Tower job launch response is not a valid json %s" % tower_serverLaunchResponse.read()

else:
    print "Failed to start job in tower"
    tower_serverLaunchResponse.errorDump()
    sys.exit(1)

jobStatus = ''
executionNode = ''
isJobFailed = False
isJobPending = True

while(isJobPending):
    #We need to detect when the job status is in any mode other than 'pending'

    #In pending mode, the execution_node value is not yet populated, so we

    #need to wait unitl the execution_node value is populated.

    # Add a 3 second sleep between the status check calls to reduce tower server load.

    time.sleep(3)
    tower_serverAPIStatusUrl = tower_serverUrl + '/api/v2/jobs/%s/' % jobId

    tower_serverStatusResponse = XLRequest(tower_serverAPIStatusUrl, 'GET', content, credentials['username'], credentials['password'], 'application/json').send()

    if tower_serverStatusResponse is not None:
        try:
            data = json.loads(tower_serverStatusResponse.read())
            jobStatus = data["status"]
            isJobFailed = data["failed"]
            executionNode = data["execution_node"]
            print "Status for Job %s in Tower is %s." % (jobId,jobStatus)
        except ValueError, e:
            print "Tower job launch response is not a valid json %s" % tower_serverStatusResponse.read()
    else:
        print "Failed to get status from tower"
        tower_serverStatusResponse.errorDump()
        sys.exit(1)

    if executionNode == "" and not isJobFailed:
        ## Restart the monitoring loop and loop until we have an execution_node or the job status is failed.
        isJobPending = True
        #Put in a circuit breaker if the job status is failed or canceled or error, we don't need to keep loopin
        #The 'failed' property for the Tower job is set to 'true' for status = failed, canceled, error
        if (isJobFailed):
            isJobPending = False
            break


print "Execution node is : %s" % execution_node
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

    try:
        tower_serverAPIStdOutUrl = 'https://' + executionNode + '/api/v2/jobs/%s/stdout?format=json' % jobId
        tower_serverAPIStdOutResponse = XLRequest(tower_serverAPIStdOutUrl, 'GET', content, credentials['username'], credentials['password'], 'application/json').send()

        if tower_serverAPIStdOutResponse is not None:
            data = json.loads(tower_serverAPIStdOutResponse.read())
            stdout = data["content"]

            print "Status in Tower is %s." % tower_serverAPIStdOutResponse.read()
        else:
            print "Failed to get status from tower"
            tower_serverAPIStdOutResponse.errorDump()
            sys.exit(1)
    except e:
        print "Tower stdout response error %s" % tower_serverAPIStdOutResponse.read()


print("* [Job %s Link](%s/#/jobs/%s)" % (jobId, tower_server['url'], jobId))

if stopOnFailure and not jobStatus == 'successful':
    raise Exception("Failed with status %s" % jobStatus)