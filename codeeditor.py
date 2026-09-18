"""Source code editor dialog used by the application.

Provides `CodeEditorDialog`, a simple text editor with syntax
highlighting, line numbers and basic edit actions (cut/copy/paste,
undo/redo) used throughout the UI.
"""

import re

import idlelib.colorizer as ic
import idlelib.percolator as ip
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.style import Style
from ttkbootstrap.dialogs import Dialog
from tkinter import TclError

from images import Images
from toolbar import Toolbar
from tooltip import Tooltip

import ast

class CodeEditorDialog(Dialog):
    """Dialog providing a lightweight source code editor.

    Features:
    - Syntax highlighting via IDLE's colorizer
    - Line numbers
    - Toolbar with search and edit actions
    """

    INDENT = "    "

    def __init__(self, parent=None, title="Source code editor", font=("Consolas", 11), code="", lang="python", readonly=False):
        """Initialize the editor dialog.

        Args:
            parent: Optional parent widget.
            title: Window title.
            font: Tuple with font family and size.
            code: Initial code text.
            lang: Language for syntax highlighting.
            readonly: Whether the editor is read-only.
        """
        super().__init__(parent=parent, title=title)

        self.code = code
        self.font = font
        self.lang = lang
        self.fold_lookup = {}
        self.readonly = readonly

    def create_body(self, master):
        """Create the main editor widgets and layout.

        Builds the border, line number canvas, text widget with syntax
        highlighting, scrollbars and the toolbar.
        """
        # Create toolbar images
        self.images = Images().ribbon

        # Create toolbar
        self.create_toolbar(master)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        # Create a body container
        container = ttk.Frame(master, padding=(10,10,10,0))
        container.pack(fill=tk.BOTH, expand=tk.YES, anchor=tk.N)

        # Add horizontal separator at the bottom of the toolbar
        line = ttk.Separator(container, orient= tk.HORIZONTAL)
        line.grid(row=0, column=0, columnspan=3, sticky=tk.NSEW)

        # Create line numbers canvas
        self.line_numbers = ttk.Canvas(container, border=-1, width=50)
        self.line_numbers.config(bg=ttk.Style().colors.light)
        self.line_numbers.grid(row=1, rowspan=2, column=0, sticky=tk.NSEW)
        self.line_numbers.bind("<Button-1>", self.on_gutter_click)

        # Create text editor widget
        self.txt_editor = ttk.Text(
            container,
            wrap=tk.NONE,
            undo=True,
            maxundo=-1,
            padx=2,
            pady=2,
            autoseparators=True,
            font=self.font,
            bd=-1,
            autostyle=False,
            selectbackground=Style().colors.selectbg,
        )
        self.txt_editor.grid(row=1, column=1, sticky=tk.NSEW)
        # Install text proxy to intercept text widget commands for event generation
        self.install_text_proxy()

        if self.lang=="python":

            # Python syntax highlighter using IDLE's colorizer
            cdg = ic.ColorDelegator()
            cdg.prog = re.compile(r"\b(?P<SIMUNET>self)\b|" + ic.make_pat().pattern, re.S)
            cdg.idprog = re.compile(r"\s+(\w+)", re.S)

            # Custom tag colors
            cdg.tagdefs["COMMENT"] = {"foreground": "#008000", "background": "#ffffff"}
            cdg.tagdefs["KEYWORD"] = {"foreground": "#0000ff", "background": "#ffffff"}
            cdg.tagdefs["SIMUNET"] = {"foreground": "#0000ff", "background": "#ffffff"}
            cdg.tagdefs["BUILTIN"] = {"foreground": "#0000ff", "background": "#ffffff"}
            cdg.tagdefs["STRING"] = {"foreground": "#800000", "background": "#ffffff"}
            cdg.tagdefs["DEFINITION"] = {"foreground": "#A000A0", "background": "#ffffff"}
            ip.Percolator(self.txt_editor).insertfilter(cdg)

        elif self.lang=="json":

            # JSON syntax highlighter
            cdg = ic.ColorDelegator()
            cdg.prog = re.compile(
                r"""
                (?P<KEY>"(?:\\.|[^"\\])*"(?=\s*:)) |
                (?P<STRING>("([^"\\]*(\\.[^"\\]*)*)")) |
                (?P<KEYWORD>\b(?:true|false|null)\b) |
                (?P<NUMBER>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?) |
                (?P<OP>[{}\[\]:,])
                """,
                re.VERBOSE | re.MULTILINE
            )

            # Disable Python identifier matching
            cdg.idprog = re.compile(r"$^")

            # Colors
            cdg.tagdefs["KEY"] = {"foreground": "#A000A0", "background": "#ffffff"}
            cdg.tagdefs["STRING"] = {"foreground": "#800000", "background": "#ffffff"}
            cdg.tagdefs["KEYWORD"] = {"foreground": "#0000ff", "background": "#ffffff"}
            cdg.tagdefs["OP"] = {"foreground": "#000000", "background": "#ffffff"}
            cdg.tagdefs["NUMBER"] = {"foreground": "#008000", "background": "#ffffff"}
            ip.Percolator(self.txt_editor).insertfilter(cdg)

        # Create scrollbars and attach widget
        self.sb_y = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.txt_editor.yview)
        self.sb_y.grid(row=1, column=2, sticky=tk.NS)

        self.sb_x = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=self.txt_editor.xview)
        self.sb_x.grid(row=2, column=1, sticky=tk.EW)
        self.txt_editor.config(xscrollcommand=self.sb_x.set)
        self.txt_editor.config(selectforeground="")

        # Bind events for text changes, cursor movement, and view changes
        self.txt_editor.bind("<Tab>", self.on_tab)
        self.txt_editor.bind("<<TextChanged>>", self.on_text_changed)
        self.txt_editor.bind("<<CursorMoved>>", self.on_cursor_changed)
        self.txt_editor.bind("<<ViewChanged>>", self.on_view_changed)
        self.txt_editor.bind("<<EditorStateChanged>>", lambda e: self.update_ui())
        self.txt_editor.bind("<MouseWheel>", lambda e: self.txt_editor.event_generate(
                "<<ViewChanged>>",
                when="tail"
            ),
            add=True
        )
        self.txt_editor.bind("<Configure>", lambda e: self.txt_editor.event_generate(
                "<<ViewChanged>>",
                when="tail"
            ),
            add=True
        )
        # Cursor- and selections changes can be triggered by 
        # key releases, mouse clicks, and focus events. 
        # We bind these events to generate the <<EditorStateChanged>> event.
        self.txt_editor.bind(
            "<KeyRelease>",
            lambda e: self.txt_editor.event_generate(
                "<<EditorStateChanged>>",
                when="tail"
            ),
            add=True
        )

        self.txt_editor.bind(
            "<ButtonRelease-1>",
            lambda e: self.txt_editor.event_generate(
                "<<EditorStateChanged>>",
                when="tail"
            ),
            add=True
        )

        self.txt_editor.bind(
            "<FocusIn>",
            lambda e: self.txt_editor.event_generate(
                "<<EditorStateChanged>>",
                when="tail"
            ),
            add=True
        )
        self.txt_editor.bind(
            "<Button-4>",
            lambda e: self.txt_editor.event_generate(
                "<<ViewChanged>>",
                when="tail"
            ),
            add=True
        )

        self.txt_editor.bind(
            "<Button-5>",
            lambda e: self.txt_editor.event_generate(
                "<<ViewChanged>>",
                when="tail"
            ),
            add=True
        )

        self.txt_editor.configure(yscrollcommand=self.on_textscroll)

        # Configure grid rows and columns
        container.columnconfigure(1, weight=1)
        container.rowconfigure(1, weight=1)

        # Insert initial code and set state
        self.txt_editor.insert("insert", self.code)
        if self.readonly:
            self.txt_editor.configure(state=tk.DISABLED)

        # Set tool window
        self._toplevel.wm_attributes("-toolwindow", "true")
        self._toplevel.wm_resizable(width=True, height=True)

    def on_textscroll(self, first, last):
        """Update the vertical scrollbar and trigger view change event."""
        self.sb_y.set(first, last)
        self.txt_editor.event_generate("<<ViewChanged>>", when="tail")

    def on_text_changed(self, event=None):
        """Handle text changes and rebuild folds."""
        self.build_folds()
        self.restore_fold_states()
        self.update_linenumbers()
        self.update_ui()

    def on_cursor_changed(self, event=None):
        """Handle cursor position changes."""
        self.update_ui()

    def on_view_changed(self, event=None):
        """Handle view changes (scrolling) and update line numbers."""
        self.update_linenumbers()

    def build_folds(self):
        """Build foldable regions based on the current text and language."""
        text = self.txt_editor.get("1.0", "end-1c")
        lines = text.splitlines()

        # Preserve the collapsed state of existing folds
        old_state = {
            start: fold["collapsed"]
            for start, fold in self.fold_lookup.items()
        }

        # Clear existing folds
        self.fold_lookup = {}

        # Build folds based on the language
        if self.lang == "python":
            self.build_python_folds(lines)
        elif self.lang == "json":
            self.build_json_folds(lines)

        # Restore the collapsed state of folds
        for start, fold in self.fold_lookup.items():
            fold["collapsed"] = old_state.get(start, False)

    def build_python_folds(self, lines):
        """Build foldable regions for Python code using AST parsing."""
        source = "\n".join(lines)

        # Use the AST module to parse the source code and identify foldable regions
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return

        # Walk through the AST nodes and identify foldable regions
        for node in ast.walk(tree):
            if isinstance(
                node,
                (
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.If,
                    ast.For,
                    ast.AsyncFor,
                    ast.While,
                    ast.Try,
                    ast.With,
                    ast.AsyncWith,
                    ast.Match,
                ),
            ):
                # Get the start and end line numbers for the node
                start = getattr(node, "lineno", None)
                end = getattr(node, "end_lineno", None)

                # Only add the fold if both start and end are valid and end is greater than start
                if start and end and end > start:
                    self.fold_lookup[start] = {
                        "end": end,
                        "collapsed": False
                    }

    def build_json_folds(self, lines):
        """Build foldable regions for JSON code based on braces and brackets."""
        stack = []

        # Iterate through each line of the JSON code
        for lineno, line in enumerate(lines, start=1):
            for c in line:
                # Check for opening and closing braces/brackets to identify foldable regions
                if c in "{[":
                    stack.append(lineno)
                elif c in "}]":
                    if stack:
                        start = stack.pop()
                        if lineno > start:
                            self.fold_lookup[start] = {
                                "end": lineno,
                                "collapsed": False
                            }

    def restore_fold_states(self):
        """Restore the collapsed state of folds after rebuilding."""
        for start, fold in self.fold_lookup.items():
            if fold["collapsed"]:
                self.fold_region(start)


    def unfold_region(self, start):
        """Unfold the region starting at the given line number."""
        # Get the fold information for the specified start line
        fold_tag = f"fold_{start}"
        header_tag = f"fold_header_{start}"

        # Remove the tag from the fold region to make it visible again
        self.txt_editor.tag_configure(fold_tag, elide=False)
        self.txt_editor.tag_delete(header_tag)
        self.fold_lookup[start]["collapsed"] = False

    def fold_region(self, start):
        """Fold the region starting at the given line number."""

        fold = self.fold_lookup[start]
        fold_tag = f"fold_{start}"
        header_tag = f"fold_header_{start}"

        self.txt_editor.tag_remove(fold_tag, "1.0", "end")
        self.txt_editor.tag_add(fold_tag, f"{start + 1}.0", f"{fold['end'] + 1}.0")
        self.txt_editor.tag_configure(fold_tag, elide=True )

        # mark header
        self.txt_editor.tag_add(header_tag, f"{start}.0", f"{start + 1}.0")
        self.txt_editor.tag_configure(header_tag, background="#e8f1ff")
        fold["collapsed"] = True
    
    def unfold_region(self, start):

        self.txt_editor.tag_configure(
            f"fold_{start}",
            elide=False
        )

        self.txt_editor.tag_delete(
            f"fold_header_{start}"
        )

        self.fold_lookup[start]["collapsed"] = False

    def on_gutter_click(self, event):
        """Handle clicks on the line number gutter to toggle folding."""
        if event.x > 12:
            return

        # Determine the line number based on the y-coordinate of the click event
        index = self.txt_editor.index(f"@0,{event.y}")
        lineno = int(index.split(".")[0])
        fold = self.fold_lookup.get(lineno)

        # Toggle the fold state if a fold exists for the clicked line
        if fold is None:
            return
        # Toggle the fold state based on whether it is currently collapsed or not
        if fold["collapsed"]:
            self.unfold_region(lineno)
        else:
            self.fold_region(lineno)

        # Update the line numbers to reflect the new fold state
        self.update_linenumbers()

    def update_linenumbers(self):
        """Update the line numbers displayed in the gutter."""

        self.line_numbers.delete("all")
        index = self.txt_editor.index("@0,0")

        # Loop through visible lines and draw line numbers and fold symbols
        while True:
            # Get the y-coordinate of the line based on the index
            dline = self.txt_editor.dlineinfo(index)
            if dline is None:
                break
            y = dline[1]
            lineno = int(index.split(".")[0])

            # Draw fold symbol if the line is a foldable region
            if lineno in self.fold_lookup:
                fold = self.fold_lookup[lineno]
                #symbol = "+" if fold["collapsed"] else "-"
                #symbol = "▸" if fold["collapsed"] else "▾"
                #symbol = "⮞" if fold["collapsed"] else "⮟"
                #symbol = "˃" if fold["collapsed"] else "˅"
                symbol = "⯈" if fold["collapsed"] else "⯆"

                self.line_numbers.create_text(
                    2,
                    y+2,
                    text=symbol,
                    anchor=tk.NW,
                    fill=Style().colors.primary,
                    font=("Consolas", 8)
                )

            # Draw the line number
            self.line_numbers.create_text(
                46,
                y,
                text=str(lineno),
                anchor=tk.NE,
                font=self.font,
                fill=Style().colors.secondary
            )
            # Move to the next line index
            index = self.txt_editor.index(f"{index}+1displaylines")

    def create_buttonbox(self, master):
        """Create dialog buttons (OK and Cancel) and a size grip."""

        # Add a sizegrip at the bottom-right
        sizegrip = ttk.Sizegrip(master)
        sizegrip.pack(side=tk.RIGHT, anchor=tk.SE)

        container = ttk.Frame(master, padding=(0, 10))
        container.pack(fill=tk.X)

        # OK button
        btn_ok = ttk.Button(
            master=container,
            bootstyle=tk.PRIMARY,
            takefocus=False,  
            width=6,
            text="OK"
        )
        btn_ok.bind("<Return>", lambda _: btn_ok.invoke())
        btn_ok.configure(command=lambda b=btn_ok: self.on_button_press(b))
        btn_ok.pack(padx=5, side=tk.RIGHT)

        # Cancel button
        btn_cancel = ttk.Button(
            container,
            bootstyle=tk.SECONDARY, 
            takefocus=False,  
            width=6, 
            text="Cancel")
        btn_cancel.bind("<Return>", lambda _: btn_cancel.invoke())
        btn_cancel.configure(command=lambda b=btn_cancel: self.on_button_press(b))
        btn_cancel.pack(padx=5, side=tk.RIGHT)

    def on_button_press(self, button):
        """Handle button presses and save edited table values on OK.

        Args:
            button: The button widget that was pressed.
        """
        self._result = button.cget('text')

        if self._result == 'OK':
            self.code = self.txt_editor.get("1.0", "end - 1 char")

        # Close window
        self.close()

    def on_tab(self, event):
        """Handle Tab key for indenting selection or inserting indent."""
        sel_first = self.txt_editor.index(tk.SEL_FIRST)
        sel_last = self.txt_editor.index(tk.SEL_LAST)

        if sel_first == sel_last:
            # Just add indent at the cursor position
            self.txt_editor.insert(tk.INSERT, self.INDENT)
        else:
            # Get linestart of the selection end
            sel_last_linestart = self.txt_editor.index("sel.last linestart")
            # If selection end is at linestart then ignore that line
            if sel_last_linestart == sel_last:
                sel_last_linestart = self.txt_editor.index("sel.last -1 char linestart")

            # Get the linestart of the selection beginning
            index = self.txt_editor.index("sel.first linestart")

            # Loop through the lines and add indent at each line start
            while self.txt_editor.compare(index, "<=", sel_last_linestart):
                self.txt_editor.insert(index, self.INDENT)
                index = self.txt_editor.index("%s + 1 line" % index)

        return "break"

    def create_toolbar(self, master):
        """Create toolbar with edit actions and search controls."""

        # Toolbar items
        tb_items = [
            ("Cut", "Cut", "Cut", "Cut selected objects (Strg+X)", self.on_cut),
            ("Copy", "Copy", "Copy", "Copy selected objects to clipboard (Strg+C)", self.on_copy),
            ("Paste", "Paste", "Paste", "Paste objects from clipboard (Strg+V)", self.on_paste),
            "---",
            ("Undo", "Undo", "Undo", "Undo previous action (Strg+Z)", self.on_undo),
            ("Redo", "Redo", "Redo", "Redo last action (Strg+Y)", self.on_redo),
            "---",
        ]

        # Create the toolbar
        self.toolbar = Toolbar(master, self.images, tb_items, show_text=False)

        # Add search frame
        frame = ttk.Frame(self.toolbar)
        frame.pack(side=tk.LEFT, padx=10)

        # Add a label
        self.lbl_chart = ttk.Label(frame, text="Search: ")
        self.lbl_chart.pack(side=tk.LEFT, fill=tk.Y)

        # Add the search entry
        self.entry_search = ttk.Entry(frame)
        self.entry_search.bind("<Return>", lambda e: self.on_search())
        self.entry_search.pack(side=tk.LEFT)

        # Add search button into the toolbar
        self.btn_search = ttk.Button(
            frame,
            bootstyle=tk.GHOST,
            image=Images().system["Search"],
            takefocus=False,
            command=self.on_search,
        )
        self.btn_search.pack(side=tk.LEFT)

        Tooltip(self.btn_search, text="Search")

        # Add clear search button
        self.btn_clear_search = ttk.Button(
            frame,
            bootstyle=tk.GHOST,
            image=Images().system["SearchClear"],
            takefocus=False,
            command=self.on_clear_search,
        )
        self.btn_clear_search.pack(side=tk.LEFT)

        Tooltip(self.btn_clear_search, text="Clear search")

        # Create a separator
        sep = ttk.Separator(self.toolbar, orient=tk.VERTICAL)
        sep.pack(after=frame, side=tk.LEFT, fill=tk.Y)

    def on_clear_search(self):
        # Clear search entry
        self.entry_search.delete(0, tk.END)
        self.on_search()

    def on_search(self):
        # Remove previous match
        self.txt_editor.tag_remove("found", "1.0", tk.END)
        
        # Get the search entry
        find_str = self.entry_search.get()
        if find_str:
            idx = "1.0"
            while 1:
                idx = self.txt_editor.search(
                    find_str, idx, nocase=1, stopindex=tk.END)
                if not idx: 
                    break
                last_idx = "%s+%dc" % (idx, len(find_str))
                
                self.txt_editor.tag_add("found", idx, last_idx)
                idx = last_idx
            self.txt_editor.tag_config(
                "found", 
                background=ttk.Style().colors.warning)
            
        self.entry_search.focus_set()

    def on_undo(self):
        self.txt_editor.edit_undo()
        self.txt_editor.event_generate("<<EditorStateChanged>>", when="tail")

    def on_redo(self):
        self.txt_editor.edit_redo()
        self.txt_editor.event_generate("<<EditorStateChanged>>", when="tail")

    def on_cut(self):
        self.on_copy()
        self.txt_editor.delete(tk.SEL_FIRST, tk.SEL_LAST)
        self.txt_editor.event_generate("<<EditorStateChanged>>", when="tail")

    def on_copy(self):
        self.txt_editor.clipboard_clear()
        text = self.txt_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        self.txt_editor.clipboard_append(text)
        self.txt_editor.event_generate("<<EditorStateChanged>>", when="tail")


    def on_paste(self):
        text = self.txt_editor.selection_get(selection="CLIPBOARD")
        self.txt_editor.insert(tk.INSERT, text)
        self.txt_editor.event_generate("<<EditorStateChanged>>", when="tail")

    def check_cut_copy(self):
        try:
            idx = self.txt_editor.index(tk.SEL_FIRST)
        except TclError:
            return False
        else:
            return True if idx!='None' else False

    def check_undo(self):
        return self.txt_editor.edit_modified()
    
    def check_redo(self):
        return True
    
    def check_paste(self):
        """Check if there is data in the clipboard to paste."""
        try:
            data = self.txt_editor.clipboard_get()
            return bool(data)
        except TclError:
            return False

    def show(self, position = None, wait_for_result = True):
        """Show the dialog and position it relative to `parent` if given.

        Blocks until the dialog is closed and cancels the redraw timer
        afterwards.
        """
        super().show(position, wait_for_result)

    def update_ui(self):
        """Update the state of toolbar buttons based on the current selection and clipboard."""
        self.toolbar.set_enabled("Cut", self.check_cut_copy())
        self.toolbar.set_enabled("Copy", self.check_cut_copy())
        self.toolbar.set_enabled("Paste", self.check_paste())
        self.toolbar.set_enabled("Undo", self.check_undo())
        self.toolbar.set_enabled("Redo", self.check_redo())

    def install_text_proxy(self):
        """Install a proxy for the text widget to intercept commands."""
        widget_name = str(self.txt_editor)
        proxy_name = widget_name + "_proxy"
        self.txt_editor.tk.call("rename", widget_name, proxy_name)
        # Create a new command with the original widget name that calls the proxy function
        self.txt_editor.tk.createcommand(
            widget_name,
            lambda *args: self._text_proxy(
                proxy_name,
                *args
            )
        )

    def _text_proxy(self, proxy_name, *args):
        """Proxy function to intercept text widget commands and generate events."""
        # Call the original text widget command
        try:

            cmd = (proxy_name,) + args
            result = self.txt_editor.tk.call(cmd)

            if args:
                # Determine the operation performed on the text widget
                operation = args[0]

                # Generate events based on the operation performed on the text widget
                if operation in ("insert", "delete", "replace"):
                    self.txt_editor.event_generate("<<TextChanged>>", when="tail")

                elif operation == "mark":
                    if len(args) >= 3:
                        if args[1] == "set" and args[2] == "insert":
                            self.txt_editor.event_generate("<<CursorMoved>>", when="tail")

                elif operation in ("xview", "yview"):
                    self.txt_editor.event_generate("<<ViewChanged>>", when="tail")

            return result
        except TclError:
            return None
        
if __name__ == "__main__":
    dlg = CodeEditorDialog(lang="python")
    dlg.show()

    print(dlg.result)
    print(dlg.code)
