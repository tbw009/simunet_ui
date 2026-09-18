"""Dialog for choosing one or more process variables from modeled objects."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
import pint
from ttkbootstrap.dialogs import Dialog
from tkinter import messagebox


class QuantityEditorDialog(Dialog):
    """Dialog for converting physical quantities."""

    def __init__(self, parent=None, value=None, title="Convert quantity"):
        """Initialize the variable chooser dialog.

        Args:
            parent: Parent widget for the dialog.
            value: Initial value for the quantity.
            title: Dialog title.
       """
        super().__init__(parent=parent, title=title)
        self._unit_registry = pint.UnitRegistry()
        self._unit_registry.formatter.default_format = "~P"

        self.quantity = value

        
    def create_body(self, master):
        """Create the main body of the dialog."""
        
        container = ttk.Frame(master, padding=(5,5))
        container.pack(fill=tk.BOTH, expand=tk.YES, anchor=tk.N)

        # From Unit label frame
        from_frame = ttk.Labelframe(container, text="From unit", padding=(5, 10))
        from_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        # Insert labels
        lbl_from_value = ttk.Label(master=from_frame, text="Value")
        lbl_from_value.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        lbl_from_unit = ttk.Label(master=from_frame, text="Unit")
        lbl_from_unit.grid(row=1, column=0, sticky=tk.NSEW, padx=5)

        # Insert entries
        self.entry_from_value = ttk.Entry(master=from_frame)
        self.entry_from_value.insert(tk.END, self.quantity[0])
        self.entry_from_value.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=2)
        self.entry_from_value.bind("<Return>", lambda e: self.on_convert())

        self.entry_from_unit = ttk.Entry(master=from_frame)
        self.entry_from_unit.insert(tk.END, self.quantity[1])
        self.entry_from_unit.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=2)
        self.entry_from_unit.bind("<Return>", lambda e: self.on_convert())

        # To Unit label frame
        to_frame = ttk.Labelframe(container, text="To unit", padding=(5, 10))
        to_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=5)

        # Insert labels
        lbl_to_value = ttk.Label(master=to_frame, text="Value")
        lbl_to_value.grid(row=0, column=0, sticky=tk.NSEW, padx=5)

        lbl_to_unit = ttk.Label(master=to_frame, text="Unit")
        lbl_to_unit.grid(row=1, column=0, sticky=tk.NSEW, padx=5)

        # Insert entries
        self.entry_to_value = ttk.Entry(bootstyle=tk.LIGHT, master=to_frame)
        self.entry_to_value.insert(tk.END, self.quantity[0])
        self.entry_to_value.config(state=tk.READONLY)
        self.entry_to_value.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=2)
        self.entry_to_value.bind("<Return>", lambda e: self.on_convert())

        self.entry_to_unit = ttk.Entry(master=to_frame)
        self.entry_to_unit.insert(tk.END, self.quantity[1])
        self.entry_to_unit.grid(row=1, column=1, sticky=tk.NSEW, padx=5, pady=2)
        self.entry_to_unit.bind("<Return>", lambda e: self.on_convert())

        self._toplevel.wm_attributes("-toolwindow", "true")

    def on_convert(self):
        try:
            from_value = float(self.entry_from_value.get())
            from_unit = self.entry_from_unit.get()
            to_unit = self.entry_to_unit.get()
            to_value = self._unit_registry.convert(from_value, from_unit, to_unit)
            self.entry_to_value.config(state=tk.NORMAL)
            self.entry_to_value.delete(0, tk.END)
            self.entry_to_value.insert(tk.END, to_value)
            self.entry_to_value.config(state=tk.READONLY)
        except Exception as e:
            messagebox.showerror(title="Conversion Error", message=str(e))

    def create_buttonbox(self, master):
        """Create the OK and Cancel buttons for the dialog."""
        container = ttk.Frame(master, padding=(5, 10))
        container.pack(fill=tk.X)

        # OK button
        btn_ok = ttk.Button(
            container, 
            bootstyle=tk.PRIMARY, 
            takefocus=False, 
            width=6, 
            text="OK")
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
            self.quantity = [float(self.entry_to_value.get()), self.entry_to_unit.get()]

        # Close window
        self.close()

if __name__ == "__main__":
    
    dlg = QuantityEditorDialog(
        None, 
        value=(3.1, "kg"),
        )
    dlg.show()
    print(dlg.result)
    print(dlg.quantity)
