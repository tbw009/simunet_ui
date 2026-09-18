"""Repository browser widgets for model repository items and categories."""

from tooltip import Tooltip
from collapsingframe import CollapsingFrame
import os
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from images import Images
import tksvg
import json
from simunetcore import logger


class RepositoryItem():
    """Represents a repository model item with metadata and icon images."""
   
    def __init__(self, item_path, icon_scale):
        """Initialize repository item metadata and load its SVG icon."""
        self.path = item_path

        # Read content
        with open(self.path +"/model.json", "r") as f:
            json_string = f.read()
            data = json.loads(json_string)

        # Store properties
        # Category
        self.category = "Common"
        if "category" in data.keys():
            self.category = data["category"]

        # Class
        self.class_name = data["class"]
        if self.class_name == "AWSModel":
            self.class_icon = Images().system["Cloud"]
        elif self.class_name == "MQTTModel":
            self.class_icon = Images().system["User"]
        else:
            self.class_icon = Images().system["Local"]

        # Model
        self.model_dict = data["model"]
        self.model_icon = self.get_image(icon_scale)

    def get_image(self, scale):
        """Load and scale the repository item SVG icon."""
        svg_source = tksvg.SvgImage(file=self.path +"/model.svg")
        svg_scale = scale / float(max(svg_source.width(), svg_source.height()))
        svg_source.configure(scale=svg_scale)
        return svg_source


class RepositoryButton(ttk.Frame):
    """Widget that displays a repository item with icon, name, and class badge."""
  
    ICON_SCALE = 32

    def __init__(self, master, repo_item, btn_style="neutral", **kwargs):
        """Create a clickable repository button for the given repository item."""
        super().__init__(master, **kwargs)

        self.repo_item = repo_item
        self.btn_style = btn_style

        # Configure grid
        self.grid_rowconfigure(0, minsize=self.ICON_SCALE+10)
        self.grid_columnconfigure(0, minsize=self.ICON_SCALE+10)
        self.grid_columnconfigure(1, weight=1)

        # Create an image for the repo item
        self.img_model = ttk.Label(
            self, 
            width=self.ICON_SCALE,
            takefocus=False, 
            bootstyle=self.btn_style, 
            image=repo_item.model_icon,
            anchor=tk.CENTER)
        self.img_model.grid(row=0, column=0, sticky=tk.NSEW)

        # Create a Label for the repo item
        self.btn = ttk.Label(
            self, 
            takefocus=True,
            bootstyle=self.btn_style, 
            text=repo_item.model_dict["name"],
            compound=tk.TOP,
            anchor=tk.W)
        self.btn.grid(row=0, column=1, sticky=tk.NSEW)

        # Create a site image for the repo item
        self.img_class = ttk.Label(
            self, 
            takefocus=False, 
            bootstyle=self.btn_style, 
            image=repo_item.class_icon,
            anchor=tk.W)
        self.img_class.grid(
            row=0, column=2, sticky=tk.NSEW, 
            padx = 0)
        
        # Attach events
        for widget in [self.btn, self.img_class, self.img_model]:
            widget.bind("<Enter>", lambda e: self.event_generate("<Enter>"))
            widget.bind("<Leave>", lambda e: self.event_generate("<Leave>"))
            widget.bind("<Button-1>", lambda e: self.event_generate("<Button-1>"))

        # Attach tooltip
        Tooltip(self.btn, text="{}\n{}\nDomain: {}\nDimension: {}".format(
            repo_item.model_dict["name"], 
            repo_item.model_dict["description"],
            repo_item.model_dict["domain"],
            repo_item.model_dict["dim"]))

        # Create a separator
        self.sep = ttk.Separator(self, orient= tk.HORIZONTAL)
        self.sep.grid(row=1, column=0, columnspan=3, sticky=tk.EW)

class Repository(ttk.Frame):
    """Repository browser with filtering, categories, and selection support."""

    def __init__(
            self, master,
            btn_style="default",
            btn_style_checked="@secondary", 
            btn_style_hover="@chrome", 
            **kwargs):
        """Initialize the repository browser UI and internal selection state."""
        super().__init__(master, **kwargs)

        # Create toolbar
        self.toolbar = ttk.Frame(self)
        self.toolbar.grid(row=0, column=0, sticky=tk.EW)

        # Add horizontal separator at the bottom of the toolbar
        line = ttk.Separator(self.toolbar, orient= tk.HORIZONTAL)
        line.pack(side=tk.BOTTOM, fill=tk.X)

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

        # Add object label
        label = ttk.Label(self, text="Model Repository", padding=(5,0), bootstyle=tk.PRIMARY)
        label.grid(row=1, column=0, sticky=tk.EW)

        # Add horizontal separator under the object label
        line = ttk.Separator(self, orient= tk.HORIZONTAL)
        line.grid(row=2, column=0, sticky=tk.EW)

        # Create collapsing frame
        self.cf = CollapsingFrame(self, padding=0)
        self.cf.grid(row=3, column=0, sticky=tk.NSEW)

        # Configure grid rows and columns
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Internal vars
        self.widgets = {}
        self.selected = None

        # Create repo button styles
        self.btn_style = btn_style
        self.btn_style_checked = btn_style_checked
        self.btn_style_hover = btn_style_hover
      
    def load(self, path):
        """Load repository items from the given path and populate the UI."""
        folders = os.listdir(path)      
        repo_items = []

        # Loop through folders
        for item in folders:
            # combine path and folder
            folder = os.path.join(path, item)
            # Inspect only folders
            if os.path.isdir(folder):
                try:
                    # Create repository item
                    repo_items.append(RepositoryItem(folder, RepositoryButton.ICON_SCALE))
                except Exception as e:
                    logger.error(f"Error loading repository item: {e}")

        # create a category dict
        categories = {}
        for category in sorted(set(item.category for item in repo_items)):
            categories[category] = []

        # append the items
        for item in repo_items:
            categories[item.category].append(item)
        
        # Loop through folders
        for category in categories:
            # Create group
            group_container = ttk.Frame(self.cf)
            # Configure grid columns
            group_container.columnconfigure(0, weight=1)

            # Create a separator for the category
            sep = ttk.Separator(
                group_container,  
                orient= tk.HORIZONTAL)
            sep.grid(row=0, column=0, sticky=tk.EW)
            
            # Loop through models
            counter = 1
            for repo_item in sorted(categories[category], key=lambda x:x.model_dict["name"]):
                # Create a surrounding frame for the repo entry
                repo_btn = RepositoryButton(group_container, repo_item, btn_style=self.btn_style)
                repo_btn.grid(row=counter, column=0, sticky=tk.NSEW)
                
                # Attach events
                repo_btn.bind("<Enter>", self.on_enter)
                repo_btn.bind("<Leave>", self.on_leave)
                repo_btn.bind("<Button-1>", self.on_left_click)
                
                # Store the widget - repo item combination
                self.widgets[repo_item] = repo_btn

                # Increment counter
                counter += 1
            
            # Add the category to the repo
            self.cf.add(child=group_container, title=category)

    def on_enter(self, event):
        """Highlight a repository button when the mouse enters it."""
        repo_btn = event.widget
        for widget in [repo_btn.btn, repo_btn.img_model, repo_btn.img_class]:
            widget.configure(bootstyle=self.btn_style_hover)
    
    def on_leave(self, event):
        """Restore repository button style when the mouse leaves it."""
        repo_btn = event.widget
        if repo_btn.repo_item == self.selected:
            for widget in [repo_btn.btn, repo_btn.img_model, repo_btn.img_class]:
                widget.configure(bootstyle=self.btn_style_checked)
        else:
            for widget in [repo_btn.btn, repo_btn.img_model, repo_btn.img_class]:
                widget.configure(bootstyle=self.btn_style)

    def on_left_click(self, event):
        """Handle repository item selection when clicked."""
        repo_btn = event.widget
        self.set_selected(repo_btn.repo_item)

    def set_selected(self, item):
        """Mark the given repository item as selected and update button styles."""
        for repo_btn in self.widgets.values():
            if repo_btn.repo_item == item:
                for widget in [repo_btn.btn, repo_btn.img_model, repo_btn.img_class]:
                    widget.configure(bootstyle=self.btn_style_checked)
            else:
                for widget in [repo_btn.btn, repo_btn.img_model, repo_btn.img_class]:
                    widget.configure(bootstyle=self.btn_style)
        self.selected = item
        self.event_generate("<<SelectionChanged>>")      

    def on_clear_filter(self):
        """Clear the repository filter text and refresh the visible items."""
        self.entry_filter.delete(0, tk.END)
        self.on_filter()

    def on_filter(self):
        """Filter repository items by the entered search string."""
        find_str = str(self.entry_filter.get())

        for repo_btn in self.widgets.values():
            if find_str in repo_btn.btn["text"]:
                repo_btn.grid()
            else:
                repo_btn.grid_remove()

if __name__ == "__main__":
    # Create app window
    app = ttk.Window()

    # Create repository
    repo = Repository(app, width=150)
    repo.load("./repository")
    repo.pack(fill=tk.BOTH, expand=tk.YES)

    app.mainloop()   
