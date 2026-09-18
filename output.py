"""Output panel containing log, console, and iteration views."""

import logging
from simunetcore import logger
from console import Console
from loglist import Loglist
from iterations import Iterations
import ttkbootstrap as ttk
import ttkbootstrap.constants as tk
from images import Images


class Output(ttk.Frame):
    """Tabbed output panel for log messages, console output, and status charts."""
    def __init__(self, master, **kwargs):
        """Initialize the output panel and create each output tab."""
        super().__init__(master, **kwargs)

        self.notebook = ttk.Notebook(self, padding=(0,-2,0,0))
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Frame 1
        self.log_messages = Loglist(self.notebook)
        self.notebook.add(
            self.log_messages, image=Images().system["Logs"], 
            text="Messages", compound=tk.LEFT, padding=-1)
 
        # Frame 2       
        self.console = Console(self.notebook)
        self.notebook.add(
            self.console, image=Images().system["Console"], 
            text="Output", compound=tk.LEFT, padding=-1)
 
        # Frame 3
        self.iterations = Iterations(self.notebook)
        self.notebook.add(
            self.iterations, image=Images().system["Iterations"], 
            text="Statistics", compound=tk.LEFT, padding=-1)

    def set_project(self, project):
        """Assign the current project and refresh the iteration charts."""
        self.iterations.set_project(project)

    def update_theme(self):
        """Update the visual theme of contained output widgets."""
        self.iterations.update_theme()

if __name__ == "__main__":
    # Prepare logging
    logger.prepare_logging("log.conf")
    logger.instance = logging.getLogger("Test")
    
    # Create app window
    app = ttk.Window()

    output = Output(app)
    output.pack(fill=tk.BOTH, expand=tk.YES)
    output.notebook.select(output.notebook.tabs()[1])
    app.mainloop()