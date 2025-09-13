#!/usr/bin/env python
"""
  Copyright (C) 2013-2025, Michele Cappellari
  E-mail: michele.cappellari_at_physics.ox.ac.uk
  http://purl.org/cappellari/software

  See example at the bottom for usage instructions.

MODIFICATION HISTORY:
    V1.0.0: Michele Cappellari, Paranal, 11 November 2013
    V1.0.1: Clip values before contouring. MC, Oxford, 26 February 2014
    V1.0.2: Include SAURON colormap. MC, Oxford, 29 January 2014
    V1.0.3: Call set_aspect(1). MC, Oxford, 22 February 2014
    V1.0.4: Call autoscale_view(tight=True). Overplot small dots by default.
        MC, Oxford, 25 February 2014
    V1.0.5: Use axis('image'). MC, Oxford, 29 March 2014
    V1.0.6: Allow changing colormap. MC, Oxford, 29 July 2014
    V1.0.7: Added optional fixpdf keyword to remove PDF visual artifacts.
      - Make nice tick levels for colorbar. Added nticks keyword for colorbar.
        MC, Oxford, 16 October 2014
    V1.0.8: Return axis of main plot. MC, Oxford, 26 March 2015
    V1.0.9: Clip values within +/-eps of vmin/vmax, to assign clipped values
        the top colour in the colormap, rather than having an empty contour.
        MC, Oxford, 18 May 2015
    V1.0.10: Removed optional fixpdf keyword and replaced with better solution.
        MC, Oxford, 5 October 2015
    V1.0.11: Activate main plot after colorbar. Return plot rather than axis.
        MC, Oxford, 6 November 2015
    V1.0.12: Simplified passing of default keywords. Included np.ravel(flux).
        MC, Oxford, 16 February 2017
    V1.1.0: Use tricontourf(extend=...) insted of clipping, for better contours.
        The colorbar edges show when contours do not extend to full range.
        MC, Oxford, 23 March 2017
    V1.1.1: Use register_sauron_colormap(). MC, Oxford, 29 March 2017
    V1.1.2: Removed fix for gaps in colorbar. MC, Oxford, 15 December 2017
    V1.1.3: Changed imports for plotbin as a package. MC, Oxford, 17 April 2018
    V1.1.4: Included `linescolor` keyword. MC, Oxford, 30 April 2018
    V1.1.5: Commented set_edgecolor to avoid bug in Matplotlib 3.3.
        MC, Oxford, 24 September 2020
    V1.1.6: Re-activated set_edgecolor. MC, Oxford, 8 April 2022
    V1.1.7: Removed .collections loop, which was deprecated in Matplotlib 3.8.
        Ensure ticks are within the given limits (to fix a new Matplotlib bug).
        Use default_rng instead of deprecated numpy.random. 
        MC, Oxford, 4 June 2024
    V1.1.8: Removed dependency on mpl_toolkits.axes_grid1.make_axes_locatable.
        This fixes a new Matplotlib bug when saving the colorbar to a PDF file.
        MC, Oxford, 12 December 2024
    V1.1.9: Allow for negative flux values in log contour plot. 
        MC, Oxford, 30 August 2025

"""

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from plotbin.sauron_colormap import register_sauron_colormap

##############################################################################


def plot_velfield(x, y, vel, vmin=None, vmax=None, ncolors=64,
                  nodots=False, colorbar=False, linescolor='k', label=None,
                  flux=None, nticks=7, markersize=3, cmap='sauron', **kwargs):

    x, y, vel, flux = map(np.ravel, [x, y, vel, flux])

    assert x.size == y.size == vel.size, 'The vectors (x, y, vel) must have the same size'

    if cmap in ['sauron', 'sauron_r']:
        register_sauron_colormap()

    if vmax is None and vmin is None:
        vmin, vmax = np.min(vel), np.max(vel)
        extend = 'neither'
    elif vmax is None:
        vmax = np.max(vel)
        extend = 'min'
    elif vmin is None:
        vmin = np.min(vel)
        extend = 'max'
    else:
        extend = 'both'

    levels = np.linspace(vmin, vmax, ncolors)

    ax = plt.gca()

    cnt = ax.tricontourf(x, y, vel, levels=levels, cmap=cmap, extend=extend, **kwargs)

    # Remove white gaps in contour levels of PDF  http://stackoverflow.com/a/32911283/
    cnt.set_edgecolor("face")  

    ax.axis('image')  # Equal axes and no rescaling

    if flux[0] is not None:
        levels = np.max(flux)*10**(-0.4*np.arange(20)[::-1])  # 1 mag contours
        ax.tricontour(x, y, flux, levels=levels, colors=linescolor) 

    if not nodots:
        ax.plot(x, y, '.k', markersize=markersize, **kwargs)

    if colorbar:
        cax = ax.inset_axes([1.02, 0, .05, 1], transform=ax.transAxes)
        ticks = MaxNLocator(nticks).tick_values(vmin, vmax)
        ticks = ticks[(ticks >= vmin) & (ticks <= vmax)]  # Fix Matplotlib bug
        cbar = plt.colorbar(cnt, cax=cax, ticks=ticks)
        if label is not None:
            cbar.set_label(label)
        plt.sca(ax)  # Activate main plot before returning

    return cnt

##############################################################################

# Usage example for plot_velfield()

if __name__ == '__main__':

    prng = np.random.default_rng(123) 
    xbin, ybin = prng.uniform(low=[-30, -20], high=[30, 20], size=(300, 2)).T
    inc = 60.                       # assumed galaxy inclination
    r = np.sqrt(xbin**2 + (ybin/np.cos(np.radians(inc)))**2) # Radius in the plane of the disk
    a = 40                          # Scale length in arcsec
    vr = 2000*np.sqrt(r)/(r+a)      # Assumed velocity profile
    vel = vr * np.sin(np.radians(inc))*xbin/r # Projected velocity field
    flux = np.exp(-r/10)

    plt.clf()
    plt.title('Velocity')
    plot_velfield(xbin, ybin, vel, flux=flux, colorbar=True, label='km/s', vmin=-120, vmax=120)
    plt.pause(10)
