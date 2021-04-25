#!/bin/bash
user="root"
remote_ip="127.0.0.1"
password='password'

/usr/bin/expect <<EOF
set timeout 10
spawn ssh ${user}@${remote_ip} $@
expect {
"*yes/no" { send "yes\r";exp_continue }
"*password:" { send "${password}\r" }
}
expect eof
EOF
