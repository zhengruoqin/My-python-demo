# -*- coding: utf-8 -*-

import os

import hugepage
import global_params

def write_cfg(is_on):
    
    file("/etc/balloon.conf","w").write("default="+is_on)
    return

def update_balloon(param):
    
    is_on = "off"
    if "on" == param.get("default"):
        is_on = "on"
    
    if "on" == is_on:
        if hugepage.hugepage_is_on_or_is_running():
            # 大内存页与balloon开启冲突
            state = "Hugepages state exist"
            return (False, state)
    write_cfg(is_on)
    return (True, "")

def balloon_is_on():
    
    fname = "/etc/balloon.conf"
    if os.access(fname, os.F_OK):
        if "default=on" in file(fname).read():
            return True
    return False


def do_web_get_balloon_info():
    
    vms = []
    for vmUuid in global_params.vms_process_info:
        description = global_params.vms_process_info[vmUuid].get("description")
        cfgMem = global_params.vms_process_info[vmUuid].get("mem")
        processMem = global_params.vms_process_info[vmUuid].get("processMem")
        sysMem = global_params.vms_process_info[vmUuid].get("sysMem")
        will_free_mem = global_params.vms_process_info[vmUuid].get("will_free_mem")
        balloon_mem = global_params.vms_process_info[vmUuid].get("balloon_mem")
        if not processMem:
            continue
        if not sysMem:
            sysMem = "Unknown"
        if not will_free_mem:
            will_free_mem = 0
        if not balloon_mem:
            balloon_mem = cfgMem
        
        balloone_size = (cfgMem - balloon_mem) #气球大小
        TrueSysMem = "Unknown"
        if sysMem != "Unknown":
            TrueSysMem = sysMem - balloone_size # 虚拟机系统真实使用内存大小
        vms.append({"vmUuid":vmUuid, "description":description, "cfgMem":cfgMem, "processMem":processMem, "sysMem":TrueSysMem, "balloone_size":balloone_size, "will_free_mem":will_free_mem, "balloon_mem":balloon_mem})
        
    service_on = "no"
    if balloon_is_on():
        service_on = "yes"

    return {"service_on":service_on, "vms":vms}

def get_process_balloon_actual(vmUuid):
    
    balloon_mem = 0
    if not balloon_is_on():
        return 0
    cmd = "info balloon\n"
    (flag, strs) = operation.vm.vm_running_script.monitor_exec(vmUuid, cmd, 5)
    if not flag or "actual=" not in strs:
        return balloon_mem
    try:
        mstr = strs.split("actual=")[1].split()[0].strip()
        balloon_mem = int(mstr)
    except:
        pass
    return balloon_mem
    
