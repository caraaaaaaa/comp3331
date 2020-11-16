#coding: utf-8
from socket import *
#using the socket module

import sys

#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
# change this port number if required
#serverPort = 12000 


if len(sys.argv) > 2 or len(sys.argv) < 1:
	print('Should only type -port- after .py')
	sys.exit()

serverPort = int(sys.argv[1])

if serverPort == 80 or serverPort == 8080 or serverPort < 1024:
	print('Please change to another port number')
	sys.exit()

serverSocket = socket(AF_INET, SOCK_STREAM)
#This line creates the server’s socket. The first parameter indicates the address family; in particular,AF_INET indicates that the underlying network is using IPv4.The second parameter indicates that the socket is of type SOCK_STREAM,which means it is a TCP socket (rather than a UDP socket, where we use SOCK_DGRAM).

serverSocket.bind(('localhost', serverPort))
#The above line binds (that is, assigns) the port number 12000 to the server’s socket. In this manner, when anyone sends a packet to port 12000 at the IP address of the server (localhost in this case), that packet will be directed to this socket.

serverSocket.listen(1)
#The serverSocket then goes in the listen state to listen for client connection requests. 

print('Server is ready to receive')

while 1:
	connectionSocket, addr = serverSocket.accept()

	sentence = connectionSocket.recv(1024)
	#wait for data to arrive from the client

	fileName = sentence.split()[1][1:]

	try:	
		file = open(fileName, "r")
		response = file.read()
		file.close()

		data = "HTTP/1.1 200 OK \r\n".encode()

		connectionSocket.send(data)
		if "html".encode() in fileName:
			data = "Content-Type: text/html \r\n\r\n".encode()
			connectionSocket.send(data)

		if "png".encode() in fileName:
			data = "Content-Type: image/png \r\n\r\n".encode()
			connectionSocket.send(data)

		connectionSocket.send(response)
		connectionSocket.close()

		print('file ' + fileName + ' request success')

	except IOError:
		data = "HTTP/1.1 File Not Found \r\n".encode()
		connectionSocket.send(data)
		data = "Content-Type: text/html \r\n\r\n".encode()

		connectionSocket.send(data)
		connectionSocket.send("<html><h1>File Not Found</h1><p></html>".encode())
		connectionSocket.close()

		print('file ' + fileName + ' Not Found')