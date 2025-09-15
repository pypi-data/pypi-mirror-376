"""
extracted from beampython by M. Lehujeur (commit 080dee4)
"""

from typing import Union
import warnings
import numpy as np
from scipy.fftpack import fft, ifft, fftfreq


def freqs2edges(freqs: np.ndarray) -> np.ndarray:
    """
    :param freqs: frequency array, sorted, positive
    :return freqs_edges:
        array with one more sample than freqs
        corresponding to bin edges associtated to freqs
    """

    assert (freqs >= 0).all()
    assert (freqs[1:] > freqs[:-1]).all(), freqs
    assert len(freqs) > 2

    assert freqs[0] != 0., 'could not compute finf'
    finf = freqs[0] ** 2. / freqs[1]  # freqs[0] / (freqs[1] / freqs[0])

    assert freqs[-2] != 0., 'could not compute fsup'
    fsup = freqs[-1] ** 2. / freqs[-2]  # freqs[-1] * (freqs[-1] / freqs[-2])

    fmid = np.sqrt(freqs[:-1] * freqs[1:])
    freqs_edges = np.concatenate(([finf], fmid, [fsup]))
    return freqs_edges


def edges(x):

    if x.max() < 0.:
        # all negative => compute for all positive
        return -edges(-x)

    if x.min() < 0.:
        raise ValueError("x must be all positive or all negative")

    # x is strictly positive
    assert x.min() > 0.

    if (x[1:] <= x[:-1]).all():
        # x is decreasing
        return edges(x[::-1])[::-1]

    # x is growing
    assert (x[1:] >= x[:-1]).all()
    return freqs2edges(x)


def arg_nearest1d_sorted(a, v):
    b = .5 * (a[1:] + a[:-1])
    i = np.searchsorted(b, v)
    return i


class PW:
    def __init__(
            self,
            npts: int,
            delta: float,
            offset_array: np.ndarray,
            offset0: float,
            velocity_array: np.ndarray,
            fmin: float, fmax: float,
            nfreq: int = 200, fscale: str = "lin",
        ):

        assert 0 < fmin < fmax, ValueError

        self.npts = npts
        self.delta = delta
        self.offset_array = offset_array
        self.offset0 = offset0
        self.nsta = len(self.offset_array)

        # all fft frequencies
        fftfreqs = fftfreq(self.npts, self.delta)

        # selector for fft frequencies
        if fscale == "lin":
            freqs = np.linspace(fmin, fmax, nfreq)

        elif fscale == "log":
            freqs = np.logspace(np.log10(fmin), np.log10(fmax), nfreq)

        else:
            raise ValueError(fscale)

        self.ifreq = arg_nearest1d_sorted(a=fftfreqs[:self.npts // 2 + self.npts % 2], v=freqs)
        self.ifreq = np.unique(self.ifreq)

        self.freq_array = fftfreqs[self.ifreq]
        self.freq_edges = edges(self.freq_array)
        self.nfreq = len(self.freq_array)

        self.velocity_array = velocity_array
        self.velocity_edges = edges(velocity_array)
        self.nvel = len(self.velocity_array)

        # store the complex sinusoids in memory
        # shape (nvel, nsta, nfreq)
        # 1d arrays extended to 3d to match e
        _velocity_array = velocity_array[:, np.newaxis, np.newaxis]
        _absoffsets_array = np.abs(self.offset_array - self.offset0)[np.newaxis, :, np.newaxis]
        _freq_array = fftfreqs[np.newaxis, np.newaxis, self.ifreq]

        self.e = np.asarray(
            np.exp(+2.j * np.pi * _freq_array * _absoffsets_array / _velocity_array),
            dtype=np.complex64)

    def __call__(self, fourierdata: np.ndarray):
        """
        fourierdata shape (nsta, nfreq)
        """
        assert fourierdata.shape == (self.nsta, self.npts)
        dg = (fourierdata[np.newaxis, :, self.ifreq] * self.e).sum(axis=1) / float(self.nsta)
        return np.abs(dg) ** 2.

    def pcolormesh(self, ax, dg, **kwargs):
        print(kwargs)
        return ax.pcolormesh(
            self.freq_edges, self.velocity_edges, dg, **kwargs)

    def contourf(self, ax, dg, **kwargs):
        return ax.contourf(
            self.freq_array, self.velocity_array, dg, **kwargs)
