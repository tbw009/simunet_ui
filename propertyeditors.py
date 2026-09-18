"""Property editors for the simulation UI.

This module contains editor widgets used by the property grid to edit
 various types of values, such as floats, ints, booleans, colors, dates, files,
 variables, and table data.
"""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.dialogs import DatePickerDialog
from ttkbootstrap import utils
from fontchooser import FontChooserDialog
from colorchooser import ColorChooserDialog
from varchooser import VarChooserDialog
from codeeditor import CodeEditorDialog
from tableeditor import TableEditorDialog
from tkinter import filedialog
from datetime import datetime
from images import Images
from functools import partial
import pint
import re
import copy
import numpy as np
from simunetcore import logger

ureg = pint.UnitRegistry()
ureg.formatter.default_format = "~P"


def create_value_editor(editor, master, value, options):
    """Create an appropriate editor widget for a property type.

    Args:
        editor: Editor type name.
        master: Parent widget.
        value: Initial editor value.
        options: Additional editor options.

    Returns:
        Instance of a value editor widget.
    """
    if editor=="float":
        value_editor = FloatEntry(master, value, options)
    elif editor=="int":
        value_editor = IntEntry(master, value, options)
    elif editor=="bool":
        value_editor = BoolEntry(master, value)
    elif editor=="bool_combo":
        value_editor = BoolComboEntry(master, value)
    elif editor=="password":
        value_editor = PasswordEntry(master, value)
    elif editor == "combo":
        value_editor = ComboboxEntry(master, value, options)
    elif editor == "spinbox":
        value_editor = SpinboxEntry(master, value, options)
    elif editor == "option":
        value_editor = OptionsEntry(master, value, options)
    elif editor == "custom":
        value_editor = CustomEntry(master, value, options)
    elif editor == "color":
        value_editor = ColorPopupEntry(master, value, options)
    elif editor == "color_str":
        value_editor = ColorEntry(master, value, options)
    elif editor == "color_map":
        value_editor = ColorMapEntry(master, value, options)
    elif editor == "font":
        value_editor = FontPopupEntry(master, value, options)
    elif editor == "single_var":
        value_editor = VarPopupEntry(master, value, options, selectmode=tk.BROWSE)
    elif editor == "multi_var":
        value_editor = VarPopupEntry(master, value, options)
    elif editor == "dir":
        value_editor = DirectoryPopupEntry(master, value, options)
    elif editor == "file":
        value_editor = FilePopupEntry(master, value, options)
    elif editor == "date":
        value_editor = DatePopupEntry(master, value, options)
    elif editor == "date_str":
        value_editor = DateEntry(master, value, options)
    elif editor == "range":
        value_editor = RangeEntry(master, value, options)
    elif editor == "quantity":
        value_editor = QuantityEntry(master, value, options)
    elif editor == "code":
        value_editor = CodeEditorEntry(master, value, options)
    elif editor == "table":
        value_editor = TableEditorEntry(master, value, options)
    elif editor == "slider":
        value_editor = SliderEntry(master, value, options)
    else:
        value_editor = StrEntry(master, value, options)
    return value_editor

class ValueEntry(ttk.Entry):
    """Base editor for typed entry fields with validation."""

    def __init__(self, master, value, cast, options=None):
        """Initialize a typed entry widget.

        Args:
            master: Parent widget.
            value: Initial text value.
            cast: Callable to cast the string value.
            options: Validation options such as min and max.
        """
        super().__init__(master, validate="focusout")

        self.cast = cast
        self.popup = None
        self.insert(tk.END, value)
        if options:
            if "min" in options:
                self.min = options["min"]

            if "max" in options:
                self.max = options["max"]
        
    def get_value(self):
        """Return the current value cast to the configured type."""
        return self.cast(self.get())

    def on_validate(self, value):
        """Validate the text value against optional min/max constraints."""
        try :
            value = self.cast(value)
            if "min" in self.__dict__:
                if value < self.min:
                    msg = "Validation failed, value must be greater than {}.".format(self.min)
                    logger.error(msg)
                    return False
            if "max" in self.__dict__:
                if value > self.max:
                    msg = "Validation failed, value must be lower than {}.".format(self.max)
                    logger.error(msg)
                    return False
            return True
        except:
            msg = "Validation failed, value must be an {}}.".format(self.cast)
            logger.error(msg)
            return False

class FloatEntry(ValueEntry):
    """Entry widget for editing floating point values."""

    def __init__(self, master, value, options=None):
        super().__init__(master, value, float, options)

class IntEntry(ValueEntry):
    """Entry widget for editing integer values."""

    def __init__(self, master, value, options=None):
        super().__init__(master, value, int, options)
    
class SpinboxEntry(ttk.Spinbox):
    """Spinbox editor for numeric range input."""

    def __init__(self, master, value, options):
        """Initialize a spinbox with the given range options."""
        super().__init__(master, **options, validate="focusout")
        self.options = options
        self.popup = None
        self.set(value)

    def get_value(self):
        """Return the spinbox value as an integer."""
        return int(self.get())
    
    def on_validate(self, value):
        try :
            if "from_" in self.options and "to" in self.options:
                min = self.options["from_"] 
                max = self.options["to"] 
                if value < min or value > max:
                    msg = "Validation failed, value must be between {} and {}.".format(min, max)
                    logger.error(msg)
                    return False
            return True
        except:
            msg = "Validation failed."
            logger.error(msg)
            return False

class BoolEntry(ttk.Checkbutton):
    """Checkbox editor for boolean values."""

    def __init__(self, master, value, options="round-toggle"):
        super().__init__(master, bootstyle=options, command=self.switch)
        self.popup = None
        self.config(text=str(value))
        if value: 
            self.state(['selected']) 
        else: 
            self.state(['!selected'])

    def on_validate(self, value):
        """Boolean editor always accepts its current state."""
        return True
    
    def switch(self):
        self.config(text=str(self.instate(['selected'])))
    
    def get_value(self):
        return(self.instate(['selected']))

class BoolComboEntry(ttk.Combobox):
    """Read-only combobox editor for boolean selection."""

    def __init__(self, master, value, options=None):
        options=[True, False]
        super().__init__(master, values=options, state=tk.READONLY)
        self.popup = None
        self.current(options.index(value))

    def on_validate(self, value):
        return True

    def get_value(self):
        return True if self.get()==str(True) else False
    
class ComboboxEntry(ttk.Combobox):
    """Combobox editor for selecting from a list of values."""

    def __init__(self, master, value, options):
        super().__init__(master, values=options)
        self.popup = None
        self.insert(tk.END, value)
        
    def on_validate(self, value):
        return True

    def get_value(self):
        return self.get()

class OptionsEntry(ttk.Combobox):
    """Read-only combobox editor for option selection."""

    def __init__(self, master, value, options):
        super().__init__(master, values=options, state=tk.READONLY)
        self.popup = None
        self.current(options.index(value))

    def on_validate(self, value):
        return True

    def get_value(self):
        return self.get()

class RangeEntry(ttk.Frame):
    """Editor for a numeric range with lower and upper bounds."""

    def __init__(self, master, value, options=None):
        super().__init__(master)
        self.popup = None

        self.lower_val = FloatEntry(self, value[0])
        self.lower_val.grid(row=0, column=0, sticky=tk.NSEW)
        self.upper_val = FloatEntry(self, value[1])
        self.upper_val.grid(row=1, column=0, sticky=tk.NSEW)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

    def on_validate(self, value):
        return True

    def get_value(self):
        return [
            self.lower_val.get_value(),
            self.upper_val.get_value()
        ]

class QuantityEntry(ttk.Frame):
    """Editor for quantity values with magnitude and unit."""

    def __init__(self, master, value, options=None):
        super().__init__(master)
        self.popup = None
        self.dest_unit = options
        self.magnitude = FloatEntry(self, value[0])
        self.magnitude.grid(row=0, column=0, sticky=tk.NSEW)

        self.unit = StrEntry(self, value[1])
        self.unit.grid(row=0, column=1, sticky=tk.NSEW)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.magnitude.focus()

    def on_validate(self, value):
        """Validate that the entered unit is compatible with the destination unit."""
        if ureg.is_compatible_with(value[1], self.dest_unit):
            return True
        else:
            raise ValueError("Unit {} is not compatible with destination unit {}".format(value[1], self.dest_unit))

    def get_value(self):
        src_unit = self.unit.get_value()
        value = self.magnitude.get_value()
        if src_unit != self.dest_unit:
            value = ureg.convert(value, src_unit, self.dest_unit)
        return [value, self.dest_unit]
   
class StrEntry(ttk.Entry):
    """Simple text entry editor."""

    def __init__(self, master, value, options=None):
        super().__init__(master)
        self.popup = None
        self.insert(tk.END, value)
        
    def on_validate(self, value):
        return True

    def get_value(self):
        return self.get()

class PasswordEntry(StrEntry):
    """Password entry editor that masks input text."""

    def __init__(self, master, value, options=None):
        super().__init__(master, value, options)
        self.config(show="•")
    
class DateEntry(ttk.Entry):
    """Entry editor for formatted dates."""

    def __init__(self, master, value, options="%d.%m.%Y"):
        """Initialize a date entry editor with a display format."""
        super().__init__(master)
        self.popup = None
        self.options=options
        self.insert(tk.END, value.strftime(self.options))
        
    def on_validate(self, value):
        """Always accept the entered text; validation is deferred."""
        return True

    def get_value(self):
        """Return the entered date as a datetime object."""
        return datetime.strptime(self.get(), self.options)
  
class DatePopupEntry(ttk.Frame):
    """Editor that displays a date preview and opens a date chooser popup."""

    def __init__(self, master, value, options="%d.%m.%Y"):
        """Initialize the date popup editor with a formatted preview."""
        super().__init__(master)
        self.options=options
        self.popup = None

        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.preview.config(text=value.strftime(self.options))
        
    def on_validate(self, value):
        """Date popup editor always accepts the current preview text."""
        return True

    def get_value(self):
        """Return the current preview date as a datetime object."""
        value = self.preview["text"]
        return datetime.strptime(value, self.options)

    def on_popup(self):
        """Open the date chooser dialog and update the preview value."""
        value = self.get_value()
        self.popup = DatePickerDialog(parent=self.btn, startdate=value, autoshow=True)
        new_value = self.popup.date_selected
        self.preview.config(text=new_value.strftime(self.options))

        self.popup = None
        self.event_generate("<<UpdateEdit>>")

class CustomEntry(ttk.Frame):
    """Editor for custom popup-driven values."""

    def __init__(self, master, value, options=None):
        """Create a custom editor with an external popup handler."""
        super().__init__(master)
        self.popup = None
        self.options = options

        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH)

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.config(text=value)
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)

    def on_validate(self, value):
        """Validate the custom value using the provided callback."""
        if "validate" in self.options:
            return self.options["validate"](value)
        else:
            return True

    def on_popup(self):
        """Invoke the custom popup callback to edit the value."""
        self.popup = True
        if "popup" in self.options:
            self.options["popup"](self)
        self.popup = None

    def get_value(self):
        return self.preview["text"]

class ColorEntry(ttk.Entry):
    """Entry editor for hex color strings."""

    def __init__(self, master, value, options=None):
        """Initialize a color string entry editor."""
        super().__init__(master, validate="focusout")
        self.popup = None
        self.insert(tk.END, value)
        
    def get_value(self):
        """Return the entered color string."""
        return self.get()

    def on_validate(self, value):
        if re.search(r"^#(?:[0-9a-fA-F]{3}){1,2}$", value):
            return True
        else:
            return False

class ColorPopupEntry(ttk.Frame):
    """Editor for choosing colors via a popup or native dialog."""

    def __init__(self, master, value, options=None):
        """Initialize a color popup editor with preview display."""
        super().__init__(master)
        self.popup = None
        self._value =value
        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.preview.config(
            text=value, background=value, 
            foreground=utils.contrast_color(value, model=utils.HEX))

    def on_validate(self, value):
        if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', value):
            return True
        else:
            return False

    def on_popup(self):
        """Open the color chooser and update the preview."""
        self.popup = ColorChooserDialog(parent=self.btn, initialcolor=self._value, title="Choose color")

        x = self.btn.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() 
        self.popup.show([x, y], True)

        if self.popup.result == "OK":
            self._value = self.popup.color

        self.preview.config(
            text=self._value, background=self._value, 
            foreground=utils.contrast_color(self._value, model=utils.HEX))        
        self.popup= None
        self.event_generate("<<UpdateEdit>>")

    def get_value(self):
        return self._value

class FontPopupEntry(ttk.Frame):
    """Editor for choosing a font via popup dialog."""

    def __init__(self, master, value, options=None):
        """Initialize the font popup entry preview."""
        super().__init__(master)
        self.popup = None
        self._value = value

        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        actual = value.actual()
        previewtext = "{} {}".format(
            actual["family"], 
            actual["size"])
        self.preview.config(text=previewtext)

    def on_validate(self, value):
        """Font editor always accepts the current value."""
        return True

    def on_popup(self):
        """Open the font chooser dialog and update the preview."""
        self.popup = FontChooserDialog(
            self.btn, 
            initialfont=self._value, 
            title="Choose font")

        x = self.btn.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() 
        self.popup.show([x, y], True)

        if self.popup.result:
            self._value = self.popup.font

        text = "{} {}".format(
            self._value.actual()["family"], 
            self._value.actual()["size"])
        self.preview.config(text=text)
        self.popup= None
        self.event_generate("<<UpdateEdit>>")

    def get_value(self):
        return self._value

class VarPopupEntry(ttk.Frame):
    """Editor for selecting one or more variables from a variable chooser."""

    def __init__(self, master, value, options=None, selectmode=tk.EXTENDED):
        """Initialize the variable popup entry with preview text."""
        super().__init__(master)
        self.popup = None
        self.options = options
        self.selectmode = selectmode
    
        if type(value) is list:
            self._value = value
        else:
            self._value = None

        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.update_preview_text()

    def update_preview_text(self):
        """Update preview label text from the current variable selection."""
        if self._value is None:
            self.preview.config(text="")
        else:
            entries = []
            for item in self._value:
                if item[0] not in self.options:
                    continue
                entries.append("{}.{}".format(
                    self.options[item[0]]["name"], 
                    item[1]))
            label = ",\n".join(entries)
            self.preview.config(text=label)

    def on_validate(self, value):
        return True

    def on_popup(self):
        self.popup = VarChooserDialog(
            self.btn, initialvars=self._value, 
            options=self.options, title="Choose Variable",
            selectmode=self.selectmode)

        x = self.btn.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() 
        self.popup.show([x, y], True)

        if self.popup.result == "OK":
            self._value = self.popup.vars
        
        self.update_preview_text()
        self.popup= None
        self.event_generate("<<UpdateEdit>>")

    def get_value(self):
        return self._value

class DirectoryPopupEntry(ttk.Frame):
    """Directory selection editor with preview label."""

    def __init__(self, master, value, options=None):
        """Initialize the directory popup entry."""
        super().__init__(master)
        self.popup = None
        self._value = value
        
        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.preview.config(text=value)

    def on_validate(self, value):
        return True

    def on_popup(self):
        self.popup = filedialog.Directory(
            self.btn, initialdir=self._value, title="Choose directory")
        result = self.popup.show()
        if result:
            self._value = result
        self.preview.config(text=self._value)
        self.popup= None
        self.event_generate("<<UpdateEdit>>")

    def get_value(self):
        return self._value

class FilePopupEntry(ttk.Frame):
    """File selection editor with preview label."""

    def __init__(self, master, value, options=None):
        """Initialize the file popup entry."""
        super().__init__(master)
        self.popup = None
        self.options = options
        self._value = value
        
        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.preview.config(text=value)

    def on_validate(self, value):
        return True

    def on_popup(self):
        self.popup = filedialog.Open(
            self.btn, initialfile=self._value, title="Choose file", **self.options)
        result = self.popup.show()
        if result:
            self._value = result
        self.preview.config(text=self._value)
        self.popup= None
        self.event_generate("<<UpdateEdit>>")

    def get_value(self):
        return self._value

class CodeEditorEntry(ttk.Frame):
    """Editor for multi-line code input using a code editor popup."""

    def __init__(self, master, value, options=None):
        """Initialize the code editor popup entry."""
        super().__init__(master)
        self.popup = None
        self._value = value
        
        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.preview.config(text="{} line(s) of code".format(self._value.count("\n")+1))

    def on_validate(self, value):
        return True

    def on_popup(self):
        self.popup = CodeEditorDialog(self.btn, code=self._value)

        x = self.btn.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() 
        self.popup.show([x, y], True)

        if self.popup.result == "OK":
            self._value = self.popup.code

        self.preview.config(text="{} line(s) of code".format(self._value.count("\n")+1))
        self.popup= None
        self.event_generate("<<UpdateEdit>>")

    def get_value(self):
        return self._value

class TableEditorEntry(ttk.Frame):
    """Editor for table data using a table editor popup."""

    def __init__(self, master, value, options=None):
        """Initialize the table editor popup entry."""
        super().__init__(master)
        self.popup = None
        self._value = value
        
        self.btn = ttk.Button(
            self, takefocus=False, 
            text="\u2026", command=self.on_popup, padding=4)
        self.btn.pack(side=tk.RIGHT, fill=tk.BOTH) 

        self.preview = ttk.Label(self, padding=(5,0))
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=tk.YES)
        self.preview.config(text="{} datarow(s)".format(len(self._value[1])))

    def on_validate(self, value):
        return True

    def on_popup(self):
        self.popup = TableEditorDialog(
            self.btn, 
            table_header=copy.deepcopy(self._value[0]), 
            table_data=copy.deepcopy(self._value[1]))

        x = self.btn.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() 
        self.popup.show([x, y], True)

        if self.popup.result == "OK":
            self._value = [self.popup.table_header, np.array(self.popup.table_data).astype(float).tolist()]

        self.preview.config(text="{} datarow(s)".format(len(self._value[1])))
        self.popup= None
        self.event_generate("<<UpdateEdit>>")

    def get_value(self):
        return self._value
    
class SliderEntry(ttk.LabeledScale):
    """Spinbox editor for numeric range input."""

    def __init__(self, master, value, options):
        """Initialize a spinbox with the given range options."""
        super().__init__(master, **options)
        self.options = options
        self.popup = None
        self.value = value

    def get_value(self):
        """Return the spinbox value as an integer."""
        return self.value
    
    def on_validate(self, value):
        try :
            if "from_" in self.options and "to" in self.options:
                min = self.options["from_"] 
                max = self.options["to"] 
                if value < min or value > max:
                    msg = "Validation failed, value must be between {} and {}.".format(min, max)
                    logger.error(msg)
                    return False
            return True
        except:
            msg = "Validation failed."
            logger.error(msg)
            return False

class ColorMapEntry(ttk.Frame):
    """Editor for selecting a color map from available colormaps."""

    def __init__(self, master, value, options=None):
        """Initialize the color map entry with a preview of the selected colormap."""
        super().__init__(master)
        self.popup = None
        self._value = value

        self.btn = ttk.Menubutton(
            self,                   
            image=Images().colormap[value], 
            takefocus=False,
            text=value,
            compound=tk.LEFT)
        self.btn.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH) 

        # Create options menu
        if options:
            sub_menu = ttk.Menu(self.btn, tearoff=True)
            self.btn.config(menu=sub_menu) 

            for entry in options:
                sub_menu.add_command(
                    label=entry, underline=0, 
                    image=Images().colormap[entry], 
                    compound=tk.LEFT, 
                    command=partial(self.on_menu_select, entry))

    def on_menu_select(self, menu_text):
        """Return a callback function that updates the color map selection."""
        self._value = menu_text
        self.btn.config(text=menu_text, image=Images().colormap[menu_text]) 
        self.event_generate("<<UpdateEdit>>")

    def on_validate(self, value):
        return True

    def get_value(self):
        return self._value
