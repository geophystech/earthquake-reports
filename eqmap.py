#! /usr/bin/env python3
"""
This script generates MAP and XLSX files.

Earthquake data could be retrieved from two sources:
- earthquake.usgs.gov (USGS FDSN Event Web Service)
- rest-api.eqalert.ru (EQAlert Seismo API)
"""

import sys
import argparse
import requests
import pandas as pd
from pandas.io.json import json_normalize
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.basemap import Basemap
from adjustText import adjust_text

# parse command line arguments
PARSER = argparse.ArgumentParser(
        description='Plot PNG maps and save XLSX files based on \
                RES-API.EQALERT.RU and USGS earthquakes data!')
PARSER.add_argument(
        'lon_min', type=float,
        help='minimal longitude (left boundary)')
PARSER.add_argument(
        'lon_max', type=float,
        help='minimal longitude (right boundary)')
PARSER.add_argument(
        'lat_min', type=float,
        help='minimal latitude (down boundary)')
PARSER.add_argument(
        'lat_max', type=float,
        help='maximum latitude (up boundary)')
PARSER.add_argument(
        '--date-min', type=str,
        help='Limit to events on or after the specified start time\
                FORMAT: YYYY-MM-DD')
PARSER.add_argument(
        '--date-max', type=str,
        help='Limit to events on or before the specified end time\
                FORMAT: YYYY-MM-DD')
PARSER.add_argument(
        '--mag-min', type=float,
        help='Limit to events with a magnitude larger than the\
                specified minimum')
PARSER.add_argument(
        '--mag-max', type=float,
        help='Limit to events with a magnitude smaller than the\
                specified maximum')
PARSER.add_argument(
        '--depth-min', type=float,
        help='Limit to events with depth more than the specified minimum')
PARSER.add_argument(
        '--depth-max', type=float,
        help='Limit to events with depth less than the specified maximum.')
PARSER.add_argument(
        '--login', type=str,
        help='Username from EQALERT.RU service\
                please note that you have to complete registration to use\
                queries without constrains, see more details on\
                https://eqalert.ru/#/register')
PARSER.add_argument(
        '--password', type=str,
        help='Password from EQALERT.RU service')
PARSER.add_argument(
        '--shape-file', type=str,
        help='Path to path to shapefile.\
                The Shapefile name must go without the shp extension.\
                The library assumes that all shp, sbf and shx files\
                will exist with this given name')
PARSER.add_argument(
        '--from-usgs', action='store_true',
        help='Wether or not gather data\
                from earthquake.usgs.gov service\
                instead of default rest-api.eqalert.ru')
PARSER.add_argument(
        '--numerate-events', action='store_true',
        help='Numerate events')
PARSER.add_argument(
        '--plot-stations', action='store_true',
        help='Plot stations, only if rest-api.eqalert.ru data source selected')
PARSER.add_argument(
        '--full-resolution', action='store_true',
        help='Plot a HIGH resolution basemap')
ARGS = PARSER.parse_args()
# print(ARGS)

# set globals from ARGS
FROM_USGS = ARGS.from_usgs
NUMERATE_EVENTS = ARGS.numerate_events
PLOT_STATIONS = ARGS.plot_stations
LAT_MIN = ARGS.lat_min
LAT_MAX = ARGS.lat_max
LON_MIN = ARGS.lon_min
LON_MAX = ARGS.lon_max
DATETIME_MIN = ARGS.date_min
DATETIME_MAX = ARGS.date_max
MAG_MIN = ARGS.mag_min
MAG_MAX = ARGS.mag_max
DEPTH_MIN = ARGS.depth_min
DEPTH_MAX = ARGS.depth_max
SHAPE_FILE = ARGS.shape_file
IMAGE_SIZE = 15
PNG_FILE_NAME = 'map.png'
XLSX_FILE_NAME = 'catalog.xlsx'

if ARGS.full_resolution:
    RESOLUTION = 'f'
else:
    RESOLUTION = 'i'

if (LAT_MAX - LAT_MIN) <= 2:
    PARALLELS = np.arange(LAT_MIN, LAT_MAX, 0.25)
elif (LAT_MAX - LAT_MIN) > 2 and (LAT_MAX - LAT_MIN) <= 10:
    PARALLELS = np.arange(LAT_MIN, LAT_MAX, 1)
else:
    PARALLELS = np.arange(LAT_MIN, LAT_MAX, 2)

if (LON_MAX - LON_MIN) <= 2:
    MERIDIANS = np.arange(LON_MIN, LON_MAX, 0.5)
elif (LON_MAX - LON_MIN) > 2 and (LON_MAX - LON_MIN) <= 5:
    MERIDIANS = np.arange(LON_MIN, LON_MAX, 1)
elif (LON_MAX - LON_MIN) > 5 and (LON_MAX - LON_MIN) <= 10:
    MERIDIANS = np.arange(LON_MIN, LON_MAX, 2)
else:
    MERIDIANS = np.arange(LON_MIN, LON_MAX, 4)

EQALERT_LOGIN = ARGS.login
EQALERT_PASSWORD = ARGS.password

USGS_ENDPOINT = 'https://earthquake.usgs.gov/fdsnws/event/1/query'
USGS_JSON_OBJECT = 'features'

EQALERT_GET_LIST = 'https://rest-api.eqalert.ru/api/v1/reports'
EQALERT_ACCESS_TOKEN = 'https://oauth-web.eqalert.ru/token'
EQALERT_JSON_OBJECT_DATA = 'data'
EQALERT_JSON_OBJECT_META = 'meta'
TOKEN = None

USGS_GET_PARAMS = {
        'format': 'geojson',
        'minlatitude': LAT_MIN,
        'minlongitude': LON_MIN,
        'maxlatitude': LAT_MAX,
        'maxlongitude': LON_MAX
        }

USGS_DATA_SELECTED_COLUMNS_1 = [
        'id', 'properties.time', 'properties.mag', 'properties.magType',
        'properties.net', 'properties.title', 'properties.mmi',
        'properties.url']

USGS_DATA_SELECTED_COLUMNS_2 = ['lon', 'lat', 'depth']

USGS_COLUMNS_RENAME = {
        "id": "id",
        "properties.time": "event_datetime",
        "lat": "lat",
        "lon": "lon",
        "depth": "depth",
        "properties.mag": "mag",
        "properties.magType": "mag_t",
        "properties.net": "agency",
        "properties.title": "nearestCity_title",
        "properties.mmi": "intensity",
        "properties.url": "event_page"}

USGS_COLUMNS_REORDER = [
        'id', 'event_datetime', 'lat', 'lon', 'depth',
        'mag', 'mag_t', 'agency', 'nearestCity_title',
        'intensity', 'event_page']


EQALERT_GET_LIST_PARAMS = {
        'include': 'nearestCity',
        'limit': 100,
        'site_url': 'true',
        'lat_min': LAT_MIN,
        'lat_max': LAT_MAX,
        'lon_min': LON_MIN,
        'lon_max': LON_MAX
        }

GET_STATIONS_PARAMS = {
        'has_realtime': 1
        }

EQALERT_DATA_SELECTED_COLUMNS = [
        'id', 'locValues.data.event_datetime', 'locValues.data.lat',
        'locValues.data.lon', 'locValues.data.depth',
        'locValues.data.mag', 'locValues.data.mag_t',
        'agency',
        'nearestCity.data.settlement.data.translation.data.title',
        'nearestCity.data.settlement.data.translation.data.region',
        'nearestCity.data.msk64_value',
        'site_url']

EQALERT_COLUMNS_RENAME = {
        "id": "id",
        "locValues.data.event_datetime": "event_datetime",
        "locValues.data.lat": "lat",
        "locValues.data.lon": "lon",
        "locValues.data.depth": "depth",
        "locValues.data.mag": "mag",
        "locValues.data.mag_t": "mag_t",
        "agency": "agency",
        "nearestCity.data.settlement.data.translation.data.title":
        "nearestCity_title",
        "nearestCity.data.settlement.data.translation.data.region":
        "nearestCity_regeon",
        "nearestCity.data.msk64_value": "nearestCity_intensity",
        "site_url": "event_page"}


if DATETIME_MIN:
    USGS_GET_PARAMS['starttime'] = DATETIME_MIN
    EQALERT_GET_LIST_PARAMS['datetime_min'] = DATETIME_MIN + ' 00:00:00'
if DATETIME_MAX:
    USGS_GET_PARAMS['endtime'] = DATETIME_MAX
    EQALERT_GET_LIST_PARAMS['datetime_max'] = DATETIME_MAX + ' 00:00:00'
if MAG_MIN:
    USGS_GET_PARAMS['minmagnitude'] = MAG_MIN
    EQALERT_GET_LIST_PARAMS['mag_min'] = MAG_MIN
if MAG_MAX:
    USGS_GET_PARAMS['maxmagnitude'] = MAG_MAX
    EQALERT_GET_LIST_PARAMS['mag_max'] = MAG_MAX
if DEPTH_MIN:
    USGS_GET_PARAMS['mindepth'] = DEPTH_MIN
    EQALERT_GET_LIST_PARAMS['depth_min'] = DEPTH_MIN
if DEPTH_MAX:
    USGS_GET_PARAMS['maxdepth'] = DEPTH_MAX
    EQALERT_GET_LIST_PARAMS['depth_max'] = DEPTH_MAX


def get_earthquake_data(
        url, params, json_object, meta_object=None, token=None):
    """
    Get json by URL, normalize it and return a DataFrame with json_object
    If meta specified return tuple of Dataframe's (data, meta)
    """
    if token:
        headers = {'Authorization': 'Bearer ' + token}
    else:
        headers = None
    response = requests.get(url, params, headers=headers)
    print('Constructed URL: ', response.url)
    if response.status_code != 200:
        print('An error occurred wile fetching the data:')
        print('HTTP status code: ', response.status_code)
        print(response.json())
        sys.exit(1)
    df_norm = json_normalize(response.json()[json_object])
    if df_norm.empty:
        print('Events no found, please modify request parameters')
        sys.exit(0)
    # https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.io.json.json_normalize.html
    # That strange IF below because
    # json_normalize(response.json()[json_object]) and
    # json_normalize(response.json(), json_object)
    # return **different** results while parsing USGS/EQALERT json response.
    # So, USGS have not cursor and it is possible to parse only
    # nested 'Feature' object. For EQALERT it's required to pass
    # data and meta json objects.
    if meta_object:
        meta_norm = json_normalize(response.json()[meta_object])
        print('return with meta')
        return (df_norm, meta_norm)
    return df_norm


def get_eqalert_access_token(
        url, username, password, access_token_key='access_token'):
    """
    Get access token for signing requests to
    EQALERT API
    """
    post_data = {'username': username, 'password': password}
    get_resp = requests.post(url, post_data)
    if get_resp.status_code != 200:
        print('An error occurred wile getting token:')
        print('HTTP status code: ', get_resp.status_code)
        print(get_resp.json())
        sys.exit(1)
    token = get_resp.json()[access_token_key]
    return token


if FROM_USGS:
    print('Getting events from USGS API...')
    print('Params are ', USGS_GET_PARAMS)
    EQ_LIST_FULL = get_earthquake_data(
        USGS_ENDPOINT, USGS_GET_PARAMS, USGS_JSON_OBJECT)
    # select meaningfull columns for plotting
    EQ_LIST_SELECTED = EQ_LIST_FULL[USGS_DATA_SELECTED_COLUMNS_1].copy()
    EQ_LIST_SELECTED[USGS_DATA_SELECTED_COLUMNS_2] = pd.DataFrame(
        EQ_LIST_FULL['geometry.coordinates'].values.tolist(),
        columns=USGS_DATA_SELECTED_COLUMNS_2)
    EQ_LIST_SELECTED = EQ_LIST_SELECTED.rename(
        index=str,
        columns=USGS_COLUMNS_RENAME)
    # reorder columns
    EQ_LIST_SELECTED = EQ_LIST_SELECTED[USGS_COLUMNS_REORDER]
    # convert time stampt to human related
    EQ_LIST_SELECTED['event_datetime'] = pd.to_datetime(
        EQ_LIST_SELECTED['event_datetime'], unit='ms')
else:
    print('Gathering events from EQALERT API...')
    print('Params are ', EQALERT_GET_LIST_PARAMS)
    if EQALERT_LOGIN is not None and EQALERT_PASSWORD is not None:
        TOKEN = get_eqalert_access_token(
            EQALERT_ACCESS_TOKEN, EQALERT_LOGIN, EQALERT_PASSWORD)
    DATA_WITH_META = get_earthquake_data(
        EQALERT_GET_LIST,
        EQALERT_GET_LIST_PARAMS,
        EQALERT_JSON_OBJECT_DATA,
        meta_object=EQALERT_JSON_OBJECT_META,
        token=TOKEN)
    EQ_LIST_FULL = DATA_WITH_META[0]
    META = DATA_WITH_META[1]
    # getting next page if exist
    print('Number of events on THIS page: ',
          META['cursor.count'].iloc[0])
    while META['cursor.next'].iloc[0]:
        print('Next cursor: ', META['cursor.next'].iloc[0])
        EQALERT_GET_LIST_PARAMS['cursor'] = META['cursor.next'].iloc[0]
        print('Add data from next cursor:')
        DATA_WITH_META = get_earthquake_data(
            EQALERT_GET_LIST,
            EQALERT_GET_LIST_PARAMS,
            EQALERT_JSON_OBJECT_DATA,
            meta_object=EQALERT_JSON_OBJECT_META,
            token=TOKEN)
        EQ_LIST_FULL = EQ_LIST_FULL.append(DATA_WITH_META[0])
        META = DATA_WITH_META[1]
        print('Number of events on THIS page: ',
              META['cursor.count'].iloc[0])
    # select meaningfull columns for plotting
    EQ_LIST_SELECTED = EQ_LIST_FULL.copy()
    EQ_LIST_SELECTED = EQ_LIST_SELECTED[EQALERT_DATA_SELECTED_COLUMNS]
    EQ_LIST_SELECTED = EQ_LIST_SELECTED.rename(
        index=str,
        columns=EQALERT_COLUMNS_RENAME)

# reorder events in chronology from earlier to the last
EQ_LIST_SELECTED = EQ_LIST_SELECTED.iloc[::-1]
# Generate index from 1 to N
EQ_LIST_SELECTED.index = np.arange(1, len(EQ_LIST_SELECTED)+1)

print(
    'Total events that were fetched from API: ',
    len(EQ_LIST_SELECTED))
# print(EQ_LIST_SELECTED)

# create a subplot and set the size of fig
FIG, AX = plt.subplots()
FIG.set_figheight(IMAGE_SIZE)
FIG.set_figwidth(IMAGE_SIZE)

print('Constructing BASEMAP...')
mpl.rcParams.update(
    {'font.weight': 'normal',
     'font.size': 12})
MAP = Basemap(
        llcrnrlon=LON_MIN, urcrnrlon=LON_MAX,
        llcrnrlat=LAT_MIN, urcrnrlat=LAT_MAX,
        projection='merc', resolution=RESOLUTION, ax=AX)
MAP.drawcoastlines()
MAP.drawrivers()
MAP.drawparallels(PARALLELS, labels=[1, 1, 0, 0])
MAP.drawmeridians(MERIDIANS, labels=[0, 0, 0, 1])

if SHAPE_FILE:
    print('Ploting shape file object...')
    MAP.readshapefile(
        SHAPE_FILE,
        'shape-object',
        linewidth=2.0,
        color='c',
        ax=AX)

print('Plotting events...')
# converting lat-lon to MAP X,Y
X, Y = MAP(
        EQ_LIST_SELECTED['lon'].values.tolist(),
        EQ_LIST_SELECTED['lat'].values.tolist())
# powering the magnitude for circle distinguishing
MAG = (EQ_LIST_SELECTED['mag'] ** 3).values.tolist()
AX.scatter(
        X, Y,
        MAG,
        c='red', alpha=0.5, zorder=10)


if NUMERATE_EVENTS:
    print('Numerating events...')
    # change fornt settings
    mpl.rcParams.update(
        {'text.color': 'purple',
         'font.size': 10,
         'font.weight': 'bold'})
    # numerate events from 1 to N
    ANN = EQ_LIST_SELECTED.index.to_list()
    ANNOTATE = [
        AX.text(
            X[i], Y[i], '%s' % txt, zorder=10) for i, txt in enumerate(ANN)]
    adjust_text(ANNOTATE, ax=AX, on_basemap=False)  # on_basemap=True is buggy


if PLOT_STATIONS & (not FROM_USGS):
    print('Plotting stations...')
    GET_STATIONS = get_earthquake_data(
        'https://rest-api.eqalert.ru/api/v1/stations',
        GET_STATIONS_PARAMS,
        'data')
    # filter according map boundaries
    GET_STATIONS = GET_STATIONS[
        (
            GET_STATIONS.sta_lon > LON_MIN) & (
                GET_STATIONS.sta_lon < LON_MAX) & (
                    GET_STATIONS.sta_lat > LAT_MIN) & (
                        GET_STATIONS.sta_lat < LAT_MAX)]
    # change fornt settings
    mpl.rcParams.update(
        {'text.color': "blue",
         'font.weight': 'normal',
         'font.size': 10})
    X, Y = MAP(
        GET_STATIONS['sta_lon'].values.tolist(),
        GET_STATIONS['sta_lat'].values.tolist())
    AX.scatter(
        X, Y,
        color='blue',
        marker="^", alpha=0.5, zorder=5)
    ANN_STA = GET_STATIONS.scnl_name.to_list()
    ANNOTATE_STA = [
        AX.text(X[i], Y[i], '%s' % txt) for i, txt in enumerate(ANN_STA)]
    adjust_text(ANNOTATE_STA, ax=AX, on_basemap=False)


print('Saving the PNG image file...')
FIG.savefig(
        PNG_FILE_NAME,
        dpi=300, quality=100, orientation='portrait')

print('Save catalog to XLSX file...')
with pd.ExcelWriter(XLSX_FILE_NAME) as writer:
    EQ_LIST_SELECTED.to_excel(writer, sheet_name='CAT')

print('Well done! Everything OK!')
