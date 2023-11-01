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


USE_BUNDLED = False
# flag to toggle whether to use system or the bundled version.
# we might want to do this if in the future this becomes necessary
BUNDLED_GPROF2DOT = "gprof2dot/gprof2dot.py"


class ProfileToDot(tk.Frame):
    def __init__(self, parent):
        # use this instead of super() due to multiple inheritance
        ttk.Frame.__init__(self, parent)
        # initially, let the fileVar be pointed at this file itself.
        self.pathVar = tk.StringVar(
            value=os.path.normpath(os.path.abspath(__file__))
        )
        self.pack(expand=1, fill="both")  # pack the ProfileToDot frame in root.

        # group of widgets responsible for selecting the target file.
        ttk.Label(self, text="Profiled Program").grid(
            row=0, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(self, textvariable=self.pathVar, state="disabled").grid(
            row=0, column=1, sticky="nsew", padx=2, pady=2
        )
        ttk.Button(
            self,
            text="Select Program",
            underline=7,
            command=self.loadProgramme,
        ).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        profileOptionFrame = ttk.LabelFrame(self, text="Profiler Options")
        profileOptionFrame.grid(
            row=1, column=0, columnspan=3, sticky="nsew", padx=10, pady=10
        )

        self.p_arg_m = tk.IntVar()
        ttk.Label(profileOptionFrame, text="-m, --module").grid(
            row=0, column=0, stick="nsew", padx=2, pady=2
        )
        ttk.Checkbutton(
            profileOptionFrame,
            variable=self.p_arg_m,
        ).grid(row=0, column=1, columnspan=2, sticky="nsew", padx=2, pady=2)

        self.p_arg_o = tk.StringVar(value=".")
        ttk.Label(profileOptionFrame, text="-o, --output").grid(
            row=1, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(profileOptionFrame, textvariable=self.p_arg_o).grid(
            row=1, column=1, sticky="nsew", padx=2, pady=2
        )
        profileOptionFrame.columnconfigure(1, weight=1)
        ttk.Button(
            profileOptionFrame,
            text="Select File",
            underline=7,
            command=lambda: self.p_arg_o.set(self.selectFile()),
        ).grid(row=1, column=2, sticky="nsew", padx=2, pady=2)

        self.p_arg_s = (
            tk.StringVar()
        )  # note: this one contains (explanatory text in parenthesis)

        ttk.Label(profileOptionFrame, text="-s, --sort").grid(
            row=2, column=0, sticky="nsew", padx=2, pady=2
        )

        p_s_Combobox = ttk.Combobox(
            profileOptionFrame,
            textvariable=self.p_arg_s,
            values=[
                "calls (call count)",
                "cumulative (cumulative time)",
                "filename (file name)",
                "pcalls (primitive call count)",
                "line (line number)",
                "name (function name)",
                "nfl (name/file/line)",
                "stdname (standard name)",
                "time (internal time)",
            ],
            state="readonly",
        )
        p_s_Combobox.current(0)
        p_s_Combobox.grid(
            row=2, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        prof2dotOptionFrame = ttk.LabelFrame(self, text="prof2dot Options")

        prof2dotOptionFrame.grid(
            row=2, column=0, columnspan=3, stick="nsew", padx=2, pady=2
        )

        self.d_arg_o = tk.StringVar(value=".")
        ttk.Label(prof2dotOptionFrame, text="-o FILE, --output=").grid(
            row=0, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(prof2dotOptionFrame, textvariable=self.d_arg_o).grid(
            row=0, column=1, sticky="nsew", padx=2, pady=2
        )
        prof2dotOptionFrame.columnconfigure(1, weight=1)
        ttk.Button(
            prof2dotOptionFrame,
            text="Select File",
            underline=7,
            command=lambda: self.d_arg_o.set(self.selectFile()),
        ).grid(row=0, column=2, sticky="nsew", padx=2, pady=2)

        self.d_arg_n = tk.StringVar(value="0.5")
        ttk.Label(
            prof2dotOptionFrame, text="-n PERCENTAGE, --node-thres="
        ).grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        ttk.Entry(prof2dotOptionFrame, textvariable=self.d_arg_n).grid(
            row=1, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        self.d_arg_e = tk.StringVar(value="0.1")
        ttk.Label(
            prof2dotOptionFrame, text="-e PERCENTAGE, --edge-thres="
        ).grid(row=2, column=0, sticky="nsew", padx=2, pady=2)
        ttk.Entry(prof2dotOptionFrame, textvariable=self.d_arg_e).grid(
            row=2, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        self.d_arg__total = tk.StringVar()

        ttk.Label(prof2dotOptionFrame, text="-total=TOTALMETHOD").grid(
            row=3, column=0, sticky="nsew", padx=2, pady=2
        )
        d__total_Combobox = ttk.Combobox(
            prof2dotOptionFrame,
            textvariable=self.d_arg__total,
            values=["callratios", "callstacks"],
            state="readonly",
        )
        d__total_Combobox.grid(
            row=3, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )
        d__total_Combobox.current(0)  # default: call-ratio

        self.d_arg_c = tk.StringVar()
        ttk.Label(prof2dotOptionFrame, text="-c THEME, --colormap=").grid(
            row=4, column=0, sticky="nsew", padx=2, pady=2
        )
        d_c_Combobox = ttk.Combobox(
            prof2dotOptionFrame,
            textvariable=self.d_arg_c,
            values=["bw", "color", "gray", "pink", "print"],
            state="readonly",
        )
        d_c_Combobox.grid(
            row=4, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )
        d_c_Combobox.current(1)  # default: color

        self.d_arg_s = tk.StringVar()
        ttk.Label(prof2dotOptionFrame, text="-s, --strip").grid(
            row=5, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(prof2dotOptionFrame, textvariable=self.d_arg_s).grid(
            row=5, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        self.d_arg__CNBSelftime = tk.IntVar()
        ttk.Label(prof2dotOptionFrame, text="-color-nodes-by-selftime").grid(
            row=6, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Checkbutton(
            prof2dotOptionFrame, variable=self.d_arg__CNBSelftime
        ).grid(row=6, column=1, columnspan=2, sticky="nsew", padx=2, pady=2)

        self.d_arg_w = tk.IntVar()
        ttk.Label(prof2dotOptionFrame, text="-w, --wrap").grid(
            row=7, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Checkbutton(prof2dotOptionFrame, variable=self.d_arg_w).grid(
            row=7, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        self.d_arg__SSamples = tk.IntVar()
        ttk.Label(prof2dotOptionFrame, text="--show-samples").grid(
            row=8, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Checkbutton(
            prof2dotOptionFrame, variable=self.d_arg__SSamples
        ).grid(row=8, column=1, columnspan=2, sticky="nsew", padx=2, pady=2)

        self.d_arg__node_label = tk.StringVar()
        ttk.Label(prof2dotOptionFrame, text="--node-label=MEASURE").grid(
            row=9, column=0, sticky="nsew", padx=2, pady=2
        )
        d__node_label_Combobox = ttk.Combobox(
            prof2dotOptionFrame,
            textvariable=self.d_arg__node_label,
            values=[
                "self-time",
                "self-time-percentage",
                "total-time",
                "total-time-percentage",
            ],
            state="readonly",
        )
        d__node_label_Combobox.current(3)
        d__node_label_Combobox.grid(
            row=9, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        self.d_arg__skew = tk.StringVar(value="1.0")
        ttk.Label(prof2dotOptionFrame, text="--skew=THEME_SKEW").grid(
            row=10, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(prof2dotOptionFrame, textvariable=self.d_arg__skew).grid(
            row=10, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        # we skip all the prune calls for now.
        self.d_arg_p = tk.StringVar(value=".")
        ttk.Label(prof2dotOptionFrame, text="-p FILTER_PATHS, --path=").grid(
            row=11, column=0, sticky="nsew", padx=2, pady=2
        )
        ttk.Entry(prof2dotOptionFrame, textvariable=self.d_arg_p).grid(
            row=11, column=1, columnspan=2, sticky="nsew", padx=2, pady=2
        )

        consoleFrame = ttk.LabelFrame(self, text="Console")
        consoleFrame.grid(
            row=3, column=0, columnspan=3, sticky="nsew", padx=10, pady=10
        )

        # allow 3,1 to unconditionally take up more space as the window is resized
        self.columnconfigure(1, weight=1)
        self.rowconfigure(3, weight=1)

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

        operationFrame = ttk.LabelFrame(self, text="Operations")
        operationFrame.grid(row=4, column=0, columnspan=3, stick="nsew")

        for i in range(2):
            operationFrame.columnconfigure(index=i, weight=1)

        ttk.Button(
            operationFrame, text="Reset Console", command=self.restart
        ).grid(row=0, column=0, columnspan=2, sticky="nsew", padx=2, pady=2)

        ttk.Button(
            operationFrame, text="Run Trace", command=self.profile2dot
        ).grid(row=1, column=0, sticky="nsew", padx=2, pady=2)
        ttk.Button(
            operationFrame,
            text="Run Trace and Save to File",
            command=lambda: self.profile2dot(tee=True),
        ).grid(row=1, column=1, sticky="nsew", padx=2, pady=2)

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

        return os.path.normpath(dirPath)

    def selectFile(self):
        filePath = tkfiledialog.askopenfilename(
            title="Select File",
            filetypes=(("File", "*.*"),),
            defaultextension=".*",
            initialfile="",
            initialdir=".",  # set to local dir relative to where this script is stored
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

    def navigateToFolder(self):
        folderPath = os.path.dirname(self.pathVar.get())

        self.p.stdin.write(
            "cd {:}\n".format(folderPath).encode()
        )  # This is also platform independent.
        self.p.stdin.flush()

        self.p_arg_o.set(".")
        self.d_arg_o.set(".")
        self.d_arg_p.set(".")

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

    def profile2dot(self, tee=False):
        parentDir, fileName = os.path.split(
            self.pathVar.get()
        )  # drive:/path/to/file.ext -> drive:/path/to/, file.ext
        file, ext = os.path.splitext(fileName)
        profileDir = file + "_profile"
        profilePath = os.path.normpath(os.path.join(parentDir, profileDir))

        if not os.path.exists(profilePath):
            os.makedirs(profilePath)

        if self.p_arg_o.get() == "." or self.p_arg_o.get() == "":
            self.p_arg_o.set(
                os.path.normpath(os.path.join(profilePath, file + ".pstats"))
            )  # output pstats file location

        if self.d_arg_o.get() == "." or self.d_arg_o.get() == "":
            self.d_arg_o.set(
                os.path.normpath(os.path.join(profilePath, file + ".png"))
            )  # output dot file

        if self.d_arg_p.get() == ".":
            normalizedPath = [
                os.path.normpath(p) for p in sys.path[1:] + [parentDir]
            ]
            """
            sys.path is modified in the following manner depending on the method
            of invocation: (per https://docs.python.org/3/library/sys.html)

                python -m module command line:
                    prepend the current working directory.

                python script.py command line:
                    prepend the script’s directory. If it’s a symbolic link, resolve symbolic links.

                python -c code and python (REPL) command lines:
                    prepend an empty string, which means the current working directory.

            parentDir is where the vast majority of calls would come from.
            """
            paths = os.pathsep.join(
                p for p in normalizedPath if os.path.exists(p)
            )
            self.d_arg_p.set(paths)

        cProfileCmd = " ".join(
            arg
            for arg in (
                "python -m",
                "cProfile",
                "-o " + self.p_arg_o.get(),
                "-s " + self.p_arg_s.get().split(" ")[0],
                ("-m " if self.p_arg_m.get() else None),
                self.pathVar.get(),
                "\n",
            )
            if arg is not None
        )

        prof2dotCmd = " ".join(
            arg
            for arg in (
                (
                    os.path.normpath(
                        os.path.join(
                            os.path.dirname(os.path.abspath(__file__)),
                            BUNDLED_GPROF2DOT,
                        )
                    )
                    if USE_BUNDLED
                    else "python -m gprof2dot"
                ),
                "-f pstats",
                (
                    "-n " + self.d_arg_n.get()
                    if self.d_arg_n.get() != ""
                    else None
                ),
                (
                    "-e " + self.d_arg_e.get()
                    if self.d_arg_e.get() != ""
                    else None
                ),
                "--total=" + self.d_arg__total.get(),
                "-c " + self.d_arg_c.get(),
                (
                    "-s " + self.d_arg_s.get()
                    if self.d_arg_s.get() != ""
                    else None
                ),
                (
                    "--color-nodes-by-selftime"
                    if self.d_arg__CNBSelftime.get()
                    else None
                ),
                ("-w" if self.d_arg_w.get() else None),
                ("--show-samples" if self.d_arg__SSamples.get() else None),
                "--node-label=" + self.d_arg__node_label.get(),
                "--skew=" + self.d_arg__skew.get(),
                (
                    " ".join(
                        "-p " + p for p in self.d_arg_p.get().split(os.pathsep)
                    )
                    if self.d_arg_p.get() != ""
                    else None
                ),  # filter path
                self.p_arg_o.get(),  # .pstats source file
                "|",
                "dot",
                "-Tpng",  # to png? this is undocumented
                "-o " + self.d_arg_o.get(),  # output to png
                "\n",
            )
            if arg is not None
        )
        self.p.stdin.write(cProfileCmd.encode())
        self.p.stdin.flush()
        self.p.stdin.write(prof2dotCmd.encode())
        self.p.stdin.flush()


def main():
    root = tk.Tk()
    root.option_add("*tearOff", False)
    root.title("cProfile + gprof2dot GUI")
    ProfileToDot(root)
    root.mainloop()


if __name__ == "__main__":
    main()
