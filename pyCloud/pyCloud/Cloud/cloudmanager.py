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

from Tools.tools import waitForTasks, getObj, getOVFDescriptor, keepLeaseAlive

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

    def getPortGroup(self):
        return vim.host.PortGroup

    def deployOVF(self):
        ovfd = getOVFDescriptor(self.args.ovf_path)

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

    def getDeploymentObjects(self):
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