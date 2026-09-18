"""Property descriptor widget for displaying name and description."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk


class PropertyDescriptor(ttk.Frame):
    """Widget displaying a property name and descriptive text."""

    def __init__(self, master, **kwargs):
        """Initialize the property descriptor control."""
        super().__init__(master, **kwargs)
 
        # Add property name
        self.name = ttk.Label(self, bootstyle=tk.PRIMARY)
        self.name.pack(side=tk.TOP, anchor=tk.W, fill=tk.X, padx=3)
        
        # Add property description frame
        container = ttk.Frame(self)
        container.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=tk.YES)

        # Add scrollbar for description
        self.sb_y = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.on_scroll_y)
        self.sb_y.grid(row=0, column=1, sticky=tk.NS)

        # Add the property description
        self.txt_description = ttk.Text(container, bd=-1, wrap=tk.WORD, height=2, yscrollcommand=self.sb_y.set)
        self.txt_description.grid(row=0, column=0, sticky=tk.NSEW)
        self.txt_description.configure(state=tk.DISABLED)

        # Configure grid rows and columns
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

    def on_scroll_y(self, event, *args):
        """Scroll the description text vertically in response to scrollbar events."""
        if event == 'moveto':
            self.txt_description.yview_moveto(*args)
        else:
            self.txt_description.yview_scroll(*args)

 
    def set(self, name, description):
        """Update the displayed property name and description text."""
        self.name.config(text=name)

        self.txt_description.configure(state=tk.NORMAL)
        self.txt_description.delete(1.0, tk.END)
        self.txt_description.insert(tk.END, description + '\n')
        self.txt_description.configure(state=tk.DISABLED)

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    desc = PropertyDescriptor(app)
    desc.set("Propertyname", "This is\na description\nfor the\nproperty...")
    desc.pack(fill=tk.BOTH, expand=tk.YES)

    app.mainloop()
