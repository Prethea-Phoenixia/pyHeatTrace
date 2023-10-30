import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox
import subprocess as sp

"""
Jinpeng Zhai
Main script to analyze a Python file, using a tk-GUI for interactivity.

"""
import sys
import os
import queue
import traceback
from threading import Thread
from platform import system

import psutil


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
        ttk.Label(self, text="Traced Programme").grid(
            row=0, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(self, textvariable=self.pathVar, state="disabled").grid(
            row=0, column=1, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(
            self,
            text="Select Programme",
            underline=7,
            command=self.loadProgramme,
        ).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

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

        strargsFrm = ttk.Frame(modifierFrame)
        strargsFrm.grid(
            row=1, column=0, columnspan=4, sticky="nsew", padx=2, pady=2
        )

        strargsFrm.columnconfigure(1, weight=1)

        self.fargs = tk.StringVar()
        ttk.Label(strargsFrm, text="--file").grid(
            row=0, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(strargsFrm, textvariable=self.fargs).grid(
            row=0, column=1, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(
            strargsFrm, text="Select File", underline=7, command=self.selectFile
        ).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        self.Cargs = tk.StringVar(
            value=os.path.normpath(
                os.path.splitext(self.pathVar.get())[0] + "_coverage"
            )
        )

        ttk.Label(strargsFrm, text="--coverdir").grid(
            row=1, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(strargsFrm, textvariable=self.Cargs).grid(
            row=1, column=1, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(
            strargsFrm,
            text="Select Directory",
            underline=7,
            command=self.selectDirectory,
        ).grid(row=1, column=2, sticky="nsew", padx=2, pady=2)

        self.ignored_module = tk.StringVar(
            value=",".join((["os", "sys", "__init__"]))
        )
        ttk.Label(strargsFrm, text="--ignored_module").grid(
            row=2, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(strargsFrm, textvariable=self.ignored_module).grid(
            row=2, column=1, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(
            strargsFrm, text="Load Ignore", underline=5, command=self.loadIgnore
        ).grid(row=2, column=2, sticky="nsew", padx=2, pady=2)

        self.ignored_dir = tk.StringVar(value=os.pathsep.join(sys.path[1:]))
        ttk.Label(strargsFrm, text="--ignored_dir").grid(
            row=3, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(strargsFrm, textvariable=self.ignored_dir).grid(
            row=3, column=1, columnspan=2, stick="nsew", padx=2, pady=2
        )

        consoleFrame = ttk.LabelFrame(self,text="Console")
        consoleFrame.grid(row = 3, column = 0, columnspan=3, sticky="nsew", padx=10, pady=10)

        consoleFrame.columnconfigure(0, weight = 1)
        consoleFrame.rowconfigure(0, weight = 1)

        scroll = ttk.Scrollbar(consoleFrame, orient="vertical")
        scroll.grid(row = 0, column = 1, sticky="nsew", padx=0, pady=0)

        self.ttyText = tk.Text(consoleFrame, wrap=tk.CHAR, undo=True, yscrollcommand = scroll.set)
        self.ttyText.grid(
            row=0, column=0, sticky="nsew"
        )
        self.ttyText.config(
            background="black",
            foreground="green",
            insertbackground="white",
            selectbackground="grey",
            selectforeground="green",
        )

        self.ttyText.tag_config(
            "stdout",
            background="black",
            foreground="white",
            selectbackground="grey",
            selectforeground="black",
        )
        self.ttyText.tag_config(
            "stderr",
            background="black",
            foreground="red",
            selectbackground="grey",
            selectforeground="red",
        )



        operationFrame = ttk.LabelFrame(self, text="Operations")
        operationFrame.grid(row=4, column=0, columnspan=3, stick="nsew")

        for i in range(3):
            operationFrame.columnconfigure(index=i, weight=1)

        ttk.Button(
            operationFrame, text="Reset Console", command=self.restart
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        ttk.Button(
            operationFrame, text="Reset File", command=self.resetFile
        ).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        ttk.Button(operationFrame, text="Run Trace", command=self.trace).grid(
            row=1, column=0, columnspan=3, sticky="nsew", padx=2, pady=2
        )

        for var in (
            self.arg_c,
            self.arg_t,
            self.arg_l,
            self.arg_r,
            self.arg_T,
            self.fargs,
            self.Cargs,
            self.arg_m,
            self.arg_s,
            self.arg_R,
            self.arg_g,
        ):
            var.trace_add("write", self.consistency)

        # make queues for keeping stdout and stderr whilst it is transferred between threads
        self.outQueue = queue.Queue()
        self.errQueue = queue.Queue()

        # keep track of where any line that is submitted starts
        self.line_start = 0

        # make the enter key call the self.enter function
        self.ttyText.bind("<Return>", self.enter)
        # and make sure the user does not delete past the starting point.
        self.ttyText.bind("<KeyRelease>", self.postKey)

        self.startSubprocess()
        self.writeLoop()  # start the write loop in the main thread

    def loadProgramme(self):
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

            name = os.path.splitext(os.path.basename(self.pathVar.get()))[0]
            self.Cargs.set(
                os.path.normpath(
                    os.path.join(
                        os.path.dirname(self.pathVar.get()), name + "_coverage"
                    )
                )
            )

            self.fargs.set(
                os.path.normpath(os.path.join(self.Cargs.get(), name + ".file"))
            )
            self.navigateToFolder()

    def loadIgnore(self):
        filePath = tkfiledialog.askopenfilename(
            title="Ignored Modules",
            filetypes=(("Text File", "*.txt"),),
            defaultextension=".txt",
            initialfile="ignore.txt",
            initialdir=".",  # set to local dir relative to where this script is stored
        )

        if filePath == "":
            tkmessagebox.showinfo("Exception:", "No File Selected")
        else:
            try:
                with open(os.path.normpath(filePath), "rt") as file:
                    ignores = file.read()

                self.ignored_module.set(ignores.replace("\n", ""))

            except (
                Exception
            ):  # normally catching a bare exception is not recommended
                exc_type, exc_value, exc_traceback = sys.exc_info()
                exceptionDesc = "".join(
                    traceback.format_exception(
                        exc_type, exc_value, exc_traceback
                    )
                )
                tkmessagebox.showinfo("Exception", exceptionDesc)

    def selectDirectory(self):
        dirPath = tkfiledialog.askdirectory(
            title="Select Directory for Cover File",
            mustexist=False,
            initialdir=".",  # set to local dir relative to where this script is stored
        )

        self.Cargs.set(os.path.normpath(dirPath))  # allow bare

    def selectFile(self):
        filePath = tkfiledialog.askopenfilename(
            title="Select File to Accumulate",
            filetypes=(("File", "*.*"),),
            defaultextension=".*",
            initialfile="",
            initialdir=".",  # set to local dir relative to where this script is stored
        )
        self.fargs.set(
            os.path.normpath(filePath)
        )  # note! this will change "" to "."

    def consistency(self, *args):
        # -l (listfuncs) is mutually exclusive with -c (--count) or -t (--trace)
        if self.arg_l.get() and any(
            v == 1 for v in (self.arg_c.get(), self.arg_t.get())
        ):
            self.arg_c.set(0)
            self.arg_t.set(0)
            self.arg_l.set(0)

        if not self.arg_t.get():
            self.arg_g.set(0)

        # if self.arg_c.get(): # count and file are used at the same time

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
        self.postKey(None)
        # ensure the Enter key, if pressed simultaneousely, effectively
        # "interrupts" other entries by forcing the postKey to be called.
        string = self.ttyText.get(1.0, tk.END)[self.line_start :]
        self.line_start += len(string)
        self.p.stdin.write(string.encode())
        self.p.stdin.flush()

    def postKey(self, e):
        ttyNow, ttyNowTagDict = self.ttyNow
        ttyNew = self.ttyText.get(1.0, tk.END)[: len(ttyNow)]
        if ttyNew != ttyNow:
            self.ttyText.edit_undo()
            self.ttyText.edit_reset()

            for tag, ranges in ttyNowTagDict.items():
                for startIndex, endIndex in zip(ranges[::2], ranges[1::2]):
                    self.ttyText.tag_add(tag, startIndex, endIndex)

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
            self.write(self.errQueue.get(), tag="stderr")
        if not self.outQueue.empty():
            out = self.outQueue.get()
            self.write(out, tag="stdout")

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

    def write(self, string, tag=None):
        self.ttyText.insert(tk.END, string, tag)
        self.ttyText.see(tk.END)
        self.ttyText.mark_set(tk.INSERT, tk.END)

        self.line_start += len(string)

        self.ttyText.edit_reset()

        self.ttyNow = (
            self.ttyText.get(1.0, tk.END)[: self.line_start],
            {tag: self.ttyText.tag_ranges(tag) for tag in ("stdout", "stderr")},
        )

    def startSubprocess(self):
        # open a subprocess to this script.
        self.p = sp.Popen(
            ["cmd" if system() == 'window' else 'bash'], # simple identification of the running system,
            stdout=sp.PIPE,
            stdin=sp.PIPE,
            stderr=sp.PIPE,
        )

        # a daemon to keep track of the threads so they can stop running
        self.alive = True
        # start the functions that get stdout and stderr in separate threads
        Thread(target=self.readFromProccessOut).start()
        Thread(target=self.readFromProccessErr).start()

    def endSubprocess(self):
        self.alive = False

        # use psutil (a cross platform tool) to recursively kill the children
        # to ensure a clean exit.
        process = psutil.Process(self.p.pid)
        for childProcess in process.children(recursive=True):
            childProcess.kill()
        process.kill()

        while not self.errQueue.empty():
            self.errQueue.get()
        while not self.outQueue.empty():
            self.outQueue.get()

        # the original way of ending subprocesses.
        self.p.terminate()
        self.p.kill()

    def restart(self):
        self.endSubprocess()
        self.clear()
        self.startSubprocess()

    def trace(self):
        fileName = os.path.basename(self.pathVar.get())

        needFilearg = (
            self.arg_c.get() or self.arg_r.get()
        )  # file arg is supplied whenever either a --report or a --count is specified.

        if needFilearg and self.fargs.get() == ".":
            name = os.path.splitext(os.path.basename(self.pathVar.get()))[0]
            filePath = os.path.normpath(
                os.path.join(self.Cargs.get(), name + ".file")
            )
            # this creates the file that trace writes to, in order to persist
            # tracing counts between runs.

            self.fargs.set(filePath)

        options = " ".join(
            (
                arg
                for arg in (
                    ("-c" if self.arg_c.get() else None),
                    ("-t" if self.arg_t.get() else None),
                    ("-l" if self.arg_l.get() else None),
                    ("-r" if self.arg_r.get() else None),
                    ("-T" if self.arg_T.get() else None),
                    ("-f " + self.fargs.get() if needFilearg else None),
                    (
                        "-C " + self.Cargs.get()
                    ),  # coverage report dir is always supplied
                    ("-m" if self.arg_m.get() else None),
                    ("-s" if self.arg_s.get() else None),
                    ("-R" if self.arg_R.get() else None),
                    ("-g" if self.arg_g.get() else None),
                    (
                        "--ignore-module=" + self.ignored_module.get()
                        if self.ignored_module.get()
                        else None
                    ),
                    (
                        "--ignore-dir=" + self.ignored_dir.get()
                        if self.ignored_dir.get()
                        else None
                    ),
                )
                if arg is not None
            )
        )
        traceCommand = " ".join(["python -m trace", options, fileName, "\n"])
        self.p.stdin.write(traceCommand.encode())
        self.p.stdin.flush()

    def resetFile(self):
        if os.path.exists(self.fargs.get()):
            os.remove(self.fargs.get())


def main():
    root = tk.Tk()
    root.option_add("*tearOff", False)
    root.title("pyHeatTrace")
    heatTrace(root)
    root.mainloop()


if __name__ == "__main__":
    main()
