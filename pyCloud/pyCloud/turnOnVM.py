#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()

    #args = arginput.getServerConnectArgs()
    args = arginput.getArgs(['Host', 'Username', 'Password', 'SearchMethod', 'SearchArgument'])
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    #serv_name = arginput.getServerName()
    #vm = cm.findVMByName(serv_name)
    vm = cm.findVM()
    cm.turnOnVM(vm)

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();