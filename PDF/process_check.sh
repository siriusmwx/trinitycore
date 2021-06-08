#!/usr/bin/bash
# source /etc/profile
current_dir=$(
    cd $(dirname $0)
    pwd
)
cd ${current_dir}

user="root"
password="Huawei12#$"
remoteIp=192.168.2.76
logdir=$(date '+%Y-%m-%d_%H%M%S')
mkdir -p ${logdir}
collect_log=${logdir}/$(date '+%Y-%m-%d_%H%M%S').log

echo_log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $@" | tee -a $collect_log
}

remote_call() {
    ssh -o StrictHostKeyChecking=no root@$remoteIp "source /etc/profile;$@"
}

SynFile() {
    if [ -f $1 ]; then
        echo -e "$1 $user@$remoteIp:$1"
        scp $1 $user@$remoteIp:$1
    elif [ -d $1 ]; then
        ssh $user@$remoteIp "mkdir -p $1"
        echo -e "scp -r $1/* $user@$remoteIp:$1"
        scp -r $1/* $user@$remoteIp:$1
    else
        echo "Error: No such file or directory"
    fi
}

check_bak_soc() {
    if [ $1 -eq 1 ]; then
        for i in {1..30}; do
            ping -c 1 $remoteIp
            if [ $? == "0" ]; then
                generate_key
                make_back_dir /root/.ssh/
                get_authorize
                return 0
            fi
            sleep 1
        done
    else
        return 0
    fi
    return 1
}

generate_key() {
    rm -rf /root/.ssh/*
    cd /root/.ssh
    expect -c "
    set timeout 10
    spawn ssh-keygen -t rsa -b 4096
    expect {
    \"*save the key*\" { send \"\n\";exp_continue }
    \"*Enter passphrase*\" { send \"\n\";exp_continue }
    \"*Enter same passphrase again*\" { send \"\n\"}
    }
    expect eof"
    echo -e "generate_key End"
}

make_back_dir() {
    echo -e "make_back_dir $1 Start"
    expect -c "
    set timeout 10
    spawn ssh $user@$remoteIp mkdir -p $1;
    expect {
            *yes/no* { send \"yes\n\"; exp_continue }
            *assword* { send \"$password\n\" }
        };
    catch wait result
    exit [lindex \$result 3]
    "
    echo -e "make_back_dir $1 End"
}

get_authorize() {
    echo -e "get_authorize Start"
    expect -c "
        set timeout 10
        spawn bash -c \"scp /root/.ssh/id_rsa.pub $user@$remoteIp:/root/.ssh/authorized_keys\";
        expect {
            yes/no { send \"yes\n\"; exp_continue }
            *assword* {send \"$password\n\" }
        };
        catch wait result
        exit [lindex \$result 3]
    "
    echo -e "get_authorize End"
}

check_bak_soc() {
    for i in {1..30}; do
        ping -c 1 $remoteIp
        if [ $? == "0" ]; then
            generate_key
            make_back_dir /root/.ssh/
            get_authorize
            return 0
        fi
        sleep 1
    done
    return 1
}

check_bak_soc &>/dev/null

if [ $? -eq 1 ]; then
    echo -e "generate key fail"
    exit 1
fi

SynFile "/home/process_check_inmdc.py" &>/dev/null
python /home/process_check_inmdc.py 2>/dev/null

ssh -o StrictHostKeyChecking=no $user@$remoteIp "python /home/process_check_inmdc.py 2>/dev/null"
