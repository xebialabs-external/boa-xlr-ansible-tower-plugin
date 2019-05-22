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
from src.main.jython.ansible_tower.connect_util import session

from src.main.resources.tower_cli import get_resource


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

def get_job_details(resource, name_or_id):
    if name_or_id.isdigit():
        return int(name_or_id)
    result = resource.list(name=name_or_id)
    count = int(result['count'])
    if count == 0:
        raise Exception("Resource name '%s''%s' not found " % (resource, name_or_id))
    if count > 1:
        raise Exception("Too many result for resource name '%s''%s' not found " % (resource, name_or_id))
    return int(result['results'][0]['id'])

def process(task_vars):
    with session(task_vars['tower_server'], task_vars['username'], task_vars['password']):
        job = get_resource('job')
        inventory = None        
        try:
            print("\n```")  # started markdown code block
            extraVars = task_vars['extraVars']           
            if task_vars['credential']:
                extraVars.append(u"credential: %s" % task_vars['credential'])
            preparedExtraVars = map(lambda v: v.replace(taskPasswordToken, taskPassword),extraVars)

            if task_vars['inventory']:
                inventory = task_vars['inventory']
                res = job.launch(job_template=task_vars['jobTemplate'], monitor=False, extra_vars=preparedExtraVars, inventory=inventory)
                print "Job launch response --> %s" % res
            else:
                res = job.launch(job_template=task_vars['jobTemplate'], monitor=False, extra_vars=preparedExtraVars)
                print "Job launch response --> %s" % res

            # 2. Setup loop to check for the status of the job

            isJobPending = True

            execution_node = ""

            isJobFailed = False

            while(isJobPending):

                # Add a 2 minute sleep between the status check calls to reduce tower server load.
                time.sleep(120)

                # Get the job status
                job_status = job.status(res['id'],detail=True)
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
                    else:
                        isJobPending = True
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
                    print job_monitor


        finally:
            print("```\n")  # end markdown code block

        globals()['jobId'] = res['id']
        globals()['jobStatus'] = res['status']
        print("[Job %s Link](%s/#jobs/%s)" % (res['id'], task_vars['tower_server']['url'], res['id']))
        if task_vars['stopOnFailure'] and not res['status'] == 'successful':
            raise Exception("Failed with status %s" % res['status'])

if __name__ == '__main__' or __name__ == '__builtin__':
    process(locals())

