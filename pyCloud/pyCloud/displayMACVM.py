#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'SearchMethod', 'SearchArgument'])
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    vm = cm.findVM()
    print str(cm.getMACAddressesVM(vm))
    #cm.displayMACAddressesVMs(vms)

    '''for vm in vms:
        print str(cm.getMACAddressesVM(vm))'''

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();