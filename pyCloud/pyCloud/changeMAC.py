#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
	cm = CloudManager()
	cm.generateMACAddress()

	'''args = arginput.getServerConnectArgs()
	arginput.addPassword(args)

	cm.setArgs(args)
	cm.connectToServer()
	cm.loadVMList()

	serv_name = arginput.getServerName()
	cm.turnOnVM(serv_name)'''

if __name__ =='__main__':
    main();
