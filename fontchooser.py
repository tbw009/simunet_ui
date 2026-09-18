"""Font chooser dialog for selecting font family, size, and style."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.dialogs import Dialog
from tkinter import font


class FontChooserDialog(Dialog):

    """A dialog that displays a variety of options for choosing a font.

    This dialog constructs and returns a `Font` object based on the
    options selected by the user. The initial font is based on OS
    settings and will vary.

    The font object is returned when the **Ok** button is pressed and
    can be passed to any widget that accepts a _font_ configuration
    option.

    """

    def __init__(self, parent=None, initialfont=None, title="Font Selector"):
        """Initialize the font chooser dialog and bind preview updates."""
        super().__init__(parent=parent, title=title)

        self._default = font.nametofont("TkDefaultFont")
        self._actual = initialfont.actual() if initialfont is not None else self._default.actual()
        self._size = ttk.Variable(value=self._actual["size"])
        self._family = ttk.Variable(value=self._actual["family"])
        self._slant = ttk.Variable(value=self._actual["slant"])
        self._weight = ttk.Variable(value=self._actual["weight"])
        self._overstrike = ttk.Variable(value=self._actual["overstrike"])
        self._underline = ttk.Variable(value=self._actual["underline"])
        self._slant.trace_add("write", self._update_font_preview)
        self._weight.trace_add("write", self._update_font_preview)
        self._overstrike.trace_add("write", self._update_font_preview)
        self._underline.trace_add("write", self._update_font_preview)

        self.font = font.Font()

        self._update_font_preview()
        #self._families = set([self._family.get()])
        self._families =[]
        for f in font.families():
            if all([f, not f.startswith("@"), "emoji" not in f.lower()]):
                self._families.append(f)
        self._families.sort()

    def create_body(self, master):
        """Create the body of the font chooser dialog."""
 
        family_size_frame = ttk.Frame(master, padding=(10,0))
        family_size_frame.pack(fill=tk.X, anchor=tk.N)
        self._initial_focus = self._font_families_selector(family_size_frame)
        self._font_size_selector(family_size_frame)
        self._font_options_selectors(master, padding=10)

        self._toplevel.wm_attributes("-toolwindow", "true")

    def create_buttonbox(self, master):
        """Create the dialog action buttons for OK and Cancel."""
        container = ttk.Frame(master, padding=(5, 5, 5, 10))
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

        # Close window
        self.close()

    def _font_families_selector(self, master):
        """Create the font family selection list."""
        container = ttk.Frame(master)
        container.pack(fill=tk.BOTH, expand=tk.YES, side=tk.LEFT)

        header = ttk.Label(
            container,
            text="Family",
            font="TkHeadingFont",
        )
        header.pack(fill=tk.X, pady=(0, 2), anchor=tk.N)

        listbox = ttk.Treeview(
            master=container,
            height=5,
            show="",
            columns=[0],
        )
        listbox.column(0, width=250)
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)

        listbox_vbar = ttk.Scrollbar(
            container,
            command=listbox.yview,
            orient=tk.VERTICAL
        )
        listbox_vbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox.configure(yscrollcommand=listbox_vbar.set)

        size = self._default.actual()["size"]
        for f in self._families:
            listbox.insert("", iid=f, index=tk.END, tags=[f], values=[f])
            listbox.tag_configure(f, font=(f, size))

        iid = self._family.get()
        listbox.selection_set(iid)  # select default value
        listbox.see(iid)  # ensure default is visible
        listbox.bind(
            "<<TreeviewSelect>>", lambda e: self._on_select_font_family(e)
        )
        return listbox

    def _font_size_selector(self, master):
        """Create the font size selection control."""
        container = ttk.Frame(master)
        container.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 0))

        header = ttk.Label(
            container,
            text="Size",
            font="TkHeadingFont",
        )
        header.pack(fill=tk.X, pady=(0, 2), anchor=tk.N)

        sizes_listbox = ttk.Treeview(container, height=7, columns=[0], show="")
        sizes_listbox.column(0, width=36)

        sizes = [*range(8, 13), *range(13, 30, 2), 36, 48, 72]
        for s in sizes:
            sizes_listbox.insert("", iid=s, index=tk.END, values=[s])

        iid = self._size.get()
        sizes_listbox.selection_set(iid)
        sizes_listbox.see(iid)
        sizes_listbox.bind(
            "<<TreeviewSelect>>", lambda e: self._on_select_font_size(e)
        )

        sizes_listbox_vbar = ttk.Scrollbar(
            master=container,
            orient=tk.VERTICAL,
            command=sizes_listbox.yview
        )
        sizes_listbox.configure(yscrollcommand=sizes_listbox_vbar.set)
        sizes_listbox.pack(side=tk.LEFT, fill=tk.Y, expand=tk.YES, anchor=tk.N)
        sizes_listbox_vbar.pack(side=tk.LEFT, fill=tk.Y, expand=tk.YES)

    def _font_options_selectors(self, master, padding: int):
        """Create radio buttons and checkboxes for font style options."""
        container = ttk.Frame(master, padding=padding)
        container.pack(fill=tk.X, padx=2, pady=2, anchor=tk.N)

        weight_lframe = ttk.Labelframe(
            container, text="Weight", padding=5
        )
        weight_lframe.pack(side=tk.LEFT, fill=tk.X, expand=tk.YES)
        opt_normal = ttk.Radiobutton(
            master=weight_lframe,
            text="normal",
            value="normal",
            variable=self._weight,
        )
        opt_normal.invoke()
        opt_normal.pack(side=tk.LEFT, padx=5, pady=5)
        opt_bold = ttk.Radiobutton(
            master=weight_lframe,
            text="bold",
            value="bold",
            variable=self._weight,
        )
        opt_bold.pack(side=tk.LEFT, padx=5, pady=5)

        slant_lframe = ttk.Labelframe(
            container, text="Slant", padding=5
        )
        slant_lframe.pack(side=tk.LEFT, fill=tk.X, padx=10, expand=tk.YES)
        opt_roman = ttk.Radiobutton(
            master=slant_lframe,
            text="roman",
            value="roman",
            variable=self._slant,
        )
        opt_roman.invoke()
        opt_roman.pack(side=tk.LEFT, padx=5, pady=5)
        opt_italic = ttk.Radiobutton(
            master=slant_lframe,
            text="italic",
            value="italic",
            variable=self._slant,
        )
        opt_italic.pack(side=tk.LEFT, padx=5, pady=5)

        effects_lframe = ttk.Labelframe(
            container, text="Effects", padding=5
        )
        effects_lframe.pack(side=tk.LEFT, padx=(2, 0), fill=tk.X, expand=tk.YES)
        opt_underline = ttk.Checkbutton(
            master=effects_lframe,
            text="underline",
            variable=self._underline,
        )
        opt_underline.pack(side=tk.LEFT, padx=5, pady=5)
        opt_overstrike = ttk.Checkbutton(
            master=effects_lframe,
            text="overstrike",
            variable=self._overstrike,
        )
        opt_overstrike.pack(side=tk.LEFT, padx=5, pady=5)

    def _on_select_font_family(self, e):
        """Handle selection changes in the font family list."""
        tree: ttk.Treeview = self._toplevel.nametowidget(e.widget)
        fontfamily = tree.selection()[0]
        self._family.set(value=fontfamily)
        self._update_font_preview()

    def _on_select_font_size(self, e):
        """Handle selection changes in the font size list."""
        tree: ttk.Treeview = self._toplevel.nametowidget(e.widget)
        fontsize = tree.selection()[0]
        self._size.set(value=fontsize)
        self._update_font_preview()

    def _update_font_preview(self, *_):
        """Update the preview font object when selection changes."""
        family = self._family.get()
        size = self._size.get()
        weight = self._weight.get()
        slant = self._slant.get()
        overstrike = self._overstrike.get()
        underline = self._underline.get()

        self.font.config(
            family=family,
            size=size,
            weight=weight,
            slant=slant,
            overstrike=overstrike,
            underline=underline,
        )
     

if __name__ == "__main__":
    dlg = FontChooserDialog()
    dlg.show()

    print(dlg.result)
    print(dlg.font.actual())
