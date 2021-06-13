#!/usr/bin/env python

###########################################################################

import os
import shutil

def EnsureDir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def RemoveDir(path):
    if os.path.exists(path):
        shutil.rmtree(path)

def split_list(a, n):
    k, m = divmod(len(a), n)
    return (a[i*k+min(i, m):(i+1)*k+min(i+1, m)] for i in range(n))

###########################################################################

# min_len - number, lower boundary for length of password (>=)
# max_len - number, upper boundary for length of password (<=)
# charset - list of characters ['a', 'b']
from itertools import product as iterproduct
def gen_passwords(min_len, max_len, charset):
    for length in range(min_len,max_len+1):
        for item in iterproduct(charset, repeat=length):
            yield "".join(item)

# used to calculate number of possible passwords without actually creating them
def calculate_number_of_passwords(min_len, max_len, charset):
    output = 0
    for i in range(min_len, max_len+1):
        output = output + len(charset) ** i
    return output


###########################################################################

# filename - string, name of ZIP file
# index - process index, for VERBOSEose output
# passwords - list of strings, containing all passwords to be checked
# tmpdir - path to temporary directory. MUST BE ENSURED AND DELETED OUTSIDE OF THIS FUNCTION
from zipfile import ZipFile
def decrypt(filename, process_index, verbose, passwords, tmppath):
    file = ZipFile(filename)
    pass_num = len(passwords)
    index = 0
    for password in passwords:
        if verbose > 0:
            index=index+1
            if index % verbose == 0:
                print(f'Process {process_index}: checked {index}/{pass_num} passwords in current bulk') 
        try:
            file.extractall(path=tmppath, pwd=password.encode())
            return password
        except:
            continue
    return None

###########################################################################

import multiprocessing
from multiprocessing import Process, Manager
from ctypes import c_char_p

def subprocess(ret, index, verbose, filename, tmpdir, passwords, ):
    pid = os.getpid()
    tmppath = tmpdir + "/" + str(pid)
    EnsureDir(tmppath)
    result = decrypt(filename, index, verbose, passwords, tmppath)
    RemoveDir(tmppath)
    ret.value = result if result else ""

def start(filename, passwords, tmpdir, thread_num, verbose):
    splitted_passwords = list(split_list(passwords, thread_num))
    threads = []
    manager = Manager()
    
    index = 0 # for output
    for pass_list in splitted_passwords:
        index = index+1
        ret = manager.Value(c_char_p, "")
        thread = Process(target=subprocess, args=(ret, index, verbose, filename, tmpdir, pass_list,))
        thread.start()
        threads.append( (thread, ret) )
    
    still_alive = True
    output = None
    while still_alive:
        still_alive = False
        for (thread,ret) in threads:
            if thread.is_alive():
                still_alive = True 
            else:
                if ret.value != "":
                    output = ret.value
                    still_alive = False
                    break
    for (thread,ret) in threads:
        if thread.is_alive():
            thread.terminate()
    return output

def contact_server(ip, tmpdir, thread_num):
    return 1


def main(ip, thread_num, verbose):
    thread_num = int(thread_num) if thread_num else multiprocessing.cpu_count()
    verbose = int(verbose) if verbose else 10000
    EnsureDir(".tmp")
    #charset = [ i for i in "abcdefghijklmnopqrstuvwxyz1234567890" ]
    charset = [ i for i in "1234567890" ]
    pwd = [p for p in gen_passwords(4,6,charset) ]
    print(start("a.zip", pwd, ".tmp", thread_num, verbose))
    RemoveDir(".tmp")

###########################################################################

import argparse
parser = argparse.ArgumentParser(description='Client program. Allows to connect to the server, in order to crack.')
parser.add_argument('-ip', required=True, metavar='ip', help='IP address of the server')
parser.add_argument('-threads', required=False, metavar='threads', help='Number of threads to be used')
parser.add_argument('-verbose', required=False, metavar='verbose', help='Number of passwords, after which program will raport progress')
# args.ip
if __name__ == '__main__':
    args = parser.parse_args()
    #charset = [ i for i in "abcdefghijklmnopqrstuvwxyz1234567890" ]
    charset = [ i for i in "1234567890" ]
    main(args.ip, args.threads, args.verbose)