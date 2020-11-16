# coding: utf-8
import socket
import threading
import time
import sys
import random

# Server port
serverPort = int(sys.argv[1])   # 400
# The user failed to prevent three times of authentication:(seconds)
block_duration = int(sys.argv[2])  # 60


# Initialize the server
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('127.0.0.1', serverPort))
server.listen(5)

# Blocking logon users
blockedUser = dict()    # example:  {username: [start_time, end_time]}
credentials = dict()    # example:  {username: password}
tempIDs = dict()        # example:  {username: {tempID:'', startTime:'', endTime:''}}

# The duration of tempID (minute)
tempID_duration = 15


def init_data():
    global credentials
    global tempIDs

    # read credentials.txt
    with open("credentials.txt", "r") as file:
        content = file.read().splitlines()
        for text in content:
            if text != "":
                data = text.split(" ")
                user, pwd = data[0], data[1]
                credentials[user] = pwd

    # read tempIDs.txt
    with open("tempIDs.txt", "r") as file2:
        content = file2.read()
        for text in content.split("\n"):
            data = text.split()
            username = data[0]
            tempID = data[1]
            startTime = data[2] + " " + data[3]
            endTime = data[4] + " " + data[5]
            tempIDs.update({
                username: {
                    "tempID": tempID,
                    "startTime": startTime,
                    "endTime": endTime
                }
            })


# keep tempID valid
def update_tempID():
    global tempID_duration
    # Check that tempID is valid every 10 seconds
    while True:
        nowTimeStamp = time.time()
        hasUpdate = False
        for username in tempIDs:
            endTime = tempIDs[username]['endTime']
            endTimeStamp = time.mktime(time.strptime(endTime, '%d/%m/%Y %H:%M:%S'))
            # tempID invalid, update tempID
            if endTimeStamp < nowTimeStamp:
                tempIDs[username]['tempID'] = create_tempID()

                startTime = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time()))
                # endTime is Current timestamp + (tempID_duration * 60)
                endTime = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time() + tempID_duration * 60))

                tempIDs[username]['startTime'] = startTime
                tempIDs[username]['endTime'] = endTime
                hasUpdate = True

        # If tempID is updated, write to the file

        if hasUpdate:
            with open("tempIDs.txt", "w") as file_tempID:
                line = 0
                for username, items in tempIDs.items():
                    content = username + " " + items['tempID'] + " " + items['startTime'] + " " + items['endTime']
                    if line == 0:
                        file_tempID.write(content)
                    else:
                        file_tempID.write('\n' + content)
                    line += 1

        time.sleep(10)


# create new tempID
def create_tempID():
    key = ""
    for i in range(20):
        key += str(random.randint(0, 9))
    return key


def register(username, password):
    global credentials

    credentials.update({username: password})
    tempIDs.update({
        username: {
            'tempID': create_tempID(),
            'startTime': time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time())),
            'endTime': time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time() + tempID_duration * 60))
        }
    })

    # update credentials.txt
    with open("credentials.txt", "a") as f:
        f.write("\n" + username + " " + password)

    # update tempIDs.txt
    with open("tempIDs.txt", "a") as f2:
        items = tempIDs[username]
        content = username + " " + items['tempID'] + " " + items['startTime'] + " " + items['endTime']
        f2.write("\n" + content)


# Check if the user has a tempID, If not, generate tempID
def login(username):
    if username not in tempIDs:
        tempIDs.update({
            username: {
                'tempID': create_tempID(),
                'startTime': time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time())),
                'endTime': time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(time.time() + tempID_duration * 60))
            }
        })

        # update tempIDs.txt
        with open("tempIDs.txt", "a") as f2:
            items = tempIDs[username]
            content = username + " " + items['tempID'] + " " + items['startTime'] + " " + items['endTime']
            f2.write("\n" + content)


def print_contactlog(data):
    if data == "":
        return
    content = data.splitlines()
    for text in content:
        if text != "":
            data = text.split(" ")
            print("{}, {} {}, {} {};".format(*data))


def check_contactlog(data):
    if data == "":
        return
    print("Contact log checking")
    content = data.splitlines()
    for text in content:
        if text != "":
            data = text.split(" ")
            temp_id = data[0]
            start_time = data[1] + " " + data[2]
            findUser = None
            hasTempID = False
            for username, item in tempIDs.items():
                if item['tempID'] == temp_id:
                    findUser = username
                    hasTempID = True

            if hasTempID:
                print("{}, {}, {};".format(findUser, start_time, temp_id))
            else:
                print("No user of the {} was found".format(temp_id))


def recv_client(client, address):
    global block_duration

    # The status code returned when the user logs in
    class LoginStatus:
        BlockedAccount = "-2"
        PasswordError = "-1"
        LoginInhibited = "0"
        LoginSuccess = "1"

    # The user name sent by the client is received
    username = client.recv(2048).decode()

    # Determine if the user is registered
    if username in credentials:
        message = "registered"
        client.send(message.encode())
        password = client.recv(2048).decode()
    else:
        message = "unregistered"
        client.send(message.encode())
        password = client.recv(2048).decode()
        register(username, password)

    # Determines whether the logged in user is in a blocking queue
    if username in blockedUser:
        nowTime = int(time.time())  # now timestamp
        blockStartTime, blockEndTime = blockedUser[username]
        # If the user is still in the block time
        if blockStartTime <= nowTime <= blockEndTime:
            client.send(LoginStatus.BlockedAccount.encode())
            return

    # Determine if the password is correct
    tryCount = 0
    while True:
        # Password is correct
        if credentials[username] == password:
            # login success
            login(username)
            client.send(LoginStatus.LoginSuccess.encode())
            message = "Welcome to the BlueTrace Simulator!"
            client.send(message.encode())
            break

        tryCount += 1
        # if too many incorrect passwords are typed, Login inhibited
        if tryCount == 3:
            client.send(LoginStatus.LoginInhibited.encode())
            # Record blocking user
            nowTime = int(time.time())  # now timestamp
            blockStartTime, blockEndTime = nowTime, nowTime + block_duration
            blockedUser[username] = [blockStartTime, blockEndTime]
            return
        # Password error, try login again
        client.send(LoginStatus.PasswordError.encode())
        password = client.recv(2048).decode()

    # After successful login:
    while True:
        command = client.recv(2048).decode()
        # print(command)
        if command == "Download_tempID":
            client.send(tempIDs[username]['tempID'].encode())

        elif command == "Upload_contact_log":
            recv_size = 0
            file_size = int(client.recv(2048).decode())
            data = ""
            while True:
                data = client.recv(2048).decode()
                recv_size += len(data)
                if recv_size == file_size:
                    break

            print("received contact log from " + username)
            print_contactlog(data)
            check_contactlog(data)

        elif command == "logout":
            print(username, "logout")
            message = "logout success"
            client.send(message.encode())
            return


if __name__ == "__main__":
    init_data()
    updateTask = threading.Thread(target=update_tempID)
    updateTask.start()
    while True:
        conn, addr = server.accept()
        print("Connected by:", addr)
        clientThread = threading.Thread(target=recv_client, args=(conn, addr))
        clientThread.daemo = True
        clientThread.start()

