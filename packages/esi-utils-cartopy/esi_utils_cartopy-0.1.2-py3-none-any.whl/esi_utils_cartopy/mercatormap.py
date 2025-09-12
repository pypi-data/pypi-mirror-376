# local imports
import cartopy.crs as ccrs
import matplotlib

# third party imports
import matplotlib.font_manager as fm
import matplotlib.patheffects as path_effects
import matplotlib.pyplot as plt
import numpy as np
import pyproj
from esi_utils_geo.city import Cities

matplotlib.use("Agg")

XOFFSET = 4  # how many pixels between the city dot and the city text


class MercatorMap(object):
    def __init__(self, bounds, figsize, cities, padding=0.25, dimensions=[0, 0, 1, 1]):
        """
        Create an instance of MercatorMap, container class for Cartopy GeoAxes
        and city labeling.

        Usage:

        .. code-block:: python

            # set up your desired map extent
            bounds = xmin,ymin,xmax,ymax = \
                (-121.046000,-116.046000,32.143500,36.278500)

            # define desired figure width,height
            figsize = (7, 7)

            # create impactutils.Cities() instance
            cities = Cities.fromDefault()

            # Create Mercator map object
            mmap = MercatorMap(bounds,figsize,cities,padding=0.5)

            # retrieve the figure and Cartopy GeoAxes instances
            fig = mmap.figure
            ax = mmap.axes

            # this needs to be done here so that city label collision
            # detection will work
            fig.canvas.draw()

            # do whatever mapping things you need with the axes object
            # you've retrieved.
            ax.coastlines(resolution="10m", zorder=10)

            #when ready, call the drawCities method
            mmap.drawCities(shadow=True)

        Args:
            bounds: Tuple of floats (lon_min, lon_max, lat_min, lat_max).
            figsize: Tuple of floats (fig_width_inches, fig_height_inches)
            cities: impactutils Cities() instance.
            padding: Desired buffer around each cities bounding box. A padding
                value of 0.25 means that each city's bounding box be padded by
                25% of the width or height on each side (left, right, top,
                bottom).

        """
        self._cities = cities.limitByBounds(bounds)
        xmin, xmax, ymin, ymax = bounds
        clon = (xmin + xmax) / 2
        if xmax < 0 and xmax < xmin:
            clon = (xmin + (xmax + 360)) / 2

        # clat = (ymin + ymax) / 2
        # Commenting out min_latitude because of this issue:
        # https://github.com/SciTools/cartopy/issues/1155#issuecomment-432941088
        # This seems to be a better, more consistent fix than dividing
        # proj._threshold by 6
        self._proj = ccrs.Mercator(
            central_longitude=np.round(clon, decimals=1),
            #  min_latitude=ymin,
            max_latitude=ymax,
            globe=None,
        )
        # self._proj = ccrs.AzimuthalEquidistant(central_longitude=clon,
        #                                        central_latitude=clat,
        #                                        globe=None)
        self._geoproj = ccrs.PlateCarree()

        # set up an axes object
        self._figure = plt.figure(figsize=figsize)
        self._ax = self._figure.add_axes(dimensions, projection=self._proj)
        try:
            self._ax.set_extent([xmin, xmax, ymin, ymax], crs=self._geoproj)
        except Exception:
            pproj = pyproj.Proj(self._proj.proj4_init)
            ulx, uly = pproj(xmin, ymax)
            lrx, lry = pproj(xmax, ymin)
            self._ax.set_extent([ulx, lrx, lry, uly], crs=self._proj)

        # set up an identical axes object - this will be used to determine city
        # label collisions.
        self._figure_clone = plt.figure(figsize=figsize)
        self._ax_clone = self._figure_clone.add_axes(
            [0, 0, 1, 1], projection=self._proj
        )
        self._ax_clone.set_extent([xmin, xmax, ymin, ymax], crs=self._geoproj)

        # establish list of supported fonts
        self._fontlist = [f.name for f in fm.fontManager.ttflist]
        self._fontlist.sort()

        self._padding = padding

        plt.sca(self._ax)

    def __del__(self):
        plt.close(self._figure)
        plt.close(self._figure_clone)

    @property
    def figure(self):
        """Return the figure contained in the MercatorMap object.

        :returns:
          Matplotlib Figure instance.
        """
        return self._figure

    @property
    def axes(self):
        """Return the GeoAxes contained in the MercatorMap object.

        :returns:
          Cartopy GeoAxes instance.
        """
        return self._ax

    @property
    def proj(self):
        """
        Return the Cartopy CRS Mercator projection contained in the MercatorMap
        object.

        Returns:
            CRS Mercator projection object.
        """
        return self._proj

    @property
    def geoproj(self):
        """
        Return the Cartopy CRS PlateCarree projection contained in the
        MercatorMap object.

        Returns:
            CRS PlateCarree projection object.
        """
        return self._geoproj

    def getFigureClone(self):
        """
        Return the second "hidden" figure object, which is used for determining
        city label collisions.

        Probably only useful for debugging.

        Returns:
            Matplotlib Figure instance.
        """
        return self._figure_clone

    def getAxesClone(self):
        """
        Return the second "hidden" GeoAxes object, which is used for
        determining city label collisions.

        Probably only useful for debugging.

        Returns:
            Cartopy GeoAxes instance.
        """
        return self._axes_clone

    def getFonts(self):
        """Get list of supported fonts.

        Returns:
            List of supported font strings.
        """
        return self._fontlist

    def drawCities(
        self,
        fontname="DejaVu Sans",
        fontsize=10.0,
        shadow=False,
        draw_dots=False,
        zorder=10,
    ):
        """Render cities on map axes (obtainable through the axes property).

        Args:
            fontname: Desired font name for city labels.
            fontsize: Desired font size for city labels.
            shadow: Boolean indicating whether drop-shadow effect should be
                applied.
            draw_dots: Boolean indicating whether city locations should
                be marked with a black dot.
            zorder: Desired plotting z-order for city labels and dots.

        Returns:
            Cities() instance containing all cities that were rendered on the
            map.

        Raises:
            KeyError: When font name is not one of the supported Matplotlib
                font names.
        """
        # set the active axes to be the clone
        plt.sca(self._ax_clone)
        # cut down on the number of cities we can draw from
        self._cities = self._cities.limitByGrid(nx=2, ny=2, cities_per_grid=15)
        # pare down cities by removing small cities that collide with larger
        # ones.
        if len(self._cities):
            self.limitByMapCollision(fontname, fontsize, shadow, zorder)
        # set the active axes to be the "real" axes object that we want to
        # draw on
        plt.sca(self._ax)
        for idx, row in self._cities._dataframe.iterrows():
            if draw_dots:
                self._ax.plot(
                    row["lon"], row["lat"], "k.", transform=self._geoproj, zorder=zorder
                )
            _ = self.renderRow(row, fontname, fontsize, shadow, zorder, test=False)

        return Cities(self._cities._dataframe)

    def limitByMapCollision(self, fontname, fontsize, shadow, zorder):
        """
        Limit cities found on map by removing smaller cities that collide with
        larger ones.

        Args:
            fontname: Desired font name for city labels.
            fontsize: Desired font size for city labels.
            shadow: Boolean indicating whether drop-shadow effect should be
                applied.
            zorder: Desired plotting z-order for city labels and dots.

        Raises:
            KeyError: When font name is not one of the supported Matplotlib
                font names.
        """
        # make a copy of the internal dataframe
        newdf = self._cities._dataframe.copy()

        # sort that copy by descending population
        newdf = newdf.sort_values(by="pop", ascending=False)

        # get the bounding boxes of all cities as drawn on the map
        lefts, rights, bottoms, tops = self.getCityBoundingBoxes(
            newdf, fontname, fontsize, shadow, zorder
        )

        # remove those cities that were off the map
        ikeep = ~np.isnan(lefts)

        # create new dataframe with cities that are on the map
        newdf = newdf.iloc[ikeep]
        lefts = lefts[ikeep]
        rights = rights[ikeep]
        bottoms = bottoms[ikeep]
        tops = tops[ikeep]
        ikeep = [0]  # indices of non-overlapping cities in dataframe
        for i in range(1, len(tops)):
            # what is this cities name?
            # Seems like an unused variable...
            # cname = newdf.iloc[i]['name']

            # what is the bounding box of this city
            left = lefts[i]
            right = rights[i]
            bottom = bottoms[i]
            top = tops[i]

            # does this bounding box insersect with any larger city's
            # bounding box?
            clrx = (left > rights[0:i]) | (right < lefts[0:i])
            clry = (top < bottoms[0:i]) | (bottom > tops[0:i])
            allclr = clrx | clry
            if all(allclr):
                ikeep.append(i)

        newdf = newdf.iloc[ikeep]
        newdf["top"] = tops[ikeep]
        newdf["bottom"] = bottoms[ikeep]
        newdf["left"] = lefts[ikeep]
        newdf["right"] = rights[ikeep]
        self._cities = Cities(newdf)

    def getCityBoundingBoxes(self, df, fontname, fontsize, shadow, zorder):
        """Get the bounding boxes of all cities in input dataframe.

        Args:
            df: DataFrame from Cities() instance.
            fontname: Desired font name for city labels.
            fontsize: Desired font size for city labels.
            shadow: Boolean indicating whether drop-shadow effect should be
                applied.
            zorder: Desired plotting z-order for city labels and dots.

        Returns:
            Tuple of numpy arrays of left,right,bottom and top edges of each
            city's bounding box.
        """

        # get the extent of the map
        axmin, axmax, aymin, aymax = self._ax_clone.get_extent()

        # make arrays of the edges of all the bounding boxes
        tops = np.ones(len(df)) * np.nan
        bottoms = np.ones(len(df)) * np.nan
        lefts = np.ones(len(df)) * np.nan
        rights = np.ones(len(df)) * np.nan

        # get the extent of the first city
        left, right, bottom, top = self.getCityEdges(
            df.iloc[0], fontname, fontsize, shadow, zorder
        )
        lefts[0] = left
        rights[0] = right
        bottoms[0] = bottom
        tops[0] = top

        # loop over all the cities and get their extents on the map
        for i in range(1, len(df)):
            row = df.iloc[i]
            left, right, bottom, top = self.getCityEdges(
                row, fontname, fontsize, shadow, zorder
            )
            # remove cities that have any portion off the map
            if left < axmin or right > axmax or bottom < aymin or top > aymax:
                continue
            lefts[i] = left
            rights[i] = right
            bottoms[i] = bottom
            tops[i] = top

        return (lefts, rights, bottoms, tops)

    def getCityEdges(self, row, fontname, fontsize, shadow, zorder):
        """Get the bounding box of a cities in input row.

        Args:
            row: DataFrame from Cities() instance.
            fontname: Desired font name for city labels.
            fontsize: Desired font size for city labels.
            shadow: Boolean indicating whether drop-shadow effect should be
                applied.
            zorder: Desired plotting z-order for city labels and dots.

        Returns:
            Tuple of left,right,bottom and top edges of input city's bounding
            box.
        """
        th = self.renderRow(row, fontname, fontsize, shadow, zorder, test=True)
        bbox = th.get_window_extent(self._figure.canvas.get_renderer())
        axbox = bbox.transformed(self._ax_clone.transData.inverted())
        left, bottom, right, top = axbox.extents
        xpad = (right - left) * self._padding
        ypad = (top - bottom) * self._padding
        left = left - xpad
        right = right + xpad
        bottom = bottom - ypad
        top = top + ypad
        return (left, right, bottom, top)

    def renderRow(self, row, fontname, fontsize, shadow, zorder, test=True):
        """Render the city in input row.

        Args:
            row: DataFrame from Cities() instance.
            fontname: Desired font name for city labels.
            fontsize: Desired font size for city labels.
            shadow: Boolean indicating whether drop-shadow effect should be
                applied.
            zorder: Desired plotting z-order for city labels and dots.
            test: Boolean indicating whether to render city on cloned axes
                (True) or user's visible axes (False).

        Returns:
            Matplotlib Text instance.
        """
        if test:
            ax = self._ax_clone
        else:
            ax = self._ax

        ha = "left"
        va = "center"
        display1 = (1, 1)
        display2 = (1 + XOFFSET, 1)
        data1 = ax.transData.inverted().transform((display1))
        data2 = ax.transData.inverted().transform((display2))
        data_x_offset = data2[0] - data1[0]

        proj = pyproj.Proj(ax.projection.proj4_init)
        tx, ty = proj(row["lon"], row["lat"])
        tx = tx + data_x_offset

        if shadow:
            th = ax.text(
                tx,
                ty,
                row["name"],
                fontname=fontname,
                color="black",
                fontsize=fontsize,
                ha=ha,
                va=va,
                zorder=zorder,
                transform=ax.projection,
            )
            th.set_path_effects(
                [
                    path_effects.Stroke(linewidth=2.0, foreground="white"),
                    path_effects.Normal(),
                ]
            )
        else:
            th = ax.text(
                tx,
                ty,
                row["name"],
                fontname=fontname,
                fontsize=fontsize,
                ha=ha,
                va=va,
                zorder=zorder,
                transform=ax.projection,
            )

        return th
