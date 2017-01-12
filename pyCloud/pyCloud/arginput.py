#!/usr/bin/env python

import sys
'''import os.path

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))'''

import argparse

def getServerConnectArgs():
    parser = argparse.ArgumentParser(description='Process args to connect to a server.')

    parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to.')
    parser.add_argument('-o', '--port', type=int, default=22, action='store', help='Port to connect on.')
    parser.add_argument('-u', '--user', required=True, action='store', help='Username to log in with.')
    parser.add_argument('-p', '--pwd', required=False, action='store', help='Password for user.')

    args = parser.parse_args()
    return args

def getServerConnectAndSearchArgs():
    parser = argparse.ArgumentParser(description='Process args to connect to a server.')

    parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to.')
    parser.add_argument('-o', '--port', type=int, default=22, action='store', help='Port to connect on.')
    parser.add_argument('-u', '--user', required=True, action='store', help='Username to log in with.')
    parser.add_argument('-p', '--pwd', required=False, action='store', help='Password for user.')
    parser.add_argument('-m', '--search_method', required=True, action='store', help='Search method.')
    parser.add_argument('-a', '--search_argument', required=True, action='store', help='Search argument.')

    args = parser.parse_args()
    return args

def getOVFDeployArgs():
    parser = argparse.ArgumentParser(description='Process args to connect to a server.')

    parser.add_argument('-s', '--host', required=True, action='store', help='Remote host to connect to.')
    parser.add_argument('-o', '--port', type=int, default=22, action='store', help='Port to connect on.')
    parser.add_argument('-u', '--user', required=True, action='store', help='Username to log in with.')
    parser.add_argument('-p', '--pwd', required=False, action='store', help='Password for user.')
    parser.add_argument('--datacenter_name', required=False, action='store', default=None, help='Name of the Datacenter you wish to use. If omitted, the first datacenter will be used.')
    parser.add_argument('--datastore_name', required=False, action='store', default=None, help='Datastore you wish the VM to be deployed to. If left blank, VM will be put on the first datastore found.')
    parser.add_argument('--cluster_name', required=False, action='store', default=None, help='Name of the cluster you wish the VM to end up on. If left blank the first cluster found will be used')
    parser.add_argument('-v', '--vmdk_path', required=True, action='store', default=None, help='Path of the VMDK file to deploy.')
    parser.add_argument('-f', '--ovf_path', required=True, action='store', default=None, help='Path of the OVF file to deploy.')
    parser.add_argument('-n', '--new_name', required=True, action='store', default=None, help='The name of the new VM that will be deployed.')

    args = parser.parse_args()
    return args

def getServerName():
    print "What's the name of the server you want to address?"
    serv_name = str(raw_input())

    return serv_name

def addPassword(args):
    if args.pwd == None:
        print "A password is required to establish connectivity:\t"
        args.pwd = str(raw_input())