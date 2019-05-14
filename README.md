# earthquake-reports

## installation example (ubuntu)

Clone: `git clone https://github.com/geophystech/earthquake-reports.git`

Install pip for python3: `sudo apt install python3-pip`

AND optionally update it `pip3 install --upgrade pip`

Install matplotlib basemap via apt: `sudo apt install python3-mpltoolkits.basemap python-mpltoolkits.basemap-data`

Instal project dependencies: ``

## eqmap.py

This script generates PNG map and XLSX files.

Earthquake data could be retrieved from two sources:

- earthquake.usgs.gov (USGS FDSN Event Web Service)

- rest-api.eqalert.ru (EQAlert Seismo API)

### eqmap usage

`eqmap.py -h`

```
usage: eqmap.py [-h] [--date-min DATE_MIN] [--date-max DATE_MAX]
                [--mag-min MAG_MIN] [--mag-max MAG_MAX]
                [--depth-min DEPTH_MIN] [--depth-max DEPTH_MAX]
                [--login LOGIN] [--password PASSWORD]
                [--shape-file SHAPE_FILE] [--from-usgs] [--numerate-events]
                [--plot-stations] [--full-resolution]
                lon_min lon_max lat_min lat_max

Plot PNG maps and save XLSX files based on RES-API.EQALERT.RU and USGS
earthquakes data!

positional arguments:
  lon_min               minimal longitude (left boundary)
  lon_max               minimal longitude (right boundary)
  lat_min               minimal latitude (down boundary)
  lat_max               maximum latitude (up boundary)

optional arguments:
  -h, --help            show this help message and exit
  --date-min DATE_MIN   Limit to events on or after the specified start time
                        FORMAT: YYYY-MM-DD
  --date-max DATE_MAX   Limit to events on or before the specified end time
                        FORMAT: YYYY-MM-DD
  --mag-min MAG_MIN     Limit to events with a magnitude larger than the
                        specified minimum
  --mag-max MAG_MAX     Limit to events with a magnitude smaller than the
                        specified maximum
  --depth-min DEPTH_MIN
                        Limit to events with depth more than the specified
                        minimum
  --depth-max DEPTH_MAX
                        Limit to events with depth less than the specified
                        maximum.
  --login LOGIN         Username from EQALERT.RU service please note that you
                        have to complete registration to use queries without
                        constrains, see more details on
                        https://eqalert.ru/#/register
  --password PASSWORD   Password from EQALERT.RU service
  --shape-file SHAPE_FILE
                        Path to path to shapefile. The Shapefile name must go
                        without the shp extension. The library assumes that
                        all shp, sbf and shx files will exist with this given
                        name
  --from-usgs           Wether or not gather data from earthquake.usgs.gov
                        service instead of default rest-api.eqalert.ru
  --numerate-events     Numerate events
  --plot-stations       Plot stations, only if rest-api.eqalert.ru data source
                        selected
  --full-resolution     Plot a HIGH resolution basemap
 ```

### eqmap examples

**Just plot events from USGS for 1 year:**

`eqmap.py 140 165 40 60 --from-usgs --date-min 2018-01-01 --date-max 2019-01-01`

![map](https://user-images.githubusercontent.com/3518847/57697223-79176f00-769e-11e9-96b7-0062334b1b9e.png)

[catalog.xlsx](https://github.com/geophystech/earthquake-reports/files/3177543/catalog.xlsx)

**Plot from USGS, 1y, M ≥ 5.5, only crust and interplate, numerate events:**

`eqmap.py 140 165 40 60 --from-usgs --date-min 2018-01-01 --date-max 2019-01-01 --mag-min=5.5 --depth-max=150 --numerate`

![map](https://user-images.githubusercontent.com/3518847/57697543-3d30d980-769f-11e9-8724-9ad28ebf5557.png)

[catalog.xlsx](https://github.com/geophystech/earthquake-reports/files/3177574/catalog.xlsx)

**Plot from EQALERT, 10y, M ≥ 3.0, plot stations, with full resolution basemap:**

`eqmap.py 140 145 50 55 --date-min 2009-01-01 --date-max 2019-01-01 --mag-min 3.0 --plot-stations --full-resolution --login a.stepnov@geophystech.ru --pass SECRET`

![map](https://user-images.githubusercontent.com/3518847/57698637-cd701e00-76a1-11e9-8a22-a7986507be5c.png)

[catalog.xlsx](https://github.com/geophystech/earthquake-reports/files/3177674/catalog.xlsx)

**Plot shape file example:**

`eqmap.py 130 150 40 55 --from-usgs --date-min 1950-01-01 --date-max 2019-01-01 --mag-min 7.0 --shape-file ~/Desktop/mygeodata/test-polygon`

![map](https://user-images.githubusercontent.com/3518847/57699403-5f2c5b00-76a3-11e9-94e7-6335397d4a03.png)

[catalog.xlsx](https://github.com/geophystech/earthquake-reports/files/3177722/catalog.xlsx)

[mygeodata-2.zip](https://github.com/geophystech/earthquake-reports/files/3177723/mygeodata-2.zip)


