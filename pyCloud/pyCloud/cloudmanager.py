#!/usr/bin/env python

import pyVmomi
from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect

import arginput

import atexit
import ssl

class CloudManager(object):
    def __init__(self):
        self.maxVMDepth = 10
        self.createEmptyCert()

    def createEmptyCert(self):
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        self.context.verify_mode = ssl.CERT_NONE

    def setConnectArgs(self, args):
        self.args = args

    def connectToServer(self):
        try: # First try to connect with a valid certificate
            self.conn = SmartConnect(host=self.args.host, user=self.args.user, pwd=self.args.pwd)
        except: # No valid certificate, try without one
            self.conn = SmartConnect(host=self.args.host, user=self.args.user, pwd=self.args.pwd, sslContext=self.context)

    def loadVMList(self):
        '''datacenter = self.conn.content.rootFolder.childEntity[0]
        self.vms = datacenter.vmFolder.childEntity'''

        content = self.conn.RetrieveContent()
        for child in content.rootFolder.childEntity:
            if hasattr(child, 'vmFolder'):
                datacenter = child
                vmFolder = datacenter.vmFolder
                self.vmList = vmFolder.childEntity

    def displayVMs(self):
        for vm in self.vmList:
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

    def turnOnVM(self, targets):
        tasks = [vm.PowerOn() for vm in self.vmList if vm.name in targets]
        self.WaitForTasks(tasks)

    def turnOffVM(self, targets):
        tasks = [vm.PowerOff() for vm in self.vmList if vm.name in targets]
        self.WaitForTasks(tasks)