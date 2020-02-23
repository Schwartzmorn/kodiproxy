#!/bin/bash

LIB_PATH="/usr/lib/kodiproxy"
CUR_DIR=$(dirname $(realpath $0))

function create_user() {
    id -u kp > /dev/null 2>&1
    if [[ $? -ne 0 ]]; then
        echo "Creating kp user"
        sudo useradd -M kp
    else
        echo "User kp already exists. Not recreating it"
    fi
}

function rsync_lib() {
    echo "Copying files"
    sudo rsync -am --delete --filter='merge resources/rsync_filter.txt' $1/ $2
    copy_settings_file "$CUR_DIR/resources/kodiproxy.json" "$LIB_PATH/kodiproxy.json"
    sudo chown -R kp:kp $LIB_PATH
}

function get_settings() {
    local lastInstall=$CUR_DIR/install.last
    local user_input
    if [[ -e $lastInstall ]]; then
        source $lastInstall
    fi

    PORT=${PORT:-"8080"}
    echo "Please give the port on which the server will be launched (default: $PORT):"
    read user_input
    PORT=${user_input:-"$PORT"}
    if [[ -z $PORT ]]; then
        echo "Error: no port provided"
        \exit 1
    fi

    echo -ne "Please give the IP of the receiver "
    if [[ -n $RECEIVER_IP ]]; then
        echo "(default: $RECEIVER_IP):"
    else
        echo "(eg: 192.168.1.13):"
    fi
    read user_input
    RECEIVER_IP=${user_input:-"$RECEIVER_IP"}
    if [[ -z $RECEIVER_IP ]]; then
        echo "Error: no receiver ip given"
        \exit 1
    fi

    echo -ne "Please give the url of the jsonrpc server "
    if [[ -n $JRPC_TARGET ]]; then
        echo "(default: $JRPC_TARGET):"
    else
        echo "(eg: http://localhost:8081/jsonrpc):"
    fi
    read user_input
    JRPC_TARGET=${user_input:-"$JRPC_TARGET"}
    if [[ -z $JRPC_TARGET ]]; then
        echo "Error: no jsonrpc target given"
        \exit 1
    fi

    printf "PORT=$PORT\nRECEIVER_IP=$RECEIVER_IP\nJRPC_TARGET=$JRPC_TARGET\n" > $lastInstall
}

function copy_settings_file() {
    cat "$1" | \
            sed "s;%JRPC_TARGET%;$JRPC_TARGET;g" | \
            sed "s;%RECEIVER_IP%;$RECEIVER_IP;g" | \
            sed "s;%PORT%;$PORT;g" | \
            sudo tee "$2" > /dev/null
}

function install_avahi_service() {
    echo 'Installing avahi service'
    copy_settings_file "$CUR_DIR/resources/kodiproxy.avahi.service" "/etc/avahi/services/kodiproxy.service"
    sudo systemctl daemon-reload
}

function install_systemd_service() {
    echo 'Installing systemd service'
    local service="kodiproxy.service"
    local enabled=$(systemctl is-enabled $service)
    local active='notactive'
    if [[ $enabled == 'enabled' ]]; then
        active=$(systemctl is-active $service)
    fi
    if [[ $active == 'active' ]]; then
        sudo systemctl stop $service
    fi
    if [[ $enabled == 'enabled' ]]; then
        sudo systemctl disable $service
    fi

    copy_settings_file "$CUR_DIR/resources/kodiproxy.systemd.service" "/lib/systemd/system/kodiproxy.service"

    sudo systemctl enable $service
    sudo systemctl start $service
}

create_user
get_settings
rsync_lib $CUR_DIR $LIB_PATH
install_avahi_service
install_systemd_service
