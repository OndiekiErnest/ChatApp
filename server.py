"""
Modified by Abdur-rahmaan Janhangeer
arj.python@gmail.com

Challenge in Telegram @deliciouspy
Taken by Ernesto
ernestondieki12@gmail.com
"""

import socket
import threading
import parse_message
from struct import pack, unpack

# All the prints and errors can be logged better


# Global variable that mantains client's connections
connections = []
is_busy = False


class _Session():
    """
        Store information about the clients
    """
    __slots__ = "socket", "username", "address"

    def __init__(self, connection: socket.socket, user: str, addr: str):
        self.socket = connection
        self.username = user
        self.address = addr


def pad_message(msg: str, msg_type="str") -> bytes:
    """
        Pack strings for transfer (>QI == 12 bytes)
        Used for strings only
    """
    msg_type = msg_type.encode()
    msg_length = len(msg.encode())
    padded = pack(">QI", msg_length, len(msg_type))
    # return bytes
    return padded


def receive_all(sock: socket.socket, n: int) -> bytearray:
    """
        recv n bytes of strings; return None on EOF
    """
    data = bytearray()
    while len(data) < n:
        to_read = n - len(data)
        packet = sock.recv(
            4194304 if to_read > 4194304 else to_read)
        data.extend(packet)
    return data


def handle_user_connection(connection: _Session, address: str) -> None:
    '''
        Get user connection in order to keep receiving their messages and
        sent to others users/connections.
    '''
    while True:
        try:

            # If no message is received, there is a chance that connection has ended
            # so in this case, we need to close connection and remove it from connections list.
            first_msg = connection.socket.recv(12)
            if first_msg:
                # Get client message
                msg_length, ext_length = unpack(">QI", first_msg)
                sec_msg = connection.socket.recv(ext_length)
                extension = unpack(f"{ext_length}s", sec_msg)[0].decode()
                if extension == "str":
                    msg = receive_all(connection.socket, msg_length)
                    # Log message sent by user, 'replace' errors for terminal print
                    print(f'[MESSAGE] : {msg.decode("utf-8","replace")}')

                    # broadcast to users connected to server
                    send(first_msg, extension, msg.decode(), connection.socket)

                else:
                    # send to only those online at the moment
                    online = connections
                    print('[MESSAGE] : File')
                    is_busy = True
                    msg = connection.socket.recv(4194304)
                    send(first_msg, extension, msg, connection.socket)
                    while 1:
                        # receive as we send for memory sake
                        msg = connection.socket.recv(4194304)
                        if msg:
                            broadcast(msg, connection.socket,
                                      list_connections=online)
                        else:
                            break
                    # I don't know why when I omit the line below, the receiver hangs
                    broadcast(msg, connection.socket)
                    is_busy = False

            # Close connection if no message was sent/received
            else:
                print(f"[DISCONNECTION] : {connection.username}")
                to_send = f'{connection.username} went offline!'
                lengths = pad_message(to_send)
                send(lengths, "str", to_send, connection.socket)
                remove_connection(connection)
                break

        except Exception as e:
            # print(f'Error handling user connection: {e}')
            # pad message that are originating from only the server
            print(f"[DISCONNECTION] : {e}")
            to_send = f'{connection.username} went offline!'
            lengths = pad_message(to_send)
            send(lengths, "str", to_send, connection.socket)
            # minus 2; one who left and the receiver
            to_send = f"[{len(connections)-2} online]"
            lengths = pad_message(to_send)
            send(lengths, "str", to_send, connection.socket)
            remove_connection(connection)
            break


def broadcast(message: bytes, connection: socket.socket, list_connections=connections) -> None:
    '''
        Broadcast message to all users connected to the server
    '''

    # Iterate on connections in order to send message to all client's connected
    for client_conn in list_connections:
        # Check if it isn't the connection of the sender
        if client_conn.socket != connection:
            try:
                # Sending message to client connection; sendall is blocking
                client_conn.socket.sendall(message)

            # if it fails, there is a chance of socket has died
            except Exception as e:
                print(f'[Error broadcasting message] : {e}')
                remove_connection(client_conn)


def send(lengths: bytes, msg_type: str, msg: str, conn: socket.socket) -> None:
    broadcast(lengths, conn)
    ext = pack(f"{len(msg_type)}s", msg_type.encode())
    broadcast(ext, conn)
    if msg_type == "str":
        broadcast(msg.encode(), conn)
    # if it's a file
    else:
        broadcast(msg, conn)


def remove_connection(conn: _Session) -> None:
    '''
        Remove specified Session from connections list
    '''

    # Check if Session exists on connections list
    if conn in connections:
        # Close socket connection and remove Session from connections list
        conn.socket.close()
        connections.remove(conn)


def server() -> None:
    '''
        Main process that receive client's connections and start a new thread
        to handle their messages
    '''

    LISTENING_PORT = 12000
    # SERVER = socket.gethostbyname(socket.gethostname())

    try:
        # Create server instance
        socket_instance = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket_instance.bind(('', LISTENING_PORT))
        socket_instance.listen(5)

        print(f'[LISTENING] : {socket_instance.getsockname()}')

        while True:

            # Accept client connection
            socket_connection, address = socket_instance.accept()
            msg = socket_connection.recv(1024)
            msg = msg.decode()
            parser = parse_message.Parser(msg)
            user, _ = parser.parse()
            # Avoid having two usernames at the same time
            if is_taken(user):
                to_send = f"[Username {user} is already taken!]"
                lengths = pad_message(to_send)
                socket_connection.sendall(lengths)
                socket_connection.sendall("str".encode())
                socket_connection.sendall(to_send.encode())
                socket_connection.close()
            # if it ever gets here, joining when server is transferring file...
            elif is_busy:
                to_send = f"[Kindly wait for ongoing transfer to finish.]"
                lengths = pad_message(to_send)
                socket_connection.sendall(lengths)
                socket_connection.sendall("str".encode())
                socket_connection.sendall(to_send.encode())
                socket_connection.close()
            else:
                print("[CONNECTION] :", user)
                # tell the connected of a new user
                lengths = pad_message(msg)
                send(lengths, "str", msg, socket_connection)
                # Add client connection to connections list
                session = _Session(socket_connection, user, address)
                connections.append(session)
                # minus socket_connection
                to_send = f"[{len(connections)-1} online]"
                lengths = pad_message(to_send)
                send(lengths, "str", to_send, socket_connection)
                try:
                    # minus receiver (socket_connection)
                    to_send = f"[{len(connections)-1} online]"
                    lengths = pad_message(to_send)
                    socket_connection.sendall(lengths)
                    socket_connection.sendall("str".encode())
                    socket_connection.sendall(to_send.encode())
                except Exception as e:
                    print("[Error Sending online list] :", e)
                # Start a new thread to handle client connection and receive it's messages
                # in order to send to others connections
                server_thread = threading.Thread(target=handle_user_connection, args=(
                    session, address), name=user)
                server_thread.daemon = True
                server_thread.start()

    except Exception as e:
        print(f'[Error has occurred when instancing socket] : {e}')
    finally:
        # In case of any problem we clean all connections and close the server connection
        if len(connections) > 0:
            for conn in connections:
                remove_connection(conn)

        socket_instance.close()


def is_taken(new_user: str) -> bool:
    # check username and return true if found
    for user in connections:
        if new_user == user.username:
            return True
            break
    return False


if __name__ == "__main__":
    server()
