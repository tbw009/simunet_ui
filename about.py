"""About dialog for simunet GUI.

This module provides the `AboutDlg` dialog used by the application to
display application information, license text and links. 
"""

import os
import pathlib
from datetime import datetime

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.dialogs import Dialog
from PIL import ImageTk, Image

from simunetcore import __version__ as COREVERSION


# Hyperlink URLs used by the about dialog
URLS = {
    "simunet": "https://simunet.org",
    "help": "https://simunet.org/help",
    "support": "https://simunet.org/support",
    "getting_started": "https://simunet.org/getting-started",
}

# Company and frontend version
COMPANY = "Fraunhofer UMSICHT"
VERSION = "0.2.0"


class AboutDlg(Dialog):
    """About dialog window.

    Presents application logo, copyright and license text in a
    scrollable text widget.
    """

    def __init__(self, parent=None):
        """Initialize the dialog.

        Args:
            parent: Parent widget for the dialog (optional).
        """
        super().__init__(parent=parent, title="About simunet®")

    def create_body(self, master):
        """Create the main body of the about dialog.

        Builds and packs the logo, copyright label, separator, license
        text widget and scrollbar.
        """
        # Container frame for logo and copyright
        container = ttk.Frame(master)
        container.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)

        # Logo image (clickable)
        src = Image.open("./images/logo.png")
        self.app_img = ImageTk.PhotoImage(src.resize((264, 66), Image.Resampling.LANCZOS))
        lbl_logo = ttk.Label(container, cursor="hand2", image=self.app_img, anchor=tk.W)
        lbl_logo.pack(side=tk.LEFT, padx=(15, 5), pady=15)
        lbl_logo.bind("<Button-1>", self.on_logo_click)

        # Copyright and version information
        cr_text = (
            "simunet®\nCopyright© {} by {}\nFrontend: {}\nCore: {}"
        ).format(datetime.now().year, COMPANY, VERSION, COREVERSION)

        lbl_copyright = ttk.Label(container, text=cr_text)
        lbl_copyright.pack(side=tk.LEFT, padx=(5, 15), pady=15)

        # Horizontal separator
        sep = ttk.Separator(master, orient=tk.HORIZONTAL)
        sep.pack(side=tk.TOP, fill=tk.X)

        # License text frame (scrollable)
        self.license_frame = ttk.Frame(master)
        self.license_frame.pack(pady=(0, 0), fill=tk.BOTH, expand=True)

        # License text widget
        self.txt_license = ttk.Text(self.license_frame, wrap=tk.WORD, width=80, height=10)
        self.txt_license.pack(
            side=tk.LEFT,
            padx=(15, 0),
            pady=(15, 0),
            ipadx=10,
            ipady=10,
            fill=tk.BOTH,
            expand=tk.YES,
        )
        license = pathlib.Path("license.txt").read_text()
        self.txt_license.insert(tk.END, license)

        # Vertical scrollbar for license text
        self.sb_y = ttk.Scrollbar(self.license_frame, orient=tk.VERTICAL, command=self.txt_license.yview)
        self.sb_y.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 15), pady=(15, 0))

        # Attach scrollbar and disable editing
        self.txt_license.config(yscrollcommand=self.sb_y.set)
        self.txt_license.configure(state=tk.DISABLED)

        # Set window style to tool window
        self._toplevel.wm_attributes("-toolwindow", "true")

    def on_logo_click(self, event):
        """Open the project website when the logo is clicked.

        Args:
            event: Tk event (click) passed by the binding.
        """
        os.startfile(URLS["simunet"])

    def create_buttonbox(self, master):
        """Create the dialog's button box (OK button).

        The OK button closes the dialog; it also responds to Return.
        """
        container = ttk.Frame(master, padding=(5, 10))
        container.pack(side=tk.BOTTOM, fill=tk.X, anchor=tk.S)

        # OK button
        btn_ok = ttk.Button(
            container, 
            bootstyle=tk.PRIMARY, 
            takefocus=False, 
            width=6, 
            text="OK"
        )
        btn_ok.bind("<Return>", lambda _: btn_ok.invoke())
        btn_ok.configure(command=lambda b=btn_ok: self.on_button_press(b))
        btn_ok.pack(padx=5, side=tk.RIGHT)

    def on_button_press(self, button):
        """Handle button presses and persist values on OK."""

        self._result = button.cget("text")
        # Close window
        self.close()

if __name__ == "__main__":
    dlg = AboutDlg(None)
    dlg.show()
    print(dlg.result)
