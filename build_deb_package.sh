#!/bin/bash

default_package_name="setezor"
default_source_repo="1"
default_description="Multitool for working with network"
default_version="1.0"
default_version_type='OEM'
default_maintainer="LMSecurity"
default_command="cd /usr/local/share/%s\nvenv/bin/python3.11 setezor.py \$@"
default_depends="sudo, libcap2-bin, python3.11, python3.11-dev, python3-pip, python3.11-venv, nmap, masscan"
default_postinst="
cd /usr/local/share/%s

python3.11 -m venv venv

if test -d ./pip_packages/
then
    mv -n ./pip_packages/* ./venv/lib64/python3.11/site-packages/
    rm -r ./pip_packages/
else
    echo '[-] No pip packeges in src folder'
fi

venv/bin/python3.11 -m pip install -r requirements.txt
sudo setcap cap_net_raw=eip \"\$(readlink -f \`which venv/bin/python3.11\`)\"
sudo setcap cap_net_raw+eip \`which nmap\`\necho \"
\"\nvenv/bin/python3.11 setezor.py --help\necho \"\n\"\n
"
default_postrm="sudo rm -rf /usr/local/share/%s"
default_arch="all"
default_service="echo \"[Unit]\nDescription=Setezor daemon\n\n[Service]\nUser=\nWorkingDirectory=/usr/local/share/%s\nExecStart=/usr/local/share/%s/venv/bin/python3.11 /usr/local/share/%s/setezor.py\nRestart=always\nRestartSec=3\nTimeoutStopSec=5\n\n[Install]\nWantedBy=multi-user.target\" > /etc/systemd/system/setezor.service"
package_fullname=""

install_pip_packages () {
    python3.11 --version >> /dev/null
    status=$?
    status=$?
    if [[ $status -eq 0 ]]
    then
        printf -v package_fullname "%s_%s" "$package_name" "$version"
        python3.11 -m pip install -t setezor_1.0/usr/local/share/setezor/pip_packages -r ./src/requirements.txt
    else
        echo '[-] Error no python3.11!!!'
        exit
    fi
}

has_argument() {
    [[ ("$1" == *=* && -n ${1#*=}) || ( ! -z "$2" && "$2" != -*)  ]];
}

extract_argument() {
  echo "${2:-${1#*=}}"
}

usage () {
    echo "OPTIONS:
    -pn  | --package_name       Name of package. Default value \"$default_package_name\"
    -d   | --description        Some description about app. Default value \"$default_description\"
    -v   | --version_number     Version of build. Default value \"$default_version\"
    -vt  | --version-type       Build version. Default value \"defaul\"
    -m   | --maintainer         Maintainer name. Default value \"$default_maintainer\"
    -c   | --command_script     Command of run app. Default value \"$default_command\"       
    -dep | --depends_packages   Package depeneds. Default value \"$default_depends\"
    -pi  | --postinstallation   Post instalation command. Default value \"$default_postinst\"
    -pr  | --postremove         Post remove commands. Default value \"$default_postrm\"
    -a   | --arch               Architectire of package. Default value \"$default_arch\"
    -h   | --help               Show help info 
"
}
handle_options() {
    while [ $# -gt 0 ]; do
        case "${1}" in
            -pn | --package_name) if has_argument $@; then package_name=$(extract_argument $@); else package_name=''; fi ;;
            -d | --description) if has_argument $@; then description=$(extract_argument $@); else description=''; fi ;;
            -v | --version_number) if has_argument $@; then version=$(extract_argument $@); else version=''; fi ;;
            -vt | --version_type) if has_argument $@; then version_type=$(extract_argument $@); else version_type=''; fi ;;
            -m | --maintainer) if has_argument $@; then maintainer=$(extract_argument $@); else maintainer=''; fi ;;
            -c | --command_script) if has_argument $@; then command=$(extract_argument $@); else command=''; fi ;;
            -dep | --depends_packages) if has_argument $@; then depends=$(extract_argument $@); else depends=''; fi ;;
            -pi | --postinstallation) if has_argument $@; then postinst=$(extract_argument $@); else postinst=''; fi ;;
            -pr | --postremove) if has_argument $@; then postrm=$(extract_argument $@); else postrm=''; fi ;;
            -a | --arch)  if has_argument $@; then arch=$(extract_argument $@); else arch=''; fi ;;
            -h | --help)  usage; exit 1 ;;
        esac
        shift
    done
    if [ -z $package_name ]; then package_name=$default_package_name; fi
    if [ -z $description ]; then description=$default_description; fi
    if [ -z $version ]; then version=$default_version; fi
    if [ -z $version_type ]; then version_type=$default_version_type; fi
    if [ -z $maintainer ]; then maintainer=$default_maintainer; fi
    if [ -z $command ]; then printf -v command "$default_command" "$package_name"; fi
    if [ -z $depends ]; then depends=$default_depends; fi
    if [ -z $arch ]; then arch=$default_arch; fi
    if [ -z $postinst ]; then printf -v postinst "$default_postinst" "$package_name"; fi
    if [ -z $postrm ]; then printf -v postrm "$default_postrm" "$package_name"; fi
    printf -v package_fullname "%s_%s" "$package_name" "$version"
    echo -e "Build params
    Package name: \"$package_name\",
    Description: \"$description\",
    Version number: \"$version\",
    Version type: \"$version_type\"
    Maintainer: \"$maintainer\",
    Command script: \"$command\",
    Depends packages: \"$depends\",
    Archecture: \"$arch\",
    Post installation: \"$postinst\",
    Post remove: \"$postrm\"
"
}

create_local_folder_structure() {
    mkdir -p "./$package_fullname/DEBIAN"
    mkdir -p "./$package_fullname/usr/local/share/$package_name"
    mkdir -p "./$package_fullname/usr/local/bin"
    touch "./$package_fullname/DEBIAN/control"
    touch "./$package_fullname/DEBIAN/postinst"
    touch "./$package_fullname/DEBIAN/postrm"
    touch "./$package_fullname/usr/local/bin/$package_name"
    echo "[+] Create folders structure of the package"
    tree "./$package_fullname"
}

remove_local_folder_structure() {
    rm -rf "./$package_fullname"
    echo "[+] Remove package folder \"""./$package_fullname""\""
}

write_control_file() {
    control_template='Package: %s
Depends: %s
Version: %s
Architecture: %s
Maintainer: %s
Description: %s
Build-Depends: debhelper (>= 9)
'
    printf "$control_template" "$package_name" "$depends" "$version" "$arch" "$maintainer" "$description" > "./$package_fullname/DEBIAN/control"
    echo "[+] Write content to file \"""./$package_fullname/DEBIAN/control""\""
}

write_postinst_file () {
    postinst_template='#!/bin/bash
set -e
%s'
    printf "$postinst_template" "$postinst" > "./$package_fullname/DEBIAN/postinst"
    printf "$default_service" "$package_name" >> "./$package_fullname/DEBIAN/postinst"
    chmod +x "./$package_fullname/DEBIAN/postinst"
    echo "[+] Write content to file \"""./$package_fullname/DEBIAN/postinst""\" and give executable permissions"
}

write_postrm_file () {
    postrm_template="#!/bin/bash\n\
set -e\n\
%s"
    printf "$postrm_template" "$postrm" > "./$package_fullname/DEBIAN/postrm"
    chmod +x "./$package_fullname/DEBIAN/postrm"
    echo "[+] Write content to file \"""./$package_fullname/DEBIAN/postrm""\" and give executable permissions"
}

write_command_file () {
    command_template='#!/bin/sh
%s'
    printf "$command_template" "$command" > "./$package_fullname/usr/local/bin/$package_name"
    chmod +x "./$package_fullname/usr/local/bin/$package_name"
    echo "[+] Write content to file \"""./$package_fullname/usr/local/bin/$package_name""\" and give executable permissions"
}

clone_source_code () {
    git clone --branch dev -n --depth=1 --filter=tree:0 git@git.lm:netmapper/network_topology.git "./source_code" > /dev/null 2>&1
    cd "./source_code"
    git sparse-checkout set --no-cone src > /dev/null 2>&1
    git checkout > /dev/null 2>&1
    echo "[+] Clone repo to \"source_code\""
    cd ../
    cp -r ./source_code/src/* "./$package_fullname/usr/local/share/$package_name/"
    rm -rf "./source_code"
    echo "[+] Copy source code to ""./$package_fullname/etc/$package_name/"" and remove \"./source_code/\""
    
}


handle_options "$@"
create_local_folder_structure
write_control_file
write_command_file
write_postinst_file
write_postrm_file
clone_source_code
if [[ $default_version_type -ne 'OEM' ]]
echo '[+] Installing packages'
then 
install_pip_packages
fi
echo '[+] Building deb...'
dpkg-deb --build --root-owner-group "./$package_fullname" > /dev/null 2>&1
echo "[+] Build package \"""./$package_fullname"".deb\""
remove_local_folder_structure