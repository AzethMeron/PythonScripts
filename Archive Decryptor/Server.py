#!/usr/bin/env python

import socket

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

def get_passwords(generator, number):
    index = 0
    output = []
    for i in generator:
        index = index+1
        if index > number:
            break
        output.append(i)
    return output

###########################################################################

import pickle
    
def main(ip, port, filename, charset, min_len, max_len, passwords_per_thread):
    generator = gen_passwords(min_len, max_len, charset)
    file = (filename, open(filename,"rb").read()) # (filename, ByteString)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as main_socket:
        main_socket.bind((ip, port))
        #main_socket.settimeout(10)
        main_socket.listen()
        try:
            conn, addr = main_socket.accept()
            conn.sendall(file[0].encode())
            conn.sendall(pickle.dumps(len(file[1])))
            conn.sendall(file[1])
            per_bulk = passwords_per_thread
            max_num = 1+int(calculate_number_of_passwords(min_len,min_len,charset) / per_bulk)
            conn.sendall(pickle.dumps(max_num))
            for i in range(1, max_num):
                passwords = [ i for i in get_passwords(generator, per_bulk) if i != [] ]
                data = pickle.dumps(passwords)
                conn.sendall(pickle.dumps(len(data)))
                conn.sendall(data)
                result = pickle.loads(conn.recv(1024))
                if result != "":
                    return result
        except Exception as e:
            print(e)

###########################################################################

if __name__ == '__main__':
    charset = set([ i for i in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890" ])
    ip = str(socket.gethostbyname(socket.gethostname()))
    print("IP of this server: " + ip)
    port = 65432
    filename = "a.zip"
    print(main(ip, port, filename, charset, 4, 4, 50000))
    
    
    
    