"""Image management utilities for the simunet application."""

import os
import ttkbootstrap as ttk
from PIL import Image, ImageDraw, ImageTk
from matplotlib import colormaps
from matplotlib import colors


class Images:
    """Singleton container for loaded application image assets."""
    instance = None

    def __new__(cls):
        """Ensure only one Images instance is created."""
        if Images.instance is None:
            return object.__new__(cls)
        return Images.instance

    def __init__(self):
        """Initialize the singleton by loading system and ribbon image sets."""
        if Images.instance:
            return

        self.system = self.load_images("./images/system/")
        self.ribbon = self.load_images("./images/ribbon/")
        self.theme = self.create_theme_images()
        self.colormap = self.create_colormap_images()

        Images.instance = self

    def load_images(self, path):
        """Load PNG images from the specified directory into a dictionary."""
        files = os.listdir(path)
        images = {}

        for filename in files:
            key, ext = os.path.splitext(os.path.basename(filename))
            if ext.lower() == ".png":
                src = Image.open(path + filename)
                images[key] = ImageTk.PhotoImage(src)

        return images

    def create_theme_images(self):
        """Generate theme icon images for available application styles."""
        theme = {}

        # Create theme icons
        styles = ttk.Style()._theme_definitions
        for key in styles:

            bg = styles[key].colors.bg
            primary = styles[key].colors.primary
            secondary = styles[key].colors.secondary
            light = styles[key].colors.light
           
            img = Image.new('RGBA', (24, 24), (255, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle((0,1,23,22), fill=bg)
            draw.rectangle((2,3,7,20), fill=primary)
            draw.rectangle((9,3,14,20), fill=light)
            draw.rectangle((16,3,21,20), fill=secondary)

            theme[key] = ImageTk.PhotoImage(img)

        return theme

    def create_colormap_images(self):
        """Generate colormap icon images for available matplotlib colormaps."""
        colormap = {}

        matplotlib_colormaps = [
            'Pastel1', 
            'Pastel2', 
            'Paired', 
            'Accent',
            'Dark2', 
            'Set1', 
            'Set2', 
            'Set3',
            'tab10', 
            'tab20', 
            'tab20b', 
            'tab20c'
        ]
        # Create matplotlib colormap icons
        for key in matplotlib_colormaps:

            mpl_colors = list(colormaps.get_cmap(key).colors)
            bg = ttk.Style().colors.bg

            size = (64, 16)
            img = Image.new('RGBA', size, (255, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            for i, color in enumerate(mpl_colors):
                x0 = 1 + i * ((size[0]-2) / len(mpl_colors))
                x1 = 1 + (i + 1) * ((size[0]-2) / len(mpl_colors))
                draw.rectangle((x0, 1, x1, size[1]-2), fill=colors.to_hex(color))
            draw.rectangle((0,0,size[0]-1,size[1]-1), outline="#000000")

            colormap[key] = ImageTk.PhotoImage(img) 
        return colormap