#!/usr/bin/env python

import subprocess as sp
from gevent.queue import Queue
from Queue import Empty as QueueEmpty
from gevent import spawn
import signal
from gevent import select
import os
import sys


log = open('/dev/stdout', 'w')


def info(msg):
    if msg[-1] == '\n':
        log.write(msg[:-1])
    else:
        log.write(msg)
    log.flush()


def do_scan():
    print('Scanning...')
    path = '/data/incoming'
    owner = '{}@{}'.format(os.getenv('USER'),os.getenv('HOST'))
    arches = os.getenv('ARCHS', 'amd64,i386').split(',')
    for file in os.listdir(path):
        for dist in os.getenv('DISTS', 'xenial').split(','):
            for arch in arches:
                mypath = '/data/dists/{}/main/binary-{}'.format(dist, arch)
                srcfile = '{}/{}'.format(path, file)
                myfile = '{}/{}'.format(mypath, file)
                if not os.path.exists(mypath):
                    os.makedirs(mypath)
                if not os.path.exists(myfile):
                    os.symlink(srcfile,myfile)

    for dist in os.getenv('DISTS', 'xenial').split(','):
        distpath = '/data/dists/{}'.format(dist)
        for arch in arches:
            archpath = '{}/main/binary-{}'.format(distpath, arch)
            relfile = '{}/{}'.format(archpath, "Release")
            if not os.path.exists(relfile):
                myrel = open(relfile,'w+')
                myrel.write("""Archive: {}
                Origin: {}
                Label: {}
                Architecture: {}
                """.format(owner,owner,owner,arch));
                myrel.close()
            cmd = 'dpkg-scanpackages -m . | gzip -9c > {0}/Packages.gz'.format(archpath)
            sp.check_call(cmd, shell=True, close_fds=True)
        relfile = '{}/{}'.format(distpath, "Release")
        if not os.path.exists(relfile):
                myrel = open(relfile,'w+')
                myrel.write("""Origin: {}
                Label: {}
                Suite: {}
                Codename: {}
                Architectures: {}
                Description: {}
                """.format(owner,owner,dist,dist," ".join(arches),owner));
                myrel.close()
    info('Scanning...done')


def main():
    def loop():
        try:
            while True:
                rlist, _, _ = select.select([p.stdout], [], [p.stderr])
                if p.poll() is not None:
                    break
                if rlist:
                    line = p.stdout.readline().strip()
                    if len(line) == 0:
                        continue
                    if line.endswith('Packages.gz'):
                        continue
                    queue.put(('msg', line))
        except select.error:
            pass
        finally:
            try:
                p.kill()
            except:
                pass
            queue.put(('stop', 'unknown exit'))

    def stop(signum, frame):
        queue.put(('stop', str(signum)))

    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGHUP, stop)
    signal.signal(signal.SIGINT, stop)

    queue = Queue()

    cmd = ['inotifywait', '-rm', '-e',
           'close_write,moved_to,moved_from,delete', '.']
    p = sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, close_fds=True)
    t = spawn(loop)

    timeout = 1
    while True:
        try:
            msg = queue.get(True, timeout)
            if msg[0] == 'stop':
                break
            elif msg[0] == 'msg':
                try:
                    info(str(msg[1]))
                    timeout = 5
                except ValueError:
                    info('abnormal format message: ' + str(msg))
            else:
                info('unknown command: ' + str(msg))
        except QueueEmpty:
            do_scan()
            timeout = None
    try:
        p.kill()
    except OSError:
        pass
    finally:
        p.wait()
        t.join()


if __name__ == "__main__":
    do_scan()
    main()
