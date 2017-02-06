#!/usr/bin/env python

from Cloud.cloudmanager import CloudManager
from Input import arginput

def main():
    cm = CloudManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'DatacenterName', 'DatastoreName', 'ClusterName', 'VMDK_Path', 'OVF_Path', 'NewName'])
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()

    cm.deployOVF()

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();