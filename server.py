import socket
import threading

HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 5050

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

connected_users = {}  # Maps client socket to username
users_lock = threading.Lock()

def broadcast(message, sender_conn=None):
    with users_lock:
        for conn in list(connected_users.keys()):
            try:
                if conn != sender_conn:
                    conn.send(message.encode('utf-8'))
            except:
                # If sending fails, remove client
                print(f"Removing client {connected_users[conn]} due to send failure")
                conn.close()
                del connected_users[conn]

def handle_client(conn, addr):
    try:
        username = conn.recv(1024).decode('utf-8')
        if not username:
            conn.close()
            return
        with users_lock:
            connected_users[conn] = username
        print(f"{username} connected from {addr}")
        broadcast(f"*** {username} connected to the chat ***", conn)

        while True:
            try:
                msg = conn.recv(1024)
                if not msg:
                    break  # Client disconnected
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
                                broadcast(f"*** {target_user} has been disconnected by admin ***")
                                break
                    continue

                broadcast(f"{username}: {decoded}", conn)
            except ConnectionResetError:
                break
            except Exception as e:
                print(f"Error receiving from {username}: {e}")
                break
    finally:
        with users_lock:
            if conn in connected_users:
                print(f"{connected_users[conn]} disconnected")
                broadcast(f"*** {connected_users[conn]} has left the chat ***", conn)
                del connected_users[conn]
        try:
            conn.close()
        except:
            pass

def start_server():
    print(f"[LISTENING] Server running on port {PORT}...")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()