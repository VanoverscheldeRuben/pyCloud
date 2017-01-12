#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()

    args = arginput.getServerConnectAndSearchArgs()
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    vms = cm.findVMs()
    #cm.displayMACAddressesVMs(vms)

    for vm in vms:
        print str(cm.getMACAddressesVM(vm))

if __name__ =='__main__':
    main();