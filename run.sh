#!/bin/bash
MYPORT=0
MYDIR=`pwd`

RUNDIR=`realpath \`dirname $0\``

while [ $# -ne 0 ] ; do
    if [ "x$1" == "x-d" ] ; then
        MYDIR=`realpath $2`
	shift;shift
    elif [ "x$1" == "x-p" ] ; then
        MYPORT=$2
	shift;shift
    fi
done

name=`echo $MYDIR | sed -e 's#/#_#g' -e 's/^_//'`
if [ `docker ps -qf name=$name 2> /dev/null | wc -l` -gt 0 ] ; then
    echo Already running at `docker container port $name | awk '{print $3}'`
else
    docker build -t aptserver $RUNDIR > $RUNDIR/.build.out 2>&1 && docker run --name $name -dt -v $MYDIR:/data/incoming -e USER=$USER -e HOST=$HOSTNAME -p 127.0.0.1:$MYPORT:80 aptserver
    echo Running at `docker container port $name | awk '{print $3}'`
fi
