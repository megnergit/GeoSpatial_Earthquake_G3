#!/usr/bin/env python
# coding: utf-8

# |------------------------------------------------------------------
# | # Geospatial Data Exercise
# |------------------------------------------------------------------
# |
# | This is an exercise notebook for the third lesson of the kaggle course
# | ["Geospatial Analysis"](https://www.kaggle.com/learn/geospatial-analysis)
# | offered by Alexis Cook and Jessica Li. The main goal of the lesson is
# | to get used to __Interactive Maps__. We will learn how to use `folium`
# | with the following functions.
# |
# | * Map
# | * Circle (= bubble map)
# | * HeatMaps
# | * Choropleth
# |

# | Here 'interactive' means
# |
# | - zoom in  / zoom out
# | - move (drag the map)
# | - tooltip (information shows up when the pointer is on a marker)
# | - popup (information shows up when a marker is clicked)

# | ## 1. Task
# |
# | Visualize how the largest cities in Japan are vulnerable to the
# | threat of big earthquakes in the future. 

# | ## 2. Data
# |
# | 1. Known plate-boundaries.
# | 2. Historical earthquakes in 1970-2014.
# | 3. Borders (Shapely Polygon) of Japanese prefectures.
# | 4. Populations and areas in Japanese prefectures.

# | ## 3. Notebook
# |
# | Import packages.

from kaggle_geospatial.kgsp import *
from folium.plugins import HeatMap
from folium import Choropleth, Circle
import folium
import pandas as pd
import geopandas as gpd
import numpy as np
from pathlib import Path
import os
import webbrowser
import zipfile
import plotly.graph_objs as go
from plotly.subplots import make_subplots


# -------------------------------------------------------
# | Set up some directories.

CWD = '/Users/meg/git6/earthquake/'
DATA_DIR = '../input/geospatial-learn-course-data/'
KAGGLE_DIR = 'alexisbcook/geospatial-learn-course-data'
GEO_DIR = 'geospatial-learn-course-data'

set_cwd(CWD)
set_data_dir(DATA_DIR, KAGGLE_DIR, GEO_DIR, CWD)
show_whole_dataframe(True)

# ---------------------------------------
# | Read plate data. Somehow the coordinate in 'geometry' of
# | `plate_boundaries` is (longitude, latitude), instead of (latitude, longitude)
# | which is the standard of EPSG:4326. Swap them, and store them
# | to a new column `coordinates'.

plate_boundaries_dir = DATA_DIR + "Plate_Boundaries/Plate_Boundaries/"
plate_boundaries = gpd.read_file(
    plate_boundaries_dir + "Plate_Boundaries.shp")

plate_boundaries['coordinates'] = plate_boundaries.apply(
    lambda x: [(b, a) for (a, b) in list(x.geometry.coords)], axis=1)

print(plate_boundaries.info())
print(plate_boundaries.crs)
plate_boundaries.head(3)

# ---------------------------------------
# | Read the record of the historical earthquakes.

earthquakes = pd.read_csv(DATA_DIR + "earthquakes1970-2014.csv",
                          parse_dates=["DateTime"])
print(earthquakes.info())
earthquakes.head(3)

# ---------------------------------------
# | Read the prefectural boundaries.

prefectures_dir = DATA_DIR + "japan-prefecture-boundaries/japan-prefecture-boundaries/"
prefectures = gpd.read_file(
    prefectures_dir + "japan-prefecture-boundaries.shp")

prefectures.set_index('prefecture', inplace=True)

print(prefectures.info())
prefectures.head(3)

# ---------------------------------------
# | Read the population and the areas of each prefecture.

population = pd.read_csv(DATA_DIR + "japan-prefecture-population.csv")
population.set_index('prefecture', inplace=True)





# ========================================
# | Visualize the plate boundaries near Japan.
# | Overlay a heatmap of the historical earthquakes.

x = np.array([p.centroid.x for p in prefectures['geometry']]).mean()
y = np.array([p.centroid.y for p in prefectures['geometry']]).mean()
center = [y, x]
zoom = 7

# tiles = 'openstreetmap'
tiles = 'cartodbpositron'

# -------------------------------------------------------

m_1 = folium.Map(location=center, tiles=tiles, zoom_start=zoom)
dump = [folium.PolyLine(
    locations=p, weight=12, color='mediumvioletred').add_to(m_1)
    for p in plate_boundaries['coordinates']]

HeatMap(data=earthquakes[['Latitude', 'Longitude']],
        radius=30).add_to(m_1)

# -------------------------------------------------------
# | Show it on the notebook and the browser window.

embed_map(m_1, './html/m_1.html')
# --
show_on_browser(m_1, CWD + './html/m_1b.html')

# -------------------------------------------------------
# | Earthquakes often happens about 100-300 km west
# | of the plate boundaries. Northern half of Japan,
# | with Tokyo on the southern-most edge, 
# | is particularly vulnerable to the future earthquakes.
#
# =======================================================
# | Calculate the area (in square kilometers) of each prefecture.

area_sqkm = pd.Series(prefectures['geometry'].to_crs(
    epsg=32654).area / 10**6, name='area_sqkm')

# -------------------------------------------------------
# | Add the population density (per square kilometer) for each prefecture.
# | What are the most densely populated prefectures?

stats['density'] = stats['population'] / stats['area_sqkm']
stats['log10_density'] = np.log(stats['density'])

# | What are the most populous prefectures?

stats = population.join(area_sqkm)
stats.sort_values('population').tail(5)

# -------------------------------------------------------
# | Use `plotly` to see the populations and the population densities 
# | of the Japanese prefectures. 

n_rows = 1
n_cols = 2
fig = make_subplots(rows=n_rows, cols=n_cols,
                    vertical_spacing=0.05,
                    horizontal_spacing=0.05,
                    subplot_titles=['Populations in Japanese Prefectures',
                                    'Densities in Japanese Prefectures'])

trace1 = go.Bar(y=stats.sort_values('density').index,
                x=stats.sort_values('density')['population'],
                marker=dict(color='teal'),
                orientation='h',
                xaxis='x',
                yaxis='y')

trace2 = go.Bar(y=stats.sort_values('density').index,
                x=stats.sort_values('density')['density'],
                marker=dict(color='coral'),
                orientation='h',
                xaxis='x2',
                yaxis='y2')

data = [trace1, trace2]

layout = go.Layout(height=512 * 4, width=1024,
                   font=dict(size=20),
                   showlegend=False)

layout = fig.layout.update(layout)
fig = go.Figure(data=data, layout=layout)

# -------------------------------------------------------
# | Show it on the notebook and the browser window.
embed_plot(fig, './html/p_1.html')
# --
fig.show()


# -------------------------------------------------------
# Show highly populated prefectures in Choropleth.

m_2 = folium.Map(location=center, tiles=tiles, zoom_start=zoom)
Choropleth(geo_data=prefectures.__geo_interface__,
           data=stats['density'],
           #           data=stats,
           columns=['density'],
           key_on='feature.id',
           color='navy',
           fill_color='YlGnBu',
           fill_opacity=0.8
           ).add_to(m_2)

# -------------------------------------------------------
# | Show it on the notebook and the browser window.

embed_map(m_2, './html/m_2.html')
# --
show_on_browser(m_2, CWD + './html/m_2b.html')

# -------------------------------------------------------
# Show the historical earthquake record in a bubble map.

m_3 = folium.Map(location=center, tiles=tiles, zoom_start=zoom)

dump = [folium.PolyLine(
    locations=p, weight=12, color='mediumvioletred').add_to(m_3)
    for p in plate_boundaries['coordinates']]

Choropleth(geo_data=prefectures.__geo_interface__,
           data=stats['log10_density'],
           columns=['log_density'],
           key_on='feature.id',
           color='navy',
           fill_color='YlGnBu',
           fill_opacity=0.8
           ).add_to(m_3)

dump = [Circle([r['Latitude'], r['Longitude']],
               radius=4 ** r['Magnitude'],
               color='',
               fill_color='coral',
               fill_opacity=0.5,
               fill=True).add_to(m_3)
        for i, r in earthquakes.iterrows()]

# -------------------------------------------------------
# | Show it on the notebook and the browser window.

embed_map(m_3, './html/m_3.html')
# --
show_on_browser(m_3, CWD + './html/m_3b.html')

# -------------------------------------------------------
# | ## 4. Conclusion
# |
# | If we limit ourselves only to the largest earthquakes
# | that leads to potential catastrophe, the most vulnerable
# | area in Japan is the northern Kanto area near Tokyo, 
# | where the most densely populated area overlaps with the
# | south edge of the plate boundaries in the northern Japan.
# |
# | The prefectures need to invest to prepare future earthquakes are
# |
# | - Ibaraki
# | - Chiba
# | - Miyagi
# | - Gunma
# | - Tokyo
# | - Kanagawa
# |
# | in this order.
# -------------------------------------------------------
# | END
