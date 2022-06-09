# -*- coding: utf-8 -*-
"""
Created on Fri Feb 18 13:40:36 2022

@author: fabian_balzer
"""
# %%

import os
from shutil import move

import util.my_tools as mt
from input_scripts.input_plot_container import InputPlotContainer
from output_scripts.output_plot_container import OutputPlotContainer
from util.assert_config import assert_all

# %%


def assemble_catalog():
    """Runs the jython script to match the input files."""
    mt.run_jystilts_program("match_tables.py")
    mt.LOGGER.debug(
        "Successfully ran the jython program to match and write the tables.")


def run_filters():
    """Runs the LePhare filter routine with the requested settings"""
    arg_dict = {"c": mt.give_parafile_fpath(),
                "FILTER_REP": f"{mt.GEN_CONFIG['PATHS']['params']}filters",
                "FILTER_FILE": mt.CUR_CONFIG["LEPHARE"]["filter_stem"]}
    additional = ">" + mt.give_filterfile_fpath()
    mt.run_lephare_command("filter", arg_dict, additional)


def run_templates(ttype):
    """Runs the LePhare template routine with the requested settings"""
    if not mt.assert_file_overwrite(mt.give_temp_libname(ttype, "mag", suffix=".dat")):
        mt.LOGGER.info("Skipping the template run for %s.", ttype)
        return
    prefix = "STAR" if ttype == "star" else "GAL"
    arg_dict_sed = {"c": mt.give_parafile_fpath(),
                    f"{prefix}_SED": mt.give_temp_listname(ttype),
                    f"{prefix}_LIB": mt.give_temp_libname(ttype, "sed", include_path=False)}
    arg_dict_sed["t"] = "S" if ttype == "star" else "G"
    mt.run_lephare_command("sedtolib", arg_dict_sed)
    arg_dict_mag = {"c": mt.give_parafile_fpath(),
                    f"{prefix}_LIB_IN": mt.give_temp_libname(ttype, "sed", include_path=False),
                    f"{prefix}_LIB_OUT": mt.give_temp_libname(ttype, "mag", include_path=False),
                    "EM_LINES": "NO",
                    "LIB_ASCII": "YES",
                    "FILTER_FILE": mt.CUR_CONFIG["LEPHARE"]["filter_stem"]}
    arg_dict_mag["t"] = "S" if ttype == "star" else "G"
    if ttype == "pointlike":
        arg_dict_mag["EXTINC_LAW"] = "SMC_prevot.dat"
        arg_dict_mag["MOD_EXTINC"] = "11,23"
        arg_dict_mag["EB_V"] = "0.,0.05,0.1,0.15,0.2,0.25,0.3,0.35,0.4"
    mt.run_lephare_command("mag_gal", arg_dict_mag)
    try:
        # LePhare writes the output file in the same directory, so we need to move it:
        move(mt.give_temp_libname(ttype, "mag", use_workpath=True, suffix=".dat"),
             mt.give_temp_libname(ttype, "mag", suffix=".dat"))
        mt.run_jystilts_program("rewrite_fits_header.py", ttype, "MAG")
    except OSError:
        mt.LOGGER.error(
            "Something went wrong trying to move the ASCII magnitude files.")


def run_zphota(ttype):
    """Runs the LePhare zphota routine with the requested settings"""
    if not mt.assert_file_overwrite(mt.give_lephare_filename(ttype, out=True)):
        mt.LOGGER.info("Skipping the zphota run for %s.", ttype)
        return
    star_lib = mt.give_temp_libname('star', include_path=False) if os.path.isfile(
        mt.give_temp_libname('star')) else "baseline_star_mag_lib"
    arg_dict_sed = {"c": mt.give_parafile_fpath(),
                    "ZPHOTLIB": f"{mt.give_temp_libname(ttype, include_path=False)},{star_lib}",
                    "CAT_IN": mt.give_lephare_filename(ttype),
                    "CAT_OUT": mt.give_lephare_filename(ttype, out=True),
                    "PARA_OUT": mt.give_parafile_fpath(out=True),
                    "GLB_CONTEXT": mt.CONTEXT,
                    "PDZ_OUT": mt.give_lephare_filename(ttype, out=True, suffix="")
                    }
    if ttype == "pointlike":
        arg_dict_sed["MAG_REF"] = "7"
        arg_dict_sed["MAG_ABS"] = "-30,-20"
        # arg_dict_sed["APPLY_SYSSHIFT"] = "-0.2837,-0.1676,-0.0306,-0.0604,-0.0427,-0.0000,0.0304,0.0801,0.0240,-0.0225,0.0626,0.2107,-0.3830,0.0786,0.0394,-0.0746,-0.0785"
    if ttype == "extended":
        arg_dict_sed["MAG_REF"] = "7"
        arg_dict_sed["MAG_ABS"] = "-24,-8"
        # arg_dict_sed["APPLY_SYSSHIFT"] = "-0.2099,-0.1264,0.0228,-0.1534,-0.1234,-0.1437,-0.1797,-0.5375,-0.3046,-0.2395,-0.2261,-0.0718,0.0000,0.0000,-0.0294,-0.0755,-0.1896"
    mt.run_lephare_command("zphota", arg_dict_sed)
    mt.run_jystilts_program("rewrite_fits_header.py", ttype, "OUT")
    mt.assess_lephare_run(ttype)


def run_lephare_commands():
    """Runs the requested LePhare commands specified in the current config file."""
    lep_con = mt.CUR_CONFIG["LEPHARE"]
    if lep_con.getboolean("run_filters"):
        run_filters()

    if lep_con.getboolean("run_templates"):
        for ttype in mt.USED_TTYPES:
            run_templates(ttype)
        if os.path.isfile(mt.give_temp_listname("star")):
            run_templates("star")

    if lep_con.getboolean("run_zphota"):
        for ttype in mt.USED_TTYPES:
            run_zphota(ttype)
    mt.LOGGER.debug("Finished the LePhare commands")


if __name__ == "__main__":
    mt.log_run_info()
    assert_all()

    if mt.CUR_CONFIG["CAT_ASSEMBLY"].getboolean("assemble_cat"):
        assemble_catalog()

    run_lephare_commands()

    # Input-related plots:
    input_plot_container = InputPlotContainer(True)

    # Output-related plots:
    output_plot_containter = OutputPlotContainer(True)

    if mt.CUR_CONFIG["PLOTTING"].getboolean("output"):
        output_plot_containter.plot_specz_photo_z()
        output_plot_containter.plot_template_numbers()

    if mt.CUR_CONFIG["PLOTTING"].getboolean("template"):
        output_plot_containter.plot_color_vs_redshift("g", "r")

    # # %%
    # # Construct the input dataframe:
    # input_df = mt.read_plike_and_ext(prefix="matches/test2_",
    #                                  suffix="_processed_table.fits")
    # input_df = mt.add_mag_columns(input_df)
    # # av.plot_r_band_magnitude(df)
    # av.plot_input_distribution(input_df)

    # # %% Filter analysis:
    # filter_df = fc.read_filter_info_file()
    # fc.produce_filter_plot(filter_df)
    # info_df = fc.read_filter_overview_file()
    # fc.save_filter_info(info_df)
