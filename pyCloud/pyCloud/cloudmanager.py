#!/usr/bin/env python

import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from os import system, path
from sys import exit
from threading import Thread
from time import sleep

from pyVim import connect

import pyVmomi
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect

import arginput

import atexit
import ssl

import json
import random

import tasks

from powerstates import Powerstates

class CloudManager(object):
    def __init__(self):
        self.maxVMDepth = 10
        self.createEmptyCert()
        self.macParts = [0x00, 0x0c, 0x29]

    def createEmptyCert(self):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        self.context.verify_mode = ssl.CERT_NONE

    def setArgs(self, args):
        self.args = args

    def connectToServer(self):
        try: # First try to connect with a valid certificate
            self.conn = SmartConnect(host=self.args.host, user=self.args.user, pwd=self.args.pwd)
        except: # No valid certificate, try without one
            self.conn = SmartConnect(host=self.args.host, user=self.args.user, pwd=self.args.pwd, sslContext=self.context)

    def disconnectFromServer(self):
        Disconnect(self.conn)

    def getPowerStateVM(self, vm):
        return str(vm.summary.runtime.powerState)

    def loadVMList(self):
        content = self.conn.RetrieveContent()
        for child in content.rootFolder.childEntity:
            if hasattr(child, 'vmFolder'):
                datacenter = child
                vmFolder = datacenter.vmFolder
                self.vmList = vmFolder.childEntity

    def findVM(self):
        if self.vmList == None: # Load all VMs in case that hasn't happened already
            self.loadVMList()

        if self.args.search_method == 'name':
            return self.findVMByName(self.args.search_argument)
        elif self.args.search_method == 'ip':
            return self.findVMByIP(self.args.search_argument)

    def findVMByName(self, name):
        for vm in self.vmList:
            summary = vm.summary

            if name == str(summary.config.name):
                return vm

    def findVMByIP(self, ip):
        foundVM = []

        for vm in self.vmList:
            summary = vm.summary

            if ip == str(summary.guest.ipAddress):
                foundVM.append(vm)
                return foundVM

    def displayVMs(self, list=None):
        if list == None:
            list = self.vmList

        for vm in list:
            self.displayVM(vm)

    def getMACAddressesVM(self, vm):
        for dev in vm.config.hardware.device:
            if isinstance(dev, vim.vm.device.VirtualEthernetCard):
                return str(dev.macAddress)

    def displayVM(self, vm, depth=1):
        if hasattr(vm, 'childEntity'):
            if depth > self.maxVMDepth:
                return

            vms = vm.childEntity
            for i in vms:
                displayVM(i, depth+1)

        summary = vm.summary
        print "Name:\t" + str(summary.config.name)
        print "Path:\t" + str(summary.config.vmPathName)
        print "Guest:\t" + str(summary.config.guestFullName)

        annotation = summary.config.annotation
        if annotation != None and annotation != "":
            print "Annotation:\t" + str(annotation)

        print "State:\t" + str(summary.runtime.powerState)

        if summary.guest != None:
            ip = summary.guest.ipAddress
            if ip != None and ip != "":
                print "IP:\t" + str(ip)

        if summary.runtime.question != None:
            print "Question:\t" + summary.runtime.question.text

        print ""

    def WaitForTasks(self, tasks):
       """
       Given the service instance self.conn and tasks, it returns after all the
       tasks are complete
       """
    
       pc = self.conn.content.propertyCollector
    
       taskList = [str(task) for task in tasks]
    
       # Create filter
       objSpecs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                                                                for task in tasks]
       propSpec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                             pathSet=[], all=True)
       filterSpec = vmodl.query.PropertyCollector.FilterSpec()
       filterSpec.objectSet = objSpecs
       filterSpec.propSet = [propSpec]
       filter = pc.CreateFilter(filterSpec, True)
    
       try:
          version, state = None, None
    
          # Loop looking for updates till the state moves to a completed state.
          while len(taskList):
             update = pc.WaitForUpdates(version)
             for filterSet in update.filterSet:
                for objSet in filterSet.objectSet:
                   task = objSet.obj
                   for change in objSet.changeSet:
                      if change.name == 'info':
                         state = change.val.state
                      elif change.name == 'info.state':
                         state = change.val
                      else:
                         continue
    
                      if not str(task) in taskList:
                         continue
    
                      if state == vim.TaskInfo.State.success:
                         # Remove task from taskList
                         taskList.remove(str(task))
                      elif state == vim.TaskInfo.State.error:
                         raise task.info.error
             # Move to next version
             version = update.version
       finally:
          if filter:
             filter.Destroy()

    def turnOnVM(self, vm):
        powerState = self.getPowerStateVM(vm)

        if powerState == Powerstates.PoweredOff:
            tasks = [vm.PowerOn()]
            self.WaitForTasks(tasks)
        else:
            print "Unable to start vm, " + str(vm.summary.config.name) + " is already turned on!"

    def turnOffVM(self, vm):
        powerState = self.getPowerStateVM(vm)

        if powerState == Powerstates.PoweredOn:
            tasks = [vm.PowerOff()]
            self.WaitForTasks(tasks)
        else:
            print "Unable to start vm, " + str(vm.summary.config.name) + " is already turned off!"

    def rebootVM(self, vm):
        tasks = [vm.RebootGuest() for vm in self.vmList if vm.name in vm]
        self.WaitForTasks(tasks)

    def createVM(self):
        """Creates a dummy VirtualMachine with 1 vCpu, 128MB of RAM.
        :param name: String Name for the VirtualMachine
        :param service_instance: ServiceInstance connection
        :param vm_folder: Folder to place the VirtualMachine in
        :param resource_pool: ResourcePool to place the VirtualMachine in
        :param datastore: DataStrore to place the VirtualMachine on
        """
        content = self.conn.RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        vmfolder = datacenter.vmFolder
        hosts = datacenter.hostFolder.childEntity
        resource_pool = hosts[0].resourcePool

        vm_name = self.args.new_name
        datastore_path = '[' + 'datastore1' + '] ' + vm_name

        # bare minimum VM shell, no disks. Feel free to edit
        vmx_file = vim.vm.FileInfo(logDirectory=None,
                                   snapshotDirectory=None,
                                   suspendDirectory=None,
                                   vmPathName=datastore_path)

        config = vim.vm.ConfigSpec(name=vm_name, memoryMB=512, numCPUs=1,
                                   files=vmx_file, guestId='dosGuest',
                                   version='vmx-11')

        print "Creating VM {}...".format(vm_name)
        task = vmfolder.CreateVM_Task(config=config, pool=resource_pool)
        tasks.wait_for_tasks(self.conn, [task])

        vm = self.get_obj(content, [vim.VirtualMachine], self.args.new_name)
        return vm

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
        tasks.wait_for_tasks(self.conn, [task])
        print "Created SCSI controller"

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
        if self.args.hard_disk_type == 'thin':
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
        tasks.wait_for_tasks(self.conn, [task])
        print "%sGB disk added to %s" % (self.args.hard_disk_size, vm.config.name)

    def getPortGroup(self):
        return vim.host.PortGroup

    def addNIC(self, vm):
        #print "Creating NIC...."

        '''network = self.args.network_name
        spec = vim.vm.ConfigSpec()
        dev_changes = []
        
        nic_spec = vim.vm.device.VirtualDeviceSpec()
        nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        
        nic_spec.device = vim.vm.device.VirtualE1000()
        
        nic_spec.device.deviceInfo = vim.Description()
        nic_spec.device.deviceInfo.summary = 'vCenter API test'
        
        nic_spec.device.backing = \
            vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
        nic_spec.device.backing.useAutoDetect = False
        content = self.conn.RetrieveContent()
        nic_spec.device.backing.network = self.get_obj(content, [vim.Network], network)
        nic_spec.device.backing.deviceName = network
        
        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.allowGuestControl = True
        nic_spec.device.connectable.connected = False
        nic_spec.device.connectable.status = 'untried'
        nic_spec.device.wakeOnLanEnabled = True
        nic_spec.device.addressType = 'assigned'
        dev_changes.append(nic_spec)

        spec.deviceChange = dev_changes

        task = vm.ReconfigVM_Task(spec=spec)
        tasks.wait_for_tasks(self.conn, [task])
        print "Created NIC"'''
        
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
        nic_spec.device.backing.network = self.get_obj(content, [vim.Network], network)
        nic_spec.device.backing.deviceName = network
        nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
        nic_spec.device.connectable.startConnected = True
        nic_spec.device.connectable.allowGuestControl = True 
        nic_spec.device.connectable.connected = False
        nic_spec.device.connectable.status = 'untried'
        nic_spec.device.wakeOnLanEnabled = True

        macAddress = str(self.generateMACAddress())
        nic_spec.device.addressType = 'assigned'
        nic_spec.device.macAddress = macAddress
        os.system('razor update-tag-rule --name test --rule \'["has_macaddress", "' + macAddress + '"]\'')

        dev_changes.append(nic_spec)

        spec.deviceChange = dev_changes

        task = vm.ReconfigVM_Task(spec=spec)
        tasks.wait_for_tasks(self.conn, [task])
        print "Created NIC"

    def deployOVF(self):
        ovfd = self.getOVFDescriptor()

        objs = self.getDeploymentObjects()
        manager = self.conn.content.ovfManager
        spec_params = vim.OvfManager.CreateImportSpecParams(diskProvisioning='sparse',entityName=self.args.new_name)
        import_spec = manager.CreateImportSpec(ovfd,
                                               objs["resource pool"],
                                               objs["datastore"],
                                               spec_params)
        lease = objs["resource pool"].ImportVApp(import_spec.importSpec,
                                                 objs["datacenter"].vmFolder)
        while(True):
            if (lease.state == vim.HttpNfcLease.State.ready):
                # Assuming single VMDK.
                url = lease.info.deviceUrl[0].url.replace('*', self.args.host)
                # Spawn a dawmon thread to keep the lease active while POSTing
                # VMDK.
                keepalive_thread = Thread(target=self.keepLeaseAlive, args=(lease,))
                keepalive_thread.start()
                # POST the VMDK to the host via curl. Requests library would work
                # too.
                curl_cmd = (
                    "curl -Ss -X POST --insecure -T %s -H 'Content-Type: \
                    application/x-vnd.vmware-streamVmdk' %s" %
                    (self.args.vmdk_path, url))
                system(curl_cmd)
                lease.HttpNfcLeaseComplete()
                keepalive_thread.join()
                return 0
            elif (lease.state == vim.HttpNfcLease.State.error):
                print "Lease error: " + lease.state.error
                exit(1)
        connect.Disconnect(si)

    def keepLeaseAlive(self, lease):
        """
        Keeps the lease alive while POSTing the VMDK.
        """
        while(True):
            sleep(5)
            try:
                # Choosing arbitrary percentage to keep the lease alive.
                lease.HttpNfcLeaseProgress(50)
                if (lease.state == vim.HttpNfcLease.State.done):
                    return
                # If the lease is released, we get an exception.
                # Returning to kill the thread.
            except:
                return

    def getOVFDescriptor(self):
        """
        Read in the OVF descriptor.
        """
        if path.exists(self.args.ovf_path):
            with open(self.args.ovf_path, 'r') as f:
                try:
                    ovfd = f.read()
                    f.close()
                    print "OVF is ok!"
                    return ovfd
                except:
                    print "Could not read file: %s" % ovf_path
                exit(1)

    def getDeploymentObjectFromList(self, obj_name, obj_list):
        """
        Gets an object out of a list (obj_list) whos name matches obj_name.
        """
        for o in obj_list:
            if o.name == obj_name:
                print "Matched " + str(o.name) + "!"
                return o
        print ("Unable to find object by the name of %s in list:\n%s" %
               (o.name, map(lambda o: o.name, obj_list)))
        exit(1)

    def getDeploymentObjects(self):
        """
        Return a dict containing the necessary objects for deployment.
        """
        # Get datacenter object.
        datacenter_list = self.conn.content.rootFolder.childEntity
        if self.args.datacenter_name:
            datacenter_obj = self.getDeploymentObjectFromList(self.args.datacenter_name, datacenter_list)
        else:
            datacenter_obj = datacenter_list[0]
            print "Used default datacenter"

        # Get datastore object.
        datastore_list = datacenter_obj.datastoreFolder.childEntity
        if self.args.datastore_name:
            datastore_obj = self.getDeploymentObjectFromList(self.args.datastore_name, datastore_list)
            print "Got datastore"
        elif len(datastore_list) > 0:
            datastore_obj = datastore_list[0]
            print "Got datastore without using the name"
        else:
            print "No datastores found in DC (%s)." % datacenter_obj.name

        # Get cluster object.
        cluster_list = datacenter_obj.hostFolder.childEntity
        if self.args.cluster_name:
            cluster_obj = self.getDeploymentObjectFromList(self.args.cluster_name, cluster_list)
        elif len(cluster_list) > 0:
            cluster_obj = cluster_list[0]
        else:
            print "No clusters found in DC (%s)." % datacenter_obj.name

        # Generate resource pool.
        resource_pool_obj = cluster_obj.resourcePool

        return {"datacenter": datacenter_obj,
                "datastore": datastore_obj,
                "resource pool": resource_pool_obj}

    def generateMACAddress(self):
        mac = [ self.macParts[0], self.macParts[1], self.macParts[2],
        random.randint(0x00, 0x7f),
        random.randint(0x00, 0xff),
        random.randint(0x00, 0xff) ]

        return ':'.join(map(lambda x: "%02x" % x, mac))

    def get_obj(self, content, vimtype, name):
        """
         Get the vsphere object associated with a given text name
        """
        obj = None
        container = content.viewManager.CreateContainerView(content.rootFolder,
                                                            vimtype, True)
        for view in container.view:
            if view.name == name:
                obj = view
                break
        return obj

    def assignRandomMAC(self, vm):
        powerState = self.getPowerStateVM(vm)

        if powerState == Powerstates.PoweredOff:
            try:
                newMAC = self.generateMACAddress()
                content = self.conn.RetrieveContent()

                # This code is for changing only one Interface. For multiple Interface
                # Iterate through a loop of network names.
                device_change = []
                for device in vm.config.hardware.device:
                    if isinstance(device, vim.vm.device.VirtualEthernetCard):
                        nicspec = vim.vm.device.VirtualDeviceSpec()
                        nicspec.operation = \
                            vim.vm.device.VirtualDeviceSpec.Operation.edit
                        nicspec.device = device

                        print "Old MAC Address:\t" + str(nicspec.device.macAddress)
                        nicspec.device.macAddress = str(newMAC)
                        nicspec.device.wakeOnLanEnabled = True

                        nicspec.device.connectable.startConnected = True
                        nicspec.device.connectable.allowGuestControl = True
                        device_change.append(nicspec)
                        print "Added the NIC change to the list of tasks"
                        print "New MAC Address:\t" + nicspec.device.macAddress
                        break

                config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
                task = vm.ReconfigVM_Task(config_spec)
                self.wait_for_tasks(self.conn, [task])
                print "Successfully changed network"

            except vmodl.MethodFault as error:
                print "Caught vmodl fault : " + error.msg
                return -1
        else:
            print "The virtual machine has to be powered off before you give it a new MAC address"

        return 0

    def wait_for_tasks(self, service_instance, tasks):
        property_collector = service_instance.content.propertyCollector
        task_list = [str(task) for task in tasks]
        # Create filter
        obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                     for task in tasks]
        property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                                   pathSet=[],
                                                                   all=True)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = obj_specs
        filter_spec.propSet = [property_spec]
        pcfilter = property_collector.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            # Loop looking for updates till the state moves to a completed state.
            while len(task_list):
                update = property_collector.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue
        
                            if not str(task) in task_list:
                                continue
        
                            if state == vim.TaskInfo.State.success:
                                # Remove task from taskList
                                task_list.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                raise task.info.error
                # Move to next version
                version = update.version
        finally:
            if pcfilter:
                pcfilter.Destroy()