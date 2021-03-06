# -*- coding: utf-8 -*-
"""
Created on Sat Feb 19 17:37:14 2022

@author: fabian_balzer

Script for plotting the spectroscopic availability of the matched catalogue
"""
# %%
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import util.configure_matplotlib as cm
import util.my_tools as mt
from matplotlib.patches import Patch


def plot_r_band_magnitude(df, stem="", title=""):
    """Plots the number of sources for multiple r-band bins and shows how much spec-z is available for each."""
    fig, ax = plt.subplots(1, 1, figsize=cm.set_figsize(fraction=.5))
    with_z = df[df["ZSPEC"] > 0]
    without_z = df[~(df["ZSPEC"] > 0)]
    ax.grid(True, axis="y")
    ax.hist([with_z["mag_r"], without_z["mag_r"]],
            bins=30, stacked=True, color=['k', 'g'], alpha=0.7, label=["With spec-$z$", "Without spec-$z$"], histtype="stepfilled", edgecolor="k")
    ax.legend(loc="upper left")
    ax.set_xlabel(f"{mt.generate_pretty_band_name('r')}-band magnitude")
    ax.set_ylabel("Number of sources")
    if title != "":
        title = f"{mt.generate_pretty_band_name('r')}-band distribution ({len(df[df['mag_r']>0])} sources, eFEDS field)" if title == "default" else title
        ax.set_title(title, size="small")
    cm.save_figure(fig, directory="input_analysis",
                   stem=stem, name="r_band_hist")


def construct_band_availability_dataframe(df, desired_bands):
    """Count the number of available photometry for each band and assign colours to them depending on the surveys they stem from.
    returns a band_count_df with the bands as an index."""
    counts, source_nums = {}, {}
    for ttype in ["extended", "pointlike"]:
        subset = df[df["Type"] == ttype]
        total_length = len(subset)
        for band in desired_bands:
            refname = f"mag_{band}" if band != "ZSPEC" else band
            subset = subset[subset[refname] > 0]
            if band in counts:
                counts[band][ttype] = len(subset) / total_length
            else:
                counts[band] = {ttype: len(subset) / total_length}
        source_nums[ttype] = total_length
    band_count_df = pd.DataFrame(counts).T
    print(band_count_df)
    colour_dict = {band: mt.give_survey_color_for_band(
        band) for band in desired_bands}
    survey_dict = {band: mt.give_survey_for_band(
        band) for band in desired_bands}
    band_count_df["Colour"] = pd.DataFrame.from_dict(
        colour_dict, orient="index")
    band_count_df["Survey"] = pd.DataFrame.from_dict(
        survey_dict, orient="index")
    return band_count_df, source_nums


def construct_num_band_dataframe(df, allowed_bands):
    """Count how many bands are available for each source and return a dataframe reflecting this distribution."""
    max_band_num = len(allowed_bands)
    count_dict = {}
    # Counts the number of not-nan-entries for each row
    df["num_bands"] = df[allowed_bands].count(axis=1)
    for i in range(max_band_num + 1):
        with_z = df[df["ZSPEC"] > 0]
        without_z = df[~(df["ZSPEC"] > 0)]
        count_dict[i] = {}
        count_dict[i]["with_z"] = len(with_z[with_z["num_bands"] == i])
        count_dict[i]["without_z"] = len(
            without_z[without_z["num_bands"] == i])
    band_count_df = pd.DataFrame(count_dict).T
    return band_count_df


def construct_availability_bar_plots(band_count_df, ax, title, source_nums):
    """Constructs bar plots for the extended and pointlike subsample on the given ax."""
    ax.grid(True, axis="y")
    labels = [mt.generate_pretty_band_name(
        band) for band in band_count_df.index]
    x = np.arange(len(labels))
    width = 0.39  # the width of the bars
    space = 0
    rects1 = ax.bar(
        x - width / 2 - space, band_count_df["extended"], width, label='Extended', color=band_count_df["Colour"], edgecolor="k", alpha=0.7)
    rects2 = ax.bar(
        x + width / 2 + space, band_count_df["pointlike"], width, label='Pointlike', color=band_count_df["Colour"], edgecolor="k")
    for bar in rects1:
        bar.set_linewidth(0.5)
        bar.set_linestyle("dashed")
    for bar in rects2:
        bar.set_linewidth(0.5)
        bar.set_hatch("///")

    # Add some text for labels, title and custom x-axis tick labels, etc.
    ax.set_ylabel('Relative availability')
    ax.set_ylim(0, 1)
    if title != "":
        ax.set_title(title, size="small")
    ax.set_xticks(x)
    ax.set_xticklabels(list(labels), minor=False, rotation=90)
    ax.axhline(1, color="k", linewidth=0.6)
    ax.bar_label(rects1, labels=[
                 int(num * source_nums["extended"]) for num in band_count_df["extended"]], label_type='edge', rotation=90, padding=2.5, size="x-small")
    ax.bar_label(rects2, labels=[
                 int(num * source_nums["pointlike"]) for num in band_count_df["pointlike"]], label_type='edge', rotation=90, padding=2.5, size="x-small")


def plot_input_distribution(df, band_list: list, consider_specz=True, title=""):
    """Produce a bar plot of the relative input distribution for pointlike and extended.
    Parameters:
        df: Input or output Dataframe with magnitude columns in each band.
        glb_context: Global context to identify the used bands"""
    if consider_specz:
        band_list = list(band_list) + ["ZSPEC"]
    band_count_df, source_nums = construct_band_availability_dataframe(
        df, band_list)
    fig, axes = plt.subplots(1, 1, figsize=cm.set_figsize(fraction=.8))
    if title == "default":
        title = f"Photometry in the eFEDS field  ({len(df)} sources in total)"
    construct_availability_bar_plots(band_count_df, axes, title, source_nums)
    survey_dict = {survey: mt.give_survey_color(
        survey) for survey in set(band_count_df["Survey"])}
    legend_patches = [Patch(facecolor=color, edgecolor='k',
                            label=mt.give_survey_name(survey)) for survey, color in survey_dict.items()]
    ext_plike_patches = [Patch(facecolor="white", edgecolor='k',
                               label=f"{label.capitalize()} ({source_nums[label]})", linestyle=lstyle, hatch=hatch) for label, lstyle, hatch in [("extended", "dashed", ""), ("pointlike", "-", "///")]]
    legend_2 = plt.legend(handles=ext_plike_patches, prop={
        "size": "x-small"}, bbox_to_anchor=(1, 0.7), loc=2)
    fig.add_artist(legend_2)
    fig.legend(handles=legend_patches, prop={
        "size": "x-small"}, bbox_to_anchor=(0.9, 0.9), loc=2)
    return fig


def plot_band_number_distribution(df, stem="", glb_context=-1, title=""):
    """Construct a bar plot with the number of possible bands for each of the sources."""
    allowed_bands = [
        f"mag_{band}" for band in mt.give_bands_for_context(glb_context)]
    band_count_df = construct_num_band_dataframe(df, allowed_bands)
    fig, ax = plt.subplots(1, 1, figsize=cm.set_figsize(fraction=.8))
    ax.grid(True, axis="y")
    labels = list(band_count_df.index)
    x = np.arange(len(labels))
    width = 0.6  # the width of the bars
    rects1 = ax.bar(
        x, band_count_df["without_z"], width, color="g", bottom=band_count_df["with_z"], label=f"Without spec-$z$ ({band_count_df['without_z'].sum()})", edgecolor="k", alpha=0.7)
    rects2 = ax.bar(
        x, band_count_df["with_z"], width, label=f"With spec-$z$ ({band_count_df['with_z'].sum()})", color="k", edgecolor="k", alpha=0.7)
    ax.legend()
    if title != "":
        title = "Number of bands available for the sources in the eFEDS field" if title == "default" else title
        ax.set_title(title)
    ax.set_xlabel("Number of bands with photometry available")
    ax.set_ylabel("Number of sources")
    ax.set_xticks(x)
    ax.set_xlim(4, max(x) + 1)
    cm.save_figure(fig, "band_number_distribution", "input_analysis", stem)
