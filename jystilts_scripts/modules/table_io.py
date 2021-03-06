import os
from sys import path as p

import stilts

import jy_tools as jt

p.append("C:/Program Files/Jystilts/stilts.jar")


# %% Reading and cleaning the tables before matching
def read_table(name):
    """Returns a stilts table of the first .fits file in the jt.CATPATH/name
    folder (sweep is different)"""
    if name == "sweep":
        tables = []
        dirname = jt.CATPATH + "sweep"
        for filename in os.listdir(dirname):
            table = stilts.tread(jt.CATPATH + "sweep" +
                                 "/" + filename, fmt="fits")
            tables.append(table)
        table = tables[0]
        for t in tables[1:]:
            table += t
    else:  # Just take the first file of each directory
        filename = os.listdir(jt.CATPATH + name)[0]
        table = stilts.tread(jt.CATPATH + name + "/" + filename, fmt="fits")
    return table


def pre_clean_table(name, table):
    """Cleans a table depending on its name. These cleaning steps do not involve
    any processing, only the selection of the relevant colums."""
    funcs = {"vhs": clean_vhs, "eros": clean_eros,
             "opt_agn": clean_opt_agn, "sweep": clean_sweep, "hsc": clean_hsc,
             "kids": clean_kids, "xray_agn": clean_xray_agn,
             "ls10": clean_ls10}
    return funcs[name](table)


# %% Table-specific cleaning functions
def clean_vhs(table):
    """Cleans the vhs table by selecting primary sources and the relevant columns."""
    columnlist = ["ra", "dec", "pstar", "pgalaxy", "psf", "ebv"]
    for band in jt.VHS_BANDS:
        columnlist.append(band + "petromag")
        columnlist.append(band + "petromagerr")
        columnlist.append(band + "apermag6")
        columnlist.append(band + "apermag6err")
        columnlist.append(band + "apermag4")
        columnlist.append(band + "apermag4err")
        columnlist.append("a" + band)
    table = jt.keep_columns(table, columnlist)
    return table


def clean_kids(table):
    """Cleans the kids table by removing any flagged i band sources
    primary sources and renaming the relevant columns."""
    # Select primary sources
    table = jt.change_colnames(
        table,
        ["raj2000", "decj2000", "class_star", "Z_B", "ODDS",
         "MAG_GAAP_i", "MAGERR_GAAP_i", "EXTINCTION_i"],
        ["ra", "dec", "kids_class", "z_best_kids", "z_qual_kids",
         "mag_i_kids", "mag_err_i_kids", "ext_i", "flag_i"])
    return table


def clean_ls10(table):
    """Cleans the legacy survey dr10 table."""
    oldcols = ["ctp_ls8_ra", "ctp_ls8_dec", "LU_flux_i", "LU_flux_i_err"]
    newcols = ["ra", "dec", "c_flux_i_ls10", "c_flux_err_i_ls10"]
    table = jt.change_colnames(table, oldcols, newcols)
    table = jt.keep_columns(table, newcols)
    # oldcols = ["ctp_ls8_ra", "ctp_ls8_dec"]
    # newcols = ["ra", "dec"]
    # for band in ["i"]:  # +SWEEP_BANDS:
    #     oldcols.append("LU_flux_" + band)
    #     oldcols.append("LU_flux_" + band + "_err")
    #     newcols.append("c_flux_" + band)
    #     newcols.append("c_flux_err_" + band)
    # table = jt.change_colnames(table, oldcols, newcols)
    # table = table.cmd_keepcols(" ".join(newcols))
    return table


def clean_opt_agn(table):
    """Cleans the opt_agn table by selecting only the relevant columns."""
    discard_num = table.cmd_select("prob_rf < 0.94").count_rows()
    jt.LOGGER.info(
        "Discarding %s unreliable sources from the optical agn catalogue.", discard_num)
    table = table.cmd_select("prob_rf >= 0.94")
    selection = "dec < 6.2 & dec > -3.2 & ra < 146.2 & ra > 126"
    table = table.cmd_select(selection)
    columnlist = ["ra", "dec", "phot_z", "prob_rf"]  # , "phot_z", "gaia_sourceid", "prob_rf"
    table = jt.keep_columns(table, columnlist)
    table = jt.change_colnames(table, ["phot_z", "prob_rf"], ["opt_agn_phot_z", "opt_agn_prob_rf"])
    table = table.cmd_addcol("AGN_Sel", "1")
    return table


def clean_xray_agn(table):
    """Cleans the xray agn table by selecting only the relevant columns."""
    selection = "dec < 6.2 & dec > -3.2 & ra < 146.2 & ra > 126"
    table = table.cmd_select(selection)
    table = jt.change_colnames(
        table, ["CTP_LS8_RA", "CTP_LS8_DEC"], ["ra", "dec"])
    columnlist = ["ra", "dec"]  # CTP_quality, CTP_Redshift, CTP_Redshift_grade
    table = jt.keep_columns(table, columnlist)
    table = table.cmd_addcol("AGN_Sel", "2")
    return table


def clean_sweep(table):
    """Cleans the sweep table by selecting the relevant columns and by adding an ID column."""
    # Generate an ID column from the three identifiers 'RELEASE BRICKID OBJID' mashed together
    table = table.cmd_addcol("sweep_ident", 'concat(RELEASE, BRICKID, OBJID)')
    columnlist = ["ra", "dec", "ra_ivar", "dec_ivar",
                  "type", "ebv", "ref_cat", "ref_id", "sweep_ident", "maskbits", "fitbits"]
    for band in jt.SWEEP_BANDS:
        for prefix in ["flux_", "flux_ivar_", "mw_transmission_"]:
            columnlist.append(prefix + band)
    table = jt.keep_columns(table, columnlist)
    return table


def clean_assef(table):
    """Cleans the assef table by selecting targets with MOON-SAA_flag of 0 and dec < 10"""
    count = table.count_rows()
    # Discard sources of the northern hemisphere:
    table = table.cmd_select("DEC < 10")
    # Rule out objects from the SAA region:
    table = table.cmd_select("MOON-SAA_flag == 0")
    count2 = table.count_rows()
    # jt.LOGGER.info("Discarded %s objects in the SAA region." % (count - count2))
    # jt.LOGGER.info("There are %s objects in the assef table." % (count2))
    return table


def clean_hsc(table):
    """Cleans the hsc table by renaming the relevant columns."""
    table = table.cmd_select(
        "!i_cmodel_flux_isnull && !i_psfflux_flux_isnull")
    # We are discarding any flags for now.
    columnlist = ["ra", "dec", "i_psfflux_flux", "i_psfflux_fluxerr",
                  "i_cmodel_flux", "i_cmodel_fluxerr", "i_filterfraction_weighted", "a_i"]
    table = jt.keep_columns(table, columnlist)
    return table


def clean_eros(table):
    """Cleans the eros table by selecting only the relevant columns and changing the columnames to sensible names"""
    table = jt.change_colnames(table, ["specz_redshift"], ["ZSPEC"])
    table = jt.change_colnames(table, ["specz_normq"], ["ZSPEC_QUAL"])
    table = jt.change_colnames(table, ["ctp_ls8_ra", "ctp_ls8_dec"], [
        "ra_eros", "dec_eros"])
    columnlist = ["ctp_quality", "ra_eros", "dec_eros",
                  "ctp_redshift", "ctp_redshift_grade", "zspec", "zspec_qual"]
    table = jt.keep_columns(table, columnlist)
    # Somehow, there are some troubling strings in here
    table = table.cmd_replaceval('', '-99.', "ZSPEC")
    return table


# %% Matching

def log_match_number(table, cat):
    """Handy loger for showing the number of sources matched"""
    match_num = table.cmd_select("!NULL_dec_" + cat).count_rows()
    jt.LOGGER.info(
        "There are %s sources in the eFEDS area matched to the %s data.", match_num, cat)


def match_given_tables(table_dict):
    """Performs the necessary matching while keeping all objects from the optical agn/sweep catalogue.
    Matches to all tables provided in table_list, but the optical agn as a default.
    Also filters irrelevant columns from the tables and puts them in a nice order"""
    funcs = {"vhs": [match_table_vhs, 0.5],
             "eros": [match_table_eros, 0.1],
             "hsc": [match_table_hsc, 0.25],
             "galex": [match_table_galex, 3.5],
             "kids": [match_table_kids, 1.5],
             "ls10": [match_table_ls10, 0.1]}
    table = match_opt_agn_sweep(
        table_dict["opt_agn"], table_dict["sweep"], 0.1)
    for name, func in funcs.items():
        try:
            matching_func = func[0]
            radius = func[1]
            if name == "galex":
                table = matching_func(table, radius)
            else:
                table = matching_func(table, table_dict[name], radius)
        except KeyError:
            pass
    return table


def match_opt_agn_sweep(opt_agn, sweep, radius=1):
    """Skymatches the given tables and changes the columnames"""
    # Exclusive join with the sweep catalogue
    table = stilts.tskymatch2(in1=opt_agn, in2=sweep,
                              error=radius, find="best")
    table = jt.change_colnames(table, ["ra_1", "ra_2", "dec_1", "dec_2"], [
        "ra_opt_agn", "ra", "dec_opt_agn", "dec"])
    log_match_number(table, "opt_agn")
    return table


def match_table_galex(table, radius=3):
    """Skymatches the given table with the Galex catalogue from ViZier and changes the columnames.
    The dummy parameter is needed so it follows the pattern of the other matching funcs."""
    prev_columns = [str(column.name).upper() for column in table.columns()]
    # inclusive join with the galex catalogue
    sourcetable = "II/335/galex_ais"
    table = stilts.cdsskymatch(
        cdstable=sourcetable, ra="ra", dec="dec", in_=table, radius=radius, find="each")
    new_columns = prev_columns + \
        ["Fflux", "e_Fflux", "Nflux", "e_Nflux",
            "Prob", "E(B-V)", "RAJ2000", "DEJ2000", "Prob"]
    # Only keep columns of interest
    table = jt.keep_columns(table, new_columns)
    table = jt.change_colnames(table, ["E(B-V)", "RAJ2000", "DEJ2000", "Prob"], [
                               "EBV_Galex", "ra_galex", "dec_galex", "galex_matchprob"])
    log_match_number(table, "galex")
    return table


def match_table_kids(table, kidstable, radius=3):
    """Skymatches the given table with the kids catalogue from ViZier and changes the columnames"""
    table = stilts.tskymatch2(
        in1=table, in2=kidstable, dec1="dec", ra1="ra", error=radius, find="best", join="all1")
    table = jt.change_colnames(table, ["ra_1", "ra_2", "dec_1", "dec_2"], [
        "ra", "ra_kids", "dec", "dec_kids"])
    log_match_number(table, "kids")
    # prev_columns = [column.name.upper() for column in table.columns()]
    # # inclusive join with the kids catalogue on the CDS servers
    # sourcetable = "II/347/kids_dr3"
    # table = stilts.cdsskymatch(
    #     cdstable=sourcetable, ra="ra", dec="dec", in_=table, radius=radius, find="each")
    # new_columns = prev_columns + \
    #     ["iflg", "imag", "e_imag", "RAdeg", "DEdeg"]
    # # Only keep columns of interest
    # table = table.cmd_keepcols(" ".join(new_columns))
    # table = jt.change_colnames(
    #     table, ["RAdeg", "DEdeg", "iflg"], ["ra_kids", "dec_kids", "flag_i"])
    return table


def match_table_ls10(table, ls_table, radius=0.1):
    """Skymatches the given tables and changes the columnames"""
    # Exclusive join with the sweep catalogue
    table = stilts.tskymatch2(in1=table, in2=ls_table,
                              error=radius, find="best", join="all1")
    table = jt.change_colnames(table, ["ra_1", "ra_2", "dec_1", "dec_2"], [
        "ra", "ra_ls10", "dec", "dec_ls10"])
    log_match_number(table, "ls10")
    return table


def match_table_vhs(table, vhs, radius=0.5):
    """Skymatches the given tables and changes the columnames accordingly"""
    # Join with the VHS photometry (all1)
    table = stilts.tskymatch2(
        in1=table, in2=vhs, dec1="dec", ra1="ra", error=radius, find="best", join="all1")
    table = jt.change_colnames(table, ["ra_1", "ra_2", "dec_1", "dec_2"], [
        "ra", "ra_vhs", "dec", "dec_vhs"])
    log_match_number(table, "vhs")
    return table


def match_table_hsc(table, hsc, radius=1):
    """Skymatches the given tables and changes the columnames accordingly"""
    # Join with the VHS photometry (all1)
    jt.LOGGER.info("Table length before matching with hsc: %s",
                   str(table.count_rows()))
    table = stilts.tskymatch2(
        in1=table, in2=hsc, dec1="dec", ra1="ra", error=radius, find="best", join="all1")
    table = jt.change_colnames(table, ["ra_1", "ra_2", "dec_1", "dec_2"], [
        "ra", "ra_hsc", "dec", "dec_hsc"])
    log_match_number(table, "hsc")
    return table


def match_table_eros(table, eros, radius=1):
    """Skymatches the given tables and changes the columnames accordingly"""
    # Join with the eros data for spectroscopy
    table = stilts.tskymatch2(in1=table, in2=eros, dec1="dec", ra1="ra", error=radius,
                              find="best", join="all1", ra2="ra_eros", dec2="dec_eros")
    log_match_number(table, "eros")
    return table


# %% Cleaning the columns after matching:
def add_separation_columns(table):
    """Adds columns documenting the separation to the given other tables."""
    names = ["vhs", "galex", "eros", "ls10", "hsc", "kids"]
    for other_table in names:
        for coord in ["ra", "dec"]:
            colname = coord + "_" + other_table  # i. e. ra_eros
            try:
                is_rad = table.cmd_keepcols(colname).cmd_meta().cmd_keepcols('units')[
                    0][0].lower() == "radians"
            except:
                # unfortunately, this can produce some weird kind of Java.io-Error so I can't properly catch it...
                is_rad = False
            if is_rad:
                corr_expr = "radiansToDegrees(" + colname + ")"
                table = table.cmd_replacecol(
                    colname, corr_expr, "-units deg")
                jt.LOGGER.debug("Converted %s to degrees.", colname)
            expr = colname + " - " + coord
            name = "delta_" + colname
            table = table.cmd_addcol(name, expr, "-units deg")
        sep_exp = "sqrt(pow(delta_ra_" + other_table + \
            ", 2) + pow(delta_dec_" + other_table + ", 2))"
        name2 = "sep_to_" + other_table
        table = table.cmd_addcol(name2, sep_exp, "-units deg")
    return table


def process_table(table):
    """Performs some processing steps on the tables that are provided.
        galex fluxes are corrected for EBV
        pointlike and extended sources are split by type
        vhs fluxes are changed with respect to the aperture type
    """
    # Calculate the proper sweep columns
    for band in jt.SWEEP_BANDS:
        table = calculate_sweep_column(table, band)
    table = correct_galex_fluxes(table)
    table = correct_kids_fluxes(table)
    pointlike, extended = split_by_type(table)
    pointlike, extended = correct_hsc_flux(pointlike, extended)
    pointlike, extended = convert_vega_mag_to_flux(pointlike, extended)
    return pointlike, extended


def calculate_sweep_column(table, band):
    """Add a column to the table correcting the sweep fluxes for the MW_TRANSMISSION.
    Errors are calculated by taking the inverse variance.
    Convert from nanomaggie to erg/cm**2/Hz/s by multiplying with 3631*10**(-23)*10**(-9).
    """
    oldname, newname = "flux_" + band, "c_flux_" + band
    e_oldname, e_newname = "flux_ivar_" + band, "c_flux_err_" + band
    mwname = "MW_TRANSMISSION_" + band
    # Correct for transmission, i. e. MW_TRANSMISSION_W1 > 0 ? flux_W1 / MW_TRANSMISSION_W1 * 3.631 * pow(10, -29) : -99.
    expr = mwname + ' > 0 ? ' + oldname + ' / ' + \
        mwname + ' * 3.631 * pow(10, -29) : -99.'
    # Calculate the error
    e_expr = mwname + ' > 0 && ' + e_oldname + \
        ' > 0 ? 1/sqrt(' + e_oldname + ') / ' + mwname + \
        '  * 3.631 * pow(10, -29): -99.'

    # Add the new columns by using the expressions
    table = table.cmd_addcol(newname, expr, "-after " +
                             e_oldname + " -units ergs/(cm**2*Hz*s)")
    table = table.cmd_addcol(
        e_newname, e_expr, "-after " + newname + " -units ergs/(cm**2*Hz*s)")
    # table = table.cmd_delcols(mwname)
    return table


def correct_galex_fluxes(table):
    """Corrects the GALEX NUV and FUV fluxes by using the suggested prescription of
    A_FUV = 8.06 * EBV_Galex and A_NUV = 7.95 * EBV_Galex as correction magnitudes, giving
    a flux correction of F_real = F_mes*10**(-A).
    As the flux is given in 10**(-6)Jy, we multiply it by 10**(-29)."""
    for shortcut, band, value in zip(["F", "N"], ["FUV", "NUV"], [8.06, 7.95]):
        mag_err = "e_" + band + "mag"
        c_flux = "c_flux_" + band
        c_flux_err = "c_flux_err_" + band
        flux = shortcut + "flux"
        flux_err = "e_" + shortcut + "flux"
        # Expression for correcting flux
        flux_corr_expr = 'NULL_' + flux + ' ? -99 : ' + flux + \
            ' * pow(10, ' + str(value) + ' * EBV_Galex/2.5 - 29)'
        flux_err_corr_expr = 'NULL_' + flux + \
            ' ? -99. : ' + flux_err + \
            ' * pow(10, ' + str(value) + ' * EBV_Galex/2.5 - 29)'

        table = table.cmd_addcol(c_flux, flux_corr_expr, "-after " +
                                 mag_err + " -units ergs/(cm**2*Hz*s)")  # Add corrected flux
        table = table.cmd_addcol(c_flux_err, flux_err_corr_expr, "-after " +
                                 c_flux + " -units ergs/(cm**2*Hz*s)")  # Corrected flux
    return table


def correct_kids_fluxes(table):
    """Converts the KiDS magnitudes to fluxes and corrects for extinction"""
    c_flux = "c_flux_i_kids"
    c_flux_err = "c_flux_err_i_kids"
    # Expression for calculating the conversion
    flux_corr_expr = "mag_i_kids > 0 ? pow(10, -0.4*(mag_i_kids + 48.6)) : -99."
    flux_err_corr_expr = "mag_i_kids > 0 ? pow(10, -0.4*(mag_err_i_kids + 48.6))*mag_i_kids*ln(10)*0.4 : -99."

    table = table.cmd_addcol(c_flux, flux_corr_expr, "-after " +
                             "mag_err_i_kids" + " -units ergs/(cm**2*Hz*s)")  # Add corrected flux
    table = table.cmd_addcol(c_flux_err, flux_err_corr_expr, "-after " +
                             c_flux + " -units ergs/(cm**2*Hz*s)")  # Corrected flux
    return table


def split_by_type(table):
    """Splits the given table into two subsets of point-like and extended sources and
    deletes irrelevant (vhs) columns."""
    # We treat sources with pgal < 0.5 as point-like and need 2''8 (aperMag4) photometry
    pointlike = table.cmd_select('TYPE == "PSF"').cmd_delcols(
        " ".join([band + "AperMag6 " + band + "AperMag6Err" for band in jt.VHS_BANDS]))
    extended = table.cmd_select('TYPE != "PSF"').cmd_delcols(
        " ".join([band + "AperMag4 " + band + "AperMag4Err" for band in jt.VHS_BANDS]))
    return pointlike, extended


def correct_hsc_flux(pointlike, extended):
    """Correct the hsc flux: Take psf for pointlike and cmodel for extended sources.
    Also, split the i band data into two relevant categories i and i2.
    Also also, convert from nJy to cgs (1 nJy = 10**(-9) Jy = 10**(-9-23) ergs/s/Hz/cm**2)"""
    for colname in ["i_psfflux_flux", "i_psfflux_fluxerr", "i_cmodel_flux", "i_cmodel_fluxerr"]:
        pointlike = pointlike.cmd_replacecol(
            colname, colname + "*pow(10, -32)")
        extended = extended.cmd_replacecol(colname, colname + "*pow(10, -32)")

    pointlike = pointlike.cmd_delcols("i_cmodel_flux i_cmodel_fluxerr")
    pointlike = jt.change_colnames(pointlike, ["i_psfflux_flux", "i_psfflux_fluxerr"], [
        "c_flux_i_hsc", "c_flux_err_i_hsc"])
    pointlike = introduce_filter_weights(pointlike)

    extended = extended.cmd_delcols("i_psfflux_flux i_psfflux_fluxerr")
    extended = jt.change_colnames(extended, ["i_cmodel_flux", "i_cmodel_fluxerr"], [
        "c_flux_i_hsc", "c_flux_err_i_hsc"])
    extended = introduce_filter_weights(extended)
    return pointlike, extended


def introduce_filter_weights(hsctable):
    """Adds columns for i and i2 depending on the filterfraction provided."""
    hsctable = hsctable.cmd_addcol(
        "c_flux_i2_hsc", "i_filterfraction_weighted >= 0.75 ? c_flux_i_hsc : -99.")
    hsctable = hsctable.cmd_addcol(
        "c_flux_err_i2_hsc", "i_filterfraction_weighted >= 0.75 ? c_flux_err_i_hsc : -99.")
    hsctable = hsctable.cmd_replacecol(
        "c_flux_i_hsc", "i_filterfraction_weighted <= 0.25 ? c_flux_i_hsc : -99.")
    hsctable = hsctable.cmd_replacecol(
        "c_flux_err_i_hsc", "i_filterfraction_weighted <= 0.25 ? c_flux_err_i_hsc : -99.")
    return hsctable


def convert_vega_mag_to_flux(point, extended):
    """Coming from a column with name magcolname, convert its values from the vega
    to AB system and add a column with the corresponding flux (and errors) in ergs/(cm**2*Hz*s)"""
    for table, sourcetype in zip([point, extended], ["4", "6"]):  # Use AperMag4 for pointlike, AperMag6 for extended sources
        for band in jt.VHS_BANDS:
            ab_corr = jt.VEGA_AB_DICT[band]
            aper_mag = band + "AperMag" + sourcetype
            aper_mag_err = aper_mag + "Err"
            dust_corr = "a" + band
            c_mag = "c_mag_" + band
            c_mag_err = "c_mag_err_" + band
            c_flux = "c_flux_" + band
            c_flux_err = "c_flux_err_" + band
            # Expression for correcting magnitude
            mag_corr_expr = '%s > 0 && %s > 0 ? %s + %s + %s : -99.' % (
                aper_mag, dust_corr, aper_mag, ab_corr, dust_corr)
            mag_err_corr_expr = '%s > 0 && %s > 0 ? %s + %s + %s : -99.' % (
                aper_mag, dust_corr, aper_mag_err, ab_corr, dust_corr)
            table = table.cmd_addcol(
                c_mag, mag_corr_expr, "-after " + aper_mag_err + " -units mag")  # Add AB mag
            # AB mag error is the same
            table = table.cmd_addcol(
                c_mag_err, mag_err_corr_expr, "-after " + c_mag + " -units mag")

            # Expression for converting to Flux
            flux_expr = '%s > 0 ? pow(10, -(%s + 48.6)/2.5) : -99.' % (c_mag, c_mag)
            flux_err_expr = '%s > 0 ? pow(10, -(%s + 48.6)/2.5) * %s * ln(10)/2.5 : -99.' % (
                c_mag, c_mag, c_mag_err)
            table = table.cmd_addcol(
                c_flux, flux_expr, "-after " + c_mag_err + " -units ergs/(cm**2*Hz*s)")
            table = table.cmd_addcol(
                c_flux_err, flux_err_expr, "-after " + c_flux + " -units ergs/(cm**2*Hz*s)")
        if sourcetype == "4":
            point = table
        else:
            extended = table
    return point, extended


# %% Prepare the table for being written

def discard_problematic_matches(table):
    """Remove any matches that are too far out (adopting a circle around the systematic centre of the offsets).
    In addition to that, an Identifier column is added."""
    table = table.cmd_addcol("IDENT", "toInteger($index)")
    # We want to use the medians as center points, and the stds as offsets
    for cat in ["vhs", "galex"]:
        cols_to_keep = "delta_ra_" + cat + " delta_dec_" + cat
        stats = table.cmd_keepcols(cols_to_keep).cmd_stats("Median")
        ra_med = stats.getCell(0, 0)
        ra_expr = "delta_ra_" + cat + " - " + str(ra_med)
        table = table.cmd_addcol("new_delta_ra_" + cat, ra_expr)
        dec_med = stats.getCell(1, 0)
        dec_expr = "delta_dec_" + cat + " - " + str(dec_med)
        table = table.cmd_addcol("new_delta_dec_" + cat, dec_expr)
        sep_expr = "sqrt(pow(new_delta_ra_" + cat + \
            ", 2) + pow(new_delta_dec_" + cat + ", 2))"
        table = table.cmd_addcol("true_sep_" + cat, sep_expr, "-units deg")
        # Filter out anything that is at > 3 times the standard deviation
        stdev = table.cmd_keepcols(
            "true_sep_" + cat).cmd_stats("StDev").getCell(0, 0)
        # Set the values with true_sep > 3*stdev to -99. so they aren't considered:
        for band in jt.BAND_DICT[cat]:
            expr = "true_sep_" + cat + " < " + \
                str(3 * stdev) + " ? c_flux_" + band + " : -99."
            table = table.cmd_replacecol("c_flux_" + band, expr)
            err_expr = "true_sep_" + cat + " < " + \
                str(3 * stdev) + " ? c_flux_err_" + band + " : -99."
            table = table.cmd_replacecol("c_flux_err_" + band, err_expr)
    return table


def calculate_context(bands, excluded_bands):
    """Calculates the context provided to LePhare"""
    return -1 if (len(excluded_bands) == 0) else \
        sum([2**i for i, band in enumerate(bands)
             if band not in excluded_bands])


def process_for_lephare(table):
    """Returns a table only containing SWEEP ra and dec and then, in
    alternating fashion, flux and flux error for each of the requested bands (in the order given by BAND_LIST), followed by the ZSPEC column.
    """
    z_corr_expr = 'zspec_qual == 3 & ZSPEC > 0.002 ? ZSPEC : -99.'  # Because of problems with the E-4-representation, we leave out very nearby objects. Perhaps there might be a more elegant way.
    table = table.cmd_replacecol(
        "ZSPEC", z_corr_expr)  # Filter away bad spec_z
    table = table.cmd_replaceval('null', '-99.', 'ZSPEC')
    # Put them in the right order
    # jt.LOGGER.info("FILTER_LIST " +
    #       ",".join([FILTER_NAME_DICT[band] for band in bands]))
    col_list = ["IDENT"]
    newnames = ["IDENT"]
    for band in jt.BAND_LIST:
        col_list.append("c_flux_" + band)
        col_list.append("c_flux_err_" + band)
        newnames.append(band)
        newnames.append(band + "_err")
    for infocol in ["CONTEXT", "ZSPEC", "String"]:
        col_list.append(infocol)
        newnames.append(infocol)
    table = table.cmd_addcol("CONTEXT", str(-1))
    # TODO: change so important columns are carried with this
    table = table.cmd_addcol(
        "STRING", 'join(" ", toString(ra), toString(dec), toString(ctp_redshift_grade), toString(zspec_qual))')
    table = table.cmd_keepcols(" ".join(col_list))
    table = jt.change_colnames(table, col_list, newnames)
    # Replace any null values with -99. as they otherwise cause problems for LePhare:
    for colname in newnames:
        if table.cmd_keepcols(colname).cmd_meta().cmd_keepcols('Class')[0][0] == "Double":
            expr = 'NULL_' + colname + ' ? -99. : ' + colname
            table = table.cmd_replacecol(colname, expr)
    return table


def filter_for_testing(table):
    """If requested, filters the table to only include rows where ZSPEC is properly given."""
    if jt.CUR_CONFIG.getboolean("CAT_ASSEMBLY", "reduce_to_specz"):
        nrows_before = table.count_rows()
        nrows_eros = table.cmd_select("!NULL_DEC_Eros").count_rows()
        jt.LOGGER.debug("%s rows before filtering", nrows_before)
        jt.LOGGER.debug("%s rows with eros data", nrows_eros)
        table = table.cmd_select("ZSPEC > 0")
        nrows, ngood = table.count_rows(), table.cmd_select("zspec_qual == 3").count_rows()
        jt.LOGGER.debug("%s rows after filtering.", nrows)
        jt.LOGGER.debug("%s of these have a good spec redshift grade.", ngood)
        table = table.cmd_select("zspec_qual == 3")
        discard = nrows_before - table.count_rows()
        jt.LOGGER.info(
            "Discarding %s of %s sources without good spec-z.", discard, nrows_before)
    return table


# %% Deprecated functions
# def match_opt_agn_sweep_by_id(opt_agn, sweep):
#     """Tries to match the opt_agn and sweep table based on the GAIA source ID."""
#     # Select all sources in sweep that have a Gaia Source ID
#     # it is important that G2 is in "".
#     proper_sweep = sweep.cmd_select('equalsIgnoreCase(REF_CAT, "G2")')
#     # opt_agn = opt_agn.cmd_colmeta('-name', 'REF_ID', "Gaia_sourceid")  # Change the name of the id column (not needed, but might be handy)
#     opt_agn_sweep_1 = stilts.tmatch2(in1=opt_agn, in2=proper_sweep, find="best",
#                                      matcher="exact", values1="Gaia_sourceid", values2="REF_ID")
#     jt.LOGGER.info("Matched %i files with the same gaia source id" %
#                    opt_agn_sweep_1.count_rows())
#     # The ID will be present in 'REF_ID'.
#     return opt_agn_sweep_1.cmd_delcols("Gaia_sourceid")


# def read_output_and_save_to_fits():
#     """Search for any .out files in the TESTPATH directory and save them as
#     a .fits file in the workpath directory."""
#     fnames = [fname for fname in os.listdir(
#         TESTPATH) if fname.endswith(".out")]
#     jt.LOGGER.info("Converting the following files:")
#     jt.LOGGER.info(fnames)
#     for fname in fnames:
#         table = stilts.tread(TESTPATH + fname, fmt="ASCII")
#         # create a new filename with correct extension
#         newname = os.path.splitext(fname)[0] + ".fits"
#         table.write(WORKPATH + "data/" + newname, fmt="fits")
#         jt.LOGGER.info(newname + " has been written to " + WORKPATH + "data")


# def write_testing_table(table, ttype, stem, ofmt="ASCII"):
#     """Writes the table of type ttype to the test stempath"""
#     path = + stem + "/" + ttype + "_" + stem + ".in"
#     table.write(path, fmt=ofmt)
#     jt.LOGGER.info("Successfully wrote a matched table to %s" % path)
