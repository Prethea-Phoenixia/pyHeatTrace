import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox
from ttkthemes import ThemedTk
import subprocess as sp

"""
Jinpeng Zhai
Main script to analyze a Python file, using a tk-GUI for interactivity.

"""

import os
import queue
from threading import Thread, Event


class heatTrace(tk.Frame):
    def __init__(self, parent):
        # use this instead of super() due to multiple inheritance
        ttk.Frame.__init__(self, parent)
        # initially, let the fileVar be pointed at this file itself.
        self.pathVar = tk.StringVar(value=os.path.normpath(__file__))
        self.pack(expand=1, fill="both")  # pack the heatTrace frame in root.

        # allow 3,1 to unconditionally take up more space as the window is resized
        self.columnconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)

        # group of widgets responsible for selecting the target file.
        ttk.Button(
            self, text="Select File", underline=0, command=self.load
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        ttk.Entry(self, textvariable=self.pathVar, state="disabled").grid(
            row=0, column=1, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(self, text="Run Trace", command=self.trace).grid(
            row=0, column=2, sticky="nsew", padx=2, pady=2
        )

        mainOptionFrame = ttk.LabelFrame(self, text="Options")
        mainOptionFrame.grid(
            row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=10
        )

        for i in range(5):
            mainOptionFrame.columnconfigure(i, weight=1)

        self.arg_c = tk.IntVar()
        ttk.Checkbutton(
            mainOptionFrame, text="--count", variable=self.arg_c
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.arg_t = tk.IntVar()
        ttk.Checkbutton(
            mainOptionFrame, text="--trace", variable=self.arg_t
        ).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        self.arg_l = tk.IntVar()
        ttk.Checkbutton(
            mainOptionFrame, text="--listfuncs", variable=self.arg_l
        ).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        self.arg_r = tk.IntVar()
        ttk.Checkbutton(
            mainOptionFrame, text="--report", variable=self.arg_r
        ).grid(row=0, column=3, sticky="nsew", padx=2, pady=2)

        self.arg_T = tk.IntVar()
        ttk.Checkbutton(
            mainOptionFrame, text="--trackcalls", variable=self.arg_T
        ).grid(row=0, column=4, sticky="nsew", padx=2, pady=2)

        modifierFrame = ttk.LabelFrame(self, text="Modifiers")
        modifierFrame.grid(
            row=2, column=0, columnspan=3, sticky="nsew", padx=10, pady=10
        )

        for i in range(4):
            modifierFrame.columnconfigure(i, weight=1)

        self.arg_m = tk.IntVar()
        ttk.Checkbutton(
            modifierFrame, text="--missing", variable=self.arg_m
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.arg_s = tk.IntVar()
        ttk.Checkbutton(
            modifierFrame, text="--summary", variable=self.arg_s
        ).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        self.arg_R = tk.IntVar()
        ttk.Checkbutton(
            modifierFrame, text="--no-report", variable=self.arg_R
        ).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        self.arg_g = tk.IntVar()
        ttk.Checkbutton(
            modifierFrame, text="--timing", variable=self.arg_g
        ).grid(row=0, column=3, sticky="nsew", padx=2, pady=2)

        self.fargs = tk.StringVar()
        ttk.Label(modifierFrame, text="--file").grid(
            row=1, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(modifierFrame, textvariable=self.fargs).grid(
            row=1, column=1, columnspan=3, sticky="nsew", padx=2, pady=2
        )

        self.Cargs = tk.StringVar()
        ttk.Label(modifierFrame, text="--coverdir").grid(
            row=2, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(modifierFrame, textvariable=self.Cargs).grid(
            row=2, column=1, columnspan=3, sticky="nsew", padx=2, pady=2
        )

        self.ttyText = tk.Text(self, wrap=tk.CHAR)
        self.ttyText.grid(row=3, column=0, columnspan=3, sticky="nsew")
        self.ttyText.config(background="black", foreground="white")

        # open a sp to this script.
        self.p = sp.Popen(
            ["cmd"],  # ISSUE: Platform dependency
            stdout=sp.PIPE,
            stdin=sp.PIPE,
            stderr=sp.PIPE,
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
            self.pathVar.set(os.path.normpath(filePath))
            self.navigateToFolder()

    def trace(self):
        fileName = os.path.basename(self.pathVar.get())

        options = " ".join(
            (
                v
                for v in (
                    ("-c" if self.arg_c.get() else None),
                    ("-t" if self.arg_t.get() else None),
                    ("-l" if self.arg_l.get() else None),
                    ("-r" if self.arg_r.get() else None),
                    ("-T" if self.arg_T.get() else None),
                    (
                        "-f " + self.fargs.get()
                        if self.fargs.get() != ""
                        else None
                    ),
                    (
                        "-C " + self.Cargs.get()
                        if self.Cargs.get() != ""
                        else None
                    ),
                    ("-m" if self.arg_m.get() else None),
                    ("-s" if self.arg_s.get() else None),
                    ("-R" if self.arg_R.get() else None),
                    ("-g" if self.arg_g.get() else None),
                )
                if v is not None
            )
        )
        traceCommand = " ".join(["python -m trace", options, fileName, "\n"])
        self.p.stdin.write(traceCommand.encode())
        self.p.stdin.flush()

    def destroy(self):  #
        """This is the function that is automatically called when the widget is
        destroyed, and overrides the widget's default destroy()"""
        self.alive = False
        # write exit() to the console in order to stop it running

        self.p.terminate()  # this, if the above didn't work, sends a Termination signal
        self.p.kill()  # and a kill signal. On windows this is the same.
        # these methods are a lot more effective than sending "exit" and flushing

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
        folderPath = os.path.dirname(self.pathVar.get())

        self.p.stdin.write(
            "cd {:}\n".format(folderPath).encode()
        )  # This is also platform independent.

        self.p.stdin.flush()

    def write(self, string):
        self.ttyText.insert(tk.END, string)
        self.ttyText.see(tk.END)
        self.line_start += len(string)


def main():
    root = ThemedTk(theme="equilux")
    """
    style = ttk.Style(root)
    style.theme_use("alt")
    """

    # root.option_add("*tearOff", False)
    # root.title("pyHeatTrace")

    # menubar = tk.Menu(root)
    # root.config(menu=menubar)
    heatTrace(root)
    root.mainloop()


if __name__ == "__main__":
    main()
