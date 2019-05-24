#
# Copyright 2019 XEBIALABS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

from tower_cli import get_resource
from ansible_tower.connect_util import session
import time


#

# Launches a job and monitors its progress using the Tower CLI

# Set up a loop for the job monitor process

# If the job monitor process fails because stdout can't be found or

# the 'Invalid Tower authentication credential' error

# we check the actual status of the job, if its still running, we restart monitoring

# otherwise we gracefully exit

#


def process(task_vars):
    with session(task_vars['tower_server'], task_vars['username'], task_vars['password']):
        job = get_resource('job')
        job_status = ""
        inventory = None
        try:
            print("\n```")  # started markdown code block
            extraVars = task_vars['extraVars']
            if task_vars['credential']:
                #print("* set credentials : {0}->{1}".format(task_vars['credential'], result))
                extraVars.append(u"credential: %s" % task_vars['credential'])
            preparedExtraVars = map(lambda v: v.replace(taskPasswordToken, taskPassword),extraVars)

            if task_vars['inventory']:
                #print("* set inventory : {0}->{1}".format(task_vars['inventory'], result))
                inventory = task_vars['inventory']
                res = job.launch(job_template=task_vars['jobTemplate'], monitor=False, extra_vars=preparedExtraVars, inventory=inventory)
            else:
                res = job.launch(job_template=task_vars['jobTemplate'], monitor=False, extra_vars=preparedExtraVars)


            print("\n")
            print("```")  # started markdown code block
            #res = job.launch(job_template=task_vars['jobTemplate'], monitor=False, **k_vars)
            job_status = res['status']
            print "Job Launch response is %s" % res
            print("```")
            print("\n")  # end markdown code block


            # 2. Setup loop to check for the status of the job

            isJobPending = True

            execution_node = ""

            isJobFailed = False

            while(isJobPending):

                #We need to detect when the job status is in any mode other than 'pending'

                #In pending mode, the execution_node value is not yet populated, so we

                #need to wait unitl the execution_node value is populated.

                # Add a 3 second sleep between the status check calls to reduce tower server load.
                time.sleep(3)

                # Get the job status
                job_status_res = job.status(res['id'],detail=True)
                print "Job Status is %s" % job_status_res
                print("```")
                print("\n")  # end markdown code block
                execution_node = job_status_res['execution_node']
                job_status = job_status_res['status']
                isJobFailed = job_status_res['failed']

                if execution_node == "":
                    ## Restart the monitoring loop and loop until we have an execution_node or the job status is failed.
                    isJobPending = True
                    #Put in a circuit breaker if the job status is failed or canceled or error, we don't need to keep loopin
                    #The 'failed' property for the Tower job is set to 'true' for status = failed, canceled, error
                    if (isJobFailed):
                        isJobPending = False
                        continue
                else: # We got the execution node
                    isJobPending = False
                    break

            print "Execution node is : %s" % execution_node
            print("\n")

            # 3. We need to monitor against the 'execution_node', since this is where Tower stores the

            # stdout content (other nodes in the load balancer will not be able to respond with the stdout)

            #The execution_node only populates into the job api data once the job status is running (not pending)

            # If we have an execution_node, we can start monitoring against that execution node where the

            #stdout will be present.

            if not execution_node == "" and not isJobFailed:
                #Check if execution_node is 'localhost'.  This occurs when the job is executing on the legacy Tower instances,

                #since they don't have scaled nodes, Tower records the execution_node as 'localhost'.

                #In this case, we don't need to use the -h option to specify the specific execution_node
                if execution_node == "localhost" or task_vars['isDMZ']:
                    ## TODO  Revert the execution_node back to the supplied cli_tower_host value (can be blank)
                    print "Revert the execution_node back to the supplied cli_tower_host value (can be blank)"
                    print("\n")
                    cli_tower_host = task_vars['tower_server']['url'].split("//")[1]
                    execution_node = cli_tower_host
                    print "cli_tower_host is %s " % cli_tower_host
                else:
                    print "Found Tower job execution_node = %s" % execution_node
                    print("\n")

            # We start up monitoring using the specific execution_node (scaled) or the cli_tower_host value (legacy)
                k_vars = {}
                k_vars['execution_node'] = execution_node
                job_monitor = job.monitor(res['id'],interval=5,**k_vars)
                print "Job Monitor result is %s" % job_monitor
                print("\n")
                print "Job status is %s " % job_monitor['status']
                print("\n")
                job_status = job_monitor['status']

            else: # This is an error condition, we don't know what to monitor
                print "Tower job execution_node not found... unable to setup job monitoring on job_id %s " % res['id']
                print("\n")
                if isJobFailed:
                    raise Exception("Failed with status %s" % res['status'])

        finally:
            print("```")
            print("\n")  # end markdown code block

        globals()['jobId'] = res['id']
        globals()['jobStatus'] = job_status

        print("* [Job %s Link](%s/#/jobs/%s)" % (res['id'], task_vars['tower_server']['url'], res['id']))

        if task_vars['stopOnFailure'] and not job_status == 'successful':
            raise Exception("Failed with status %s" % job_status)


if __name__ == '__main__' or __name__ == '__builtin__':
    process(locals())
