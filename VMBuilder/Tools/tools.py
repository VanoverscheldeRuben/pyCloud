#!/usr/bin/env python

import os
import sys
reload(sys)
sys.setdefaultencoding("utf-8")

from os import system, path
from sys import exit
from time import sleep
from pyVmomi import vim, vmodl

def keepLeaseAlive(lease):
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

def getOVFDescriptor(ovf_path):
    """
    Read in the OVF descriptor.
    """
    if path.exists(ovf_path):
        with open(ovf_path, 'r') as f:
            try:
                ovfd = f.read()
                f.close()
                print "OVF is ok!"
                return ovfd
            except:
                print "Could not read file: %s" % ovf_path
            exit(1)

def getDeploymentObjects(conn, datacenter_name=None, datastore_name=None, cluster_name=None):
    # Get datacenter object.
    datacenter_list = conn.content.rootFolder.childEntity
    if datacenter_name:
        datacenter_obj = getDeploymentObjectFromList(datacenter_name, datacenter_list)
    else:
        datacenter_obj = datacenter_list[0]
    
    # Get datastore object.
    datastore_list = datacenter_obj.datastoreFolder.childEntity
    if datastore_name:
        datastore_obj = getDeploymentObjectFromList(datastore_name, datastore_list)
    elif len(datastore_list) > 0:
        datastore_obj = datastore_list[0]
    else:
        print "No datastores found in DC (%s)." % datacenter_obj.name
    
    # Get cluster object.
    cluster_list = datacenter_obj.hostFolder.childEntity
    if cluster_name:
        cluster_obj = getDeploymentObjectFromList(cluster_name, cluster_list)
    elif len(cluster_list) > 0:
        cluster_obj = cluster_list[0]
    else:
        print "No clusters found in DC (%s)." % datacenter_obj.name
    
    # Generate resource pool.
    resource_pool_obj = cluster_obj.resourcePool
    
    return {"datacenter": datacenter_obj,
            "datastore": datastore_obj,
            "resource pool": resource_pool_obj}

def getDeploymentObjectFromList(obj_name, obj_list):
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

def getObj(content, vimtype, name):
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

def waitForTasks(conn, tasks):
    property_collector = conn.content.propertyCollector
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