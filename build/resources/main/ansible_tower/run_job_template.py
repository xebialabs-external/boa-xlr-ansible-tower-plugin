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


def get_resource_id(resource, name_or_id):
    if name_or_id.isdigit():
        return int(name_or_id)
    result = resource.list(name=name_or_id)
    count = int(result['count'])
    if count == 0:
        raise Exception("Resource name '%s''%s' not found " % (resource, name_or_id))
    if count > 1:
        raise Exception("Too many result for resource name '%s''%s' not found " % (resource, name_or_id))
    return int(result['results'][0]['id'])

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

        try:
            k_vars = {}
            if task_vars['inventory']:
                result = get_resource_id(get_resource('inventory'), task_vars['inventory'])
                print("* set inventory : {0}->{1}".format(task_vars['inventory'], result))
                k_vars['inventory'] = result

            if task_vars['credential']:
                result = get_resource_id(get_resource('credential'), task_vars['credential'])
                print("* set credentials : {0}->{1}".format(task_vars['credential'], result))
                k_vars['credential'] = result

            if task_vars['extraVars2']:
                vars_ = str(task_vars['extraVars2'])
                print("* set extra_vars : {0}".format(vars_))
                # TODO: manage taskPasswordToken && taskPassword (turn hidden in waiting for...)
                k_vars['extra_vars'] = [vars_]

            print("\n")
            print("```")  # started markdown code block
            res = job.launch(job_template=task_vars['jobTemplate'], monitor=False, **k_vars)

            print "Job Launch response is %s" % res


            # 2. Setup loop to check for the status of the job

            isJobPending = True

            execution_node = ""

            isJobFailed = False

            while(isJobPending):

                # Add a 2 minute sleep between the status check calls to reduce tower server load.
                time.sleep(60)

                # Get the job status
                job_status = job.status(res['id'],detail=True)
                print "Job Status is %s" % job_status
                execution_node = job_status['execution_node']
                isJobFailed = job_status['failed']

                if execution_node == "":
                    ## Restart the monitoring loop and loop until we have an execution_node or the job status is failed.
                    isJobPending = True
                    #Put in a circuit breaker if the job status is failed or canceled or error, we don't need to keep loopin
                    #The 'failed' property for the Tower job is set to 'true' for status = failed, canceled, error
                    if (isJobFailed):
                        isJobPending = False
                        break

                        # 3. We need to monitor against the 'execution_node', since this is where Tower stores the

                        # stdout content (other nodes in the load balancer will not be able to respond with the stdout)

                        #The execution_node only populates into the job api data once the job status is running (not pending)

                        # If we have an execution_node, we can start monitoring against that execution node where the

                        #stdout will be present.

                else:
                    k_vars = {}
                    k_vars['execution_node'] = execution_node
                    job_monitor = job.monitor(res['id'],interval=5,**k_vars)
                    print "Job Monitor result is %s" % job_monitor

                    isJobPending = False

        finally:
            print("```")
            print("\n")  # end markdown code block

        globals()['jobId'] = res['id']
        globals()['jobStatus'] = res['status']

        print("* [Job %s Link](%s/#/jobs/%s)" % (res['id'], task_vars['tower_server']['url'], res['id']))

        if task_vars['stopOnFailure'] and not res['status'] == 'successful':
            raise Exception("Failed with status %s" % res['status'])


if __name__ == '__main__' or __name__ == '__builtin__':
    process(locals())
