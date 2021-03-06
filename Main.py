#pylint: disable=C0111,C0103
#disable warnings for variable names and docstrings
import socket
import sys
import os
from concurrent.futures import ThreadPoolExecutor

HOST = ''   # Symbolic name, meaning all available interfaces
PORT = int(sys.argv[1])
master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
name_ref_dict = {}
ref_name_dict = {}
client_ref_dict = {}
all_chatrooms = {}

client_code = 0
chat_code = 0

def next_client_code():
    global client_code
    client_code += 1
    return client_code

def next_chat_code():
    global chat_code
    chat_code += 1
    return chat_code

def getData(params, index):
    return " ".join(params[index].split(" ")[1:]).strip('\n')


def clientthread(connection, address):
    #Sending message to connected client
    #infinite loop, stays connected until client disconnects.
    connected = True
    while connected:
        #Receiving from client
        #clients are identified by their connections
        # chatrooms are dictionaries where key is chatroom id and value is list of connections (clients) in chatroom
        data = connection.recv(8192)
        print "Recevied: " + data
        if not data:
            break
        elif data[:4] == "HELO":
            reply = str(data) + "IP:"+socket.gethostbyname(socket.gethostname())+"\nPort:" + str(PORT) + "\nStudentID:13320989"
            connection.sendall(reply)

        elif data[:len("KILL_SERVICE")] == "KILL_SERVICE":
            print "recognised kill service"
            if len(all_chatrooms) > 0:
                for chat in all_chatrooms: #disconnect all users
                    for client_conn in all_chatrooms[chat]["connections"]:
                        client_conn.close()
            connection.close()
            print "Shutting Down"
            os._exit(1) #end program

        elif data[:len("JOIN_CHATROOM")] == "JOIN_CHATROOM":
            print "received request to join"
            params = data.split('\n')
            chat_name = getData(params, 0)
            client_name = getData(params, 3)
            if chat_name not in name_ref_dict:
                ref_number = next_chat_code()
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
            reply = "CHAT:"+name_ref_dict[chat_name]+"\nCLIENT_NAME:"+client_name+"\nMESSAGE:"+client_name+" has joined this chatroom.\n\n"
            for client_conn in all_chatrooms[chat_name]["connections"]:
                client_conn.sendall(reply)
            print "finished joining"

        elif data[:len("LEAVE_CHATROOM")] == "LEAVE_CHATROOM":
            print "recognised leave"
            params = data.split('\n')
            room_ref = getData(params, 0)
            join_id = getData(params, 1)
            client_name = getData(params, 2)
            chat = ref_name_dict[room_ref]
            try:
                reply = "LEFT_CHATROOM: "+room_ref+"\nJOIN_ID: "+join_id+"\n"
                connection.sendall(reply)
                for client_conn in all_chatrooms[chat]["connections"]:
                    reply = "CHAT:"+room_ref+"\nCLIENT_NAME:"+client_name+"\nMESSAGE:"+client_name+" has left this chatroom.\n\n"
                    print reply
                    client_conn.sendall(reply)
                    print "sent leave message to "+chat
            except Exception:
                print "Already left"
            all_chatrooms[chat]["connections"].remove(connection)
            print "left chatroom "+chat
        
        elif data[:len("CHAT:")] == "CHAT:":
            params = data.split('\n')
            room_ref = getData(params, 0)
            chat = ref_name_dict[room_ref]
            join_id = getData(params, 1)
            client_name = getData(params, 2)
            message = getData(params, 3)

            reply = "CHAT: "+room_ref+"\nCLIENT_NAME: "+client_name+"\nMESSAGE: "+message+"\n\n"
            for client_conn in all_chatrooms[chat]["connections"]:
                client_conn.sendall(reply)
            print "sent message"

        elif data[:len("DISCONNECT")] == "DISCONNECT":
            print "recognised disconnect"
            connected = False
            params = data.split('\n')
            client_name = getData(params, 2)
            chats = list(all_chatrooms.keys())[::-1]
            for chat in chats:
                print "checking ", chat
                if connection in all_chatrooms[chat]["connections"]:
                    print "removing from "+ chat
                    reply = "CHAT:"+name_ref_dict[chat]+"\nCLIENT_NAME:"+client_name+"\nMESSAGE:"+client_name+" has left this chatroom.\n\n"
                    for client_conn in all_chatrooms[chat]["connections"]:
                        client_conn.sendall(reply)
                    all_chatrooms[chat]["connections"].remove(connection)
            connection.close()

    #came out of loop
    print "closing connection"
    connection.close()

if __name__ == "__main__":
    print 'Socket created successfully'
    #Bind socket to local host and port
    pool = ThreadPoolExecutor(128)
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
        cl_ref_number = next_client_code()
        client_ref_dict[str(addr[0])+str(addr[1])] = cl_ref_number
        pool.submit(clientthread, conn, addr)
    master_socket.close()
