#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()
    #print str(cm.generateMACAddress())

    args = arginput.getChangeMACArgs()
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    vms = cm.findVMs()
    cm.displayVMs(vms)

    cm.assignRandomMAC(vms[0])

if __name__ =='__main__':
    main();