#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()

    args = arginput.getServerConnectArgs()
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.loadVMList()

    serv_name = arginput.getServerName()
    cm.rebootVM(serv_name)

    cm.disconnectFromServer()

if __name__ =='__main__':
    main();