#!/usr/bin/env python

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")
from os import system, path

from powerstates import Powerstates
from Tools.tools import waitForTasks

class PowerManager(object):
    def __init__(self):
        self.macParts = [0x00, 0x0c, 0x28]

    def setConnection(self, hyper_conn):
        self.conn = hyper_conn

    def getPowerStateVM(self, vm):
        return str(vm.summary.runtime.powerState)

    def turnOnVM(self, vm):
        powerState = self.getPowerStateVM(vm)

        if powerState == Powerstates.PoweredOff:
            tasks = [vm.PowerOn()]
            waitForTasks(self.conn, tasks)
        else:
            print "Unable to start vm, " + str(vm.summary.config.name) + " is already turned on!"

    def turnOffVM(self, vm):
        powerState = self.getPowerStateVM(vm)

        if powerState == Powerstates.PoweredOn:
            tasks = [vm.PowerOff()]
            waitForTasks(self.conn, tasks)
        else:
            print "Unable to start vm, " + str(vm.summary.config.name) + " is already turned off!"

    def rebootVM(self, vm):
        powerState = self.getPowerStateVM(vm)

        if powerState == Powerstates.PoweredOn:
            tasks = [vm.RebootGuest()]
            waitForTasks(self.conn, tasks)
        else:
            print "Unable to start vm, " + str(vm.summary.config.name) + " is already turned off!"