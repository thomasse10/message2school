import tkinter as tk
from tkinter import ttk, simpledialog
import socket
import threading
import time

# --- Prompt for username ---
root = tk.Tk()
root.withdraw()
username = simpledialog.askstring("Username", "Enter your username:")
if not username:
    username = "Anonymous"
root.deiconify()

# --- Window Setup ---
root.title(f"Chat - {username}")
root.geometry("450x600")
root.minsize(400, 550)

# --- Fonts and Colors ---
FONT_MSG = ("Arial", 10)
FONT_TIME = ("Arial", 7, "italic")
COLOR_BG = "#f5f5f5"
COLOR_SELF = "#d1ffd6"
COLOR_OTHER = "#ffffff"
COLOR_SEND_BTN = "#4caf50"
COLOR_SEND_BTN_ACTIVE = "#45a049"
COLOR_SEND_BTN_DISABLED = "#a5d6a7"

root.configure(bg=COLOR_BG)

# --- Style Setup for ttk ---
style = ttk.Style()
style.theme_use('default')
style.configure('Send.TButton',
                foreground='white',
                background=COLOR_SEND_BTN,
                font=FONT_MSG,
                padding=6)
style.map('Send.TButton',
          background=[('disabled', COLOR_SEND_BTN_DISABLED),
                      ('active', COLOR_SEND_BTN_ACTIVE)],
          foreground=[('disabled', 'white'),
                      ('active', 'white')])

# --- Chat display area ---
canvas = tk.Canvas(root, bg=COLOR_BG, highlightthickness=0)
scrollbar = tk.Scrollbar(root, command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg=COLOR_BG)

scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.grid(row=0, column=0, sticky="nsew")
scrollbar.grid(row=0, column=1, sticky="ns")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# --- Input Area ---
input_frame = tk.Frame(root, bg=COLOR_BG)
input_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
input_frame.grid_columnconfigure(0, weight=1)

message_var = tk.StringVar()

def clear_placeholder(event):
    if message_entry.get() == "Type your message here...":
        message_entry.delete(0, tk.END)
        message_entry.config(fg="black")

def add_placeholder(event):
    if not message_entry.get():
        message_entry.insert(0, "Type your message here...")
        message_entry.config(fg="grey")

message_entry = tk.Entry(input_frame, textvariable=message_var, fg="grey", font=FONT_MSG)
message_entry.insert(0, "Type your message here...")
message_entry.bind("<FocusIn>", clear_placeholder)
message_entry.bind("<FocusOut>", add_placeholder)
message_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

send_button = ttk.Button(input_frame, text="Send", style='Send.TButton', state=tk.DISABLED)
send_button.grid(row=0, column=1)

# --- Invisible secret button setup ---
secret_click_count = 0

def secret_button_clicked():
    global secret_click_count
    secret_click_count += 1
    if secret_click_count >= 14:
        secret_click_count = 0
        target = simpledialog.askstring("Admin", "Enter username to disconnect:")
        if target:
            try:
                client.send(f"DISCONNECT_USER:{target}".encode("utf-8"))
                add_message(f"[ADMIN] Disconnect request sent for: {target}")
            except:
                add_message("[ADMIN] Failed to send admin command.")

# Invisible clickable area (15x15 px) in bottom-left corner
secret_button = tk.Button(root, text="", bg=COLOR_BG, activebackground=COLOR_BG,
                          borderwidth=0, highlightthickness=0, relief="flat",
                          command=secret_button_clicked)
secret_button.place(relx=0.3, rely=1.0, anchor="sw", width=15, height=10)

# --- Enable/disable send button ---
def check_send_button(*args):
    msg = message_var.get().strip()
    if msg and msg != "Type your message here...":
        send_button.state(['!disabled'])
    else:
        send_button.state(['disabled'])

message_var.trace_add("write", check_send_button)

# --- Socket connection ---
HOST = '127.0.0.1'
PORT = 5050

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((HOST, PORT))
client.send(username.encode('utf-8'))

# --- Add message to chat ---
def add_message(text, from_self=False):
    bubble = tk.Frame(scrollable_frame,
                      bg=COLOR_SELF if from_self else COLOR_OTHER,
                      bd=1, relief="solid", padx=10, pady=5)
    msg_label = tk.Label(bubble, text=text, font=FONT_MSG, bg=bubble.cget("bg"),
                         justify="left", wraplength=300)
    msg_label.pack(anchor="w")
    timestamp = time.strftime("%H:%M")
    time_label = tk.Label(bubble, text=timestamp, font=FONT_TIME,
                          bg=bubble.cget("bg"), fg="gray")
    time_label.pack(anchor="e")
    bubble.pack(fill="x", pady=2, padx=10, anchor="e" if from_self else "w")
    root.after(100, lambda: canvas.yview_moveto(1.0))

# --- Send message ---
def send_message(event=None):
    msg = message_var.get().strip()
    if msg and msg != "Type your message here...":
        add_message(f"You: {msg}", from_self=True)
        try:
            client.send(msg.encode("utf-8"))
        except:
            add_message("Failed to send message. Connection issue.", from_self=True)
        message_entry.delete(0, tk.END)
        check_send_button()

send_button.config(command=send_message)
message_entry.bind("<Return>", send_message)

# --- Receive messages ---
def receive_messages():
    while True:
        try:
            msg = client.recv(1024).decode("utf-8")
            if msg and not msg.startswith(f"{username}:"):
                add_message(msg)
        except:
            break

threading.Thread(target=receive_messages, daemon=True).start()

# --- Clean shutdown on close ---
def on_close():
    try:
        client.close()
    except:
        pass
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()