import socket
import threading

HOST = '0.0.0.0'
PORT = 5050

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen()

clients = {}
clients_lock = threading.Lock()

def broadcast(msg):
    with clients_lock:
        for client in list(clients.keys()):
            try:
                client.send(msg.encode("utf-8"))
            except:
                client.close()
                del clients[client]

def handle_client(conn, addr):
    try:
        username = conn.recv(1024).decode("utf-8")
        if not username:
            conn.close()
            return

        with clients_lock:
            clients[conn] = username

        broadcast(f"*** {username} has joined the chat ***")

        while True:
            msg = conn.recv(1024).decode("utf-8")
            if not msg:
                break

            if msg.startswith("DISCONNECT_USER:"):
                target_user = msg.split(":", 1)[1]
                with clients_lock:
                    for c, u in list(clients.items()):
                        if u == target_user:
                            try:
                                c.send("You have been disconnected by admin.".encode("utf-8"))
                            except:
                                pass
                            c.close()
                            del clients[c]
                            broadcast(f"*** {target_user} has been disconnected by admin ***")
                            break
                continue

            broadcast(f"{username}: {msg}")

    except:
        pass

    with clients_lock:
        if conn in clients:
            left = clients.pop(conn)
            broadcast(f"*** {left} has left the chat ***")
    conn.close()

def start_server():
    print(f"[LISTENING] Server running on port {PORT}...")
    while True:
        conn, addr = server.accept()
        print(f"[NEW CONNECTION] {addr} connected.")
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()

if __name__ == "__main__":
    start_server()