"""Dialog for editing CSV-style table data in a spreadsheet-like view."""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from ttkbootstrap.dialogs import Dialog
from ttkbootstrap.style import Style
from tksheet import Sheet
from tkinter import TclError
from tkinter import filedialog
import csv
import io

from images import Images
from toolbar import Toolbar
from tooltip import Tooltip


class TableEditorDialog(Dialog):
    """Dialog for editing tabular data with headers.

    Uses tksheet to display and edit rows and columns in a lightweight
    spreadsheet-style interface.
    """
    def __init__(self, parent=None, title="Edit table data", table_header=None, table_data=None, readonly=False):
        """Initialize the table editor dialog.

        Args:
            parent: Parent widget for the dialog.
            title: Dialog title.
            table_data: Initial row data for the table.
            table_header: Header row labels for the table.
        """
        super().__init__(parent=parent, title=title)

        self.table_header = table_header
        self.table_data = table_data
        self.readonly = readonly

    def create_body(self, master):
        """Construct the dialog body with the editable table view."""

        # Create toolbar images
        self.images = Images().ribbon

        # Create toolbar
        self.create_toolbar(master)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        table_theme = {
            "resizing_line_fg": "black",
            "drag_and_drop_bg": "black",
            "top_left_bg": Style().colors.bg,
            "top_left_fg": Style().colors.border,
            "top_left_fg_highlight": Style().colors.secondary,
            "outline_color": Style().colors.selectbg,
            "popup_menu_fg": Style().colors.fg,
            "popup_menu_bg": Style().colors.bg,
            "popup_menu_highlight_bg": Style().colors.selectbg,
            "popup_menu_highlight_fg": Style().colors.selectfg,
            "header_fg": Style().colors.fg,
            "header_bg": Style().colors.border,
            "header_hidden_columns_expander_bg": Style().colors.secondary,
            "header_border_fg": Style().colors.bg,
            "header_grid_fg": Style().colors.light,
            "header_selected_cells_bg": Style().colors.primary,
            "header_selected_cells_fg": Style().colors.selectfg,
            "header_selected_columns_bg":Style().colors.primary,
            "header_selected_columns_fg": Style().colors.selectfg,
            "index_fg": Style().colors.fg,
            "index_bg": Style().colors.border,
            "index_hidden_rows_expander_bg": Style().colors.secondary,
            "index_border_fg": Style().colors.bg,
            "index_grid_fg": Style().colors.light,
            "index_selected_cells_bg": Style().colors.primary,
            "index_selected_cells_fg": Style().colors.selectfg,
            "index_selected_rows_bg": Style().colors.primary,
            "index_selected_rows_fg": Style().colors.selectfg,
            "table_editor_fg": Style().colors.fg,
            "table_editor_bg": Style().colors.bg,
            "table_fg": Style().colors.fg,
            "table_bg": Style().colors.bg,
            "table_grid_fg": Style().colors.border,
            "table_selected_box_cells_fg": Style().colors.primary,
            "table_selected_box_rows_fg": Style().colors.primary,
            "table_selected_box_columns_fg": Style().colors.primary,
            "table_selected_rows_border_fg": Style().colors.primary,
            "table_selected_columns_border_fg": Style().colors.primary,
            "table_selected_cells_border_fg": Style().colors.primary,
            "table_selected_cells_bg": Style().colors.selectbg,
            "table_selected_cells_fg": Style().colors.selectfg,
            "table_selected_rows_bg": Style().colors.selectbg,
            "table_selected_rows_fg": Style().colors.selectfg,
            "table_selected_columns_bg": Style().colors.selectbg,
            "table_selected_columns_fg": Style().colors.selectfg,
            "font": ("TkDefaultFont",  9, "normal"),
            "header_font": ("TkDefaultFont", 9, "normal"),
            "index_font": ("TkDefaultFont", 9, "normal"),
            "popup_menu_font": ("TkDefaultFont", 9, "normal"),
        }
        # Create border
        container = ttk.Frame(master, padding=(10,10,10,0))
        container.pack(fill=tk.BOTH, expand=tk.YES, anchor=tk.N)

        self.table = Sheet(container, expand_sheet_if_paste_too_big=True)
        self.table.pack(fill=tk.BOTH, expand=tk.YES)

        self.table.enable_bindings("all", "edit_header", "edit_index", "rc_add_row", "rc_insert_row", "rc_delete_row")
        self.table.set_options(**table_theme)

        # Set table header and table data
        if self.table_header:
            self.table.set_header_data(self.table_header)
        if self.table_data:
            self.table.set_sheet_data(self.table_data)

        # Set read only cells
        if self.readonly:
            self.table[None, 0, None, None].options(table=True, header=True).readonly(True)
            self.table[None, 0, None, None].readonly(True)

        if "t" in self.table_header:
            self.table[None, list.index(self.table_header, "t"), None, 1].options(table=False, header=True).readonly(True)

        # Update toolbar items
        self.update_ui()
        self.redraw()

        # Set tool window
        self._toplevel.wm_attributes("-toolwindow", "true")
        self._toplevel.wm_resizable(width=True, height=True)

    def create_buttonbox(self, master):
        """Create the OK and Cancel button row at the bottom of the dialog."""
        # Add a sizegrip at the bottom-right
        sizegrip = ttk.Sizegrip(master)
        sizegrip.pack(side=tk.RIGHT, anchor=tk.SE)

        container = ttk.Frame(master, padding=(0, 10))
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

    def create_toolbar(self, master):
        """Create toolbar with edit actions and search controls."""

        # Toolbar items
        tb_items = [
            ("Open", "Open", "Open", "Open CSV Datasource...", self.on_open),
            ("SaveAs", "SaveAs", "Save As", "Save Datasource as CSV...", self.on_save),
            "---",
            ("Cut", "Cut", "Cut", "Cut selected objects (Strg+X)", self.on_cut),
            ("Copy", "Copy", "Copy", "Copy selected objects to clipboard (Strg+C)", self.on_copy),
            ("Paste", "Paste", "Paste", "Paste objects from clipboard (Strg+V)", self.on_paste),
            "---",
            ("Undo", "Undo", "Undo", "Undo previous action (Strg+Z)", self.on_undo),
            ("Redo", "Redo", "Redo", "Redo last action (Strg+Y)", self.on_redo),
            "---",
        ]

        # Create the toolbar
        self.toolbar = Toolbar(master, self.images, tb_items, show_text=False)

        # Add search frame
        frame = ttk.Frame(self.toolbar)
        frame.pack(side=tk.LEFT, padx=10)

        # Add a label
        self.lbl_chart = ttk.Label(frame, text="Search: ")
        self.lbl_chart.pack(side=tk.LEFT, fill=tk.Y)

        # Add the search entry
        self.entry_search = ttk.Entry(frame)
        self.entry_search.bind("<Return>", lambda e: self.on_search())
        self.entry_search.pack(side=tk.LEFT)

        # Add search button into the toolbar
        self.btn_search = ttk.Button(
            frame,
            bootstyle=tk.GHOST,
            image=Images().system["Search"],
            takefocus=False,
            command=self.on_search,
        )
        self.btn_search.pack(side=tk.LEFT)

        Tooltip(self.btn_search, text="Search")

        # Add clear search button
        self.btn_clear_search = ttk.Button(
            frame,
            bootstyle=tk.GHOST,
            image=Images().system["SearchClear"],
            takefocus=False,
            command=self.on_clear_search,
        )
        self.btn_clear_search.pack(side=tk.LEFT)

        Tooltip(self.btn_clear_search, text="Clear search")

        # Create a separator
        sep = ttk.Separator(self.toolbar, orient=tk.VERTICAL)
        sep.pack(after=frame, side=tk.LEFT, fill=tk.Y)

    def on_button_press(self, button):
        """Handle button presses and save edited table values on OK.

        Args:
            button: The button widget that was pressed.
        """
        self._result = button.cget('text')

        if self._result == 'OK':
            self.table_data = self.table.get_sheet_data(get_header=False, get_index=False)
            self.table_header = self.table.headers()

        # Close window
        self.close()

    def on_open(self):
        """Prompt the user for a file path and load the csv file."""
        filetypes = [("CSV files", "*.csv"), ("All files", "*")]
        dialog = filedialog.Open(self, filetypes=filetypes)
        path = dialog.show()

        if path:
            with open(path, "r") as f:
                # Read csv file
                filedata = f.read()

            # Create a csv Dictreader
            reader = csv.reader(
                io.StringIO(filedata), 
                dialect=csv.Sniffer().sniff(filedata))
            
            table_header = next(reader)
            table_data = [row for row in reader]

            # Update table
            self.table.set_header_data(table_header)
            self.table.set_sheet_data(table_data)

    def on_save(self):
        """Prompt the user for a file path and save the csv file."""
        filetypes = [("CSV files", "*.csv"), ("All files", "*")]
        defaultextension = "csv"
        dialog = filedialog.SaveAs(
            self, filetypes=filetypes, 
            defaultextension=defaultextension)
        path = dialog.show()

        if path:
            with open(path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(self.table.headers())
                writer.writerows(self.table.get_sheet_data(get_header=False, get_index=False))

    def on_clear_search(self):
        # Clear search entry
        self.entry_search.delete(0, tk.END)
        self.on_search()

    def on_search(self):
        find_str = self.entry_search.get()
        if find_str:
            self.table.next_match(False, find_str)

    def on_undo(self):
        self.table.undo()

    def on_redo(self):
        self.table.redo()

    def on_cut(self):
        self.on_copy()
        self.table.cut()

    def on_copy(self):
        self.table.copy()

    def on_paste(self):
        self.table.paste()

    def check_cut_copy(self):
        try:
            if self.table.selected is not None:
                return True
            else:
                return False
        except TclError:
            return False

    def check_undo(self):
        return len(self.table.get_undo_stack())
    
    def check_redo(self):
        return len(self.table.get_redo_stack())
    
    def check_paste(self):
        try:
            self.table.tk.call("tk::GetSelection", self.table, "CLIPBOARD")
        except TclError:
            return False
        else:
            return True

    def show(self, position = None, wait_for_result = True):
        """Show the dialog and position it relative to `parent` if given.

        Blocks until the dialog is closed and cancels the redraw timer
        afterwards.
        """
        super().show(position, wait_for_result)
        self.after_cancel(self.redraw_id)

    def redraw(self, *args):
        """Refresh UI state.

        This method schedules itself to run every 50ms.
        """
        self.update_ui()

        # Refresh the canvas widget after 50ms
        self.redraw_id = self.after(100, self.redraw)

    def update_ui(self):
        self.toolbar.set_enabled("Cut", self.check_cut_copy())
        self.toolbar.set_enabled("Copy", self.check_cut_copy())
        self.toolbar.set_enabled("Paste", self.check_paste())
        self.toolbar.set_enabled("Undo", self.check_undo())
        self.toolbar.set_enabled("Redo", self.check_redo())

if __name__ == "__main__":
    with open("data/csv_data.csv", "r") as f:
        # Read csv file
        filedata = f.read()

    # Create a csv Dictreader
    reader = csv.reader(
        io.StringIO(filedata), 
        dialect=csv.Sniffer().sniff(filedata))
    
    dlg = TableEditorDialog(
        table_header=next(reader),
        table_data=[row for row in reader])
    dlg.show()

    print(dlg.result)
    print(dlg.table_header)
    print(dlg.table_data)
