import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox
import subprocess as sp

import sys
import os
import queue
import traceback
from threading import Thread
from platform import system

import psutil


class Reverse(tk.Frame):
    def __init__(self, parent):
        # use this instead of super() due to multiple inheritance
        ttk.Frame.__init__(self, parent)
        # initially, let the fileVar be pointed at this file itself.
        self.pathDir = tk.StringVar(
            value=os.path.normpath(os.path.split(os.path.abspath(__file__))[0])
        )
        self.pack(expand=1, fill="both")  # pack the Reverse frame in root.

        self.addReverseWidgets()

        self.addConsoleWidgets()
        self.addControlWidgets()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

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

    def addReverseWidgets(self):
        reverseFrame = ttk.LabelFrame(self, text="pyreverse Options")
        reverseFrame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        reverseFrame.columnconfigure(1, weight=1)
        # group of widgets responsible for selecting the target file.
        ttk.Label(reverseFrame, text="Directory").grid(
            row=0, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(reverseFrame, textvariable=self.pathDir).grid(
            row=0, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(
            reverseFrame,
            text="Select Directory",
            underline=7,
            command=self.loadDirectory,
        ).grid(row=0, column=3, sticky="nsew", padx=2, pady=2)

        self.outputFormat = tk.StringVar()
        outFmtCombobox = ttk.Combobox(
            reverseFrame,
            textvariable=self.outputFormat,
            values=["svg", "png"],
            state="readonly",
            width=5,
        )
        outFmtCombobox.current(0)
        outFmtCombobox.grid(row=0, column=4, sticky="nsew", padx=2, pady=2)

    def addConsoleWidgets(self):
        consoleFrame = ttk.LabelFrame(self, text="Console")
        consoleFrame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # allow 3,1 to unconditionally take up more space as the window is resized

        consoleFrame.columnconfigure(0, weight=1)
        consoleFrame.rowconfigure(0, weight=1)

        scroll = ttk.Scrollbar(consoleFrame, orient="vertical")
        scroll.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.ttyText = tk.Text(
            consoleFrame, wrap=tk.CHAR, undo=True, yscrollcommand=scroll.set
        )

        scroll.config(command=self.ttyText.yview)

        self.ttyText.grid(row=0, column=0, sticky="nsew")
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

    def addControlWidgets(self):
        operationFrame = ttk.LabelFrame(self, text="Operations")
        operationFrame.grid(row=2, column=0, stick="nsew")

        for i in range(2):
            operationFrame.columnconfigure(index=i, weight=1)

        ttk.Button(
            operationFrame, text="Reset Console", command=self.restart
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        ttk.Button(operationFrame, text="Run Trace", command=self.Reverse).grid(
            row=0, column=1, sticky="nsew", padx=2, pady=2
        )

    def loadDirectory(self):
        dirPath = tkfiledialog.askdirectory(
            title="Select Directory for Cover File",
            mustexist=False,
            initialdir=".",  # set to local dir relative to where this script is stored
        )
        exceptionMsg = "Exception:"
        if dirPath == "":
            tkmessagebox.showinfo(exceptionMsg, "No File Selected")
        else:
            self.pathDir.set(os.path.normpath(dirPath))

    def selectFile(self):
        filePath = tkfiledialog.askopenfilename(
            title="Select File",
            filetypes=(("File", "*.*"),),
            defaultextension=".*",
        )

        return os.path.normpath(
            filePath
        )  # this will convert an empty selection to "."

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
            [
                "cmd" if system() == "Windows" else "bash"
            ],  # simple identification of the running system,
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

    def Reverse(self):
        parentDir = self.pathDir.get()
        profileDir = parentDir + "_uml"

        outputFormat = self.outputFormat.get()

        if not os.path.exists(profileDir):
            os.makedirs(profileDir)

        reverseCmd = " ".join(
            arg
            for arg in (
                "pyreverse",
                parentDir,
                "--output-directory " + profileDir,
                "\n",
            )
            if arg is not None
        )

        dotClassesCmd = " ".join(
            arg
            for arg in (
                "dot",
                os.path.join(profileDir, "classes.dot"),
                "-T " + outputFormat,
                "-o " + os.path.join(profileDir, "classes." + outputFormat),
                "\n",
            )
            if arg is not None
        )

        dotPackagesCmd = " ".join(
            arg
            for arg in (
                "dot",
                os.path.join(profileDir, "packages.dot"),
                "-T " + outputFormat,
                "-o " + os.path.join(profileDir, "packages." + outputFormat),
                "\n",
            )
            if arg is not None
        )

        self.p.stdin.write(reverseCmd.encode())
        self.p.stdin.flush()

        self.p.stdin.write(dotClassesCmd.encode())
        self.p.stdin.flush()

        self.p.stdin.write(dotPackagesCmd.encode())
        self.p.stdin.flush()


def main():
    root = tk.Tk()
    root.option_add("*tearOff", False)
    root.title("pyReverse GUI")
    Reverse(root)
    root.mainloop()


if __name__ == "__main__":
    main()
