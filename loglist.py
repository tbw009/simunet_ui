"""Logging queue display widget for simunet UI.

This module provides a GUI frame that polls a thread-safe logging queue
and displays log records in a searchable tree view.
"""

import logging
import queue
from simunetcore import logger
from tooltip import Tooltip
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap import utils
from tkinter import messagebox
from images import Images


class QueueHandler(logging.Handler):
    """Logging handler that forwards records into a queue."""

    def __init__(self, log_queue):
        """Create a queue handler that places formatted records into the queue."""
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        """Format and enqueue the logging record."""
        self.format(record)
        self.log_queue.put(record)


class Loglist(ttk.Frame):
    """Frame that polls a logging queue and displays records in a tree view."""
                
    def __init__(self, master, **kwargs):
        """Initialize the log list frame and start queue polling."""
        super().__init__(master, **kwargs)

        self.timeout = 100
 
        # Create toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.grid(row=0, columnspan=2, sticky=tk.EW)

        # Add horizontal separator at the bottom of the toolbar
        #line = ttk.Separator(self.toolbar, orient= tk.HORIZONTAL)
        #line.pack(side=tk.BOTTOM, fill=tk.X)

        # Add search label into the toolbar
        self.lbl_filter = ttk.Label(self.toolbar, text="Filter:", padding=(5,0))
        self.lbl_filter.pack(side=tk.LEFT)

        # Add search entry into the toolbar
        self.entry_filter = ttk.Entry(self.toolbar)
        self.entry_filter.bind("<Return>", lambda e: self.on_filter())
        self.entry_filter.bind("<Escape>", lambda e: self.on_clear_filter())
        self.entry_filter.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES, padx=0, pady=3)
        
        # Add search button into the toolbar
        self.btn_filter = ttk.Button(
                    self.toolbar, 
                    bootstyle=tk.GHOST, 
                    image=Images().system["Filter"], 
                    takefocus=False,
                    command=self.on_filter)
        self.btn_filter.pack(side=tk.LEFT)

        # Add a tooltip for the search button
        Tooltip(self.btn_filter, text="Filter")

        # Messagelist list images
        self.images = {
            "CRITICAL": Images().system["Critical"],
            "ERROR": Images().system["Error"],
            "WARNING": Images().system["Warning"],
            "INFO": Images().system["Info"],
            "DEBUG": Images().system["Debug"]
        }

        # Create treeview
        self.treeview = ttk.Treeview(
            self, bootstyle="primary-table", 
            columns=["#1", "#2", "#3"],
            selectmode=tk.EXTENDED)
        self.treeview.grid(row=1, column=0, sticky=tk.NSEW)

        # Configure columns
        self.treeview.column('#0', anchor=tk.W, width=utils.scale_size(self, 100), stretch=tk.NO)
        self.treeview.column('#1', anchor=tk.W, width=utils.scale_size(self, 150), stretch=tk.NO)
        self.treeview.column('#2', anchor=tk.W, width=utils.scale_size(self, 1000), stretch=tk.YES)

        # Configure heading
        self.treeview.heading('#0', text='Severity', anchor=tk.W)
        self.treeview.heading('#1', text='Time', anchor=tk.W)
        self.treeview.heading('#2', text='Message', anchor=tk.W)
        self.treeview.bind("<Double-1>", self.on_double_click)
        self.detached = set()

        # Create and attach scrollbar to treeview
        self.sb_y = ttk.Scrollbar(
            self, orient=tk.VERTICAL, 
            command=self.treeview.yview)
        self.sb_y.grid(row=1, column=1, sticky=tk.NS)
        self.treeview.configure(yscrollcommand=self.sb_y.set)

        # Configure grid rows and columns
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Create a logging handler using a queue
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        formatter = logging.Formatter("%(asctime)s: %(levelname)s - %(message)s")
        self.queue_handler.setFormatter(formatter)
        logger.instance.addHandler(self.queue_handler)

        # Start polling messages from the queue
        self.after(self.timeout, self.poll_log_queue)
    
    def on_clear_filter(self):
        """Clear the current filter text and refresh the display."""
        self.entry_filter.delete(0, tk.END)
        self.on_filter()

    def on_filter(self):
        """Filter log entries by severity, time, or message text."""
        find_str = str(self.entry_filter.get())
        # Create search list
        children = list(self.detached) + list(self.treeview.get_children())
        # Create new detached set
        self.detached = set()

        iid = -1
        for item_id in children:
            # Get the row string
            text = self.treeview.item(item_id)["text"]
            values = self.treeview.item(item_id)["values"]
            if find_str in values[0] or find_str in values[1] or find_str in text:
                # Show entry if search string matches
                iid += 1
                self.treeview.reattach(item_id, "", iid)
            else:
                # Detach entry if search string does not match
                self.detached.add(item_id)
                self.treeview.detach(item_id)        

    def on_double_click(self, event):
        """Show a message box with details for the selected log entry."""
        item = self.treeview.identify("item", event.x, event.y)
        if item != "":
            text = self.treeview.item(item, "text")
            values = self.treeview.item(item, "values")
            msg = "{}\n\n{}".format(values[0], values[1])
            if values[1].startswith("Traceback"):
                msg = msg.replace(";", "\n")

            # Show messagebox
            if text == "CRITICAL":
                messagebox.showerror(title=text, message=msg)
            elif text == "ERROR":
                messagebox.showerror(title=text, message=msg)
            elif text == "WARNING":
                messagebox.showwarning(title=text, message=msg)
            elif text == "INFO":
                messagebox.showinfo(title=text, message=msg)
            elif text == "DEBUG":
                messagebox.showinfo(title=text, message=msg)
 
    def append(self, record):
        """Append a logging record to the tree view."""
        self.treeview.insert(
            parent='',
            index=tk.END,
            image=self.images[record.levelname],
            text=record.levelname,
            values=(record.asctime, record.message),
        )

        self.treeview.yview_moveto(1)

    def poll_log_queue(self):
        """Poll the logging queue and display any new records."""
        while True:
            try:
                record = self.log_queue.get(block=False)
            except queue.Empty:
                break
            else:
                self.append(record)
        self.after(self.timeout, self.poll_log_queue)

if __name__ == "__main__":
    # Prepare logging
    logger.prepare_logging("log.conf")
    logger.instance = logging.getLogger("Test")
    
    # Create app window
    app = ttk.Window()

    log = Loglist(app)
    log.pack(fill=tk.BOTH, expand=tk.YES)
    
    logger.warning("Test is not implemented!")
    logger.info("Test is implemented!")
    logger.error("Test is corrupt!")

    app.mainloop() 
