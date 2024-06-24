import pandas as pd
import geopandas
import routingpy as rp
import contextily as cx
import matplotlib.pyplot as plt

# This line imports an API key from a .txt file in the same folder as the code that is being run
# You could instead hard-code the API key by running
# ors_api_key = "myapikey"
# replacing this with your actual key, but you should not commit this to version control like Github
with open("routingpy_api_key.txt", "r") as file:
    ors_api_key = file.read().replace("\n", "")

ors_api = rp.ORS(api_key=ors_api_key)

lsoa_boundaries = geopandas.read_file("https://github.com/hsma-programme/h6_3c_interactive_plots_travel/raw/main/h6_3c_interactive_plots_travel/example_code/LSOA_2011_Boundaries_Super_Generalised_Clipped_BSC_EW_V4.geojson")

lsoa_centroids = pd.read_csv("https://github.com/hsma-programme/h6_3c_interactive_plots_travel/raw/main/h6_3c_interactive_plots_travel/example_code/england_lsoa_2011_centroids.csv")

# filter lsoa centroid file to just those with 'Brighton and Hove' in the name
brighton_lsoas_with_coords = lsoa_centroids[lsoa_centroids["name"].str.contains("Brighton and Hove")]

# Turn this into a geodataframe
brighton_lsoas_with_coords_gdf = geopandas.GeoDataFrame(
    brighton_lsoas_with_coords,
    geometry = geopandas.points_from_xy(
        brighton_lsoas_with_coords['x'],
        brighton_lsoas_with_coords['y']
        ),
    crs = 'EPSG:27700' # as our current dataset is in BNG (northings/eastings)
    )

# Convert to lat/long from northings/eastings
brighton_lsoas_with_coords_gdf = brighton_lsoas_with_coords_gdf.to_crs('EPSG:4326')

source_coord_pairs = list(zip(
   brighton_lsoas_with_coords_gdf.geometry.x,
   brighton_lsoas_with_coords_gdf.geometry.y
   ))

source_coord_pairs_list = [list(coord_tuple) for coord_tuple in source_coord_pairs]

# Define site locations
locations = [
    [50.84510657697442, -0.19543939173180552],
    [50.844345428338784, -0.13365357930540253],
    [50.833469545267626, -0.10763304889918592],
    [50.83075017843111, -0.17652193515449327],
    [50.865971443211656, -0.11961372476967412],
    [50.85758221272246, -0.17259077588448932]
    ]

# Swap site locations into order expected by ORS/routingpy service
locations_long_lat = [
    [  x[1], x[0]  ]
    for x
    in locations]

# Create empty list to store all source and destination coordinates
all_coordinates = []

# Put our sources (our LSOA centre points) into the list
all_coordinates.extend(source_coord_pairs_list)

# Put our destinations (our potential sites) into the list
all_coordinates.extend(locations_long_lat)

sources_indices = [i for i in range(len(source_coord_pairs_list))]

destinations_indices = [i for i in
                        range(
                            # first number in list of indices
                            # this will be 1 more than the number of sources (which were first in our
                            # full list of coordinates)
                            len(source_coord_pairs_list),
                            # last number in list of indices (remember the last number won't
                            # actually be included)
                            len(all_coordinates))
                            ]

# Request the travel times
location_matrix = ors_api.matrix(
    locations = all_coordinates, # remember this is sources first, then destinations
    profile = 'driving-car',
    sources = sources_indices,
    destinations = destinations_indices,
    metrics=["distance", "duration"]
    )

# turn the output into a dataframe
brighton_travel_matrix = pd.DataFrame(
    location_matrix.durations,
    columns=[f"Site {i+1}" for i in range(len(destinations_indices))],
    index=brighton_lsoas_with_coords.name
    )

# calculate the shortest travel time
brighton_travel_matrix['shortest'] = brighton_travel_matrix.min(axis=1)

# join travel data to geometry data
nearest_site_travel_brighton_gdf = pd.merge(
    left=lsoa_boundaries,
    right=brighton_travel_matrix.reset_index(),
    left_on = "LSOA11NM",
    right_on = "name"
)

# create column with shortest travel time in minutes (converted from seconds)
nearest_site_travel_brighton_gdf["shortest_minutes"] = nearest_site_travel_brighton_gdf["shortest"] / 60

# create geodataframe of site locations for plotting
brighton_sites = geopandas.GeoDataFrame(
    [f"Site {i+1}" for i in range(len(destinations_indices))],
    geometry = geopandas.points_from_xy(
        [i[1] for i in locations],
        [i[0] for i in locations]
        ),
    crs = 'EPSG:4326' # as our current dataset is in BNG (northings/eastings)
    )

# plot travel times as choropleth
ax = nearest_site_travel_brighton_gdf.plot(
    "shortest_minutes",
    legend=True,
    cmap="Blues",
    alpha=0.7,
    edgecolor="black",
    linewidth=0.5,
    figsize=(12,6)
    )

# plot potential hospitals/sites as point layer
hospital_points = (brighton_sites.to_crs('EPSG:27700')).plot(ax=ax, color='magenta', markersize=60)

# add basemap
cx.add_basemap(ax, crs=nearest_site_travel_brighton_gdf.crs.to_string(), zoom=14)

# Add site labels
for x, y, label in zip(brighton_sites.to_crs('EPSG:27700').geometry.x,
                      brighton_sites.to_crs('EPSG:27700').geometry.y,
                      brighton_sites.to_crs('EPSG:27700')[0]):
    ax.annotate(label, xy=(x,y), xytext=(10,3), textcoords="offset points", bbox=dict(facecolor='white'))

# Turn off axis coordinate markings
ax = ax.axis('off')

# Add title to whole plot
plt.title("Travel Time (minutes - driving) to nearest proposed site in Brighton")
