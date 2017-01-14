#!/usr/bin/env python

from cloudmanager import CloudManager
import arginput

def main():
    cm = CloudManager()

    args = arginput.getOVFDeployArgs()
    arginput.addPassword(args)

    cm.setArgs(args)
    cm.connectToServer()
    cm.deployOVF()

if __name__ =='__main__':
    main();