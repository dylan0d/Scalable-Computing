#pylint: disable=C0111,C0103
#disable warnings for variable names and docstrings
import socket
import sys
import os
from thread import start_new_thread
from random import randint

HOST = ''   # Symbolic name, meaning all available interfaces
PORT = int(sys.argv[1]) # Arbitrary non-privileged port
master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
name_ref_dict = {}
ref_name_dict = {}
client_ref_dict = {}
all_chatrooms = {}

def getData(params, index):
    return " ".join(params[index].split(" ")[1:]).strip('\n')


def clientthread(connection, address):
    #Sending message to connected client
    #infinite loop so that function do not terminate and thread do not end.
    connected = True
    while connected:
        #Receiving from client
        print "hello I am alive"
        data = connection.recv(8192)
        print "data: "+data
        if not data:
            break
        elif data[:4] == "HELO":
            reply = str(data) + "IP:" + str(address[0]) + ":" + str(address[1]) + "\nPort:" + str(PORT) + "\nStudentID:13320989"
            connection.sendall(reply)

        elif data == "KILL_SERVICE\n":
            if len(all_chatrooms)>0:
                for chat in all_chatrooms:
                    for client_conn in chat["connections"]:
                        client_conn.close()
            connection.close()
            print "Shutting Down"
            os._exit(1)
            break
        elif data[:len("JOIN_CHATROOM")] == "JOIN_CHATROOM":
            params = data.split('\n')
            chat_name = getData(params, 0)
            ip = getData(params, 1)
            port =getData(params, 2)
            client_name = getData(params, 3)
            if chat_name not in name_ref_dict:
                picked_ref = False
                while not picked_ref:
                    ref_number = randint(0, 128)
                    if ref_number not in name_ref_dict.itervalues():
                        picked_ref = True
                        name_ref_dict[chat_name] = str(ref_number)
                        ref_name_dict[str(ref_number)] = chat_name
                all_chatrooms[chat_name] = {
                    "connections":[connection],
                    "IP":"127.0.0.1",
                    "Port":str(PORT),
                    "ref":name_ref_dict[chat_name]
                }
            else:
                if connection not in all_chatrooms[chat_name]["connections"]:
                    all_chatrooms[chat_name]["connections"].append(connection)
            reply = "JOINED_CHATROOM: "+chat_name+"\nSERVER_IP: "+str(all_chatrooms[chat_name]["IP"])+"\nPORT: "+str(all_chatrooms[chat_name]["Port"])+"\nROOM_REF: "+str(name_ref_dict[chat_name])+"\nJOIN_ID: "+str(client_ref_dict[str(address[0])+str(address[1])])+"\n"
            connection.sendall(reply)
            reply = "CHAT:"+name_ref_dict[chat_name]+"\nCLIENT_NAME:"+client_name+"\nMESSAGE:"+client_name+" has joined this chatroom.\n"
            print all_chatrooms
            for conn in all_chatrooms[chat_name]["connections"]:
                print reply
                conn.sendall(reply)
            print "finished joining"

        elif data[:len("LEAVE_CHATROOM")] == "LEAVE_CHATROOM":
            print "recognised leave"
            params = data.split('\n')
            room_ref = getData(params, 0)
            join_id = getData(params, 1)
            client_name = getData(params, 2)
            chat = ref_name_dict[room_ref]
            print chat
            try:
                print "connection removed"
                for conn in all_chatrooms[chat]["connections"]:
                    reply = "CHAT:"+name_ref_dict[chat_name]+"\nCLIENT_NAME:"+client_name+"\nMESSAGE:"+client_name+" has left this chatroom."
                    print reply
                    conn.sendall(reply)
                    print "sent reply"
            except Exception:
                print "Already left"

            reply = "LEFT_CHATROOM: "+room_ref+"\nJOIN_ID: "+join_id+"\n\n"
            connection.sendall(reply)
            all_chatrooms[chat]["connections"].remove(connection)

        
        elif data[:len("CHAT:")] == "CHAT:":
            params = data.split('\n')
            room_ref = getData(params, 0)
            chat = ref_name_dict[room_ref]
            join_id = getData(params, 1)
            client_name = getData(params, 2)
            message = getData(params, 3)

            reply = "CHAT: "+room_ref+"\nCLIENT_NAME: "+client_name+"\nMESSAGE: "+message+"\n\n"
            for conn in all_chatrooms[chat]["connections"]:
                if not conn is connection:
                    conn.sendall(reply)
        
        elif data[:len("DISCONNECT")] == "DISCONNECT":
            connected = False
        print "starting while again"
    #came out of loop
    print "left loop unexpectedly"
    connection.close()

if __name__ == "__main__":
    print 'Socket created successfully'
    #Bind socket to local host and port
    try:
        master_socket.bind((HOST, PORT))
    except socket.error as msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()

    print 'Socket bind complete'

    #Start listening on socket
    master_socket.listen(10)
    print 'Socket now listening'

    #now keep talking with the client
    while 1:
        #wait to accept a connection - blocking call
        conn, addr = master_socket.accept()
        print 'Connected with ' + addr[0] + ':' + str(addr[1])
        picked_ref = False
        while not picked_ref:
            ref_number = randint(0, 1024)
            if ref_number not in name_ref_dict.itervalues():
                picked_ref = True
                client_ref_dict[str(addr[0])+str(addr[1])] = ref_number
        start_new_thread(clientthread, (conn, addr))

    master_socket.close()
