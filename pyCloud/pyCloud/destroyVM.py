#!/usr/bin/env python

from Cloud.cloudmanager import CloudManager
from Input import arginput

def main():
    cm = CloudManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'SearchMethod', 'SearchArgument'])
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    vm = cm.findVM()

    if vm != None:
        cm.destroyVM(vm)
    else:
        print "No VM found"

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();