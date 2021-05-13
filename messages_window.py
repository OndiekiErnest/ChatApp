__author__ = "Ernesto"
__email__ = "ernestondieki12@gmail.com"

import message
from tkinter import Canvas, Scrollbar, Frame

class MsgWindow(Frame):

    def __init__(self, parent, **kwargs):
        self.parent = parent
        self.canvas = Canvas(self.parent, borderwidth=0, width=500, height=500)
        super().__init__(self.canvas, **kwargs)
        scroll_frame = Frame(self.parent, height=504, width=20)
        scroll_frame.pack(side="right", anchor="ne", fill="y")
        self._scrollbar = Scrollbar(
            scroll_frame, command=self.canvas.yview, orient="vertical")
        self._scrollbar.place(x=1, y=0, height=504)
        self.canvas.config(yscrollcommand=self._scrollbar.set)
        self.canvas.pack(fill="both")
        self.frame_id = self.canvas.create_window(
            (2, 4), window=self, anchor="nw", tags="self")
        self.canvas.bind("<Configure>", self.onConfig)

    def onConfig(self, event=None):
        """
            update scroll region, keep the bottom text in view
        """
        self.canvas.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        if event is not None:
            self.canvas.itemconfig(
                self.frame_id, width=event.width)
            # if called and not event bound, no scrolling
            self.canvas.yview_moveto(1.0)


if __name__ == '__main__':
    from tkinter import Tk
    from datetime import datetime
    tk = Tk()
    tk.title("Test Window")
    tk.geometry("500x500")
    tk.config(bg="gray67")
    mw = MsgWindow(tk, bg="gray67")
    # loop to see that the scrolling works
    for i in range(3):

        msg2 = message.Outgoing(
            mw, "Short story. Once upon a time there lived Ernesto! He was very kind to everyone. Ernesto loved music and design but never got a chance to design. End of story.")
        msg2.create(datetime.utcnow())

        msg1 = message.Incoming(
            mw, "Oops!")
        msg1.create(datetime.utcnow())

        msg = message.NotSent(
            mw, "Thank you.")
        msg.create(datetime.utcnow())

    tk.mainloop()
