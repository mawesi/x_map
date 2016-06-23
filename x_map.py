#! /usr/bin/env python3
# -*- coding: utf-8 -*-

__version__ = '0.0.3'
__author__ = 'Maximilian Singh'
__copyright__ = 'Maximilian Singh'

import smopy
import numpy as np
import matplotlib.cm as cm
import matplotlib.pyplot as plt



def calculate_bounding_coordinates(data, extend_percentage):
    """Calculate the bounding box for given coordinates.

    Parameters
    ----------
    data : array_like
        Column 0 should be latitude coordinates and column 1 should be
        longitude coordinates
    extend_percentage : int, float
        Determines how much the shown map is extended around the
        bounding box of the values.  Given in percent of the bounding
        box extents.

    """
    # Get minimum and maximum latitude and longitude for bounding box.
    lat_long_min = np.array([data[:, 0].min(), data[:, 1].min()])
    lat_long_max = np.array([data[:, 0].max(), data[:, 1].max()])

    # Extend bounding box by extend_percentage in each direction.
    lat_long_extend = (lat_long_max - lat_long_min) * extend_percentage / 100
    lat_long_min = lat_long_min - lat_long_extend
    lat_long_max = lat_long_max + lat_long_extend
    
    # Return minimum and maximum bounding box coordinates.
    return lat_long_min, lat_long_max
    

    
def calculate_optimal_zoom(lat_long_min, lat_long_max, min_size_px):
    """Calculate the minimal necessary zoom.

    Parameters
    ----------
    lat_long_min : array_like
        Minimal latitude and longitude of the bounding box.
    lat_long_max : array_like
        Maximal latitude and longitude of the bounding box.
    min_size_px : int
        Minimum number of pixels in each dimension of the resulting
        plot.

    """
    # Get minimum and maximum tile coordinates of bounding box.
    ## min -> max[0], min[1] because of mercator projection:
    ## http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python
    min_loc = np.array(smopy.deg2num(lat_long_max[0], lat_long_min[1], 0, do_round=False))
    max_loc = np.array(smopy.deg2num(lat_long_min[0], lat_long_max[1], 0, do_round=False))

    # Calculate distance in x and y direction.
    dist = max_loc - min_loc

    # Calculate minimal necessary zoom level.
    ## Refer to http://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Python
    ## for formula.
    zoom = int(np.max(np.ceil(np.log2((min_size_px / smopy.TILE_SIZE) / dist))))

    return zoom



def plot(data, min_size_px=512, extend_percentage=10, filename=False,
         markers=True, gradient_lines=True, caption=False,
         show_plot=True):
    """Plot data in a map.

    Parameters
    ----------
    data : array_like
        The input data.  Columns should be latitude, longitude, value.
        If multiple value columns are given, one plot for each value
        column is generated.
    min_size_px : int, optional
        Minimum size of generated plot in pixels.  Defaults to 512.
    extend_percentage : int, float, optional
        Determines how much the shown map is extended around the
        bounding box of the values.  Given in percent of the bounding
        box extents.  Defaults to 10.
    filename : str, list, optional
        Filename of the generated png image.  If `False`, the image is
        not saved.  If multiple value columns are given, this can also
        be a list of filenames.  Defaults to `False`.
    markers : bool, optional
        If `True`, markers for each value are plotted.  Defaults to
        `True`.
    gradient_lines : bool, optional
        If `True` gradient color lines are plotted between the values.
        Defaults to `True`.
    caption : str, list, optional
        Caption printed on the plot if given.  If multiple value
        columns are given, this can also be a list of captions.
        Defaults to `False`.
    show_plot : bool, optional
        If `True`, the generated plot is displayed.  Defaults to
        `True`.

    """
    # Calculate bounding box and zoom.
    lat_long_min, lat_long_max = calculate_bounding_coordinates(data, extend_percentage=extend_percentage)
    zoom = calculate_optimal_zoom(lat_long_min, lat_long_max, min_size_px)

    # Get map data from OpenStreetMaps.
    dpi = 72
    m = smopy.Map((*lat_long_min, *lat_long_max), z=zoom)

    # Calculate resulting figure size.
    size = m.to_pil().size
    print(size)
    figsize = (10/32 + size[0] / dpi, 10/32 + size[1] / dpi)

    # Plot map and data for each value column.
    for value_index in range(2, data.shape[1]):
        # Convert map to matplotlib.
        ax = m.show_mpl(figsize=figsize, dpi=dpi)


        # Plot markers and gradient lines for each value.
        for i, (lat, long, value) in enumerate(data[:,(0, 1, value_index)]):
            loc_px = m.to_pixels(lat, long)

            # Plot markers.
            if markers:
                ax.plot(*loc_px, 'o', color=cm.plasma(float(-value / 100)), markersize=10)

            # Plot gradient lines.
            ## Skip first value and then plot line from last value to current value.
            if i != 0 and gradient_lines:
                # Calculate line length.
                line_length = np.sqrt((last_loc_px[0] - loc_px[0]) ** 2 + (last_loc_px[1] - loc_px[1]) ** 2)
                # Calculate x and y coordinates of line points.
                x = np.linspace(last_loc_px[0], loc_px[0], line_length)
                y = (loc_px[1] - last_loc_px[1]) * ((x - last_loc_px[0]) / (loc_px[0] - last_loc_px[0])) + last_loc_px[1]
                # Generate a gradient color map.
                colors = [cm.plasma(float(-((value - last_value) * i / len(x) + last_value) / 100)) for i in range(len(x))]
                # Gradient lines are generated using scatter plots.
                ax.scatter(x, y, c=colors, marker='o', s=1, edgecolor='face')

            # Store last location and value for next gradient line.
            last_loc_px = loc_px
            last_value = value


        # Get the extended bounding box in pixels.
        x_min, y_min = m.to_pixels(lat_long_max[0], lat_long_min[1])
        x_max, y_max = m.to_pixels(lat_long_min[0], lat_long_max[1])

        # Set the axes limits to show only the extended bounding box.
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_max, y_min)

        # Add caption to the plot.
        if caption is not False:
            if isinstance(caption, str):
                this_caption = caption
            else:
                this_caption = caption[value_index - 2]
            ax.text(10 + x_min, y_max - 10, this_caption, fontsize=48, fontdict={'weight': 'bold'})

        # Save plot if filename is given.
        if filename is not False:
            if isinstance(filename, str):
                this_filename = filename
            else:
                this_filename = filename[value_index - 2]
            plt.savefig(this_filename, pad_inches=0, bbox_inches='tight', dpi=dpi)

        # Show plot if requested.
        if show_plot:
            plt.show()

        # Close plot.
        plt.close()



def plot_map(data, min_size_px=512, extend_percentage=10, **imshow_kwargs):
    """Plot map for given data.

    Parameters
    ----------
    data : array_like
        The input data.  Columns should be latitude, longitude.
    min_size_px : int, optional
        Minimum size of generated plot in pixels.  Defaults to 512.
    extend_percentage : int, float, optional
        Determines how much the shown map is extended around the
        bounding box of the values.  Given in percent of the bounding
        box extents.  Defaults to 10.
    **imshow_kwargs : optional
        All remaining keyword arguments are passed to matplotlib
        imshow.

    Returns
    -------
    smopy_map : Smopy Map
        The generated smopy map object.
    ax : AxesImage
        The matplotlib AxesImage containing the map.

    """
    # Calculate bounding box and zoom.
    lat_long_min, lat_long_max = calculate_bounding_coordinates(data, extend_percentage=extend_percentage)
    zoom = calculate_optimal_zoom(lat_long_min, lat_long_max, min_size_px)

    # Get map data from OpenStreetMaps.
    dpi = 72
    smopy_map = smopy.Map((*lat_long_min, *lat_long_max), z=zoom)

    # Calculate resulting figure size.
    size = smopy_map.to_pil().size
    print(size)
    figsize = (10/32 + size[0] / dpi, 10/32 + size[1] / dpi)

    # Convert map to matplotlib.
    ax = smopy_map.show_mpl(figsize=figsize, dpi=dpi, **imshow_kwargs)

    # Get the extended bounding box in pixels.
    x_min, y_min = smopy_map.to_pixels(lat_long_max[0], lat_long_min[1])
    x_max, y_max = smopy_map.to_pixels(lat_long_min[0], lat_long_max[1])

    # Set the axes limits to show only the extended bounding box.
    #ax.set_xlim(x_min, x_max)
    #ax.set_ylim(y_max, y_min)
    print(x_min, x_max)
    print(y_min, y_max)

    return smopy_map, ax
