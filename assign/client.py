# COMP3331 Assignment 
# BlUETRACE protocol simulator
# client.py
# Zixuan Guo (z5173593)


# coding: utf-8
import socket
import threading
import time
import sys

# Get <server address> <server port> <UDP port> from the command
serverAddr = sys.argv[1]    # '127.0.0.1'
serverPort = int(sys.argv[2])    # 4000
udpPort = int(sys.argv[3])      # 8000

# Create TCP UDP communication
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clientSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Connect to the server
serverSocket.connect((serverAddr, serverPort))
# Bind UDP port
clientSocket.bind(('localhost', udpPort))

# contact log retention time (minute)
logRetention = 3
contactlog = dict()     # example:  {tempID: {startTime:'', endTime:'', durationTime:''}}

tempID = ""
t_lock = threading.Condition()


# read z5173593_contactlog.txt
def read_contactlog():
    global contactlog
    with open("z5173593_contactlog.txt", "r") as file:
        content = file.read().splitlines()
        for text in content:
            if text != "":
                data = text.split(" ")
                tempID = data[0]
                startTime = data[1] + " " + data[2]
                endTime = data[3] + " " + data[4]

                # Add log retention time,
                # If the log retention time is exceeded,
                # the log record is deleted.
                durationTime = int(time.time() + logRetention * 60)
                contactlog.update({
                    tempID: {
                        "startTime": startTime,
                        "endTime": endTime,
                        "durationTime": durationTime
                    }
                })


# check contactlog, If the log retention time is exceeded, the log record is deleted
def check_contactlog_valid():
    global contactlog
    # Check that contactlog is valid every 5 seconds
    while True:
        with t_lock:
            if t_lock.acquire():
                delKeys = list()
                for tempID, item in contactlog.items():
                    nowTimeStamp = int(time.time())
                    durationTime = int(item['durationTime'])
                    # Log retention time exceeded, the log record is deleted
                    if durationTime < nowTimeStamp:
                        delKeys.append(tempID)

                for i in range(len(delKeys)):
                    contactlog.pop(delKeys[i])
                # Update contactlog file
                save_contactlog()

                t_lock.notify()
                t_lock.release()
        time.sleep(5)


# add one contactlog
def add_contactlog(temp_id, start_time, end_time):
    with t_lock:
        if t_lock.acquire():

            durationTime = int(time.time() + logRetention * 60)
            contactlog.update({
                temp_id: {
                    "startTime": start_time,
                    "endTime": end_time,
                    "durationTime": durationTime
                }
            })
            save_contactlog()

            t_lock.notify()
            t_lock.release()


# Update contactlog file
def save_contactlog():
    with open("z5173593_contactlog.txt", "w") as file:
        # line = 0
        for tempID, item in contactlog.items():
            content = tempID + " " + item["startTime"] + " " + item["endTime"]
            file.write(content + "\n")
            # if line == 0:
            #     file.write(content)
            # else:
            #     file.write(content + "\n")
            # line += 1


# Beacon <dest_ip> <dest_port>
def send_udp(dest_ip, dest_port):
    global tempID
    global serverPort
    if tempID == "":
        print("You haven't downloaded tempID yet.")
        return
    if dest_port == serverPort:
        print("upd communication should be sent to the client, not the server")
        return
            
    startTime = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time()))
    endTime = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time() + 15 * 60))
    message = tempID + "-" + startTime + "-" + endTime
    clientSocket.sendto(message.encode(), (dest_ip, dest_port))


# Upload the Contactlog file to the server
def upload_contact_log():

    with t_lock:
        if t_lock.acquire():
            with open("z5173593_contactlog.txt", "r") as file:
                content = file.read()
                # send file size
                serverSocket.send(str(len(content)).encode())
                message = serverSocket.recv(2048).decode()
                if message == "ok" and len(content) != 0:
                    # send file data
                    serverSocket.sendall(content.encode())

        t_lock.notify()
        t_lock.release()


# Receive udp client messages
def recv_udp():
    global clientSocket
    while True:
        Message, Address = clientSocket.recvfrom(2048)
        data = Message.decode().split("-")

        recv_tempID = data[0]
        recv_startTime = data[1]
        recv_endTime = data[2]

        print("received beacon:\n{}, {}, {}.".format(recv_tempID, recv_startTime, recv_endTime))

        nowTimeStamp = time.time()
        startTimeStamp = time.mktime(time.strptime(recv_startTime, '%d/%m/%Y %H:%M:%S'))
        endTimeStamp = time.mktime(time.strptime(recv_endTime, '%d/%m/%Y %H:%M:%S'))

        date_time = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(nowTimeStamp))
        print('Current time is {}.'.format(date_time))

        if startTimeStamp <= nowTimeStamp <= endTimeStamp:
            print("The beacon is valid.")
            add_contactlog(recv_tempID, recv_startTime, recv_endTime)
        else:
            print("The beacon is invalid.")


# Receiving server message
def recv_server():
    # The status code returned when the user logs in
    class LoginStatus:
        BlockedAccount = "-2"
        PasswordError = "-1"
        LoginInhibited = "0"
        LoginSuccess = "1"

    # Enter user name
    serverSocket.send(input("Username: ").encode())
    message = serverSocket.recv(2048).decode()
    if message == 'unregistered':
        print("The user is not registered and will enter the registration process.")

    # Enter password
    while True:
        serverSocket.send(input("Password: ").encode())

        status = serverSocket.recv(2048).decode()
        if status == LoginStatus.LoginSuccess:
            welcome_message = "Welcome to the BlueTrace Simulator!"
            print(welcome_message)
            break
        elif status == LoginStatus.PasswordError:
            print("Invalid Password. Please try again")
            continue
        elif status == LoginStatus.LoginInhibited:
            print("Invalid Password. Your account has been blocked. Please try again Later")
            return
        elif status == LoginStatus.BlockedAccount:
            print("Your account is blocked due to multiple login failures. Please try again later")
            return
        else:
            print("error:" + status)

    menu = """---------------------------
options:
    Download_tempID
    Upload_contact_log
    Beacon <dest IP> <dest port>
    logout
---------------------------"""
    print(menu)

    while True:
        command = input()   # "Command: "
        if command == "Download_tempID":
            serverSocket.send(command.encode())
            global tempID
            tempID = serverSocket.recv(2048).decode()
            print("TempID: " + tempID)

        elif command == "Upload_contact_log":
            serverSocket.send(command.encode())
            upload_contact_log()

        elif command[:6] == "Beacon":
            data = command.split(" ")
            dest_ip = data[1]
            dest_port = int(data[2])
            send_udp(dest_ip, dest_port)

        elif command == "logout":
            serverSocket.send(command.encode())
            message = serverSocket.recv(2048).decode()
            print(message)
            return
        else:
            print("Error. Invalid command")
            continue


if __name__ == "__main__":
    read_contactlog()

    udpThread = threading.Thread(target=recv_udp)
    udpThread.daemon = True
    udpThread.start()

    checkLogThread = threading.Thread(target=check_contactlog_valid)
    checkLogThread.daemon = True
    checkLogThread.start()

    recv_server()
