"""
#####################################################################
Copyright (C) 2025 Michele Cappellari  
E-mail: michele.cappellari_at_physics.ox.ac.uk  

Updated versions of this software are available at:  
https://pypi.org/project/powerbin/  

If you use this software in published research, please acknowledge it as:  
“PowerBin method by Cappellari (2025, MNRAS submitted)”  
https://arxiv.org/abs/2509.06903  

This software is provided “as is”, without any warranty of any kind,  
express or implied.  

Permission is granted for:  
 - Non-commercial use.  
 - Modification for personal or internal use, provided that this  
   copyright notice and disclaimer remain intact and unaltered  
   at the beginning of the file.  

All other rights are reserved. Redistribution of the code, in whole or in part,  
is strictly prohibited without prior written permission from the author.  

#####################################################################

V1.0.0: PowerBin created — MC, Oxford, 10 September 2025

"""

from time import perf_counter

import numpy as np
import matplotlib.pyplot as plt
from scipy import ndimage, spatial

from powerbin.bin_accretion import accretion
from powerbin.early_stopper import EarlyStopper
from powerbin.plotting import plot_power_diagram, format_asinh_axis

#----------------------------------------------------------------------------

def power_diagram(xy, xybin, rbin):
    """
    Computes a Power Diagram of the pixel grid (xy) given
    the generators' coordinates and radii (xybin, rbin).
    """
    rmax = 1.001*np.max(np.abs(rbin))   # Needs to make z**2 > 0 below
    znode = np.sqrt(rmax**2 - rbin**2)  # z**2 = R - r**2  Sec.5 Imai+84
    tree = spatial.KDTree(np.column_stack([xybin, znode]))
    _, bin_num = tree.query(np.column_stack([xy, np.zeros(len(xy))]), workers=-1)
    return bin_num

#----------------------------------------------------------------------

def update_bins(fun_capacity, xy, xybin, rbin, args=()):
    """Update the non-empty bin coordinates, sizes, and capacities."""
    bin_num = power_diagram(xy, xybin, rbin)
    bins = np.unique(bin_num)  # This may not have xbin.size if some bins are empty
    for dim in range(xy.shape[1]):
        xybin[bins, dim] = ndimage.mean(xy[:, dim], labels=bin_num, index=bins)
    npix = np.bincount(bin_num, minlength=rbin.size)
    index = ndimage.value_indices(bin_num)
    capacity = np.zeros_like(rbin)
    for j, w in index.items():  # NB: w[0] extracts the ndarray from the tuple (w,)
        capacity[j] = fun_capacity(w[0], *args)
    return xybin, npix, capacity, bin_num

#----------------------------------------------------------------------------

def regularization(xy, xybin, target_capacity, fun_capacity, verbose, args, maxiter):
    """Algorithm 1 of Cappellari (2025, https://arxiv.org/abs/2509.06903)"""

    diff = np.zeros(maxiter)
    rbin = np.ones(len(xybin))

    stopper = EarlyStopper(rel_tol=1e-1, patience=20, window=40)

    for it in range(maxiter):

        xybin_old = xybin.copy()
        xybin, npix, capacity, bin_num = update_bins(fun_capacity, xy, xybin, rbin, args)

        # Nearest neighbours of every bin
        dist = spatial.KDTree(xybin).query(xybin, 2, workers=-1)[0][:, 1]

        w = capacity > 0
        fac = np.ones(len(xybin))
        fac[w] = target_capacity/capacity[w]
        rbin = np.sqrt(fac*npix/np.pi)
        rbin = rbin.clip(0.5, dist)

        diff[it] = np.linalg.norm(xybin - xybin_old)

        if verbose >= 2:
            print(f'Iter: {it:4d}  Diff: {diff[it]:.4g}')

        # Test for convergence
        if diff[it] < 0.1:
            if verbose >= 2:
                print("Converged")
            break
        if stopper.update(diff[it]):
            if verbose >= 2:
                print(f"Early stop at iter {it} (cycling)")
            break
        if verbose >= 3:
            plt.clf()
            plot_power_diagram(xy, None, bin_num, xybin, rbin, npix)
            plt.pause(1)

    # If coordinates have changed, re-compute Tessellation of the pixels grid
    if diff[it] > 0:
        bin_num = power_diagram(xy, xybin, rbin)

    return bin_num, xybin, rbin, capacity, npix, it

#-----------------------------------------------------------------------

class PowerBin:
    """
    PowerBin Class
    ==============

    PowerBin Purpose
    ----------------

    Performs 2D adaptive spatial binning to achieve a target capacity per bin.

    This class implements the **PowerBin** algorithm described in
    `Cappellari (2025) <https://arxiv.org/abs/2509.06903>`_. Like the classic
    Voronoi binning method, it partitions a set of 2D points (pixels) into bins
    so that each bin reaches a nearly constant *capacity* — a user‑defined
    quantity such as signal‑to‑noise squared.

    **Key advances over the classic method include:**

    - **Centroidal Power Diagram tessellation:** Produces bins that are
      nearly round, convex, and connected, and eliminates the disconnected
      or nested bins that could occur with earlier approaches.

    - **Scalability:** Employs a new bin‑accretion algorithm with **O(N log N)**
      time complexity, removing the O(N^2) bottleneck of the original method and
      making million‑pixel datasets practical.

    - **Stable CPD construction:** Uses a heuristic inspired by packed soap
      bubbles, avoiding the numerical fragility of formal CPD solvers with
      realistic non-additive capacities (e.g., correlated noise).

    The algorithm proceeds in two main stages:

    1. **Initial bin‑accretion** to generate starting bin centers.
    2. **Iterative regularization** that adjusts bin shapes using the CPD to
       better equalize bin capacities.

    Parameters
    ----------

    xy: ndarray of shape (npix, 2)
        Coordinates of the pixels to be binned.
    fun_capacity: callable
        Function to compute the capacity of a set of pixels. It must have the
        signature `fun_capacity(indices, *args)`, where `indices` is an array
        of integer indices into the original `xy` array, and `*args` are
        any additional arguments passed via the `args` parameter. The function
        should return a single float value representing the capacity.
    target_capacity: float
        The target capacity for each bin.
    pixelsize: float, optional
        The size of a pixel in the input coordinate units. This is used to
        internally work in pixel units, which is more numerically stable.
        If None, it is estimated as the median distance to the second‑nearest
        neighbor using a KDTree.
    verbose: int, optional
        Controls the level of printed output.
        - 0: No output.
        - 1: Basic summary information (default).
        - 2: Detailed iteration-by-iteration printed progress.
        - 3: Same as 2, but also plots the binning at each iteration.
    regul: bool, optional
        If True (default), perform the iterative regularization step after the
        initial accretion. If False, only the initial accretion is performed.
    args: tuple, optional
        Additional positional arguments to be passed to `fun_capacity`.
    maxiter: int, optional
        Maximum number of iterations for the regularization step (default: 50).

    Attributes
    ----------

    xy: ndarray of shape (npix, 2)
        The original input pixel coordinates.
    dens: ndarray of shape (npix,)
        The input capacity density of every pixel.
    bin_num: ndarray of int of shape (npix,)
        A one‑dimensional array with one entry per element of `xy`, where each
        entry gives the index of the bin containing that pixel. This bin-index
        array is the principal output and is sufficient for any further
        processing of the bins.
    fun_capacity: callable
        The function used to compute bin capacity.
    target_capacity: float
        The target capacity value for the bins.
    pixelsize: float
        The pixel size used for scaling (all internal computations use pixel units).
    verbose: int
        The verbosity level.
    args: tuple
        Additional arguments for `fun_capacity`.
    single: ndarray of bool of shape (nbin,)
        Boolean array indicating which bins contain just one pixel.
    xybin: ndarray of shape (nbin, 2)
        The coordinates of the Power Diagram generators (bin centers), in the
        same units as the input `xy`.
    rbin: ndarray of shape (nbin,)
        The radii of the Power Diagram generators, in the same units as the
        input `xy`.
    capacity: ndarray of shape (nbin,)
        The final calculated capacity for each bin.
    npix: ndarray of int of shape (nbin,)
        The number of pixels in each bin.
    rms_frac: float
        The fractional root-mean-square scatter of the bin capacities,
        calculated for non-single bins, as a percentage.

    References
    ----------
    
    .. [1] Cappellari, M. 2025, MNRAS submitted, https://arxiv.org/abs/2509.06903

    
    ###########################################################################

    """

    def __init__(self, xy, fun_capacity, target_capacity, 
                 pixelsize=None, verbose=1, regul=True, args=(), maxiter=50):

        self.xy = xy
        self.fun_capacity = fun_capacity
        self.target_capacity = target_capacity
        self.verbose = verbose
        self.args = args

        if pixelsize is None:
            dist, _ = spatial.KDTree(xy).query(xy, [2], workers=-1)
            pixelsize = np.median(dist)
        self.pixelsize = pixelsize

        # All operation in powerbin are performed in pixel units
        xy = xy/pixelsize

        t1 = perf_counter()
        xybin, dens = accretion(xy, target_capacity, fun_capacity, verbose, args)
        t2 = perf_counter()

        if regul:
            if verbose >= 1:
                print(f'Regularization...')
            bin_num, xybin, rbin, capacity, npix, it = regularization(
                xy, xybin, target_capacity, fun_capacity, verbose, args, maxiter)
        else:
            it = 0
            rbin = np.zeros(len(xybin))
            xybin, npix, capacity, bin_num = update_bins(fun_capacity, xy, xybin, rbin, args)
            rbin = np.sqrt(npix/np.pi)
        t3 = perf_counter()

        single = npix <= 1   # single or empty bins
        rms = np.std(capacity[~single], ddof=1)/np.mean(capacity[~single])*100

        self.single = single 
        self.bin_num = bin_num
        self.xybin = xybin*pixelsize
        self.rbin = rbin*pixelsize
        self.capacity = capacity
        self.npix = npix
        self.rms_frac = rms
        self.dens = dens

        if verbose >= 1:
            print(f'Bins: {rbin.size}; Unbinned Pixels: {np.sum(single)}/{len(xy)}')
            print(f'Fractional Capacity Scatter (%): {rms:.2f}')
            print(f'Time Accretion: {t2 - t1:.2f} s')
            if regul:
                print(f'Time Regularization (it={it}): {t3 - t2:.2f} s')

#----------------------------------------------------------------------------

    def plot(self, capacity_scale="raw", ylabel=None, ylim=None, magrange=10):
        """
        Plot the bins and the bin capacity vs radius.

        Parameters
        ----------
        capacity_scale: {"raw", "sqrt"}
            Transform to apply to the internal capacity quantity before plotting.

            - "raw":  Plot the stored quantity directly. This is the form you
            would typically optimise on if the quantity is already in the
            desired additive form — for example, (S/N)^2, inverse variance,
            or any metric that adds linearly across pixels/bins.

            - "sqrt": Plot the square root of the stored quantity. This is
            useful when the stored quantity is something like (S/N)^2:
            taking the square root recovers S/N itself, which is often the
            more intuitive scale for presentation, while still benefiting
            from the fact that the squared form adds linearly in the
            Poissonian limit.

        ylabel: str or None
            Custom y-axis label. If None, a default is chosen from base_label
            and the transform.

        magrange: float
            Magnitude range for the left panel density contours.

        """
        xy = self.xy / self.pixelsize
        xybin = self.xybin / self.pixelsize
        rbin = self.rbin / self.pixelsize
        npix = self.npix
        bin_num = self.bin_num

        dens = self.dens
        capacity = self.capacity
        target_capacity = self.target_capacity

        if capacity_scale == "sqrt":
            dens = np.sqrt(dens)
            capacity = np.sqrt(capacity)
            target_capacity = np.sqrt(target_capacity)

        if ylabel is None:
            ylabel = "Capacity"

        single = npix <= 1

        rx, ry = np.ptp(xy, axis=0)
        rat1 = ry / rx
        rat2 = 3 / 4

        fig, (ax0, ax1) = plt.subplots(1, 2, width_ratios=[rat2, rat1], constrained_layout=True)

        plt.sca(ax0)
        plot_power_diagram(xy, dens, bin_num, xybin, rbin, npix, magrange)

        plt.sca(ax1)
        ax1.set_box_aspect(rat2)
        r = np.hypot(*xy.T)
        rad = np.hypot(*xybin.T)
        ax1.plot(r, dens, '.k', label='Input')
        if single.sum() > 0:
            ax1.plot(rad[single], capacity[single], 'xb', label='Single')
        ax1.plot(rad[~single], capacity[~single], 'or', label='Bins')
        ax1.plot(rad[~single], capacity[~single], '.k', markersize=0.5)
        ax1.axhline(target_capacity, linestyle='--')
        ax1.axis([-1, np.max(r), np.min(dens), np.max(capacity) * 1.5])
        ax1.set_yscale('asinh')
        format_asinh_axis(ax1)
        ax1.set_xlabel('R (pixels)')
        ax1.set_ylabel(ylabel)
        if ylim is not None:
            ax1.set_ylim(ylim)
        ax1.legend(loc='best', handletextpad=0)

#----------------------------------------------------------------------------
