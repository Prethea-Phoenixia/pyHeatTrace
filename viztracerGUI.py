import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox
import subprocess as sp
from time import strftime, localtime

import sys
import os
import queue
import traceback
from threading import Thread
from platform import system

import psutil


class VizTracer(tk.Frame):
    def __init__(self, parent):
        # use this instead of super() due to multiple inheritance
        ttk.Frame.__init__(self, parent)
        # initially, let the fileVar be pointed at this file itself.
        self.pathVar = tk.StringVar(
            value=os.path.normpath(os.path.abspath(__file__))
        )
        self.pack(expand=1, fill="both")  # pack the VizTracer frame in root.

        self.addTracerWidgets()
        self.addViewerWidgets()

        self.addConsoleWidgets()
        self.addControlWidgets()

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

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

    def addTracerWidgets(self):
        tracerFrame = ttk.LabelFrame(self, text="Tracer Options")
        tracerFrame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        tracerFrame.columnconfigure(1, weight=1)

        ttk.Label(tracerFrame, text="Program").grid(
            row=0, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(tracerFrame, textvariable=self.pathVar).grid(
            row=0, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(
            tracerFrame,
            text="Select Program",
            underline=7,
            command=self.loadProgramme,
        ).grid(row=0, column=3, sticky="nsew", padx=2, pady=2)

        self.programArgs = (
            tk.StringVar()
        )  # additional arguments supplied to the profiled program
        ttk.Label(tracerFrame, text="arguments").grid(
            row=1, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(tracerFrame, textvariable=self.programArgs).grid(
            row=1, column=1, columnspan=3, sticky="nsew", padx=2, pady=2
        )

        self.output = tk.StringVar(value=".")
        ttk.Label(tracerFrame, text="-o, --output").grid(
            row=2, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(tracerFrame, textvariable=self.output).grid(
            row=2, column=1, sticky="nsew", padx=2, pady=2
        )
        self.outputFormat = tk.StringVar()
        outFmtCombobox = ttk.Combobox(
            tracerFrame,
            textvariable=self.outputFormat,
            values=["html", "json"],
            state="readonly",
            width=5,
        )
        outFmtCombobox.current(0)
        outFmtCombobox.grid(row=2, column=2, sticky="nsew", padx=2, pady=2)
        ttk.Button(
            tracerFrame,
            text="Select File",
            underline=7,
            command=lambda: self.output.set(self.selectFile()),
        ).grid(row=2, column=3, sticky="nsew", padx=2, pady=2)

        checkFrame = tk.Frame(tracerFrame)
        checkFrame.grid(
            row=3, column=0, columnspan=4, sticky="nsew", padx=10, pady=10
        )

        for i in range(4):
            checkFrame.columnconfigure(i, weight=1)

        self.ignoreCFunction = tk.IntVar(value=1)
        ttk.Checkbutton(
            checkFrame,
            text="--ignore_c_functions",
            variable=self.ignoreCFunction,
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        self.ignoreFrozen = tk.IntVar(value=1)
        ttk.Checkbutton(
            checkFrame,
            text="--ignore_frozen",
            variable=self.ignoreFrozen,
        ).grid(row=0, column=1, sticky="nsew", padx=2, pady=2)

        self.sanitizeFunctionName = tk.IntVar(value=1)
        ttk.Checkbutton(
            checkFrame,
            text="--sanitize_function_name",
            variable=self.sanitizeFunctionName,
        ).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        self.logException = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_exception",
            variable=self.logException,
        ).grid(row=1, column=0, sticky="nsew", padx=2, pady=2)

        self.logExit = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_exit",
            variable=self.logExit,
        ).grid(row=1, column=1, sticky="nsew", padx=2, pady=2)

        self.logFuncArgs = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_func_args",
            variable=self.logFuncArgs,
        ).grid(row=1, column=2, sticky="nsew", padx=2, pady=2)

        self.logFuncRetval = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_func_retval",
            variable=self.logFuncRetval,
        ).grid(row=1, column=3, sticky="nsew", padx=2, pady=2)

        self.logPrint = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_print",
            variable=self.logPrint,
        ).grid(row=2, column=0, sticky="nsew", padx=2, pady=2)

        self.logSparse = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_sparse",
            variable=self.logSparse,
        ).grid(row=2, column=1, sticky="nsew", padx=2, pady=2)

        self.logGC = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_gc",
            variable=self.logGC,
        ).grid(row=2, column=2, sticky="nsew", padx=2, pady=2)

        self.open = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--open",
            variable=self.open,
        ).grid(row=2, column=3, sticky="nsew", padx=2, pady=2)

        self.logAsync = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--log_async",
            variable=self.logAsync,
        ).grid(row=3, column=0, sticky="nsew", padx=2, pady=2)

        self.ignoreMltiprocess = tk.IntVar(value=0)
        ttk.Checkbutton(
            checkFrame,
            text="--ignore_multiprocess",
            variable=self.ignoreMltiprocess,
        ).grid(row=3, column=1, sticky="nsew", padx=2, pady=2)

    def addViewerWidgets(self):
        viewerFrame = ttk.LabelFrame(self, text="vizViewer Options")
        viewerFrame.grid(row=1, column=0, stick="nsew", padx=10, pady=10)
        viewerFrame.columnconfigure(1, weight=1)

        checkFrame = tk.Frame(viewerFrame)
        checkFrame.grid(
            row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=10
        )
        for i in range(2):
            checkFrame.columnconfigure(i, weight=1)

        self.flameGraph = tk.IntVar(value=0)

        ttk.Checkbutton(
            checkFrame, text="--flamegraph", variable=self.flameGraph
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

    def addConsoleWidgets(self):
        consoleFrame = ttk.LabelFrame(self, text="Console")
        consoleFrame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        # allow 3,1 to unconditionally take up more space as the window is resized

        consoleFrame.columnconfigure(0, weight=1)
        consoleFrame.rowconfigure(0, weight=1)

        scroll = ttk.Scrollbar(consoleFrame, orient="vertical")
        scroll.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)

        self.ttyText = tk.Text(
            consoleFrame,
            wrap=tk.CHAR,
            undo=True,
            yscrollcommand=scroll.set,
            height=10,
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
        operationFrame.grid(row=3, column=0, stick="nsew")

        for i in range(2):
            operationFrame.columnconfigure(index=i, weight=1)

        ttk.Button(
            operationFrame, text="Reset Console", command=self.restart
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        ttk.Button(operationFrame, text="Run Trace", command=self.trace).grid(
            row=0, column=1, sticky="nsew", padx=2, pady=2
        )

    def loadProgramme(self):
        filePath = tkfiledialog.askopenfilename(
            title="Load Programme to be Analyzed",
            filetypes=(("Python Programme", "*.py"),),
            defaultextension=".py",
        )

        exceptionMsg = "Exception:"
        if filePath == "":
            tkmessagebox.showinfo(exceptionMsg, "No File Selected")
        else:
            self.pathVar.set(os.path.normpath(filePath))
            self.navigateToFolder()

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

        # self.p.terminate()  # this, if the above didn't work, sends a Termination signal
        # self.p.kill()  # and a kill signal. On windows this is the same.
        # these methods are a lot more effective than sending "exit" and flushing

        self.endSubprocess()

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

        self.output.set(".")

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
        self.navigateToFolder()

    def trace(self):
        parentDir, fileName = os.path.split(
            self.pathVar.get()
        )  # drive:/path/to/file.ext -> drive:/path/to/, file.ext
        file, ext = os.path.splitext(fileName)
        profileDir = file + "_viz"
        profilePath = os.path.normpath(os.path.join(parentDir, profileDir))

        if not os.path.exists(profilePath):
            os.makedirs(profilePath)

        if self.output.get() == ".":
            self.output.set(
                os.path.normpath(
                    os.path.join(
                        profilePath, file + "." + self.outputFormat.get()
                    )
                )
            )
        else:
            self.output.set(
                os.path.splitext(self.output.get())[0]
                + "."
                + self.outputFormat.get()
            )

        vizTracerCmd = " ".join(
            arg
            for arg in (
                "viztracer",
                "--ignore_frozen" if self.ignoreFrozen.get() else None,
                "--ignore_c_function" if self.ignoreCFunction.get() else None,
                "--sanitize_function_name"
                if self.sanitizeFunctionName.get()
                else None,
                "--log_exception" if self.logException.get() else None,
                "--log_exit" if self.logExit.get() else None,
                "--log_func_args" if self.logFuncArgs.get() else None,
                "--log_func_retval" if self.logFuncRetval.get() else None,
                "--log_print" if self.logPrint.get() else None,
                "--log_sparse" if self.logSparse.get() else None,
                "--log_gc" if self.logGC.get() else None,
                "--open" if self.open.get() else None,
                "--log_async" if self.logAsync.get() else None,
                "--ignore_multiprocess"
                if self.ignoreMltiprocess.get()
                else None,
                '-o "' + self.output.get() + '"',
                "-- " + self.pathVar.get(),
                self.programArgs.get(),
                "\n",
            )
            if arg is not None
        )

        vizViewerCmd = " ".join(
            arg
            for arg in (
                "vizviewer",
                "--flamegraph" if self.flameGraph.get() == 1 else None,
                self.output.get(),
                "\n",
            )
            if arg is not None
        )

        self.p.stdin.write(vizTracerCmd.encode())
        self.p.stdin.flush()
        self.p.stdin.write(vizViewerCmd.encode())
        self.p.stdin.flush()


def main():
    root = tk.Tk()
    root.option_add("*tearOff", False)
    root.title("vizTracer + vizViewer")
    VizTracer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
