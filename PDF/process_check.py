#!/usr/bin/python
# -*- coding:utf-8 -*-
import os
import re
import sys
import time
import yaml
from subprocess import Popen, PIPE

currend_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(currend_dir)
state_dic = {
    "1,3": ["SS_MPI_APP_LIST", "SS_OM_APP_LIST", "SS_BASIC_SRV_APP_LIST"],
    "1,4": ["SS_AVP_APP_LIST", "SS_OM_APP_LIST", "SS_BASIC_SRV_APP_LIST"],
    "3,5": "SS_INSTALL_APP_LIST",
    "3,6": "SS_VERIFY_APP_LIST",
    "4,0": "SS_CAL_APP_LIST"
}
check_flag = False
board_type = ""


def get_board_type():
    stdout, stderr = Popen("ifconfig ethx0",
                           stdout=PIPE,
                           stderr=PIPE,
                           universal_newlines=True,
                           shell=True).communicate()
    if "192.168.2.12" in stdout:
        return "A"
    elif "192.168.2.76" in stdout:
        return "B"
    return


def get_vehicle_info():
    vehicle_info = {}
    stdout, stderr = Popen(
        'source /etc/profile;pmupload rosparam get cfgmgr_env',
        stdout=PIPE,
        stderr=PIPE,
        universal_newlines=True,
        shell=True).communicate()
    if stdout:
        for line in stdout.strip().split('\n'):
            info = line.split(':')
            if info[0] not in vehicle_info:
                vehicle_info[info[0]] = info[1].strip()
    return vehicle_info


def get_app_launch_total(vehicle_info):
    app_launch_total_config = {}
    with open('/etc/ads/service/ss/app_launch.yaml') as f:
        app_launch_config = yaml.load(f)
    with open('app_launch_total.yaml', 'w') as f:
        for path in app_launch_config['startup_path_list']:
            if r"${vehicle_factory}" in path:
                path = path.replace(r"${vehicle_factory}",
                                    vehicle_info['vehicle_factory']).replace(
                                        r'${vehicle_type}',
                                        vehicle_info['vehicle_type'])
            with open(path) as f1:
                yaml.dump(yaml.load(f1), f)
    with open('app_launch_total.yaml') as f:
        app_launch_total_config = yaml.load(f)
    return app_launch_total_config


def get_mdc_base_app(board_type):
    mdc_base_app_config = {}
    with open('/etc/ads/service/ss/mdc_base_app_%s.yaml' % board_type) as f:
        mdc_base_app_config = yaml.load(f)
    return mdc_base_app_config


def get_full_process(mdc_base_app_config, app_launch_total_config):
    global check_flag
    full_process_names = set()
    count = 0
    while count < 5:
        stdout, stderr = Popen(
            'source /etc/profile;pmupload mdc_ss_dfx query-state',
            stdout=PIPE,
            stderr=PIPE,
            universal_newlines=True,
            shell=True).communicate()
        if "5,10" not in stdout:
            break
        time.sleep(5)
        count += 1
    print(stdout.rstrip())
    state = re.search(' ([0-9],[0-9]+)', stdout).group(1)
    if state not in state_dic:
        print('%s not in state_dic' % state)
        return
    print('The app list is %s' % state_dic[state])
    for app_list in state_dic[state]:
        if app_list not in mdc_base_app_config:
            print('Key %s is not in mdc_base_app_config!')
            check_flag = False
            continue
        for key in mdc_base_app_config[app_list]:
            if mdc_base_app_config[app_list][key]["OptionType"] != 0:
                continue
            # print "%s stage :check app %s".format(app_list, key)
            if not mdc_base_app_config[app_list][key]["Arguments"]:
                full_process_name = app_launch_total_config[key]["bin_path"]
                full_process_names.add(full_process_name)
            else:
                full_process_name = app_launch_total_config[key][
                    "bin_path"] + " " + ' '.join(
                        mdc_base_app_config[app_list][key]["Arguments"])
                full_process_names.add(full_process_name.strip())
    return full_process_names


def parse_processes(full_process_names):
    pattern = re.compile('[0-9]{2}:[0-9]{2}:[0-9]{2} ')
    process_dict = {x: [] for x in full_process_names}
    for i in range(3):
        stdout, stderr = Popen('ps -elf',
                               stdout=PIPE,
                               stderr=PIPE,
                               universal_newlines=True,
                               shell=True).communicate()
        process_list = stdout.strip().split('\n')
        for process_info in process_list:
            process_pid = process_info.split()[3]
            process_name = pattern.split(process_info)[-1]
            if process_name in process_dict:
                process_dict[process_name].append(process_pid)
        time.sleep(5)
    return process_dict


def main():
    global check_flag, board_type
    vehicle_info = get_vehicle_info()
    if not vehicle_info:
        print('get vehicle info fail!')
        return
    print("vehicle_info is %s" % vehicle_info)
    board_type = get_board_type()
    if not board_type:
        print('get board type info fail!')
        return
    print("the board is %s" % board_type)
    mdc_base_app_config = get_mdc_base_app(board_type)
    if not mdc_base_app_config:
        print('get mdc_base_app_config info fail!')
        return
    app_launch_total_config = get_app_launch_total(vehicle_info)
    if not app_launch_total_config:
        print('get app_launch_total_config info fail!')
        return
    check_flag = True
    full_process_names = get_full_process(mdc_base_app_config,
                                          app_launch_total_config)
    if not full_process_names:
        print('get full_process_names info fail!')
        check_flag = False
        return
    process_dict = parse_processes(full_process_names)
    for process in process_dict:
        if len(set(process_dict[process])) != 1:
            print('Failed process:%s with pid %s' %
                  (process, ' '.join(process_dict[process])))
            check_flag = False
        else:
            print('Success process:%s with pid %s' %
                  (process, ' '.join(process_dict[process])))


if __name__ == '__main__':
    main()
    if check_flag:
        print('%s check process pass' % board_type)
    else:
        print('%s check process fail' % board_type)
