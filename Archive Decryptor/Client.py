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

# filename - string, name of ZIP file
# process_index - process index, for VERBOSEose output
# verbose - number of passwords, after which program will raport progress 
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
import time

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
        time.sleep(10)
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

###########################################################################

import socket
import pickle

def init_connection(conn, thread_num):
    return 1

def run_task(conn, thread_num, verbose):
    return 1

def send_results(conn, result):
    return 1

def main(ip, port, thread_num, verbose):
    EnsureDir(".tmp")
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip, port))
            found = pickle.loads(s.recv(8)) # receive "found" from server
            print(found)
            if found:
                break
    RemoveDir(".tmp")

###########################################################################

import argparse
parser = argparse.ArgumentParser(description='Client program. Allows to connect to the server, in order to crack.')
parser.add_argument('-ip', required=True, metavar='ip', help='IP address of the server')
parser.add_argument('-port', required=False, metavar='port', help='IP address of the server')
parser.add_argument('-threads', required=False, metavar='threads', help='Number of threads to be used')
parser.add_argument('-verbose', required=False, metavar='verbose', help='Number of passwords, after which program will raport progress')
if __name__ == '__main__':
    args = parser.parse_args()
    thread_num = int(args.threads) if args.threads else multiprocessing.cpu_count()
    verbose = int(args.verbose) if args.verbose else 100000
    port = int(args.port) if args.port else 65432
    main(args.ip, port, thread_num, verbose)