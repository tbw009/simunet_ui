"""Notebook converter utilities.

This module converts Jupyter notebook (.ipynb) files to HTML using nbconvert.
"""

from nbconvert import HTMLExporter
import io


def translate(ipynb_file, template_name="classic", embed_images=True, file_out=None):
    """Convert a notebook file to HTML and save the output.

    Parameters
    ----------
    ipynb_file : str
        Path to the input .ipynb file.
    template_name : str, optional
        Name of the nbconvert HTML template to use, by default "classic".
    embed_images : bool, optional
        Whether to embed images in the HTML output, by default True.
    file_out : str, optional
        Output path for the generated HTML file. If None, uses the notebook
        filename with a .html extension.

    Returns
    -------
    str
        The path of the written HTML file.
    """

    exporter = HTMLExporter(template_name=template_name, embed_images=embed_images)
    (body, resources) = exporter.from_filename(ipynb_file)

    if file_out is None:
        file_out = "{}.html".format(ipynb_file)

    with io.open(file_out, "w+", encoding="utf-8") as f:
        f.write(body)

    return file_out

