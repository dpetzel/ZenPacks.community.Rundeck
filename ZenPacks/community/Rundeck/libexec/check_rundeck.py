#!/usr/bin/env python
import logging
import urllib2
import sys
from optparse import OptionParser
import xml.etree.ElementTree as ET

logging.basicConfig()
logger = logging.getLogger('.'.join(['zen', "check_rundeck"]))


# What version of the Rundeck API should be used
API_VERSION=6

class ZenossRundeckPlugin(object):
    '''
    Zenoss Plugin for interacting with Rundeck
    
    Attributes:
        host: A String representing the hostname or IP of the Rundeck host
        port: An Integer representing the tcp port at which the API is located
        token: A String used as the API token used in place of password auth
        metrics: A *List of Tuples*, where each tuple is a key/value pair
            The first element in the tuple is a data point name
            The second element is the numerical value for that data point
    '''
    def __init__(self, host, port, token, scheme):
        self.host = host
        self.port = port
        self.token = token
        self.scheme = scheme.lower()
        
        self.metrics = []
        
    def api_call(self, rel_url):
        '''
        Make a call to the Rundeck API and return parsed response
        
        Args:
            rel_url: A relative URL string for the API call.
                This will automatically appended to the API base URL
        Returns:
            An instance of xml.etree.ElementTree.Element
        '''
        base_url = "{0}://{1}:{2}/api/{3}".format(self.scheme, self.host,
                                                  self.port, API_VERSION)
        if rel_url.startswith("/"):
            url = "{0}{1}".format(base_url, rel_url)
        else:
            url = "{0}/{1}".format(base_url, rel_url)
        
        try:
            req = urllib2.Request(url)
            req.add_header('X-Rundeck-Auth-Token', self.token)
            resp = urllib2.urlopen(req)
            resp_content = resp.read()
            return ET.fromstring(resp_content)
        except IOError as e:
            print "Rundeck API connection failed"
            sys.exit(1)
            
        if resp.getcode() == 403:
            logger.error("API Authentication failure")
            sys.exit(1)
            
    def get_system_metrics(self):
        '''
        Extract system stats from the API
        '''
        xml = self.api_call("/system/info")
        self.metrics.append(('active_threads', 
                    xml.findall("./system/stats/threads/active")[0].text))
        self.metrics.append(('jobs_running', 
                    xml.findall("./system/stats/scheduler/running")[0].text))
        self.metrics.append(('load_average', 
                    xml.findall("./system/stats/cpu/loadAverage")[0].text))
        self.metrics.append(('processors', 
                    xml.findall("./system/stats/cpu/processors")[0].text))
        self.metrics.append(('uptime', 
                    xml.findall("./system/stats/uptime")[0].get('duration')))
        self.metrics.append(('memory_max', 
                    xml.findall("./system/stats/memory/max")[0].text))
        self.metrics.append(('memory_free', 
                    xml.findall("./system/stats/memory/free")[0].text))
        self.metrics.append(('memory_total', 
                    xml.findall("./system/stats/memory/total")[0].text))
        
    def get_project_metrics(self):
        '''
        Collect stats related to projects
        '''
        xml = self.api_call("projects")
        self.metrics.append(('projects', xml.find("projects").get('count')))
        projects = xml.findall("./projects/project")
        
        job_count = 0
        
        # Now look at each project and count the number of jobs
        for project in projects:
            project_name = project.find('name').text
            jobsxml = self.api_call("project/{0}/jobs".format(project_name))
            job_count += int(jobsxml.find('jobs').get('count'))
        
        self.metrics.append(('jobs_total', str(job_count)))
        
    
    def run(self):

        self.get_system_metrics()
        self.get_project_metrics()
            
        print "Rundeck OK|%s" % (' '.join(map('='.join, self.metrics)),)


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-H', '--host', dest='host',
        help='Hostname of Rundeck server')
    parser.add_option('-p', '--port', dest='port', default='4440',
        help='Port that Rundeck API is listening on')
    parser.add_option('-T', '--token', dest='token',
        help='API Token')
    parser.add_option('-S', '--scheme', dest='scheme', choices=['http', 'https'],
        default='http', help='http or https')
    options, args = parser.parse_args()

    if not options.host:
        print "You must specify the host parameter."
        sys.exit(1)

    cmd = ZenossRundeckPlugin(options.host, options.port, 
                              options.token, options.scheme)
    cmd.run()