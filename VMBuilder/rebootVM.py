#!/usr/bin/env python

from Cloud.cloudmanager import CloudManager
from Power.powermanager import PowerManager
from Input import arginput

def main():
    cm = CloudManager()
    pm = PowerManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'SearchMethod', 'SearchArgument'])
    arginput.addPassword(args)

    cm.setArgs(args)
    
    cm.connectToServer()
    conn = cm.getConnection()
    pm.setConnection(conn)

    cm.loadVMList()

    vm = cm.findVM()
    pm.rebootVM(vm)

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();