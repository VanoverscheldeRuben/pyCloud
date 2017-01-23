#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'NewName', 'DatastoreName', 'HardDiskSize', 'HardDiskType', 'NetworkName', 'Task'])
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    vm = cm.createVM()

    cm.addSCSIController(vm)
    cm.addHardDisk(vm)
    cm.addNIC(vm)
    cm.assignRandomMAC(vm)
    cm.turnOnVM(vm)

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();
