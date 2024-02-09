#!/usr/bin/env bash

function one_command {
echo "[*] $1"
echo "[*] ${@:2}"
${@:2} > /dev/null

if [ $? -eq 0 ]
then
    echo "[+] SUCCESS"
else
    echo "[-] FAILED"
fi
echo
}


one_command 'Start upadate OS packages' sudo apt update
one_command 'Start install NMAP' sudo apt install -y nmap
if [ $# -eq 0 ]
then
    one_command 'Start install python requirements' pip3 install -r $(dirname "$0")/requirements.txt
else
    one_command 'Start install python requirements' $@ -m pip install -r $(dirname "$0")/requirements.txt
fi
if [ $# -eq 0 ]
then
    one_command 'Give caps for PYTHON3'  sudo setcap cap_net_raw=eip "$(readlink -f `which python3`)"
else
    one_command 'Give caps for PYTHON3'  sudo setcap cap_net_raw=eip "$(readlink -f $@)"
fi
one_command 'Give caps for NMAP' sudo setcap cap_net_raw,cap_net_admin,cap_net_bind_service+eip `which nmap`

