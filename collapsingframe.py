"""Collapsible frame widget for grouping expandable UI sections.

This module defines `CollapsingFrame`, a scrollable container that can
add child frames as expandable/collapsible sections with header buttons.
"""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk

from images import Images


class CollapsingFrame(ttk.ScrolledFrame):
    """A collapsible section frame widget."""

    def __init__(self, master, buttonside=tk.LEFT, **kwargs):
        """Create a new collapsing frame container."""

        super().__init__(master, **kwargs)

        self._cumulative_rows = 0
        self._buttonside = buttonside
        self.columnconfigure(0, weight=1)

    def add(self, child, title="", bootstyle="@primary"):
        """Add a child frame as a collapsible section.

        Args:
            child (Frame): The child frame to add to the widget.
            title (str): Section header text.
            bootstyle (str): Style for the header.
        """
        # Currently only frames are accepted as children
        if child.winfo_class() != "TFrame":
            return

        # Create the header frame
        container = ttk.Frame(self)
        container.grid(row=self._cumulative_rows, column=0, sticky=tk.EW)
        container.bind("<ButtonRelease-1>", lambda e: self._toggle_open_close(child))

        # Create header label
        header = ttk.Label(
            master=container,
            text=title,
            bootstyle=bootstyle
        )
        header.bind("<Button-1>", lambda e: self._toggle_open_close(child))
                    
        # Create toggle button
        btn = ttk.Label(
            master=container,
            image=Images().system["Expanded"], 
            bootstyle=bootstyle,
            padding=5
        )
        btn.bind("<Button-1>", lambda e: self._toggle_open_close(child))

        # Pack header label and toggle button in the desired order
        if self._buttonside == tk.LEFT:
            btn.pack(side=tk.LEFT)
            header.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH, padx=0)
        else:
            header.pack(side=tk.LEFT, expand=tk.YES, fill=tk.BOTH, padx=(2,0))
            btn.pack(side=tk.RIGHT)

        # Assign toggle button to child so that it can be toggled
        child.btn = btn
        child.header = header
        child.container = container
        child.expanded = True
        child.grid(row=self._cumulative_rows + 1, column=0, sticky=tk.NSEW)
        
        # Increment the row assignment
        self._cumulative_rows += 2

    def remove(self, child):
        """Remove a section and its header from the frame.

        Args:
            child (Frame): The child element to remove.
        """
        if child in self.winfo_children():
            child.container.destroy()
            child.destroy()


    def collapse(self, child):
        """Collapse a section and update its toggle button icon.

        Args:
            child (Frame): The child element to collapse.
        """
        if child.winfo_viewable():
            child.grid_remove()
            child.btn.configure(image=Images().system["Collapsed"])
            child.expanded = False

    def expand(self, child):
        """Expand a section and update its toggle button icon.

        Args:
            child (Frame): The child element to expand.
        """
        if not child.winfo_viewable():
            child.grid()
            child.btn.configure(image=Images().system["Expanded"])
            child.expanded = True
        
    def _toggle_open_close(self, child):
        """Toggle the open/closed state of a section.

        Args:
            child (Frame): The child element to toggle.
        """
        if child.winfo_viewable():
            self.collapse(child)
        else:
            self.expand(child)

    def show(self, child):
        """Show a section header and expand its child frame.

        Args:
            child (Frame): The child element to show.
        """
        if not child.container.winfo_viewable():
            child.container.grid()
            self.expand(child)

    def hide(self, child):
        """Hide a section header and collapse its child frame.

        Args:
            child (Frame): The child element to hide.
        """
        if child.container.winfo_viewable():
            self.collapse(child)
            child.container.grid_remove()


    def clear(self):
        """Destroy all child sections and headers."""

        for item in self.winfo_children():
            item.destroy()


if __name__ == "__main__":
    # Create app window
    app = ttk.Window()
 
    cf = CollapsingFrame(app, buttonside=tk.RIGHT, padding=0)
    cf.pack(fill=tk.BOTH, expand=tk.YES)

    # Option group 1
    group1 = ttk.Frame(cf, padding=5)
    for x in range(5):
        ttk.Checkbutton(group1, text="Option {}".format(x+1)).pack(fill=tk.X)
    cf.add(child=group1, title="Option Group 1")

    # Option group 2
    group2 = ttk.Frame(cf, padding=5)
    for x in range(5):
        ttk.Checkbutton(group2, text="Option {}".format(x+1)).pack(fill=tk.X)
    cf.add(group2, title="Option Group 2", bootstyle="@danger")

    # Option group 3
    group3 = ttk.Frame(cf, padding=5)
    for x in range(5):
        ttk.Checkbutton(group3, text="Option {}".format(x+1)).pack(fill=tk.X)
    cf.add(group3, title="Option Group 3", bootstyle="@success")

    app.mainloop()