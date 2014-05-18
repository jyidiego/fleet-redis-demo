#
# Description: Publishes container network information using docker API
# Name: John Yi
# Version: 0.1.0

import docker
import etcd
import socket
import string
import json
import os
import re
import threading


class DockerSocket(threading.Thread):

    ''' Using a Unix Domain Socket just returns the event strings
        events as json. 
    '''

    def __init__(self, url, call_back):
        super(DockerSocket, self).__init__()
        self.events_store = {}
        self.call_back = call_back
        self.docker_client = docker.Client(url)
        if re.search(r'unix://', url):
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            socket_file_path = string.replace(url, r'unix://', '')
            s.connect( socket_file_path )
            s.send("GET /events HTTP/1.1\n\n")
            self.file_interface = s.makefile()

    def run(self):
        while ( True ):
            line = self.file_interface.readline()
            
            #
            # Will find all events need to be able cache some of the events because
            # they could be also events that deleted the information
            #
            if re.search('^\{.*\}', line): # will find all events
                try:
                    event_dict = json.loads(line.strip())

                    if event_dict['status'] == 'destroy':
                        event = self.events_store.pop(event_dict['id'])
                    elif event_dict['status'] == 'create':
                        event = Event( event_dict, self.docker_client )
                        self.events_store[event_dict['id']] = event
                    else:
                        event = Event( event_dict, self.docker_client )

                    self.call_back(event)
                except docker.APIError, e:
                    print "docker.APIError: {0}".format(e)
                    continue 
                except KeyError, e:
                    print "KeyError: {0}".format(e)
                    continue


class Event(object):

    ''' Docker specific Event object that uses docker client
        found here: https://github.com/dsoprea/PythonEtcdClient.git
    '''

    def __init__(self, event, docker_client):
        self.event = event
        self.client = docker_client
        self.container_info = self.client.inspect_container(event['id']) 

    def get_status(self):
        return self.event['status']

    def get_id(self):
        return self.event['id']

    def get_location(self):
        for env_variable in self.container_info['Config']['Env']:
            if re.search('ETCD_SERVICES', env_variable):
                return os.path.join('/services', \
                                string.lstrip( string.split( env_variable, '=' )[1].strip(), '/'), \
                                string.lstrip( self.container_info['Name'], '/'))
        return '/services'

    def get_node(self):
        return self.container_info['HostConfig']['PortBindings']
        


class EventWatcher(object):

    ''' Setup event states to take action on.

        event_entry: { <event_status> : <class_instance_method> }
        example event_entry: {  'state' : register.publish } where register.publish is the
                                 method that get's called to start an action

    ''' 

    def __init__(self, event_map={}):
        self.event_map = event_map

    def add_event(self, event_entry):
        self.event_map.update( event_entry )

    def remove_event(self, event_status):
        return self.event_map.pop( event_status )

    def event_action(self, event):
        if event.get_status() in self.event_map:
            # event_map[event.get_status()] should refer to a method to execute
            # also use the event as an argument
            print "DEBUG: {0}".format(event.get_status())
            self.event_map[event.get_status()](event.location, event.node)


class Register(object):

    ''' Publishes and deletes entries in the Registry.
    '''

    def __init__(self, registry_client):
        self.client = registry_client

    def publish( self, location, node ):
        print "publish registry"
        self.client.node.set(location, node)

    def delete( self, location, node ):
        print "delete entry registry"

