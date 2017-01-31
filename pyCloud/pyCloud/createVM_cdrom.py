#!/usr/bin/env python

from Cloud.cloudmanager import CloudManager
from Power.powermanager import PowerManager
from Hardware.hardwaremanager import HardwareManager
from Input import arginput

def main():
    cm = CloudManager()
    pm = PowerManager()
    hm = HardwareManager()

    args = arginput.getArgs(['Host', 'Username', 'Password', 'NewName', 'DatastoreName', 'Memory', 'HardDiskSize', 'HardDiskType', 'NetworkName', 'Task', 'PowerOn', 'ISO_Path'])
    arginput.addPassword(args)

    cm.setArgs(args)
    hm.setArgs(args)

    cm.connectToServer()
    conn = cm.getConnection()
    pm.setConnection(conn)
    hm.setConnection(conn)

    cm.loadVMList()
    vm = cm.createVM() # Create a very basic VM with only a CPU, RAM, a graphics card and VMCI device

    ''' Add the bare essentials to the VM: a SCSI controller, a hard disk and a NIC '''
    hm.addSCSIController(vm)
    hm.addHardDisk(vm)
    hm.addNIC(vm)
    hm.assignRandomMAC(vm)

    ''' Add a CD drive to the VM '''
    hm.addIDEController(vm)
    hm.addCDDrive(vm)

    if args.power_on != None:
        pm.turnOnVM(vm)

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();
