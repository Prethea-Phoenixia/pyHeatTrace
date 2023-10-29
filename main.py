import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfiledialog
import tkinter.messagebox as tkmessagebox


"""
Jinpeng Zhai
Main script to analyze a Python file, using a tk-GUI for interactivity
"""

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
        self.pack(expand=1, fill="both")  # pack the heatTrace frame in root.

        fileMenu = tk.Menu(menubar)
        menubar.add_cascade(
            label="File", underline=0, menu=fileMenu
        )  # cascading file menu
        fileMenu.add_command(
            label="Load Programme", underline=0, command=self.load
        )  # command button to load programmes

        self.columnconfigure(1, weight=1)

        ttk.Label(self, text="Entry Point", underline=0, anchor="e").grid(
            row=0, column=0, sticky="nsew"
        )

        # entryPointStr = tk.StringVar()
        self.entryPointDropdown = ttk.Combobox(
            self,
            # textvariable=entryPointStr,
            # values=self.getTopLevel(),
            values=[],  # initialize it empty
            justify="center",
            state="readonly",
        )
        self.entryPointDropdown.grid(row=0, column=1, sticky="nsew")
        self.entryPointDropdown.option_add(
            "*TCombobox*Listbox.Justify", "center"
        )
        ttk.Button(self, text="Run", command=self.trace).grid(
            row=0, column=2, sticky="nsew"
        )

        self.parse("main.py")

    def load(self):
        fileName = tkfiledialog.askopenfilename(
            title="Load Programme to be Analyzed",
            filetypes=(("Python Programme", "*.py"),),
            defaultextension=".py",
            initialfile="main.py",
            initialdir="./",  # set to local dir relative to where this script is stored
        )

        exceptionMsg = "Exception Occured during Load"
        if fileName == "":
            tkmessagebox.showinfo(exceptionMsg, "No File Selected")
            return

        try:
            self.parse(fileName)
        except (
            Exception
        ):  # normally catching a bare exception is not recommended
            exc_type, exc_value, exc_traceback = sys.exc_info()
            exceptionDesc = "".join(
                traceback.format_exception(exc_type, exc_value, exc_traceback)
            )
            tkmessagebox.showinfo(exceptionMsg, exceptionDesc)

    def parse(self, fileName):
        """
        Parse a given filename. Works entirely via side-effects:
        Side effects:
            self.tree:
                is set
            self.entryPointDropdown:
                is set to the list of global function definitions, the
                current selection is set to the last.

        Is called on every load (to target file) and during initialization
        (to this script itself.)
        """
        with open(fileName, "rt", encoding="utf-8") as file:  # rt: read as text
            tree = ast.parse(
                file.read(), filename=fileName
            )  # read the file into ast nodes

        topLevels = tuple(
            f.name for f in tree.body if isinstance(f, ast.FunctionDef)
        )

        if len(topLevels) == 0:
            raise ValueError(
                "The file being loaded does not contain any valid global function definition!"
            )

        self.entryPointDropdown["values"] = topLevels
        self.entryPointDropdown.current(
            len(topLevels) - 1
        )  # set the default entry point to the last one

        self.tree = tree

    def trace(self):
        pass


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

"""
def test():
    pass
"""
