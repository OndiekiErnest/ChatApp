__author__ = "Ernesto"
__email__ = "ernestondieki12@gmail.com"

from tkinter import Tk, Frame, Label, Menu, PhotoImage
from datetime import datetime
from os import startfile
from os.path import expanduser, exists, join, basename
import parse_message


class Settings():
    WRAPLENGTH = 220
    REPLY_BG = "SeaGreen3"
    REPLY_FG = "black"
    REPLY_FONT = ("Arial", 8, "normal")
    MESSSAGE_BG = "SeaGreen2"
    MESSAGE_FG = "black"
    MSG_FONT = ("Helvetica", 9, "normal")
    TIME_FONT = ("Arial", 7, "italic")
    TIME_FG = MESSAGE_FG
    ANCHOR = "ne"

class Message(Settings):

    def __init__(self, root: Tk, msg: str):
        self.message_str = msg.strip().encode()
        self._root = root
        self.msg_box = Frame(self._root)
        self.reply_label = Label(self.msg_box)
        self.msg_label = Label(self.msg_box)
        self.msg_label.bind(
            "<Button-2>", self._on_rightClick)
        self.msg_label.bind(
            "<Button-3>", self._on_rightClick)
        self.time = Label(self.msg_box)

    def __str__(self):
        return self.message_str.decode()

    def create(self, time_recv: datetime):
        """create message box


        Arguments:
            time_recv {datetime.now()/utcnow()} -- [time message was received/created]
        """
        if len(self.message_str) > 0:
            self.msg_box.config(relief="solid",
                                bg=self.MESSSAGE_BG
                                )
            self.msg_box.pack(pady=3, padx=4, anchor=self.ANCHOR)
            if self.message_str.decode().startswith("replied-("):
                parser = parse_message.Parser(self.message_str.decode())
                reply, self.message_str = parser.parse_replied()
                self.reply_label.config(bg=self.REPLY_BG,
                                        fg=self.REPLY_FG,
                                        font=self.REPLY_FONT,
                                        text=reply,
                                        padx=3,
                                        wraplength=self.WRAPLENGTH,
                                        anchor="w",
                                        borderwidth=1
                                        )
                self.reply_label.pack(fill="x")
            # the message label
            self.msg_label.config(text=self.message_str,
                                  bg=self.MESSSAGE_BG,
                                  fg=self.MESSAGE_FG,
                                  wraplength=self.WRAPLENGTH,
                                  justify="left",
                                  font=self.MSG_FONT,
                                  pady=0
                                  )
            self.msg_label.pack(anchor="nw")
            # time label for displaying time received
            self.time.config(bg=self.MESSSAGE_BG,
                             fg=self.TIME_FG,
                             pady=0,
                             text=time_recv.strftime("%H:%M"),
                             font=self.TIME_FONT
                             )
            self.time.pack(anchor="se")

    def _on_rightClick(self, event):
        """
            create popup; delete message or copy text
        """
        popup = Menu(self.msg_box, tearoff=False,
                     font=("New Times Roman", 9, "bold"),
                     activebackground="DeepSkyBlue3")
        popup.add_separator()
        popup.add_command(label="Copy text",
                          command=lambda: self.copy_text(e=event))
        popup.add_separator()
        popup.add_command(label="Delete for me", command=self.delete)
        popup.add_separator()
        try:
            popup.tk_popup(event.x_root - 10, event.y_root + 30, 0)
        except Exception:
            pass
        finally:
            popup.grab_release()

    def copy_text(self, e=None):
        # copy text to clipboard; clear before appending
        self._root.clipboard_clear()
        self._root.clipboard_append(e.widget["text"])

    def delete(self):
        # delete message; destroy msg_box and update scroll region
        self.msg_box.pack_forget()
        self.msg_box.destroy()
        try:
            # update scroll region
            self._root.onConfig()
        except AttributeError:
            pass


class Outgoing(Message):

    def __init__(self, win: Tk, msg: str):
        super().__init__(win, msg)


class Incoming(Message):

    def __init__(self, win: Tk, msg: str):
        super().__init__(win, msg)
        self.MESSSAGE_BG = "LightSkyBlue2"
        self.ANCHOR = "nw"
        self.REPLY_BG = "LightSkyBlue3"

class NotSent(Message):

    def __init__(self, win: Tk, msg: str):
        super().__init__(win, msg)
        self.TIME_FG = "red"
        self.TIME_FONT = ("Arial", 8, "italic bold")

class Media(Message):

    def __init__(self, win: Tk, msg: str, sender: str):
        super().__init__(win, msg)
        self.media_from = f"From: {sender}".encode()
        self.MSG_FONT = ("Helvetica", 8, "normal")
        self.MESSSAGE_BG = "gray73"
        self.doc_image = PhotoImage(file="doc.png")

    def open_file(self, event):
        txt = event.widget["text"].decode()
        if exists(txt):
            startfile(txt, operation="open")
        elif exists(join(expanduser("~\\Downloads"), txt)):
            startfile(join(expanduser("~\\Downloads"), txt), operation="open")
        else:
            pass

    def create(self, time_recv: datetime):
        """create media box
            override create method


        Arguments:
            time_recv {datetime.now()/utcnow()} -- [time message was received/created]
        """
        if len(self.message_str) > 0:
            self.msg_box.config(relief="solid",
                                bg=self.MESSSAGE_BG
                                )
            self.msg_box.pack(pady=3, padx=4, anchor=self.ANCHOR)
            self.reply_label.config(bg="gray80",
                                    fg=self.REPLY_FG,
                                    font=self.REPLY_FONT,
                                    # return file name without path if it's a path, else return message_str
                                    text=basename(self.message_str.decode()
                                                  ).encode(),
                                    padx=3,
                                    wraplength=self.WRAPLENGTH,
                                    anchor="w",
                                    borderwidth=1
                                    )
            self.reply_label.pack(fill="x")
            # the message label
            self.msg_label.config(text=self.message_str,
                                  image=self.doc_image,
                                  bg=self.MESSSAGE_BG,
                                  fg=self.MESSAGE_FG,
                                  wraplength=self.WRAPLENGTH,
                                  anchor="w",
                                  font=self.MSG_FONT,
                                  pady=0,
                                  # increase width so the user can click anywhere few pixels past the file icon
                                  width=210
                                  )
            self.msg_label.pack(anchor="nw")
            # time label for displaying time received
            self.sender_label = Label(self.msg_box,
                                      text=self.media_from,
                                      font=self.TIME_FONT,
                                      pady=0, padx=0,
                                      bg=self.MESSSAGE_BG)
            self.sender_label.pack(side="left")
            # for displaying sender
            self.time.config(bg=self.MESSSAGE_BG,
                             fg=self.TIME_FG,
                             pady=0,
                             text=time_recv.strftime("%H:%M"),
                             font=self.TIME_FONT
                             )
            self.time.pack(side="right")

    def _on_rightClick(self, event):
        """
            create popup; delete message or open media
            override method
        """
        popup = Menu(self.msg_box, tearoff=False,
                     font=("New Times Roman", 9, "bold"),
                     activebackground="DeepSkyBlue3")
        popup.add_separator()
        popup.add_command(label="Open", command=lambda: self.open_file(event))
        popup.add_separator()
        popup.add_command(label="Delete for me", command=self.delete)
        popup.add_separator()
        try:
            popup.tk_popup(event.x_root - 10, event.y_root + 30, 0)
        except Exception:
            pass
        finally:
            popup.grab_release()


if __name__ == '__main__':
    from tkinter import Tk
    tk = Tk()
    tk.title("Test Message")
    m = Outgoing(tk, "Hello!")
    # test characters that cause UnicodeError too
    n = Incoming(
        tk, "replied-(deliciouspy: Good morning, how are you today?) Ernesto: My morning and I are great! \n🎶")

    m.create(datetime.utcnow())
    n.create(datetime.utcnow())
    for i in range(5):
        n = Incoming(tk, "Hello!")
        msg1 = Incoming(
            tk, "Hello! How are you doing?")
        n.create(datetime.utcnow())
        msg1.create(datetime.utcnow())
    media = Media(tk, "<path to your file here>.<extension>", "Ernesto")
    # this attribute wasn't set so it could be set from its instance
    media.ANCHOR = "nw"
    media.create(datetime.utcnow())
    tk.mainloop()
