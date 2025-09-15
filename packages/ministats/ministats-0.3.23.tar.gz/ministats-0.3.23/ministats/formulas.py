
import numpy as np

from .estimators import mean
from .estimators import var


# STANDARDIZED EFFECT SIZE MEASURES
################################################################################

def cohend(sample, mu0):
    """
    Compute Cohen's d for one group compared to the theoretical mean `mu0`.
    """
    mean = np.mean(sample)
    std = np.std(sample, ddof=1)
    d = (mean - mu0) / std
    return d


def cohend2(sample1, sample2):
    """
    Compute Cohen's d measure of effect size for two independent samples.
    """
    n1, n2 = len(sample1), len(sample2)
    mean1, mean2 = mean(sample1), mean(sample2)
    var1, var2 = var(sample1), var(sample2)
    # calculate the pooled variance and standard deviation
    varp = ((n1-1)*var1 + (n2-1)*var2) / (n1 + n2 - 2)
    stdp = np.sqrt(varp)
    d = (mean1 - mean2) / stdp
    return d



# UTILS
################################################################################

def calcdf(stdX, n, stdY, m):
    """
    The Welch-Satterthwaite formula for the degrees of freedom parameter
    used for confidence intervals and Welch's t-test.
    """
    vX = stdX**2 / n
    vY = stdY**2 / m
    df = (vX + vY)**2 / (vX**2/(n-1) + vY**2/(m-1))
    return df



# KOLMOGOROV-SMIRNOV DISTANCE
################################################################################

def ks_distance(sample, rv):
    """
    Compute the Kolmogorov-Smirnov distance between an data in `sample` and 
    and the CDF function of the random variable `rv`.
    """
    n = len(sample)
    sample = np.sort(sample)

    # Empirical CDF values: i/n for the right-limit, (i-1)/n for left-limit
    ecdf_vals = np.arange(1, n+1) / n
    cdf_vals = rv.cdf(sample)

    # Compute KS distances
    ks_dist_plus = np.max(ecdf_vals - cdf_vals)
    ks_dist_minus = np.max(cdf_vals - (np.arange(0, n) / n))
    max_ks_dist = max(ks_dist_plus, ks_dist_minus)

    return max_ks_dist
