import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox
import subprocess

"""
Jinpeng Zhai
Main script to analyze a Python file, using a tk-GUI for interactivity.

"""

import os
import queue
from threading import Thread


class heatTrace(tk.Frame):
    def __init__(self, parent, menubar):
        # use this instead of super() due to multiple inheritance
        ttk.Frame.__init__(self, parent)
        # initially, let the fileVar be pointed at this file itself.
        self.fileVar = tk.StringVar(value=os.path.normpath(__file__))
        self.pack(expand=1, fill="both")  # pack the heatTrace frame in root.

        fileMenu = tk.Menu(menubar)
        menubar.add_cascade(
            label="File", underline=0, menu=fileMenu
        )  # cascading file menu
        fileMenu.add_command(
            label="Load Programme", underline=0, command=self.load
        )  # command button to load programmes

        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # group of widgets responsible for selecting the target file.
        ttk.Label(self, text="File Selected", underline=0, anchor="e").grid(
            row=0, column=0, sticky="nsew"
        )
        ttk.Entry(self, textvariable=self.fileVar, state="disabled").grid(
            row=0, column=1, sticky="nsew"
        )
        ttk.Button(self, text="Run", command=self.trace).grid(
            row=0, column=2, sticky="nsew"
        )

        self.ttyText = tk.Text(self, wrap=tk.CHAR)
        self.ttyText.grid(row=1, column=0, columnspan=3, sticky="nsew")
        self.ttyText.config(background="black", foreground="white")

        # open a subprocess to this script.
        self.p = subprocess.Popen(
            ["cmd"],  # ISSUE: Platform dependency
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # make queues for keeping stdout and stderr whilst it is transferred between threads
        self.outQueue = queue.Queue()
        self.errQueue = queue.Queue()

        # keep track of where any line that is submitted starts
        self.line_start = 0

        # make the enter key call the self.enter function
        self.ttyText.bind("<Return>", self.enter)

        # a daemon to keep track of the threads so they can stop running
        self.alive = True
        # start the functions that get stdout and stderr in separate threads
        Thread(target=self.readFromProccessOut).start()
        Thread(target=self.readFromProccessErr).start()

        # start the write loop in the main thread
        self.clear()
        self.writeLoop()

    def load(self):
        filePath = tkfiledialog.askopenfilename(
            title="Load Programme to be Analyzed",
            filetypes=(("Python Programme", "*.py"),),
            defaultextension=".py",
            initialfile="main.py",
            initialdir=".",  # set to local dir relative to where this script is stored
        )

        exceptionMsg = "Exception:"
        if filePath == "":
            tkmessagebox.showinfo(exceptionMsg, "No File Selected")
        else:
            self.fileVar.set(os.path.normpath(filePath))

        self.navigateToFolder()

    def trace(self):
        pass

    def destroy(self):  #
        """This is the function that is automatically called when the widget is
        destroyed, and overrides the widget's default destroy()"""
        self.alive = False
        # write exit() to the console in order to stop it running
        self.p.stdin.write("exit\n".encode())
        # TODO: make this platform independent
        self.p.stdin.flush()
        # call the destroy methods to properly destroy widgets
        self.ttyText.destroy()
        tk.Frame.destroy(self)

    def enter(self, e):
        """The <Return> key press handler"""
        string = self.ttyText.get(1.0, tk.END)[self.line_start :]
        self.line_start += len(string)
        self.p.stdin.write(string.encode())
        self.p.stdin.flush()

    def readFromProccessOut(self):
        """To be executed in a separate thread to make read non-blocking"""
        while self.alive:
            data = self.p.stdout.raw.read(1024).decode()
            self.outQueue.put(data)

    def readFromProccessErr(self):
        """To be executed in a separate thread to make read non-blocking"""
        while self.alive:
            data = self.p.stderr.raw.read(1024).decode()
            self.errQueue.put(data)

    def writeLoop(self):
        """Used to write data from stdout and stderr to the Text widget"""
        # if there is anything to write from stdout or stderr, then write it
        if not self.errQueue.empty():
            self.write(self.errQueue.get())
        if not self.outQueue.empty():
            out = self.outQueue.get()
            self.write(out)

        # run this method again after 10ms
        if self.alive:
            self.after(10, self.writeLoop)

    def clear(self):
        self.line_start = 0
        self.ttyText.delete(1.0, tk.END)

    def navigateToFolder(self):
        folderPath = os.path.dirname(self.fileVar.get())

        self.p.stdin.write(
            "cd {:}\n".format(folderPath).encode()
        )  # AT LEAST this is platform independent thank god.

        self.p.stdin.flush()

    def write(self, string):
        self.ttyText.insert(tk.END, string)
        self.ttyText.see(tk.END)
        self.line_start += len(string)


def main():
    root = tk.Tk()
    # style = ttk.Style(root)
    # style.theme_use("")

    root.option_add("*tearOff", False)
    root.title("pyHeatTrace")

    menubar = tk.Menu(root)
    root.config(menu=menubar)
    heatTrace(root, menubar)
    root.mainloop()


if __name__ == "__main__":
    main()
