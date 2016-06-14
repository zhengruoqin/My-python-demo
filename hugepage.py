# -*- coding: utf-8 -*-

import os

def get_shell_output(cmd):
    return os.popen(cmd).read()

def get_memnode_size(memnodeid, hugepagesz):
    
    # /sys/devices/system/node/node0/hugepages/hugepages-1048576kB/nr_hugepages
    pages = file("/sys/devices/system/node/node%s/hugepages/hugepages-%skB/nr_hugepages" % (memnodeid, hugepagesz)).read().strip()
    return int(pages) * hugepagesz
    
def get_cpuflags():
    
    file_name = "/proc/cpuinfo"
    #cmd = "cat %s | grep flags | awk '{for(i=3;i<=NF;++i) printf $i '\n';}'" %file_name
    cmd = "cat %s | grep flags | awk '{$1=\"\";$2=\"\";print $0}'" %file_name
    flags = get_shell_output(cmd).split()
    fs = {}.fromkeys(flags).keys()
    
    tflags = []
    for x in fs:
        if x not in tflags:
            tflags.append(x)
            
    return tflags

def write_ksm_congfig(state):
    
    ksm_cfg_file = "/etc/ksm.conf"
    strs = "default=%s\n" % state
    fd = file(ksm_cfg_file, "w")
    fd.write(strs)
    fd.close()
    
def update_grub_hugepage(hugepagesz=None, hugepages=None):
    
    nlines = []
    for line in file("/boot/grub2/grub.cfg").readlines():
        #if line.strip().startswith("        linux16"):
        if "linux16" in line.strip():
            # hugepagesz=123M hugepages=1
            line_str = ""
            for x in line.strip().split():
                if "hugepagesz=" in x:
                    continue
                if "hugepages=" in x:
                    continue
                if "crashkernel=" in x:
                    continue
                if "default_hugepagesz=" in x:
                    continue
                line_str = line_str + " " + x
            if hugepagesz and hugepages:
                line_str = line_str + " crashkernel=auto default_hugepagesz=%sM hugepagesz=%sM hugepages=%s" % (str(hugepagesz), str(hugepagesz), str(hugepages))
            line_str = line_str + "\n"
            nlines.append(line_str)
            continue
        nlines.append(line)
    strs = "".join(nlines)
    file("/boot/grub2/grub.cfg", "w").write(strs)
    return nlines

#def update_grub_hugepage(hugepagesz=None, hugepages=None):
#    cmd = 'sed -i "/linux16/ s/$/ crashkernel=auto default_hugepagesz=%sM hugepagesz=%sM hugepages=%s/g /boot/grub2/grub.cfg"  %(str(hugepagesz), str(hugepagesz), str(hugepages))
#    os.system(cmd)
    
def turn_on_hugepage(param):
    
    hugepagesz = param["hugepagesz"]
    hugepages = param["hugepages"]
    
    flags = get_cpuflags()
    if 2 == int(hugepagesz):
        if "pse" not in flags and "pdpe1gb" not in flags:
            return (False, "Cpu not support hugepage")
    elif 1024 == int(hugepagesz):
        if "pdpe1gb" not in flags:
            return (False, "Cpu not support 1024M hugepage size")
    else:
        return (False, "Cpu not support this hugepage size")
    
    update_grub_hugepage(hugepagesz, hugepages)
    write_ksm_congfig("off")
    return (True, "It will effect in next system reboot")

def turn_off_hugepage():
    
    update_grub_hugepage()
#     write_ksm_congfig("on")
    return (True, "It will effect in next system reboot")

def update_hugepage(param):
    
#     开启设置：
#     action：327
#     param = {
#              "hostUuid":"xxx"
#              "service_on":"yes",
#              "hugepagesz":123,           每一页的大小，单位为M，单位不传，只传数字。只有两个值2或1024。
#              "hugepages":123,            大内存页的总页数。通过选择的内存值计算得出。
#     }
#     实现：
#     修改grub.conf，在kernel行增加hugepagesz=123M hugepages=1，
#     关闭ksm.conf服务配置，
#     涉及：
#     ksm服务开启ksm.conf时，检测到大内存页提示失败，
#     ksm循环检测到大内存页时，关闭sys下的ksm文件为0，并直接continue，
#     手动balloon检测到大内存页时，直接返回失败，
#     balloon循环，检测到大内存页的时候，直接continue，
#     init_bussness.py开机检测到开启了大内存，则执行mkdir /dev/hugepages，mount -t hugetlbfs hugetlbfs /dev/hugepages
# 
#     关闭设置：
#     action：328
#     param = {
#              "hostUuid":"xxx"
#              "service_on":"no",
#     }
#     实现：
#     修改grub.conf，在kernel行去掉hugepagesz=123M hugepages=1，
#     启动ksm.conf服务配置，
    
    service_on = param.get("service_on")
    if "yes" == service_on:
        return turn_on_hugepage(param)
    else:
        return turn_off_hugepage()

def get_grub_hugepage():
    
    hugepagesz = "0"
    hugepages = "0"
    for line in file("/boot/grub/grub.conf").readlines():
        if line.strip().startswith("kernel"):
            # hugepagesz=123M hugepages=1
            line_str = ""
            for x in line.strip().split():
                if "hugepagesz=" in x:
                    hugepagesz = x.split("=")[1]
                if "hugepages=" in x:
                    hugepages = x.split("=")[1]
                line_str = line_str + " " + x
            if hugepagesz and hugepages:
                break
    return {"hugepagesz":hugepagesz, "hugepages":hugepages}

def get_mem_fileinfo():

    file_name = "/proc/meminfo"
    lines = file(file_name).readlines()
    memtotal = "0"
    memfree = "0"
    swaptotal = "0"
    swapfree = "0"
    buffers = "0"
    cached = "0"
    HugePages_Total = "0"
    HugePages_Free = "0"
    for meminfoline in lines:
        llist = meminfoline.split()
        if len(llist) < 2:
            continue
        if "MemTotal:" == llist[0]:
            memtotal = llist[1]
            continue
        if "MemFree:" == llist[0]:
            memfree = llist[1]
            continue
        if "SwapTotal:" == llist[0]:
            swaptotal = llist[1]
            continue
        if "SwapFree:" == llist[0]:
            swapfree = llist[1]
            continue
        if "Buffers:" == llist[0]:
            buffers = llist[1]
            continue
        if "Cached:" == llist[0]:
            cached = llist[1]
            continue
        if "HugePages_Total:" == llist[0]:
            HugePages_Total = llist[1]
            continue
        if "HugePages_Free:" == llist[0]:
            HugePages_Free = llist[1]
            continue

    memotp = {}
    memotp["memtotal"] = memtotal
    memotp["memfree"] = memfree
    memotp["buffers"] = buffers
    memotp["cached"] = cached
    memotp["swaptotal"] = swaptotal
    memotp["swapfree"] = swapfree
    memotp["HugePages_Total"] = HugePages_Total
    memotp["HugePages_Free"] = HugePages_Free
    return (True, memotp)
    
def get_hugepage_info():
    
    par = get_grub_hugepage()
    if "0" != par["hugepagesz"]:
        par["service_on"] = "yes"
    else:
        par["service_on"] = "no"
    
    if os.path.ismount("/dev/hugepages"):
        par["is_running"] = "yes"
    else:
        par["is_running"] = "no"
    
    # 暂未更新此值，默认为0，需要从/proc/meminfo中获取
    par["HugePages_Free"] = "0"
    par["HugePages_Total"] = "0"
    (flag,memotp)=get_mem_fileinfo()
    if flag:
        par["HugePages_Free"] = str(memotp["HugePages_Free"])
        par["HugePages_Total"] = str(memotp["HugePages_Total"])
    return par

def do_web_get_hugepage_info():
    
#     读取状态：
#     do_web_get_hugepage_info()
#     参数：无
#     返回：
#           {
#              "service_on":"yes/no",      大内存是否开启
#              "is_running":"yes/no",      大内存页是否运行，以/dev/hugepages是否挂载为判断
#              "hugepagesz":123,           每一页的大小，单位为M，单位不传，只传数字
#              "hugepages":123,            大内存页的总页数
#              "HugePages_Free":123,       备用参数，将来使用
#              "HugePages_Total":123,      备用参数，将来使用
#              }

    return get_hugepage_info()

def hugepage_is_on_or_is_running():
    
    if os.path.ismount("/dev/hugepages"):
        return True
    
    par = get_grub_hugepage()
    if "0" != par["hugepagesz"]:
        return True

    return False
    
    
    

