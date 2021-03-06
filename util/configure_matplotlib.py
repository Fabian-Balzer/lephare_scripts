# -*- coding: utf-8 -*-
"""
Created on Sat Feb 19 17:43:01 2022

@author: fabian_balzer

Script for setting the matplotlib defaults
"""


import os

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import util.my_tools as mt

LATEXHEIGHT = 8.94046  # in inches
LATEXWIDTH = 5.87614


# TODO: Change this to actually search for the availability of LaTeX (this is just a workaround)
USE_LATEX = "LEPHAREDIR" not in os.environ.keys()


def set_figsize(width=LATEXWIDTH, height=None, fraction=1, subplots=(1, 1), aspect=False):
    """Set figure dimensions to avoid scaling in LaTeX.

    Parameters
    ----------
    width: float or string
            Document width in points, or string of predined document type
    fraction: float, optional
            Fraction of the width which you wish the figure to occupy
    subplots: array-like, optional
            The number of rows and columns of subplots.
    Returns
    -------
    fig_dim: tuple
            Dimensions of figure in inches
    """

    # Width of figure (in pts)
    fig_width = width * fraction

    # Figure height in inches
    if height is None:
        # Golden ratio to set aesthetic figure height
        # https://disq.us/p/2940ij3
        golden_ratio = (5**.5 - 1) / 2
        fig_height = fig_width if aspect else fig_width * \
            golden_ratio * (subplots[0] / subplots[1])
    else:
        fig_height = height
    return (fig_width, fig_height)


def save_figure(fig, name="", directory="", stem="", format_="pdf"):
    """Save a given figure while removing excess whitespace"""
    directory = directory + "/" if directory != "" else directory
    stem = stem + "_" if stem != "" else stem
    fpath = f"{mt.GEN_CONFIG['PATHS']['plot']}{directory}{stem}{name}.{format_}"
    if mt.assert_file_overwrite(fpath):
        fig.savefig(fpath, format=format_, bbox_inches='tight')
        mt.LOGGER.info(
            f"Successfully saved the {stem}{name}.{format_} plot at {directory}.")
    else:
        mt.LOGGER.info(f"Skipped writing the {stem}{name} plot.")


def save_current_figures(name, format_="pdf"):
    """Takes the current instances of figures and saves them all to a single file"""
    path = f"{mt.PLOTPATH}{name}.{format_}"
    pp = PdfPages(path)
    fig_nums = plt.get_fignums()
    figs = [plt.figure(n) for n in fig_nums]
    for fig in figs:
        fig.savefig(pp, format=format_, bbox_inches='tight')
    pp.close()
    plt.close('all')
    mt.LOGGER.info(f"Saved a joint figure to {path}")


font = {'family': 'sans',
        'weight': 'normal',
        'size': 6}
mpl.rc('font', **font)

if USE_LATEX:
    tex_fonts = {
        # Use LaTeX to write all text
        "text.usetex": True,
        "font.family": "serif",
        # Use 10pt font in plots, to match 10pt font in document
        "axes.labelsize": 8,
        "font.size": 8,
        # Make the legend/label fonts a little smaller
        "legend.fontsize": 8,
        "xtick.labelsize": 6,
        "ytick.labelsize": 6,
    }

    mpl.rcParams.update(tex_fonts)
mpl.rcParams["figure.facecolor"] = "white"

custom_params = {
    "legend.borderaxespad": .7,  # Legend closer to the border
    "legend.handletextpad": 0.5,  # Distance between circle and label is smaller
    "legend.labelspacing": .9,  # Vertical space between labels
    "legend.markerscale": .5,     # The size of the dots
    "legend.handlelength": 1,    # Length of the handles
    "legend.columnspacing": .2,
    "figure.autolayout": True,
    "figure.titlesize": 9,
    "savefig.dpi": 300,
}
mpl.rcParams.update(custom_params)
