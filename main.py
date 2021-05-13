
__author__ = "Ernesto"
__email__ = "ernestondieki12@gmail.com"

from tkinter import Tk, Button, Text, StringVar, Label
from tkinter.filedialog import askopenfile
from tkinter.messagebox import askyesno
import message
import messages_window
from datetime import datetime
import sys
import threading
import socket
import struct
import os
import time


class ChatApp():

    def __init__(self, root, username, **kwargs):
        self.root = root
        self.user = username
        # on clicking attach, open Documents folder first
        self.initialdir = os.path.expanduser("~\\Documents")
        # variable to hold replies
        self.reply = StringVar()
        self.reply.set("")
        self.status = ""
        # instantiate online users to 0
        self.online_users = "0 online"
        # call self.kill on closing the chat window
        self.root.wm_protocol("WM_DELETE_WINDOW", self.kill)
        self.root.title(self.user)
        # Instantiate our messages window for display
        self.msgs_window = messages_window.MsgWindow(
            self.root)
        self.msgs_window.bind("<Double-Button-1>", self.clear)
        # get canvas from messages window for configurations
        self.canvas = self.msgs_window.canvas
        # set up the typing area for user input
        self.__typingArea()

        self.SERVER_ADDRESS = kwargs.get("server_addr", "127.0.0.1")
        self.SERVER_PORT = kwargs.get("server_port", 12000)
        self.message_box = message

        # Instantiate socket and start connection with server
        self.socket_instance = socket.socket()
        try:
            self.socket_instance.connect((self.SERVER_ADDRESS,
                                          self.SERVER_PORT))
            # this is padded on the server after checking username; no need to pad with its length
            self.socket_instance.sendall(f"{self.user} is online!".encode())
            print(f"{self.user} online!")
        except Exception as e:
            print("[Client init Error] :", e)
            self.status = "| Server is down!"
            self.update_status_bar()
            self.socket_instance.close()

        try:
            # Create a thread in order to handle messages sent by server
            self.client_thread = threading.Thread(target=self.handle_messages,
                                                  args=(self.socket_instance,))
            self.client_thread.start()

        except Exception as e:
            print(f'[Client Error] : {e}')
            self.status = "| No message can be received! Restart."
            self.update_status_bar()
            self.socket_instance.close()

    def __typingArea(self) -> None:
        """
            text area for user to type messages in

            with buttons for sending plain texts and another for file attachment
        """

        BG = "gray55"
        self.status_bar = Label(self.root, relief="groove", anchor="w")
        self.status_bar.pack(side="bottom", expand=True, fill="x")
        self.attach_button = Button(self.root,
                                    text="ATTACH",
                                    bg=BG, relief="flat",
                                    width=5, command=self._handle_file,
                                    font=("Helvetica", 10, "bold"))
        self.attach_button.pack(side="left", expand=True, fill="both")

        self.text_widget = Text(self.root,
                                # 40 words wide
                                width=40,
                                # three lines high
                                height=3,
                                bd=0,
                                relief="flat",
                                takefocus=1,
                                wrap="word",
                                selectbackground="LightSkyBlue2",
                                selectforeground="black",
                                insertborderwidth=4,
                                font=("Helvetica", 10, "bold")
                                )
        # In some machines, right click button is Button-2
        self.text_widget.bind("<Button-2>", self._from_clipborad)
        self.text_widget.bind("<Button-3>", self._from_clipborad)
        self.text_widget.pack(side="left", expand=True, fill="both")

        self.send_button = Button(
            self.root, text="SEND", bg=BG, relief="flat", font=("Helvetica", 10, "bold"), command=self.client_response)
        self.send_button.pack(side="right", expand=True, fill="both")

    def _from_clipborad(self, event=None):
        """
            Get clipboard content and paste on cursor position
        """
        try:
            self.text_widget.insert(self.text_widget.index(
                "insert"), self.root.clipboard_get())
        except Exception:
            pass

    def sendall(self, lengths: bytes, ext: bytes, msg: bytes) -> None:
        try:
            self.socket_instance.sendall(lengths)
            self.socket_instance.sendall(ext)
            self.socket_instance.sendall(msg)
        except Exception as e:
            print("[Error Sending] :", e)

    def receive_all(self, sock: socket.socket, n: int) -> bytearray:
        """
            recv n string bytes; return bytearray of received
        """
        data = bytearray()
        while len(data) < n:
            to_read = n - len(data)
            packet = sock.recv(
                4194304 if to_read > 4194304 else to_read)
            data.extend(packet)
        return data

    def pad_message(self, msg: str, msg_type="str") -> bytes:
        # pad 12 bytes of size of message to be received and its type; for strings
        msg_type = msg_type.encode()
        padded = struct.pack(">QI", len(msg.encode()), len(msg_type))
        return padded

    def send_file(self, file, size_bytes: int, remaining: int):
        # passed to a thread
        # sent earlier
        sent = 4194304
        t = time.time()
        file_size_mbs = round((size_bytes / 1048576), 2)
        while remaining > 0:
            try:
                # read at most 4 MB (4194304)
                file_data = file.read(4194304)
                if file_data:
                    self.socket_instance.sendall(file_data)
                    sent += 4194304
                    self.status = f"| Sending {round((sent / 1048576), 2)} MB / {file_size_mbs} MB"
                    self.update_status_bar()
                    remaining = size_bytes - sent
                else:
                    break
            except Exception as e:
                print("[Error Sending File:]", e)
        t_taken = round(time.time() - t, 2)
        mins, secs = divmod(t_taken, 60)
        self.status = f"| Finished in {mins} mins {round(secs, 2)} seconds."
        self.update_status_bar()

    def _handle_file(self):
        if not self.status.endswith(("MB",)):
            options = {
                "title": "Share file",
                "filetypes": (("All files", "*"),),
                "initialdir": self.initialdir
            }
            # return the open file with some more functionalities
            file = askopenfile(mode="rb", **options)
            # if cancel wasn't clicked
            if file is not None:
                self.initialdir = os.path.dirname(file.name)
                # send only when at someone else is online
                if self.online_users[0] != "0":
                    size_bytes = os.path.getsize(file.name)
                    file_mbs = round((size_bytes / 1048576), 2)
                    shared_filename = os.path.basename(file.name)
                    # Confirmation
                    if askyesno(title="Share file...", message=f"Share {shared_filename}?\n\t({file_mbs} MB)"):

                        media_instance = self.message_box.Media(self.msgs_window,
                                                                file.name, self.user)
                        # anchor the msg box to the right
                        media_instance.ANCHOR = "ne"
                        # Double click to open file
                        media_instance.msg_label.bind(
                            "<Double-Button-1>", self.start_file)
                        media_instance.create(datetime.now())
                        file_data = file.read(4194304)
                        filename = f"{self.user}\\{os.path.basename(file.name)}".encode()
                        lengths = struct.pack(">QI", size_bytes, len(filename))
                        ext = struct.pack(f"{len(filename)}s", filename)
                        self.sendall(lengths, ext, file_data)
                        remaining = size_bytes - 4194304
                        sending_thread = threading.Thread(target=self.send_file,
                                                          name="sending_thread", args=(file, size_bytes, remaining))
                        sending_thread.daemon = True
                        sending_thread.start()
                else:
                    self.status = f"| Couldn't share! No one online."
                    self.update_status_bar()

    def handle_messages(self, connection: socket.socket):
        """
            Receive messages sent by the server and display them to user
            Threaded
        """

        while True:
            try:
                # receive the string that was packed and unpack
                # If there is no message, there is a chance that connection has closed
                # so the connection will be closed and an error will be displayed.
                # If not, it will try to decode message in order to show to user.
                first_msg = connection.recv(12)
                if first_msg:
                    msg_length, ext_length = struct.unpack(">QI", first_msg)
                    sec_msg = connection.recv(ext_length)
                    extension = struct.unpack(f"{ext_length}s",
                                              sec_msg)[0].decode()

                    if extension == "str":
                        msg = self.receive_all(connection, msg_length).decode()
                        # receive server message for online users
                        if msg.startswith("[") and msg.endswith("online]"):
                            self.online_users = msg[1:-1]
                            self.update_status_bar()
                        # get notified if username taken
                        elif msg.startswith("[Username") and msg.endswith("taken!]"):
                            self.status = f"| {msg[1:-1]} Try another one."
                            self.update_status_bar()
                        # if it's a message from another client
                        else:
                            self.inbox_instance = self.message_box.Incoming(
                                self.msgs_window, msg)
                            # bind double clicking the message label
                            self.inbox_instance.msg_label.bind(
                                "<Double-Button-1>", self.fromIncoming)
                            self.inbox_instance.create(datetime.now())
                            # make sure the last text is in view by auto-scrolling to bottom
                            self.canvas.update_idletasks()
                            # first update the scrollregion
                            self.canvas.config(
                                scrollregion=self.canvas.bbox("all"))
                            # then move to bottom of that region
                            self.canvas.yview_moveto(1.0)
                    else:
                        # msg = self.receive_all(connection, msg_length)
                        sender, received_filename = extension.split("\\")
                        BUFFER = 4194304
                        file_size = round((msg_length / 1048576), 2)
                        file = os.path.join(os.path.expanduser("~\\Downloads"),
                                            received_filename)
                        # TODO: ask for user consent before downloading
                        # TODO: user choose directory to download to
                        # if askyesno(title="Incoming File", message=f"Save {received_filename} to Downloads?\n\t{file_size}"):
                        data = connection.recv(BUFFER)
                        received = len(data)
                        to_read = msg_length - received
                        # if the file exists, it's overwritten
                        with open(file, "wb") as file:
                            file.write(data)
                            while to_read > 1:
                                data = connection.recv(
                                    BUFFER if to_read > BUFFER else to_read)
                                if data:
                                    received += len(data)
                                    to_read = msg_length - received
                                    incoming = round((received / 1048576), 2)
                                    file.write(data)
                                    # update status bar
                                    self.status = f"| Receiving {incoming} MB / {file_size} MB"
                                    self.update_status_bar()
                                else:
                                    break
                        self.status = "| File saved to Downloads!"
                        self.update_status_bar()
                        media_instance = self.message_box.Media(
                            self.msgs_window, received_filename, sender)
                        # anchor msg_box to left
                        media_instance.ANCHOR = "nw"
                        # Double click to open file
                        media_instance.msg_label.bind(
                            "<Double-Button-1>", self.start_file)
                        media_instance.create(datetime.now())

                else:
                    print('[Error server cannot respond]')
                    # print("Server is down!")
                    self.status = "| Server is down! Restart."
                    self.online_users = "0 online"
                    self.update_status_bar()
                    connection.close()
                    break

            except Exception as e:
                print(f'[Error Handling Message] : {e}')
                # print("Server is down!")
                self.status = "| Server is down! Restart."
                self.online_users = "0 online"
                self.update_status_bar()
                connection.close()
                break

    def update_status_bar(self) -> None:
        # Update the status bar to give information to the user
        try:
            # if the first item isn't an integer
            try:
                # rarely happens; not an impossibility
                if int(self.online_users[0]) < 0:
                    self.online_users = "0 online"
            except ValueError:
                self.online_users = "0 online"
            self.status_bar["text"] = f"{self.online_users} {self.status}"
        except Exception:
            pass

    def clear(self, event=None) -> None:
        """
            Clear status bar of reply content
        """
        self.reply.set("")
        self.status = ""
        self.update_status_bar()

    def fromOutgoing(self, event=None) -> None:
        # Get text from outgoing msg widget and create reply text
        copied_txt = event.widget["text"].decode()[:17] + "..."
        self.reply.set(f'{self.user}: {copied_txt}')
        self.status = f"| Replying to: {self.reply.get()[:23]}"
        self.update_status_bar()

    def fromIncoming(self, event=None) -> None:
        # Get text from Incoming msg widget and create reply text
        copied_txt = event.widget["text"].decode().replace("\n",
                                    "")[:20] + "..."
        self.reply.set(copied_txt)
        self.status = f"| Replying to: {self.reply.get()[:23]}"
        self.update_status_bar()

    def start_file(self, event=None):
        if event is not None:
            txt = event.widget["text"].decode()
            try:
                # using 'Downloads' directly takes care of the receiver side
                filename = os.path.join(
                    os.path.expanduser("~\\Downloads"), txt)
                # the sender has the file path in widget text
                if os.path.exists(txt):
                    os.startfile(txt, operation="open")
                # for the receiver side
                elif os.path.exists(filename):
                    os.startfile(filename, operation="open")
                else:
                    self.status = "| Couldn't open! File was moved or deleted."
                    self.update_status_bar()
            except Exception as e:
                print("[Error Opening File]", e)

    def client_response(self) -> None:
        """
            Read user's input; close connection if there's an error
        """

        self.root.update_idletasks()
        try:
            # Get typed text
            txt = self.text_widget.get("1.0", "end")
            # Skip if nothing has been typed or contains only spaces or status is not good
            if len(txt.strip()) > 0 and not self.status.endswith(("another one.", "Restart.", "down!", "MB")):

                # Add sender/current user to txt; strip [ and ] to distinguish server commands
                msg = f'{self.user}:\n {txt}'
                # if the text has a reply format txt and reply
                reply_txt = self.reply.get()
                if len(reply_txt):
                    # add replied flag and format, then add msg (this is the msg to be sent)
                    msg = f"replied-({reply_txt}) {msg}"
                    # format to avoid outgoing message labels having sender name
                    msg_without_sender = f"replied-({reply_txt}) {txt}"

                else:
                    msg_without_sender = txt
                if self.online_users[0] == "0":
                    self.notSent(msg_without_sender, "no one online")
                    self.text_widget.delete("1.0", "end")
                else:
                    self.sent_instance = self.message_box.Outgoing(
                        self.msgs_window, msg_without_sender)
                    # bind double clicking the message label
                    self.sent_instance.msg_label.bind(
                        "<Double-Button-1>", self.fromOutgoing)
                    # Map message unto the display window
                    self.sent_instance.create(datetime.now())
                    # Parse message to utf-8
                    lengths = self.pad_message(msg)
                    msg_type = "str".encode()
                    ext = struct.pack(f"{len(msg_type)}s", msg_type)
                    self.sendall(lengths, ext, msg.encode())
                    # clear status bar
                    self.clear()
                    # success
                    self.status = "| Sent!"
                    self.update_status_bar()
                # make sure the last text is in view by auto-scrolling to bottom
                self.canvas.update_idletasks()
                # first update the scrollregion
                self.canvas.config(
                    scrollregion=self.canvas.bbox("all"))
                # then move to bottom of that region
                self.canvas.yview_moveto(1.0)
                # Clear typed text for next typing, and reply
                self.text_widget.delete("1.0", "end")
        except Exception as e:
            self.notSent(txt, "error")
            self.text_widget.delete("1.0", "end")
            print("[Error sending] :", e)

    def notSent(self, msg: str, why: str) -> None:
        """
            handle messages not sent
        """
        self.status = f"| Message not sent, {why}!"
        self.update_status_bar()
        self.not_sent = self.message_box.NotSent(
            self.msgs_window, msg)
        self.not_sent.msg_label.bind(
            "<Double-Button-1>", self.fromOutgoing)
        # Map message unto the display window
        self.not_sent.create(datetime.now())

    def kill(self) -> None:
        # killing while sending in progress will make
        # the server and receiver clients hang in while loop;
        # incomplete files will be saved
        if not self.status.endswith("MB"):
            # self.socket_instance.shutdown(socket.SHUT_RDWR)
            self.root.destroy()
            self.socket_instance.close()
            sys.exit(0)
        else:
            self.status = "| File transfer in progress."
            self.update_status_bar()


if len(sys.argv) < 2:
    print("Usage: > main.py <Username>")
else:
    try:
        tk = Tk()
        tk.geometry("450x600+20+20")
        chat_instance = ChatApp(tk, sys.argv[1])
        tk.mainloop()

    except Exception as e:
        print("[Main Program Error] :", e)
        tk.destroy()
