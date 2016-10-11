#usr/bin/env python
# -*- coding: utf-8 -*-
"""Create hydrological contour maps for http://www.wenfo.org/apwm/

This module reads data from NetCDF files, the output from the APWM model,
and creates a number of hydrological contour maps.  It is limited in scope
to finding data within the supplied and structured input dir, processing it,
and saving maps to a specified output dir.

Generation of the data and uploads to the website are handled by other tools.
(see https://github.com/ANU-WALD/job-scheduler).  As of 2016-10-11, the script
can be run under the xc0 group's "apwm-plotmap" conda environment.
("conda create -n apwm-plotmap numpy matplotlib scipy basemap python=3")
"""
#pylint:disable=invalid-name,no-member,logging-format-interpolation
# Standard library imports
import argparse
import datetime
import glob
import logging
import os

# Scientific imports
import numpy as np
import matplotlib
matplotlib.use('AGG') # for Raijin, which doesn't have tk/Tcl renderer
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
from scipy.io.netcdf import netcdf_file

# Global constants
TODAY = datetime.date.today()
log = logging.getLogger()

VARIABLES = {
    'E0': 'Potential Evapotranspiration',
    'Etot': 'Actual Evapotranspiration',
    'Pg': 'Precipitation',
    'Qtot': 'Streamflow',
    'Ssnow': 'Snow Water Depth',
    'Stot': 'Catchment Water Storage'
    }

ALL_VARS = tuple('{}_{}'.format(abbr, kind)
                 for kind in ('anom', 'daily', 'decile', 'meanv', 'percent')
                 for abbr in VARIABLES)

ALL_MAPS = tuple((var, t) for t in ('d1', 'd30') for var in ALL_VARS
                 if not (t == 'd1' and 'meanv' in var) or
                 (t == 'd30' and 'daily' in var))


class MapStyles(object):
    """Class holding graph style information for APWM charts."""
    #pylint:disable=too-many-instance-attributes

    DATA_FORMATS = {
        # Categories and no-data values for each data set.
        tuple('{}_decile'.format(s) for s in VARIABLES): {
            'values': [-1, 0, 1, 3, 7, 9, 10],
            'nanval': 4.0},
        tuple('{}_percent'.format(s) for s in VARIABLES): {
            'values': [0, 20, 40, 60, 80, 100, 125,
                       150, 200, 300, 400],
            'nanval': -0.1},
        ('E0_anom', 'Etot_anom'): {
            'values': [-2**31, -4, -2, -1, -0.5, -0.25,
                       -0.1, 0, 0.1, 0.25, 0.5, 1, 2, 4],
            'nanval': 0.001},
        ("E0_daily", "Etot_daily", "E0_meanv", "Etot_meanv"): {
            'values': [0, 0.02, 0.1, 0.2, 0.3, 0.5, 1, 2, 3, 4, 6, 8],
            'nanval': 0.0},
        ('Pg_anom', 'Qtot_anom'): {
            'values': [-2**31, -20, -10, -5, -2.5, -1.25,
                       -0.5, 0, 0.5, 1.25, 2.5, 5, 10, 20],
            'nanval': 0.001},
        ('Pg_daily', 'Pg_meanv', 'Qtot_daily', 'Qtot_meanv'): {
            'values': [0, 1, 5, 10, 15, 25, 50, 100, 150, 200, 300, 400],
            'nanval': 0},
        ('Ssnow_anom', 'Stot_anom'): {
            'values': [-2**31, -400, -200, -100, -50, -25, -10,
                       0, 10, 25, 50, 100, 200, 400],
            'nanval': 0.001},
        ('Ssnow_daily', 'Ssnow_meanv', 'Stot_daily', 'Stot_meanv'): {
            'values': [0, 2, 10, 20, 30, 50, 100, 200, 300, 400, 600, 800],
            'nanval': 0}
        }

    COLOR_SCHEMES = {
        # Colour scheme to use when plotting each dataset
        'anom': (
            (254, 51, 51), (254, 101, 101), (253, 152, 50), (253, 202, 101),
            (253, 253, 51), (254, 254, 203), (239, 239, 239), (254, 254, 254),
            (203, 254, 254), (151, 202, 252), (153, 153, 254), (203, 101, 253),
            (203, 50, 203), (153, 0, 204)),
        'daily&meanv': (
            (254, 254, 254), (254, 191, 87), (254, 172, 0), (254, 254, 0),
            (178, 254, 0), (76, 254, 0), (0, 228, 153), (0, 164, 254),
            (62, 62, 254), (178, 0, 254), (254, 0, 254), (254, 76, 155)),
        'decile': (
            (254, 25, 25), (254, 101, 101), (254, 203, 203), (254, 254, 254),
            (203, 203, 254), (101, 101, 254), (0, 0, 254)),
        'percent': (
            (203, 101, 50), (254, 101, 50), (253, 152, 50), (253, 203, 152),
            (254, 254, 203), (203, 253, 203), (101, 203, 101), (0, 152, 0),
            (102, 153, 253), (0, 0, 254), (101, 0, 153))
        }

    def __init__(self, var_name, timespan='d1'):
        """Sets up the object properties for each variable and timespan.

        The var_name is a string including the variable abbreviation and type,
        eg "E0_anom" or "Pg_decile".  The timespan is either "d1" for daily
        or "d30" for monthly data.
        """
        self.unit = ''
        assert var_name in ALL_VARS
        self.var_name = var_name
        abbr_type = var_name.strip().split('_')
        assert len(abbr_type) == 2
        self.var_abbr, self.var_type = abbr_type
        assert timespan in ('d1', 'd30')
        self.timespan = timespan
        self.subtitle = 'month ending ' if self.timespan == 'd30' else ' '
        types = {
            'anom': ('', 'Anomalies (mm)'),
            'daily': (' Total', '(mm)'),
            'decile': ('', 'Deciles'),
            'meanv': (' Mean',
                      '(mm per day)' if self.timespan == 'd30' else '(mm)'),
            'percent': ('', 'Percentages')
            }
        self.title = '{}{} {} {}'.format(
            'Monthly' if self.timespan == 'd30' else 'Daily',
            types[self.var_type][0],
            VARIABLES[self.var_abbr],
            types[self.var_type][1]
            )
        for key_tuple, metadata in self.DATA_FORMATS.items():
            if self.var_name in key_tuple:
                self.values = metadata['values'] + [2**31]
                self.nanval = metadata['nanval']
        var = self.var_type
        if self.var_type in ('daily', 'meanv'):
            var = 'daily&meanv'
        # The top colour doesn't display, so we add a dummy colour/value pair
        self.colors = self.COLOR_SCHEMES[var] + ((0, 0, 0),)
        assert len(self.colors) == len(self.values)

    def clean_data(self, data):
        """Performs some generic data cleanup - set nodata values correctly,
        clip data to the valid range, and extend data slightly to avoid missing
        data at some coastlines."""
        data[data == -9999] = np.nan
        data[data == self.nanval] = np.nan
        max_, min_ = max(self.values), min(self.values)
        data[data > max_] = max_
        data[data < min_] = min_
        for axis, shift in ((0, -1), (1, 1), (0, 1), (1, -1)):
            dropin = np.roll(data, shift, axis=axis)
            data = np.where(np.isnan(data), dropin, data)
        return data

    def formatter(self):
        """Formatter for the colorbar."""
        #pylint:disable=unused-argument
        def _decile_format(v, x):
            """Decile category descriptions are stored elsewhere."""
            return ''

        def _basic_format(v, x):
            """Basic formatter function."""
            if v == -2**31 or v == 2**31:
                return ''
            if v == max(self.values) or (
                    self.values[-1] == 2**31 and v == self.values[-2]):
                return '>{}'.format(v)
            if v == min(self.values) and v < 0 or (
                    self.values[0] == -2**31 and v == self.values[1]):
                return '<{}'.format(v)
            return str(v)

        def _percent_format(v, x):
            """Add percent sign ('%') to each label."""
            s = _basic_format(v, x)
            return s + ' %' if s else s

        if self.var_type == 'decile':
            return matplotlib.ticker.FuncFormatter(_decile_format)
        if self.var_type == 'percent':
            return matplotlib.ticker.FuncFormatter(_percent_format)
        return matplotlib.ticker.FuncFormatter(_basic_format)


def date_from_data_filename(fname):
    """Get the date of the data from it's filename."""
    return datetime.datetime.strptime(
        os.path.basename(fname)[:8], '%Y%m%d').date()

def parse_data_date():
    """Get the date or date range to seek data from, or specify latest
    available.

    Input is None, one date in ISO format, or two (colon-separated).
    The range is open-ended if the string starts or finishes with a colon.

    Outputs: None (latest data), one datetime.date instance, or a two-tuple
    of datetime.date instances with None for an open end.
    """
    if args.date is None:
        return None
    dates = args.date.split(':')
    for i, d in enumerate(dates):
        try:
            if not d:
                dates[i] = None
                continue
            dates[i] = datetime.datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            log.error('Date parse error, using open range or latest data')
            dates[i] = None
    if len(dates) == 1:
        return dates[0]
    return dates[:2]

def find_data(style, data_date):
    """Return a list of data files of the supplied style, within the time
    range given."""
    typedir = {
        'daily': 'actual',
        'anom': 'anomaly',
        'decile': 'decile',
        'percent': 'percent_of_average',
        'meanv': 'mean'
        }[style.var_type]
    files = sorted(glob.glob(os.path.join(
        args.inputdir,
        '1d' if style.timespan == 'd1' else '30d',
        typedir,
        style.var_abbr,
        '????????_{}.nc'.format(style.var_name))))
    if not files:
        return []
    if data_date is None:
        return [files[-1]]
    if isinstance(data_date, datetime.date):
        return [f for f in files if data_date == date_from_data_filename(f)]
    return [f for f in files if all(
        data_date[0] is None or data_date[0] <= date_from_data_filename(f),
        data_date[1] is None or date_from_data_filename(f) <= data_date[1])]

def get_data(filename, style):
    """Return gridded data from a NetCDF file."""
    log.info('Importing ' + filename)
    dset = netcdf_file(filename, mmap=False)
    lats = dset.variables['latitude'][:]
    lons = dset.variables['longitude'][:]
    data = dset.variables[style.var_name][0][:]
    dset.close()
    return lats, lons, style.clean_data(data)

def map_template():
    """Return template figure for the given title and date."""
    fig = plt.figure(figsize=(11.69, 8.27), dpi=300)
    plt.text(62, -47, "wenfo.org/apwm/", ha="left", fontsize=10)
    plt.text(208, -47, 'Created ' + TODAY.isoformat(), ha="right", fontsize=10)
    m = Basemap(projection='cyl', resolution='l', llcrnrlat=-50, urcrnrlat=40,
                llcrnrlon=60, urcrnrlon=210)
    m.drawcoastlines(linewidth=0.75)
    m.drawcountries()
    m.drawlsmask(land_color=(0, 0, 0, 0), ocean_color='white', lakes=True)
    m.drawparallels(np.arange(-23, 24, 23), labels=[1, 0, 0, 1],
                    linewidth=0.6, color=(0.2, 0.2, 0.2))
    m.drawmeridians(np.arange(-180, 181, 30), labels=[1, 0, 0, 1],
                    linewidth=0.6, color=(0.2, 0.2, 0.2))
    return fig, m

def plotMap(style, filename):
    """Make a single map, with the given options and data for the date."""
    fig, m = map_template()
    plt.title("{title}\n{date.day} {date:%B} {date.year}".format(
        title=style.title, date=date_from_data_filename(filename)))
    lats, lons, data = get_data(filename, style)
    xx, yy = np.meshgrid(lons, lats)
    # Ensures lats don't drop at 180, which was causing smearing
    xx[xx < 0] += 360
    cols = tuple(tuple(colour) for colour in
                 np.array(style.colors) / 255)
    m.contour(xx, yy, data, style.values, colors='gray', zorder=-1,
              linewidths=0.75, linestyles='solid')
    cs = m.contourf(xx, yy, data, style.values, colors=cols, zorder=-2)
    cbar = m.colorbar(
        cs, location='right', pad="5%", drawedges=True, extendfrac=0,
        format=style.formatter(), ticks=style.values, values=style.values)
    if style.var_type in ('anom', 'daily', 'meanv'):
        cbar.set_label('mm')
    if style.var_type == 'decile':
        midpoints = [(a + style.values[i+1]) / 2 for i, a in
                     enumerate(style.values[:-1])]
        cbar.set_ticks(midpoints)
        cbar.set_ticklabels([
            'lowest on record',
            'far below average\n(<1 in 10 years)',
            'below average\n(<3 in 10 years)',
            'normal',
            'above average\n(<3 in 10 years)',
            'far above average\n(<1 in 10 years)',
            'highest on record'])
        # TODO:  find a way of doing this that doesn't upsize the main plot
        fig.set_size_inches(11.69 + 1.6, 8.27)
    return fig

def goMap():
    """Make all maps."""
    if not os.path.isdir(args.outputdir):
        os.makedirs(args.outputdir)
    data_date = parse_data_date()
    for var_abbr, timespan in ALL_MAPS:
        map_style = MapStyles(var_abbr, timespan)
        data_files = find_data(map_style, data_date)
        if not data_files:
            log.debug('No data for {}_{} in date range {}'.format(
                var_abbr, timespan, data_date))
        for fname in data_files:
            fig = plotMap(map_style, fname)
            outpath = args.outputdir if args.date is None else os.path.join(
                args.outputdir, os.path.basename(fname)[8])
            if not os.path.isdir(outpath):
                os.makedirs(outpath)
            fname_date = 'latest'
            if data_date is not None:
                fname_date = date_from_data_filename(fname).isoformat()
            fig.savefig(os.path.join(outpath, '{}_{}_{}.png'.format(
                fname_date,
                map_style.var_name,
                map_style.timespan)))
            log.info('produced map: {} {}'.format(timespan, var_abbr))

def get_args():
    """Return parsed command line arguments."""
    parser = argparse.ArgumentParser(
        description='Makes maps from APWM NetCDF data.  You can process the '
        'latest data, or data for a specified day or range of days.')
    parser.add_argument('-i', '--inputdir', default='../nc',
                        help='NetCDF input data folder, default ../nc')
    parser.add_argument('-o', '--outputdir', default='.',
                        help='maps are saved here if no date is given (latest '
                        'data), or in per-day archive subdirs otherwise.')
    parser.add_argument('-l', '--loglevel', default='warning',
                        help='Logging level in: debug, info, warning, error')
    parser.add_argument('-d', '--date', default=None,
                        help='Which day(s) to process.  ISO format (eg '
                        '2015-06-30).  Specify a range with ":", ranges can '
                        'be open-ended.  Processes only most recent day if not'
                        ' given.')
    return parser.parse_args()

if __name__ == '__main__':
    args = get_args()
    logging.basicConfig(level=args.loglevel.upper())
    if not os.path.isdir(args.inputdir):
        log.error('Input dir does not exist: ' + args.inputdir)
    else:
        goMap()
