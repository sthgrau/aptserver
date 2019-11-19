#!/bin/bash

mkdir -p /data/dists/xenial/main/binary-amd64/
exec /usr/bin/supervisord -n
