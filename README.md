# x_map

## What is x_map?

x_map is a simple way to plot data on an OpenStreetMap map.  It uses smopy to fetch the map while latitude, longitude and zoom are derived from the data and the minimum expected image size.  The input data should be a numpy array_like, where the first column is latitude, the second column is longitude and the remaining columns are value series.

## Examples

A simple example can be found in x_map_example.ipynb.
