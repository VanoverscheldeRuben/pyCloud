#!/usr/bin/env python

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from os import system, path

from pyVmomi import vim, vmodl
import random

from Power.powermanager import PowerManager
from Power.powerstates import Powerstates
from Tools.tools import waitForTasks, getObj, getDeploymentObjects


class HardwareManager(object):
    def __init__(self):
        self.pm = PowerManager()
        self.registeredMacDir = '/home/user/.RegisteredMACs/'
        self.macParts = [0x00, 0x0c, 0x28]

    def setArgs(self, args):
        self.args = args

    def setConnection(self, hyper_conn):
        self.conn = hyper_conn

    def getMACAddressesVM(self, vm):
        macList = []

        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                macList.append(str(dev.macAddress))

        return macList

    def ajustMemory(self, vm):
        print "Adjusting memory vm..."

        spec = vim.vm.ConfigSpec()
        spec.memoryMB = int(self.args.memory)
        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])

        print "Set memory to " + str(self.args.memory) + " MB\n"

    def addSCSIController(self, vm):
        print "Creating SCSI controller..."

        spec = vim.vm.ConfigSpec()

        dev_changes = []

        ctrl_spec = vim.vm.device.VirtualDeviceSpec()
        ctrl_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        ctrl_spec.device = vim.vm.device.ParaVirtualSCSIController()
        ctrl_spec.device.busNumber = 0
        ctrl_spec.device.controllerKey = 100
        ctrl_spec.device.sharedBus = 'noSharing'
        dev_changes.append(ctrl_spec)

        spec.deviceChange = dev_changes

        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])
        print "Created SCSI controller\n"

    def addIDEController(self, vm):
        print "Creating IDE controller..."

        spec = vim.vm.ConfigSpec()

        dev_changes = []

        ctrl_spec = vim.vm.device.VirtualDeviceSpec()
        ctrl_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        ctrl_spec.device = vim.vm.device.VirtualIDEController()
        ctrl_spec.device.busNumber = 0
        ctrl_spec.device.controllerKey = 200
        dev_changes.append(ctrl_spec)

        spec.deviceChange = dev_changes

        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])
        print "Created IDE controller\n"

    def findFreeIDEController(self, vm):
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualIDEController):
                # If there are less than 2 devices attached, we can use it.
                if len(dev.device) < 2:
                    return dev
        return None

    def addUSBController(self, vm):
        print "Creating USB controller..."

        spec = vim.vm.ConfigSpec()

        dev_changes = []

        ctrl_spec = vim.vm.device.VirtualDeviceSpec()
        ctrl_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        ctrl_spec.device = vim.vm.device.VirtualUSBController()
        ctrl_spec.device.controllerKey = 300
        dev_changes.append(ctrl_spec)

        spec.deviceChange = dev_changes

        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])
        print "Created USB controller\n"

    def findUSBController(self, vm):
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualUSBController):
                return dev
        return None

    def removeUSBController(self, vm):
        print "Removing USB Controller..."

        usb = self.findUSBController(vm)

        spec = vim.vm.ConfigSpec()
        dev_changes = []
        
        dev_spec = vim.vm.device.VirtualDeviceSpec()
        dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        dev_spec.device = usb
        
        dev_changes.append(dev_spec)
        spec.deviceChange = dev_changes
        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])
    
        print "Removed USB Controller\n"

    def addCDDrive(self, vm):
        print "Creating CD drive..."

        controller = self.findFreeIDEController(vm)
        if controller != None:
            spec = vim.vm.ConfigSpec()
            dev_changes = []

            dev_spec = vim.vm.device.VirtualDeviceSpec()
            dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

            connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            connectable.allowGuestControl = True
            connectable.startConnected = True
            connectable.connected = False
            connectable.status = 'untried'

            dev_spec.device = vim.vm.device.VirtualCdrom()
            dev_spec.device.controllerKey = controller.key
            dev_spec.device.key = -1
            dev_spec.device.connectable = connectable

            dev_spec.device.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo() # Mount an ISO file to the CD drive
            objs = getDeploymentObjects(self.conn)
            dev_spec.device.backing.datastore = objs["datastore"]
            dev_spec.device.backing.fileName = self.args.iso_path

            dev_changes.append(dev_spec)
            spec.deviceChange = dev_changes
            task = vm.ReconfigVM_Task(spec=spec)
            waitForTasks(self.conn, [task])

            print "Created CD drive\n"
        else:
            print 'Unable to add CD drive, no free IDE controller available'

    def findCDDrive(self, vm):
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualCdrom):
                return dev
        return None

    def removeCDDrive(self, vm):
        print "Removing CD drive..."

        cdDrive = self.findCDDrive(vm)

        spec = vim.vm.ConfigSpec()
        dev_changes = []
        
        dev_spec = vim.vm.device.VirtualDeviceSpec()
        dev_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove
        dev_spec.device = cdDrive
        
        dev_changes.append(dev_spec)
        spec.deviceChange = dev_changes
        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])
    
        print "Removed CD drive\n"

    def addHardDisk(self, vm):
        print "Creating hard disk..."

        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        unit_number = 0
        for dev in vm.config.hardware.device:
            if hasattr(dev.backing, 'fileName'):
                unit_number = int(dev.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    print "we don't support this many disks"
                    return
            if isinstance(dev, vim.vm.device.VirtualSCSIController):
                controller = dev

        # add disk here
        dev_changes = []
        new_disk_kb = int(self.args.hard_disk_size) * 1024 * 1024

        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        dev_changes.append(disk_spec)

        spec.deviceChange = dev_changes
        #vm.ReconfigVM_Task(spec=spec)
        #print "%sGB disk added to %s" % (self.args.hard_disk_size, vm.config.name)

        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])
        print "%sGB disk added to %s\n" % (self.args.hard_disk_size, vm.config.name)

    def changeSizeThinProvisionedDisk(self, vm):
        print "Adjusting hard disk size..."

        spec = vim.vm.ConfigSpec()

        disk = self.findFreeHardDisk(vm, thinProvisioned=True) # Fetch the required hard disk

        if disk != None:
            dev_changes = []
            new_disk_kb = int(self.args.hard_disk_size) * 1024 * 1024

            disk_spec = vim.vm.device.VirtualDeviceSpec()
            disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
            disk_spec.device = disk

            if int(disk_spec.device.capacityInKB) < new_disk_kb:
                disk_spec.device.capacityInKB = new_disk_kb
                dev_changes.append(disk_spec)

                spec.deviceChange = dev_changes

                task = vm.ReconfigVM_Task(spec=spec)
                waitForTasks(self.conn, [task])
                print "%sGB disk changed to %s\n" % (self.args.hard_disk_size, vm.config.name)
            else:
                print "Unable to make the disk smaller, you can only make it larger"
        else:
            print 'No thin provisioned disk found'

    def findFreeHardDisk(self, vm, thinProvisioned=None):
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualDisk):
                if thinProvisioned == True: # Return is the device is a thin provisioned disk
                    if dev.backing.thinProvisioned:
                        return dev
                elif thinProvisioned == False: # Return is the device is not a thin provisioned disk
                    if not dev.backing.thinProvisioned:
                        return dev

        return None

    def addNIC(self, vm):        
        print "Creating NIC...."

        #add a NIC. the network Name must be set as the device name to create the NIC.
        dev_changes = []
        spec = vim.vm.ConfigSpec()
        network = self.args.network_name
        content = self.conn.RetrieveContent()

        dev_changes = []

        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        nic_spec.device = vim.vm.device.VirtualE1000()
        nic_spec.device.deviceInfo = vim.Description()
        nic_spec.device.deviceInfo.summary = 'VM Network'
        nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.useAutoDetect = False
        nic_spec.device.backing.network = getObj(content, [vim.Network], network)
        nic_spec.device.backing.deviceName = network
        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.allowGuestControl = True 
        nic_spec.device.connectable.connected = False
        nic_spec.device.connectable.status = 'untried'
        nic_spec.device.wakeOnLanEnabled = True

        dev_changes.append(nic_spec)

        spec.deviceChange = dev_changes

        task = vm.ReconfigVM_Task(spec=spec)
        waitForTasks(self.conn, [task])
        print "Created NIC\n"

    def generateMACAddress(self):
        mac = [ self.macParts[0], self.macParts[1], self.macParts[2],
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]

        return ':'.join(map(lambda x: "%02x" % x, mac))

    def assignRandomMAC(self, vm):
        powerState = self.pm.getPowerStateVM(vm)
        
        if powerState == Powerstates.PoweredOff:
            try:
                newMAC = self.generateMACAddress()
                content = self.conn.RetrieveContent()
                
                device_change = []
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        nicspec = vim.vm.device.VirtualDeviceSpec()
                        nicspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
                        nicspec.device = device
                        
                        print "Old MAC Address:\t" + str(nicspec.device.macAddress)
                        nicspec.device.addressType = 'manual'
                        nicspec.device.macAddress = str(newMAC)
                        nicspec.device.wakeOnLanEnabled = True
                        
                        nicspec.device.connectable.startConnected = True
                        nicspec.device.connectable.allowGuestControl = True
                        device_change.append(nicspec)
                        print "Added the NIC change to the list of tasks"
                        print "New MAC Address:\t" + nicspec.device.macAddress
                        
                        if self.args.task != None:
                            if self.args.task == "centos":
                                macFileName = "centos"
                                tagName = "test"
                            elif self.args.task == "ubuntu":
                                macFileName = "ubuntu"
                                tagName = "ubuntu15_test"
                            elif self.args.task == "centos_pe":
                                macFileName = "centos_pe"
                                tagName = "centos_pe_tag"
                            else:
                                print 'Task not recognized, using the default task instead'
                                macFileName = "centos"
                                tagName = "test"

                            path = self.registeredMacDir + macFileName
                            macList = open(path, "a")
                            macList.write(newMAC + "\n")
                            macList.close()

                            macList = open(path)
                            cmd = 'razor update-tag-rule --name ' + tagName + ' --force --rule \'["in", ["fact", "macaddress"]'
                            for line in macList.readlines():
                                cmd = cmd + ', "' + line.rstrip("\n") + '"'

                            cmd = cmd + "]\'"
                            os.system(cmd)
                            macList.close()

                        break

                config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
                task = vm.ReconfigVM_Task(config_spec)
                waitForTasks(self.conn, [task])
                print "Successfully changed network"
            except vmodl.MethodFault as error:
                print "Caught vmodl fault : " + error.msg
                return -1
        else:
            print "The virtual machine has to be powered off before you give it a new MAC address"

        return 0
