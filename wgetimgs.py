#!/usr/bin/env python
# -*- coding: utf-8 -*-
# version: release
# fixed 20160825: 1.sformat = '%%0%dd' % l 2.default = '/media/d/QQDownload/xxx/'

""" urlopen is fast then wget, why? urlopen will be not full download, so use wget for default.
wget dont support mimetype filter, it is so bad when request images download but the response is html.
"""

import os
import sys
import urlparse
import urllib2
import socket
import argparse
import random
import time
import threading
import glob
import subprocess
from multiprocessing import Pool, Manager

''' global variables '''
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36'
PROXY_ADDR = 'http://127.0.0.1:8087'


def save_pic_wget(queue, url, args):
    cmd = 'wget --max-redirect=0 --spider -c -t 3 -T 30 -P "' + args.d + '" ' + url \
        + ' --user-agent="' + USER_AGENT + '"'
    cmd = args.r is False and cmd or cmd + ' --referer=' + url[:url.find('/', 8)]
    cmd = args.p is False and cmd or cmd + ' -e "http_proxy=' + PROXY_ADDR + '"'
    output = ''
    if not args.dbg:
        p = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        output = p.communicate()[1]
    if output.find('[image/') > -1:
        cmd = cmd.replace('--spider', '-q')
        os.system(cmd)
    queue.put(cmd)


def save_pic(queue, url, args, count=0):
    retry = 3
    if count > retry:
        return

    filename = os.path.join(args.d, os.path.basename(url))
    proxy_addr = PROXY_ADDR.replace('http://', '')
    referer = url[:url.find('/', 8)]
    msg = 'urlopen ' + url
    if args.p:
        msg += ' --user-agent "' + USER_AGENT + '"'
    if args.r:
        msg += ' --referer "' + referer + '"'
    msg += ' begin ...'
    queue.put(msg)
    if not args.dbg:
        try:
            # proxy
            if args.p:
                proxy = urllib2.ProxyHandler({'http': proxy_addr})
                opener = urllib2.build_opener(proxy)
                urllib2.install_opener(opener)
            # timeout setting
            socket.setdefaulttimeout(30)
            uinfo = urlparse.urlparse(url)
            req = urllib2.Request(url)
            req.add_header('Host', uinfo.netloc)
            req.add_header('User-Agent', USER_AGENT)
            if args.r:
                req.add_header('referer', referer)
            r = urllib2.urlopen(req)
            data = r.read()
            info = r.info().getmaintype()
            if info.getmaintype() == 'image':
                data = r.read()
                with open(filename, 'wb') as f:
                    f.write(data)
            r.close()

        except socket.timeout:
            count += 1
            queue.put('timeout:' + str(count) + ':' + filename)
            save_pic(queue, url, args, count)
        except Exception, e:
            count += 1
            queue.put('urlopen ' + url + ':' + str(count) + ' other fault:' + str(e))
            save_pic(queue, url, args, count)
        else:
            time.sleep(0.5 * random.random())
            queue.put('urlopen ' + url + '\nsave to:' + filename)


def save_pics(queue, urls, args):
    start = time.time()
    imax = 20
    size = len(urls) > imax and imax or len(urls)
    pool = Pool(size)
    callfunc = args.u is True and save_pic or save_pic_wget
    for url in urls:
        pool.apply_async(callfunc, (queue, url, args))
    pool.close()
    pool.join()
    end = time.time()
    failed = len(urls) - len(glob.glob(args.d + os.sep + '*'))
    msg = 'All save sucessed. Pool Size:' + str(size) \
        + ', Seconds:%.3f' % (end - start) \
        + ', Total:' + str(len(urls)) \
        + ', Falied:' + str(failed)
    queue.put(msg)
    queue.put('STOP')


class Printer(threading.Thread):
    """@summary: The queue is for printing msg
    @param queue: queue
    """

    def __init__(self, queue):
        super(Printer, self).__init__()
        self.queue = queue

    def run(self):
        while True:
            msg = self.queue.get()
            if msg == 'STOP':
                break
            print(msg)


if __name__ == "__main__":
    desc = '''Batch Fetch Images From Web.
    Auto download the images from img_url,
    or img_url template like 'http://www.xxx.com/beauty_[00-18]_big.jpg',
    [00-18] parse the url like [00 01 ... 18],
    [0-18] parse the url like [0 1 ... 18]
    '''
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-d', metavar='WORD', action='store', nargs='*', help='where to be save.')
    parser.add_argument('-y', action='store_true', default=False, help='dont check the exists dir.')
    parser.add_argument('-u', action='store_true', default=False, help='use urlopen to download. default: False')
    parser.add_argument('-r', action='store_true', default=False, help='use referer. default: False')
    parser.add_argument('-p', action='store_true', default=False, help='use proxy. default: False')
    parser.add_argument('-l', action='store_true', default=False, help='put stdout to file "out.log". default: False')
    parser.add_argument('-dbg', action='store_true', default=False, help='use debug mode, just print msg and dont download. default: False')
    parser.add_argument('url', metavar='URL', nargs='*', help='the last img url OR use url template OR more url')

    args = parser.parse_args()

    if args.l:
        saveout = sys.stdout
        fsock = open('out.log', 'w')
        sys.stdout = fsock

    if args.dbg:
        print args

    manager = Manager()
    queue = manager.Queue()

    if args.url == []:
        parser.print_help()
        sys.exit()

    if args.d is None:
        args.d = './'
    else:
        sdir = ' ' . join(args.d)
        rsep = os.name == 'nt' and '/' or '\\'
        sdir = sdir.replace(rsep, os.sep)
        # default = 'D:\\Download\\ZIG\\IMAGES\\'
        default = '/media/d/QQDownload/xxx/'
        args.d = sdir.find(os.sep) > -1 and sdir or default + sdir
    if args.dbg is False:
        try:
            os.mkdir(args.d)
        except Exception, e:
            print 'Cant mkdir because it had exists already?'
            if args.y is not True:
                raise e

    urls = []
    if len(args.url) > 1:
        urls = args.url
    else:
        url = args.url[0]
        addone = 0
        if url.rfind('+') > -1:
            url, addone = url.split('+')
            addone = int(addone)

        if url.find('[') > -1:
            part = url[url.find('[') + 1: url.rfind(']')]
            s, e = part.split('-')
            l = len(str(s))
            sformat = '%%0%dd' % l
            s, e = int(s), int(e) + 1
            for i in range(s, e):
                urls.append(url.replace('[' + part + ']', sformat % (i)))
        else:
            basename = os.path.basename(url)
            dirname = os.path.dirname(url)
            sep = basename.rfind('_') > -1 and '_' or '-'
            maxn = int(basename[basename.rfind(sep) + 1:].replace('.jpg', ''))
            s, e = 0, maxn + 1
            s += addone
            for i in range(s, e):
                urls.append(dirname + '/' + basename.replace(str(maxn), '%02d' % (i)))

    if args.dbg:
        print "\n" . join(urls)

    # Thread Printer
    printer = Printer(queue)
    printer.daemon = True  # make sure sub thread exit when main thread is die
    printer.start()

    # Download Handle
    save_pics(queue, urls, args)

    # Thread Printer Wait To End
    printer.join()

    if args.l:
        sys.stdout = saveout
        print 'All done and save log to out.log'
        fsock.close()
