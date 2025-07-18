import socket
import threading

HOST = '0.0.0.0'
PORT = 5050

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

connected_users = {}  # conn -> username
users_lock = threading.Lock()

def broadcast(message, sender_conn=None):
    print(f"[BROADCAST] {message}")
    to_remove = []

    with users_lock:
        recipients = list(connected_users.items())

    for conn, username in recipients:
        if conn == sender_conn:
            continue
        try:
            conn.send(message.encode('utf-8'))
        except Exception as e:
            print(f"[ERROR] Could not send to {username}: {e}")
            to_remove.append(conn)

    if to_remove:
        with users_lock:
            for conn in to_remove:
                try:
                    conn.close()
                except:
                    pass
                if conn in connected_users:
                    print(f"[CLEANUP] Removing {connected_users[conn]}")
                    del connected_users[conn]

def handle_client(conn, addr):
    try:
        username = conn.recv(1024).decode('utf-8')
        if not username:
            conn.close()
            return

        # Replace old socket with same username
        with users_lock:
            for c, u in list(connected_users.items()):
                if u == username:
                    try:
                        c.close()
                    except:
                        pass
                    del connected_users[c]
            connected_users[conn] = username

        print(f"[CONNECTED] {username} from {addr}")
        broadcast(f"*** {username} joined the chat ***", sender_conn=conn)

        conn.settimeout(1.0)

        while True:
            try:
                msg = conn.recv(1024)
                if not msg:
                    break
                decoded = msg.decode('utf-8')

                if decoded.startswith("DISCONNECT_USER:"):
                    target_user = decoded.split(":", 1)[1]
                    with users_lock:
                        for c, u in list(connected_users.items()):
                            if u == target_user:
                                try:
                                    c.send("You have been disconnected by admin.".encode('utf-8'))
                                except:
                                    pass
                                c.close()
                                del connected_users[c]
                                broadcast(f"*** {target_user} was disconnected by admin ***")
                                break
                else:
                    broadcast(f"{username}: {decoded}", sender_conn=conn)

            except socket.timeout:
                continue
            except Exception as e:
                print(f"[ERROR] {username}: {e}")
                break
    finally:
        with users_lock:
            if conn in connected_users:
                print(f"[DISCONNECTED] {connected_users[conn]}")
                broadcast(f"*** {connected_users[conn]} left the chat ***", sender_conn=conn)
                del connected_users[conn]
        try:
            conn.close()
        except:
            pass

def start_server():
    print(f"[STARTING] Group chat server running on port {PORT}...")
    while True:
        try:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
        except Exception as e:
            print(f"[ERROR] Accept failed: {e}")

if __name__ == "__main__":
    start_server()