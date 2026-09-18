"""Console widget and stdout queue integration.

This module provides a `Console` widget that displays output text in a
scrollable view and supports searching. `StdoutQueue` is a multiprocessing
queue wrapper used to capture stdout messages and display them inside the
console.
"""

import multiprocessing as mp
import multiprocessing.queues as mpq
import queue
import sys

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk

from images import Images
from tooltip import Tooltip


class StdoutQueue(mpq.Queue):
    """Multiprocessing queue wrapper that can be used as a stdout stream."""

    def __init__(self, *args, **kwargs):
        ctx = mp.get_context()
        super().__init__(*args, **kwargs, ctx=ctx)

    def write(self, msg):
        """Write a message to the queue."""
        self.put(msg)

    def flush(self):
        """Flush the underlying stdout stream."""
        sys.__stdout__.flush()


class Console(ttk.Frame):
    """Scrollable console widget with search and stdout polling."""

    # Console attributes
    FONT = ("Consolas", 9)
    DIVIDER = "===============================================================================\n"
 
    def __init__(self, master, autoscroll=True, **kwargs):
        """Initialize the console widget and its toolbar, search box, and text view."""
        super().__init__(master, **kwargs)
        self.autoscroll = autoscroll

        # Create toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.grid(row=0, columnspan=2, sticky=tk.EW)

        # Add horizontal separator at the bottom of the toolbar
        #line = ttk.Separator(self.toolbar, orient= tk.HORIZONTAL)
        #line.pack(side=tk.BOTTOM, fill=tk.X)

        # Add search label into the toolbar
        self.lbl_search = ttk.Label(self.toolbar, text="Search:", padding=(5,0))
        self.lbl_search.pack(side=tk.LEFT)

        # Add search entry into the toolbar
        self.entry_search = ttk.Entry(self.toolbar)
        self.entry_search.bind("<Return>", lambda e: self.on_search())
        self.entry_search.bind("<Escape>", lambda e: self.on_clear_search())
        self.entry_search.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=0, pady=3)
        
        # Add search button into the toolbar
        self.btn_search = ttk.Button(
                    self.toolbar, 
                    bootstyle=tk.GHOST, 
                    image=Images().system["Filter"], 
                    takefocus=False,
                    command=self.on_search)
        self.btn_search.pack(side=tk.LEFT)

        # Add a tooltip for the search button
        Tooltip(self.btn_search, text="Search")
        
        # Polling timeout
        self.timeout = 100

        # Text widget
        self.scrolled_text = ttk.Text(self, bd=-1, wrap=tk.NONE, height=5, font=self.FONT)
        self.scrolled_text.grid(row=1, column=0, sticky=tk.NSEW)
        self.append("simunet® console output\n")
        self.append_divider()

        # Scrollbar y
        self.sb_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.scrolled_text.yview)
        self.sb_y.grid(row=1, column=1, sticky=tk.NS)

        # Scrollbar x
        self.sb_x = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.scrolled_text.xview)
        self.sb_x.grid(row=2, column=0, sticky=tk.EW)

        # Configure Scrollbar
        self.scrolled_text.config(yscrollcommand=self.sb_y.set)
        self.scrolled_text.config(xscrollcommand=self.sb_x.set)
        self.scrolled_text.configure(state=tk.DISABLED)

        # Configure grid rows and columns
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Start polling messages from the queue
        self.stdout_queue = StdoutQueue()
        self.after(self.timeout, self.poll_stdout_queue)

    def on_clear_search(self):
        """Clear the search field and refresh highlight results."""
        self.entry_search.delete(0, tk.END)
        self.on_search()

    def on_search(self):
        """Search console text and highlight matching results."""
        self.scrolled_text.tag_remove("found", "1.0", tk.END)

        find_str = self.entry_search.get()
        if find_str:
            idx = "1.0"
            while 1:
                idx = self.scrolled_text.search(
                    find_str, idx, nocase=1, stopindex=tk.END
                )
                if not idx:
                    break
                last_idx = "%s+%dc" % (idx, len(find_str))

                self.scrolled_text.tag_add("found", idx, last_idx)
                idx = last_idx
            self.scrolled_text.tag_config(
                "found",
                background=ttk.Style().colors.warning,
            )

        self.entry_search.focus_set()

    def append(self, message):
        """Append a message to the console text widget."""
        self.scrolled_text.configure(state=tk.NORMAL)
        self.scrolled_text.insert(tk.END, message)
        self.scrolled_text.configure(state=tk.DISABLED)

        if self.autoscroll:
            self.scrolled_text.yview(tk.END)

    def append_divider(self):
        """Append a divider line to the console output."""
        self.append(self.DIVIDER)

    def poll_stdout_queue(self):
        """Poll the stdout queue and append any pending messages."""
        while True:
            try:
                record = self.stdout_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.append(record)
        self.after(self.timeout, self.poll_stdout_queue)

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    con = Console(app)
    con.pack(fill=tk.BOTH, expand=tk.YES)
    
    for i in range(0,10):
        con.append("Message_{}\n".format(i))

    app.mainloop()
