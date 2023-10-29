import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox


root = tk.Tk()

import sys
import trace

import traceback

# use this instead of bare import since we want to parse code,
# not import (and risk running the code being imported)
import ast


class heatTrace(tk.Frame):
    def __init__(self, parent, menubar):
        # use this instead of super() due to multiple inheritance
        ttk.Frame.__init__(self, parent)
        fileMenu = tk.Menu(menubar)
        menubar.add_cascade(label="File", underline=0, menu=fileMenu)

        fileMenu.add_command(
            label="Load Programme", underline=0, command=self.load
        )

    def load(*_):
        fileName = tkfiledialog.askopenfilename(
            title="Load Programme to be Analyzed",
            filetypes=(("Python Programme", "*.py"),),
            defaultextension=".py",
            initialfile="",
        )
        exceptionMsg = "Exception Occured during Load"
        if fileName == "":
            tkmessagebox.showinfo(exceptionMsg, "No File Selected")
            return

        try:
            with open(
                fileName, "rt", encoding="utf-8"
            ) as file:  # rt: read as text
                astNodes = ast.parse(
                    file.read(), filename=fileName
                )  # read the file into ast nodes
                print(astNodes)

        except (
            Exception
        ):  # normally catching a bare exception is not recommended
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exceptionDesc = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
            tkmessagebox.showinfo(exceptionMsg, exceptionDesc)


if __name__ == "__main__":
    root.option_add("*tearOff", False)
    root.title("pyHeatTrace")

    menubar = tk.Menu(root)
    root.config(menu=menubar)
    heatTrace(root, menubar)
    root.mainloop()
