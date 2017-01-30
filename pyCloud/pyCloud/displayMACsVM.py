#!/usr/bin/env python

from Cloud.cloudmanager import CloudManager
from Hardware.hardwaremanager import HardwareManager
from Input import arginput

def main():
    cm = CloudManager()
    hm = HardwareManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'SearchMethod', 'SearchArgument'])
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    vm = cm.findVM()
    macList = hm.getMACAddressesVM(vm)

    for mac in macList:
        print mac

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();