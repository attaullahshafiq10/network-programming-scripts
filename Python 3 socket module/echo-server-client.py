# Echo client Program
# HM Attaullah
# mr_attaullah@hotmail.com

import socket

HOST = 'localhost'
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send(b 'Hello, Attaullah')
data = s.recv(1024)
s.close()
print('Recieved' , repr(data))
