#!/bin/bash
# description: Runs command as daemon using the "daemon" command 
# see: http://manpages.ubuntu.com/manpages/trusty/man1/daemon.1.html)
#
# Author: Wilson Santos (wilson.santos@penguinformula.com)


CMD=localbox.sh
PROGRAM_NAME=${CMD}

DAEMON_CMD="daemon --name ${PROGRAM_NAME}"


start() {
    ${DAEMON_CMD} ${CMD}
}

stop() {
    ${DAEMON_CMD} --stop
}

restart() {
    ${DAEMON_CMD} --restart
}

status() {
    ${DAEMON_CMD} --running
    if [ $? -eq 0 ]; then
        echo "${PROGRAM_NAME} is running."
    else
        echo "${PROGRAM_NAME} is stopped."
    fi
}

case "$1" in 
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart}"
esac
