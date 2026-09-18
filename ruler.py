"""Ruler widget for drawing horizontal and vertical guides.

This module provides a canvas-based ruler component that supports both
horizontal and vertical orientations, zoom scaling, and a movable
position indicator.
"""

import ttkbootstrap as ttk
import ttkbootstrap.constants as tk


class Ruler(ttk.Canvas):
    """Canvas-based ruler widget for horizontal or vertical orientation."""

    # Ruler attributes
    SIZE = 25
    FONT = ("TkDefaultFont", 8)

    def __init__(self, master, length, orient, step=20, **kwargs):
        """Initialize the ruler widget.

        Args:
            master: Parent widget.
            length: Length of the ruler in pixels.
            orient: Orientation constant, either tk.HORIZONTAL or tk.VERTICAL.
            step: Distance between tick marks.
            **kwargs: Additional Canvas options.
        """
        super().__init__(master, width=self.SIZE, height=self.SIZE, **kwargs)

        self.orient = orient
        self.length = length
        self.zoom_factor = 1.0
        self.step = step

        self.update_dimensions()

        # Subscribe to ThemeChanged message
        self.bind("<<ThemeChanged>>", self._on_theme_change)
        
    def update_dimensions(self):
        """Refresh ruler dimensions and redraw the ruler.

        This method reapplies the current zoom factor and recreates the ruler
        graphics to reflect any layout changes.
        """
        self.set_zoom_factor(self.zoom_factor)
        self.create_ruler()

    def create_ruler(self):
        """Draw the ruler tick marks, labels, and indicator."""
        self.delete("grid")
        self.delete("label")

        style = ttk.Style()
        grid_color = style.colors.selectbg
        label_color = style.colors.dark
        indicator_color = style.colors.danger

        if self.orient == tk.VERTICAL:
            # Create lines
            self.create_line(
                self.SIZE-1, 0, self.SIZE-1, self.length*self.zoom_factor, 
                width=1, fill=grid_color, tags="grid")
                
            for y in range(0, self.length, self.step):
                if y % 100 == 0:
                    # Draw longer line with text
                    self.create_line(
                        self.SIZE-10, y*self.zoom_factor, self.SIZE, 
                        y*self.zoom_factor, width=1, fill=label_color, tags="label")
                    if y > 0:
                         self.create_text(
                             self.SIZE-18, y*self.zoom_factor, text=str(y), angle=90, 
                             fill=label_color, font=self.FONT, tags="label")
                else:
                    # Draw short line
                    self.create_line(
                        self.SIZE-8, y*self.zoom_factor, self.SIZE, 
                        y*self.zoom_factor, width=1, fill=grid_color, tags="grid")

            # Create position indicator
            self.position = self.create_line(
                0, 0, self.SIZE, 0, fill=indicator_color, 
                width=2, state=tk.HIDDEN, tags="indicator")

        else:
            # Create lines
            self.create_line(
                0, self.SIZE-1, self.length*self.zoom_factor, self.SIZE-1, 
                width=1, fill=grid_color, tags="grid")

            for x in range(0, self.length, self.step):
                if x % 100 == 0:
                    # Draw long line with text
                    self.create_line(
                        x*self.zoom_factor, self.SIZE-10, x*self.zoom_factor, 
                        self.SIZE, width=1, fill=label_color, tags="label")
                    if x > 0:
                        self.create_text(
                            x*self.zoom_factor, self.SIZE-18, text=str(x), angle=0,
                            fill=label_color, font=self.FONT, tags="label")
                else:
                    # Draw short line
                    self.create_line(
                        x*self.zoom_factor, self.SIZE-8, x*self.zoom_factor, 
                        self.SIZE,  width=1, fill=grid_color, tags="grid")
                        
            # Create position indicator
            self.position = self.create_line(
                0, 0, 0, self.SIZE, fill=indicator_color, 
                width=2, state=tk.HIDDEN, tags="indicator")
 
    def set_position(self, pos):
        """Move the position indicator to the supplied coordinate."""
        if self.orient == tk.VERTICAL:
            self.coords(self.position, 0, pos, self.SIZE - 1, pos)
        else:
            self.coords(self.position, pos, 0, pos, self.SIZE - 1)

    def get_zoom_factor(self):
        """Return the current zoom factor."""
        return self.zoom_factor

    def set_zoom_factor(self, zoom_factor):
        """Scale the ruler contents by the new zoom factor."""
        factor = zoom_factor / self.zoom_factor

        if self.orient == tk.VERTICAL:
            self.scale(tk.ALL, 0, 0, 1.0, factor)
            self.config(scrollregion=(0, 0, 0, int(self.length * zoom_factor)))
        else:
            self.scale(tk.ALL, 0, 0, factor, 1.0)
            self.config(scrollregion=(0, 0, int(self.length * zoom_factor), 0))

        self.zoom_factor = zoom_factor

    def hide_position(self):
        """Hide the position indicator line."""
        self.itemconfigure(self.position, state=tk.HIDDEN)

    def show_position(self):
        """Show the position indicator line."""
        self.itemconfigure(self.position, state=tk.NORMAL)

    def _on_theme_change(self, *_):
        """Refresh ruler colors from the current theme."""
        style = ttk.Style()

        self.configure(bg=style.colors.bg)
        self.itemconfigure("grid", fill=style.colors.selectbg)
        self.itemconfigure("label", fill=style.colors.fg)
        self.itemconfigure("indicator", fill=style.colors.danger)


if __name__ == "__main__":
    # Create app window
    app = ttk.Window()
    app.geometry("800x600+100+100")

    h_ruler = Ruler(app, 2000, tk.HORIZONTAL) 
    h_ruler.grid(row=0, column=1, sticky=tk.NSEW)

    v_ruler = Ruler(app, 2000, tk.VERTICAL)
    v_ruler.grid(row=1, column=0, sticky=tk.NSEW)
    
    app.columnconfigure(1, weight=1)
    app.rowconfigure(1, weight=1)
    
    app.mainloop()