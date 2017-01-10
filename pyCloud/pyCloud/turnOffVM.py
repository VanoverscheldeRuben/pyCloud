#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()

    args = arginput.getServerConnectArgs()
    arginput.addPassword(args)

    cm.setConnectArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    serv_name = arginput.getServerName()
    cm.turnOffVM(serv_name)

if __name__ =='__main__':
    main();