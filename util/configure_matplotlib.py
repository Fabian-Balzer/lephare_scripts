# -*- coding: utf-8 -*-
"""
Created on Sat Feb 19 17:43:01 2022

@author: fabian_balzer

Script for setting the matplotlib defaults
"""


import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

import util.my_tools as mt

LATEXHEIGHT = 8.94046  # in inches
LATEXWIDTH = 5.87614


def set_figsize(width=LATEXWIDTH, fraction=1, subplots=(1, 1), aspect=False):
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

    # Golden ratio to set aesthetic figure height
    # https://disq.us/p/2940ij3
    golden_ratio = (5**.5 - 1) / 2

    # Figure height in inches
    fig_height = fig_width if aspect else fig_width * \
        golden_ratio * (subplots[0] / subplots[1])
    return (fig_width, fig_height)


def save_figure(fig, name, format_="pdf"):
    # Save and remove excess whitespace
    fig.savefig(f"{mt.PLOTPATH}{name}.{format_}",
                format=format_, bbox_inches='tight')


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
    print(f"Saved a joint figure to {path}")


font = {'family': 'sans',
        'weight': 'normal',
        'size': 6}
matplotlib.rc('font', **font)

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


matplotlib.rcParams.update(tex_fonts)
matplotlib.rcParams["figure.facecolor"] = "white"