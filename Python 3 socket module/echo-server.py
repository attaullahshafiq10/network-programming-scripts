# Echo server Program
# HM Attaullah
# mr_attaullah@hotmail.com

import socket

HOST = socket.gethostname()
PORT = 50007
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print("connected by" , addr)
while True:
    data = conn.recv(1024)
    if not data: break
    conn.send(data)
conn.close()                 
                  
                  
                  
