#!/usr/bin/env python

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from os import system, path
from sys import exit
from threading import Thread

from pyVim import connect
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

import ssl

from Tools.tools import waitForTasks, getObj, getOVFDescriptor, keepLeaseAlive, getDeploymentObjects

class CloudManager(object):
    def __init__(self):
        self.maxVMDepth = 10
        self.createEmptyCert()

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

    def getConnection(self):
        return self.conn

    def disconnectFromServer(self):
        Disconnect(self.conn)

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
        elif self.args.search_method == 'uuid':
            return self.findVMByUUID(self.args.search_argument)

    def findVMByName(self, name):
        for vm in self.vmList:
            summary = vm.summary

            if name == str(summary.config.name):
                return vm

    def findVMByIP(self, ip):
        for vm in self.vmList:
            summary = vm.summary

            if ip == str(summary.guest.ipAddress):
                return vm

    def findVMByUUID(self, uuid):
        for vm in self.vmList:
            summary = vm.summary

            if uuid == str(summary.config.uuid):
                return vm

    def displayVMs(self, list=None):
        if list == None:
            list = self.vmList

        for vm in list:
            self.displayVM(vm)

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
        print 'Guest OS id:\t' + str(summary.config.guestId)
        print 'Instance UUID:\t' + str(summary.config.instanceUuid)
        print 'Bios UUID:\t' + str(summary.config.uuid)

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

        print ''
        print 'Runtime info'
        print 'Host name:\t' + str(vm.runtime.host.name)
        print 'Last booted timestamp:\t' + str(vm.runtime.bootTime)

        print ""

    def createVM(self):
        content = self.conn.RetrieveContent()
        datacenter = content.rootFolder.childEntity[0]
        vmfolder = datacenter.vmFolder
        hosts = datacenter.hostFolder.childEntity
        resource_pool = hosts[0].resourcePool

        vm_name = self.args.new_name
        datastore_path = '[' + 'datastore1' + '] ' + vm_name

        vmx_file = vim.vm.FileInfo(logDirectory=None,
                                   snapshotDirectory=None,
                                   suspendDirectory=None,
                                   vmPathName=datastore_path)

        config = vim.vm.ConfigSpec(name=vm_name, memoryMB=int(self.args.memory), numCPUs=1,
                                   files=vmx_file, guestId='dosGuest',
                                   version='vmx-11')

        print "Creating VM {}...".format(vm_name)
        task = vmfolder.CreateVM_Task(config=config, pool=resource_pool)
        waitForTasks(self.conn, [task])

        vm = getObj(content, [vim.VirtualMachine], self.args.new_name)
        return vm

    def destroyVM(self, vm):
        name = vm.summary.config.name

        print('Destroying vm ' + name + '...')

        task = vm.Destroy_Task()
        waitForTasks(self.conn, [task])

        print('Destroyed vm ' + name)

    def getPortGroup(self):
        return vim.host.PortGroup

    def deployOVF(self):
        ovfd = getOVFDescriptor(self.args.ovf_path)

        objs = getDeploymentObjects(self.conn, self.args.datacenter_name, self.args.datastore_name, self.args.cluster_name)
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
                keepalive_thread = Thread(target=keepLeaseAlive, args=(lease,))
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