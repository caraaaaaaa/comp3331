# COMP3331 Lab 2
# z5173593
# Zixuan Guo


import time
from socket import *


import sys
host = sys.argv[1]
serverPort = int(sys.argv[2])


clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(1)  

for i in range(0, 15):
    sendTime = time.time()
    # PING sequence_number time CRLF
    message = ('PING %d %s\r\n' % (i + 1, sendTime)).encode()
    try:
    	# send
        clientSocket.sendto(message, (host, serverPort)) 
        modifiedMessage, serverAddress = clientSocket.recvfrom(2048) 
        # RTT
        rtt = time.time() - sendTime
        print('ping to %s, seq = %d, rtt = %fms' % (host, i+1, rtt*1000))
    # timeout    
    except Exception as e:
        print('ping to %s, seq = %d: Request timed out' % (host, i+1)) 

clientSocket.close()