#!/usr/bin/env python

from Cloud.cloudmanager import CloudManager
from Hardware.hardwaremanager import HardwareManager
from Input import arginput

def main():
    cm = CloudManager()
    hm = HardwareManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'SearchMethod', 'SearchArgument', 'Memory'])
    arginput.addPassword(args)

    cm.setArgs(args)
    hm.setArgs(args)

    cm.connectToServer()
    conn = cm.getConnection()
    hm.setConnection(conn)

    cm.loadVMList()

    vm = cm.findVM()

    if vm != None:
        ''' Add memory of the VM '''
        hm.ajustMemory(vm)
    else:
        print "No VM found"

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();