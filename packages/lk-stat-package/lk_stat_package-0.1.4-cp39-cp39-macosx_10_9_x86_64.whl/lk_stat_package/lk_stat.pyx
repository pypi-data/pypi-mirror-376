# cython: boundscheck=False, wraparound=False, nonecheck=False, cdivision=True
cimport cython
cimport numpy as np
import numpy as np
from libc.stdlib cimport malloc, free

@cython.boundscheck(False)
@cython.wraparound(False)
def lk_stat(double[:] periods, double[:] mag, double[:] magerr, double[:] Time):
    """
    Compute the Lafler–Kinman statistic for a given set of periods, magnitudes, and errors.
    """

    cdef int periods_size = periods.shape[0]
    cdef int data_size = mag.shape[0]
    cdef double p, phi_val, diff, w, sum_w, sum_w_diff_sq, sum_var
    cdef int i, j

    # Output array
    cdef np.ndarray[np.float64_t, ndim=1] theta_array = np.zeros(periods_size, dtype=np.float64)

    # Temp array for phases
    cdef np.ndarray[np.float64_t, ndim=1] phi = np.empty(data_size, dtype=np.float64)
    cdef np.ndarray[np.intp_t, ndim=1] order

    # Precompute weighted mean magnitude (constant for all periods)
    cdef double sum_wm = 0.0
    cdef double sum_wtot = 0.0
    cdef double mean_m
    for j in range(data_size):
        sum_wm += mag[j] / (magerr[j] * magerr[j])
        sum_wtot += 1.0 / (magerr[j] * magerr[j])
    mean_m = sum_wm / sum_wtot

    # Loop over periods
    for i in range(periods_size):
        p = periods[i]

        # Compute fractional phases
        for j in range(data_size):
            phi_val = Time[j] / p
            phi[j] = phi_val - <int>phi_val   # keep fractional part only

        # Sort indices by phi
        order = np.argsort(phi)

        # Reset accumulators
        sum_w = 0.0
        sum_w_diff_sq = 0.0
        sum_var = 0.0

        # Compute sums in a single pass
        for j in range(1, data_size):
            diff = mag[order[j]] - mag[order[j - 1]]
            w = 1.0 / (magerr[order[j]] * magerr[order[j]] +
                       magerr[order[j - 1]] * magerr[order[j - 1]])
            sum_w += w
            sum_w_diff_sq += w * (diff * diff)
            sum_var += (mag[order[j]] - mean_m) * (mag[order[j]] - mean_m)

        theta_array[i] = sum_w_diff_sq / (sum_var * sum_w)

    return theta_array