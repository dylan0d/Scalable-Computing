import socket
import sys
import os
from thread import *

HOST = ''   # Symbolic name, meaning all available interfaces
PORT = int(sys.argv[1]) # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
all_connections = []

def clientthread(connection):
    #Sending message to connected client
    connection.send('Welcome to the server. Type something and hit enter\n') #send only takes string

    #infinite loop so that function do not terminate and thread do not end.
    while True:

        #Receiving from client
        data = connection.recv(1024)
        if data == "KILL_SERVICE\n":
            for conn in all_connections:
                conn.close()
            s.close()
            "Shutting Down"
            os._exit(1)
            break
        reply = 'OK...' + data
        if not data:
            break
        for conn in all_connections:
            if not conn == connection:
                conn.sendall(reply)

    #came out of loop
    conn.close()

if __name__ == "__main__":
    print 'Socket created successfully'

    #Bind socket to local host and port
    try:
        s.bind((HOST, PORT))
    except socket.error as msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()

    print 'Socket bind complete'

    #Start listening on socket
    s.listen(10)
    print 'Socket now listening'

    #now keep talking with the client
    while 1:
        #wait to accept a connection - blocking call
        conn, addr = s.accept()
        print 'Connected with ' + addr[0] + ':' + str(addr[1])
        all_connections.append(conn)
        start_new_thread(clientthread, (conn,))

    s.close()
