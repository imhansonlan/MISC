#!/usr/bin/env python
# -*- coding: utf-8 -*-
# version: release
from __future__ import division

import argparse
import base64
import copy
import dbm
import glob
import hashlib
import math
import os
import queue
import random
import sys
import threading
import time


def group(lst, n):
    num = len(lst) % n
    zipped = zip(*[iter(lst)] * n)
    return zipped if not num else zipped + [lst[-num:], ]


def partition(lst, n):
    return group(lst, int(math.ceil(len(lst)/n)))


def rand(min, max):
    return random.randint(min, max)


def md5(s: str, raw_output=False):
    """Calculates the md5 hash of a given string"""
    res = hashlib.md5(s.encode())
    if raw_output:
        return res.digest()
    return res.hexdigest()


def substr_replace(subject, replace, start, length):
    if length is None:
        return subject[:start] + replace
    elif length < 0:
        return subject[:start] + replace + subject[length:]
    else:
        return subject[:start] + replace + subject[start+length:]


def base64_decode(data: str):
    return base64.b64decode(data.encode()).decode()


def base64_encode(data: str):
    return base64.b64encode(data.encode()).decode()


def strpos(haystack, needle, offset=0):
    """ Rewrite this to make it same with php when return is '-1', Or it will cause some error someway. """
    result = haystack.find(needle, offset)
    result = result if result > -1 else False
    return result


class FileSafeException(Exception):
    """docstring for FileSafeException"""

    msg = ''

    def __init__(self, msg):
        super(FileSafeException, self).__init__()
        self.msg = msg

    def __str__(self):
        return self.msg

    @classmethod
    def getMsg(self):
        return self.msg


class FileSafe():
    """Encrypt binaryfile class helper"""

    arrps = [[0, 20], [5, 30], [20, 10]]
    bFileNameEncode = True
    bFileEncrypt = True
    bRecurse = False
    bDebug = False
    count = 0
    sdir = ''
    subdir = []

    @classmethod
    def setWorkQueue(self, work_queue):
        self.work_queue = work_queue

    @classmethod
    def setFileNameEncode(self, encode=True):
        self.bFileNameEncode = encode

    @classmethod
    def setFileEncrypt(self, encrypt=True):
        self.bFileEncrypt = encrypt

    @classmethod
    def setRecurse(self, recurse=True):
        self.bRecurse = recurse

    @classmethod
    def setDebug(self, debug=True):
        self.bDebug = debug

    @classmethod
    def strDecrypt(self, key):
        value = db.get(key).decode()
        return base64_decode(value)

    @classmethod
    def strEncrypt(self, txt):
        key = md5(txt);
        value = base64_encode(txt)
        db[key] = value
        return key

    @classmethod
    def getFiles(self, sdir):
        fileStore = []
        if os.path.exists(sdir):
            if self.bRecurse:
                for root, dirs, files in os.walk(sdir, True):
                    root = root.replace('\\', '/').rstrip('/')
                    sep = '/'
                    for file in files:
                        if file.endswith('.db'):
                            continue
                        fileStore.append(root + sep + file)
                    for sdir in dirs:
                        self.subdir.append(root + sep + sdir)
            else:
                sdir = os.name == 'nt' \
                    and sdir.replace('/', os.sep).rstrip(os.sep) \
                    or sdir.replace('\\', os.sep).rstrip(os.sep)
                self.sdir = sdir
                # fileStore = [file for file in glob.glob(sdir + os.sep + '*') if os.path.isfile(file)]
                for file in glob.glob(sdir + os.sep + '*'):
                    if file.endswith('.db'):
                        continue
                    if os.path.isfile(file):
                        fileStore.append(file)
                    elif os.path.isdir(file):
                        self.subdir.append(file)
        return fileStore

    @classmethod
    def encrypts(self, sdir):
        files = self.getFiles(sdir)
        if files:
            self.encryptsByList(files)

    @classmethod
    def decrypts(self, sdir):
        self.setFileEncrypt(False)
        self.encrypts(sdir)

    @classmethod
    def encryptsByList(self, filelist):
        for file in filelist:
            try:
                self.encrypt(file)
            except FileSafeException as e:
                self.work_queue.put(str(e))

    @classmethod
    def encrypt(self, file):
        if os.path.isfile(file):
            self.fileEncrypt(file)
            if self.bFileNameEncode:
                self.fileNameEncode(file)

    @classmethod
    def fileEncrypt(self, file):
        """ Notice: let 'copy.deepcopy' do it, 'arrps = self.arrps' will always change 'self.arrps',
        because variables passed by reference in python. You can also do it like: 'arrps = self.arrps[:]'
        """
        arrps = copy.deepcopy(self.arrps)
        if self.bFileEncrypt is False:
            arrps.reverse()
            for ps in arrps:
                ps.reverse()

        info = os.stat(file)
        mtime = info.st_mtime
        atime = info.st_atime

        try:
            with open(file, 'rb+') as f:
                for pos in arrps:
                    pos1 = pos[0]
                    pos2 = pos[1]
                    f.seek(pos1)
                    char1 = f.read(1)
                    f.seek(pos2)
                    char2 = f.read(1)

                    f.seek(pos1)
                    f.write(char2)
                    f.seek(pos2)
                    f.write(char1)
        except Exception as e:
            msg = "EncryptError: " + str(e)
            raise FileSafeException(msg)

        os.utime(file, (atime, mtime))
        self.count += 1

        tag = self.bFileEncrypt and 'encrypt' or 'decrypt'
        msg = "Filename '" + file + "' has been " + tag
        if self.bDebug:
            self.work_queue.put(msg)

    @classmethod
    def subDirNameEncode(self):
        self.subdir.reverse()
        for sdir in self.subdir:
            self.fileNameEncode(sdir)

    @classmethod
    def fileNameEncode(self, file):
        """ 'os.path.basename' sometime it got wrong idea (specail char in win?) """
        try:
            # basename = os.path.basename(file)
            # dirname  = os.path.dirname(file)
            dirname = self.bRecurse and file[:file.rindex('/') + 1] or self.sdir + os.sep
            basename = file.replace(dirname, '')
            basename = self.bFileEncrypt and self.strEncrypt(basename) or self.strDecrypt(basename)
            oldname = file
            newname = os.path.join(dirname, basename)
            os.rename(oldname, newname)

            msg = "File '" + oldname + "' has been rename '" + newname + "'."
            if self.bDebug:
                self.work_queue.put(msg)
        except Exception as e:
            msg = "!EncodeError: " + str(e) + \
                ", Do you action decrypt and filename still be not fileNameEncode ?" + \
                "\n*You better with option '-x'*"
            raise FileSafeException(msg)


class ThreadRunner(threading.Thread):
    '''@summary: __init__ function def

    @param work_queue: queue for sending thread status
    @param showStatus: whether print thread end status
    @param callback: FileSafe class
    @param parameter: files to be handle via FileSafe class
    '''
    def __init__(self, work_queue, showStatus, callback, *parameter):
        super(ThreadRunner, self).__init__()    # Notice: must call supper __init__
        self.showStatus = showStatus
        self.callback = callback
        self.parameter = parameter
        self.work_queue = work_queue

    def run(self):
        self.callback(*self.parameter)
        if self.showStatus:
            msg = " *" + self.name.ljust(9) + " is ending at: " + time.ctime()
            self.work_queue.put(msg)


class Printer(threading.Thread):
    """@summary: The queue is for printing msg
    @param work_queue: queue
    """
    def __init__(self, work_queue):
        super(Printer, self).__init__()
        self.work_queue = work_queue

    def run(self):
        while True:
            msg = self.work_queue.get()
            if msg == 'ENDTAG':
                break
            print(msg)

""" ################################################################ """
""" ##################### Main code ################################ """
""" ################################################################ """
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Encrypt Or Decrypt binaryfile.')
    parser.add_argument('-e', action='store_true', default=True, help='encrypt binaryfile, default: True')
    parser.add_argument('-d', action='store_true', help='decrypt binaryfile')
    parser.add_argument('-x', action='store_true', default=False, help='dont encrypt filename')
    parser.add_argument('-r', action='store_true', default=False, help='recurse the dir')
    parser.add_argument('-s', action='store_true', help='run with single thread')
    parser.add_argument('-m', action='store_true', default=True, help='run with multiple thread, default: True')
    parser.add_argument('-a', action='store_true', default=False, help='subdir name encode, default: False')
    parser.add_argument('-p', action='store_true', default=False, help='run with debug mode and print msg?')
    parser.add_argument('-n', metavar='ThreadCount', type=int, default=50, help='thread count, default is 50')
    parser.add_argument('dir', metavar='Directory', nargs='?', help='the directory to be handle')

    args = parser.parse_args()

    # print args
    # sys.exit()

    if args.dir is None:
        parser.print_help()
        sys.exit()

    if os.path.exists(args.dir) is False:
        print("Please check the sdir, it may be not exists.")
        sys.exit()

    """ ########### >> init variables ################################### """
    work_queue = queue.Queue()
    tcount = args.n     # Max Thread Count
    sucessed = '''
     _____________
     < well done >
     -------------
        \\   ^__^
         \\  (oo)\\_______
            (__)\\       )\\/\\

                ||----w |
                ||     ||
    '''
    """ ########### << init variables ################################## """

    FileSafe.setWorkQueue(work_queue)
    FileSafe.setDebug(args.p)
    FileSafe.setFileNameEncode(not args.x)
    FileSafe.setRecurse(args.r)

    """ ################################################################ """
    """ #################### single thread main run #################### """
    """ ################################################################ """
    if args.s:
        start = time.time()

        if args.d:
            FileSafe.decrypts(args.dir)
        else:
            FileSafe.encrypts(args.dir)

        # finally subdir name handle
        if args.a:
            FileSafe.subDirNameEncode()

        end = time.time()
        print(sucessed)
        print("**Take times: ", 'seconds: %.3f' % (end - start))
        sys.exit()

    """ ################################################################ """
    """ #################### multiple thread main run ################## """
    """ ################################################################ """
    if args.d:
        FileSafe.setFileEncrypt(False)
    else:
        FileSafe.setFileEncrypt(True)

    files = FileSafe.getFiles(args.dir)
    if len(files) == 0:
        print('No files to be handle...')
        sys.exit()
    fpartition = partition(files, tcount)

    # open db
    dbfile = os.path.join(args.dir, 'data')
    db = dbm.open(dbfile,'c')
    
    work_queue.put("**Threading Starting ... %s ... " % time.ctime())
    start = time.time()

    # Thread start
    threads = []
    for p in fpartition:
        t = ThreadRunner(work_queue, True, FileSafe.encryptsByList, p)
        threads.append(t)
        t.daemon = True
        t.start()

    # Thread Printer
    printer = Printer(work_queue)
    printer.daemon = True  # make sure sub thread exit when main thread is die
    printer.start()

    # Thread end
    for t in threads:
        t.join()

    work_queue.put(sucessed)
    end = time.time()
    msg = "**Threading(%d) all ending at:%s, Take times:%.3f seconds" % (len(threads), time.ctime(), (end - start))
    work_queue.put(msg)

    # All to be end.
    work_queue.put("ENDTAG")
    printer.join()

    # finally subdir name handle
    if args.a:
            FileSafe.subDirNameEncode()
    
    # close db
    db.close()

    # remove db file after decrypt 
    if args.d:
        os.remove(dbfile + '.db')

    # work_queue.join()
