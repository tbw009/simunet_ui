"""Dialog wrapper for color selection using ttkbootstrap.

This module defines `ColorChooserDialog`, which displays a color chooser
widget inside a reusable dialog window.
"""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.dialogs import Dialog
from ttkbootstrap.dialogs.colorchooser import ColorChooser


class ColorChooserDialog(Dialog):
    """Dialog for choosing colors with OK and Cancel actions."""

    def __init__(self, parent=None, title="Color Chooser", initialcolor=None):
        """Initialize the color chooser dialog.

        Args:
            parent: Optional parent widget.
            title: Title of the dialog window.
            initialcolor: Initial selected color value.
        """
        super().__init__(parent=parent, title=title)
        self.color = initialcolor

    def create_body(self, master):
        """Create the main color chooser body.

        Args:
            master: Parent widget for the dialog body.
        """
        self.colorchooser = ColorChooser(master, self.color)
        self.colorchooser.pack(fill=tk.BOTH, expand=tk.YES)

        # Set tool window
        self._toplevel.wm_attributes("-toolwindow", "true")

    def create_buttonbox(self, master):
        """Create the OK/Cancel button row for the dialog."""
        container = ttk.Frame(master, padding=(5, 10))
        container.pack(side=tk.BOTTOM, fill=tk.X, anchor=tk.S)

        # OK button
        btn_ok = ttk.Button(
            container,
            bootstyle=tk.PRIMARY,
            takefocus=False,
            width=6,
            text="OK",
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
            text="Cancel",
        )
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
            values = self.colorchooser.get_variables()
            self.color = values.hex

        # Close window
        self.close()

if __name__ == "__main__":
    dlg = ColorChooserDialog()
    dlg.show()

    print(dlg.result)
    print(dlg.color)
