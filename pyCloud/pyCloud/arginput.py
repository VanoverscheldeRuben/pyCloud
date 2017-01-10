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

def getServerName():
    print "What's the name of the server you want to address?"
    serv_name = str(raw_input())

    return serv_name

def addPassword(args):
    if args.pwd == None:
        print "A password is required to establish connectivity:\t"
        args.pwd = str(raw_input())