"""Tooltip widget helper for delayed hover text display."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.window import Toplevel


class Tooltip:
    """Manage hover tooltips for widgets."""
    
    def __init__(
            self, widget, text, padx=5, pady=3, 
            waittime=600, wraplength=250):
        """Initialize a tooltip for a given widget.

        Args:
            widget: Widget to attach the tooltip to.
            text: Tooltip text.
            padx: Horizontal padding inside the tooltip.
            pady: Vertical padding inside the tooltip.
            waittime: Delay before showing the tooltip, in milliseconds.
            wraplength: Maximum tooltip text width in pixels.
        """

        self.waittime = waittime  # in miliseconds
        self.wraplength = wraplength  # in pixels
        self.widget = widget
        self.text = text
        self.padx = padx
        self.pady = pady
        self.id = None
        self.toplevel = None

        # Bind events
        self.widget.bind("<Enter>", self.on_enter, add=True)
        self.widget.bind("<Leave>", self.on_leave, add=True)
        self.widget.bind("<ButtonPress>", self.on_leave, add=True)
 
    def on_enter(self, event):
        """Schedule the tooltip to appear when the mouse enters."""
        self.schedule()

    def on_leave(self, event):
        """Hide the tooltip and cancel any pending show event."""
        self.unschedule()
        self.hide()

    def schedule(self):
        """Schedule the tooltip display after the waiting period."""
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.show)

    def unschedule(self):
        """Cancel a pending tooltip display if one is scheduled."""
        if self.id:
            id = self.id
            self.id = None
            self.widget.after_cancel(id)

    def show(self):
        """Create and display the tooltip window."""
        self.toplevel = Toplevel(self.widget)
        
        # Leaves only the label and removes the app window
        self.toplevel.wm_overrideredirect(True)

        # Create and pack tooltip frame
        container = ttk.Frame(self.toplevel, bootstyle=tk.DARK)
        container.pack(fill = tk.BOTH)

         # Create and pack label
        label = ttk.Label(           
            container, 
            text=self.text, 
            justify=tk.LEFT, 
            wraplength=self.wraplength,
            padding = (self.padx, self.pady))
        label.pack(fill = tk.BOTH, padx=1, pady=1) 
 
        # Set geometry
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height()
        self.toplevel.wm_geometry("+%d+%d" % (x, y))

    def hide(self):
        """Destroy the tooltip window if it is visible."""
        if self.toplevel:
            self.toplevel.destroy()
        self.toplevel = None


if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    btn = ttk.Button(app, text="Testwidget")
    btn.pack()
    Tooltip(btn, text="Tooltip for Testwidget")

    app.mainloop()