#! /usr/bin/env python

# vim:syntax=python

# Joseph Anderson 2007


# Muse
# ==========

# This is the start of the Muse project, a Music V type language.

# Built on pyaudiolab.
# """


# seem to need to have these imports here. . . to make sure names are defined
# from numpy import *
# from pyaudiolab import *
from muse import *
from generators import *
from scipy.signal import *
from scipy.signal.signaltools import *


# #=========================
# # Definition of constants
# #=========================


#=========================
# Functions
#=========================


#=========================
# FIR Filter Designers
#=========================

# should add IIR methods. . .

# ceptral methods
def rceps(b, min = -120.):
    """rceps(b, min = -120.)

    Return the real part of the cepstrum of kernel b.
    
    Inputs:
    
      b  -- signal (or filter) kernel
      min -- minimum dB value to clip amplitude response to.
               Reduces time aliasing.

    Outputs:
    
      b -- resulting kernel.
    """
    res = real(
        ifft(
            log(
                clip(
                    abs(fft(b)),
                    db_to_amp(min),
                    inf))))

    return res


def irceps(b):
    """irceps(b)

    Return the real part of the inverse cepstrum of kernel b.
    
    Inputs:
    
      b  -- signal (or filter) kernel
      min -- minimum value to clip input fft to.

    Outputs:
    
      b -- resulting kernel.
    """
    res = real(
        ifft(
            numpy.exp(
                fft(b))
            ))

    return res


# FIR methods. . . 

def reff(b, Wn):
    """reff(b, Wn)

    Return spectral reflection of kernel b about Wn.
    
    Inputs:
    
      b  -- filter kernel
      Wn -- center frequency of reflection (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)

    Outputs:
    
      b -- resulting kernel.
    """
    N = len(b)

    if N % 2 is 1:
        phi = (1 - N) * pi / 2 * Wn
        reff_b = 2 * fcososc(Wn, phi, N) * b

    else:
        phi = ((1 - N) * Wn + cos(pi / 2 * Wn)) * pi / 2
        reff_b = 2 * fsinosc(Wn, phi, N) * b

    return reff_b


def mirf(b):
    """mirf(b)

    Return spectral mirror of kernel b.
    (Reflection about Nyquist)
    """
    mir_b = .5 * reff(b, 1.)
    
    return mir_b


def invf(b):
    """invf(b)

    Return spectral inversion of kernel b.

    b + invf(b) returns allpass

    Note: invf is not optimal for even length b
    """
    N = len(b)

    ap_b = zeros(N)
    ap_b[N / 2] = 1

    inv_b = ap_b - b
    
    return inv_b


# minimum phase
# see: http://www.sfr-fresh.com/unix/privat/uade-2.09.tar.gz:a/uade-2.09/contrib/sinc-integral.py
# UADE (Unix Amiga Delitracker Emulator) plays old Amiga tunes with UAE emulation.
# Jens Schleusener 
# (T-Systems SfR)
# Bunsenstr. 10 
# D-37083 Gottingen 
# E-Mail: Jens.Schleusener@t-systems-sfr.com
# E-Mail: info@sfr-fresh.com

# also see. . .
# JOS:
# http://ccrma-www.stanford.edu/~jos/fp/Creating_Minimum_Phase_Filters.htmlhttp://ccrma-www.stanford.edu/~jos/fp/Creating_Minimum_Phase_Filters.html
# http://ccrma.stanford.edu/~jos/sasp/Minimum_Phase_Filter_Design.html
# http://ccrma.stanford.edu/~jos/fp/Matlab_Utilities.html
# http://ccrma.stanford.edu/~jos/sasp/Minimum_Phase_Causal_Cepstra.html#sec:laurent

# Cain:
# http://www.music.columbia.edu/pipermail/music-dsp/2004-February/059372.html

# see also:
# http://cnx.org/content/m12469/latest/

# for cepstrum see:
# http://www.dsprelated.com/showmessage/48073/1.php

def minf(b, min = -120., oversampling = 8):
    """minf(b, min = -120., oversampling = 8)

    Return a magnitude equivalent minimum phase kernel from b.
    
    Inputs:
    
      b  -- filter kernel
      min -- minimum dB value to clip amplitude response to.
               Reduces time aliasing.
      oversampling -- fft * size oversampling.
               Reduces time aliasing.

    Outputs:
    
      b -- resulting kernel.
    """
    n_b = len(b)                # length of input

    p = append(b,
               zeros(n_b * (oversampling - 1))
               )                # zero padded input

    n_p = len(p)                # length of padded

    # compute the real cepstrum
    x = rceps(p, min)

    # window the cepstrum so anticausal components are rejected
    w = zeros(n_p)
    w[0] = 1.
    w[1:n_p / 2] = 2.

    x *= w

    # take the inverse real cepstrum to return minimum phase
    res = irceps(x)[:n_b]

    return res


# consider replacing FIR design methods with sinc methods
# see also: http://www.nicholson.com/rhn/dsp.html
def fir_lp(N, Wn, width=pi):
    """fir_lp(N, Wn, width=pi)

    Lowpass FIR Filter Design using windowed ideal filter method, with the
    Kaiser window.
    
    Inputs:
    
      N  -- order of filter (number of taps)
      Wn -- cutoff frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.
    
    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    return firwin(N, Wn, window = ('kaiser', width))


def fir_hp(N, Wn, width=pi):
    """fir_hp(N, Wn, width=pi)

    Highpass FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N  -- order of filter (number of taps)
      Wn -- cutoff frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.
    
    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    lp_b = fir_lp(N, Wn, width)
    hp_b = invf(lp_b)

    return hp_b


def fir_ls(N, Wn, k, width=pi):
    """fir_ls(N, Wn, k, width=pi)

    Low shelf FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N  -- order of filter (number of taps)

      Wn -- cutoff frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      k -- scale at low frequencies
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.
        
    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    lp_b = fir_lp(N, Wn, width)
    hp_b = invf(lp_b)

    ls_b = k * lp_b + hp_b

    return ls_b


def fir_hs(N, Wn, k, width=pi):
    """fir_hs(N, Wn, k, width=pi)

    High shelf FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N  -- order of filter (number of taps)

      Wn -- cutoff frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      k -- scale at high frequencies
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.
    
    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    lp_b = fir_lp(N, Wn, width)
    hp_b = invf(lp_b)

    hs_b = lp_b + k * hp_b

    return hs_b


def fir_bp(N, Wn, bw, width=pi):
    """fir_bp(N, Wn, bw, width=pi)

    Bandpass FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N      -- order of filter (number of taps)
      Wn -- center frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      bw -- bandwidth of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.

    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    if N % 2 is 1:
        lp_b = fir_lp(N, bw / 2, width)
        
        bp_b = reff(lp_b, Wn)
        
    else:
        bp_b = fir_lp(N, Wn + bw / 2, width) - fir_lp(N, Wn - bw / 2, width)

    return bp_b


def fir_bs(N, Wn, bw, width=pi):
    """fir_bs(N, Wn, bw, width=pi)

    Bandstop FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N      -- order of filter (number of taps)
      Wn -- cutoff frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      bw -- bandwidth of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.
        
    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    if N % 2 is 1:
        bp_b = fir_bp(N, Wn, bw, width)
        
        bs_b = invf(bp_b)
        
    else:
        bs_b = fir_hp(N, Wn + bw / 2, width) + fir_lp(N, Wn - bw / 2, width)

    return bs_b


def fir_pk(N, Wn, bw, k, width=pi):
    """fir_pk(N, Wn, bw, k, width=pi)

    Peaking FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N      -- order of filter (number of taps)
      Wn -- cutoff frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      bw -- bandwidth of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      k -- scale at peaking frequencies
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.

    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    bp_b = fir_bp(N, Wn, bw, width)
    bs_b = fir_bs(N, Wn, bw, width)

    pk_b = k * bp_b + bs_b

    return pk_b


def fir_sk(N, Wn, bw, k, width=pi):
    """fir_sk(N, Wn, bw, k, width=pi)

    Skirting FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N      -- order of filter (number of taps)
      Wn -- cutoff frequency of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      bw -- bandwidth of filter (normalized so that 1 corresponds to
                  Nyquist or pi radians / sample)
    
      k -- scale at peaking frequencies
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.

    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    bp_b = fir_bp(N, Wn, bw, width)
    bs_b = fir_bs(N, Wn, bw, width)

    sk_b = bp_b + k * bs_b

    return sk_b


def fir_bps(N, Wn, bw, k, width=pi):
    """fir_bps(N, Wn, bw, k, width=pi)

    Bandpass bank FIR Filter Design using windowed ideal filter method.
    
    Inputs:
    
      N      -- order of filter (number of taps)
      Wn -- an array of center frequencies of filter (normalized so that
                 1 corresponds to Nyquist or pi radians / sample)
    
      bw -- an array of cutoff bandwidths of filter (normalized so that
                 1 corresponds to Nyquist or pi radians / sample)
    
      k -- an array of scales at center frequencies
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.

    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    bps_b = zeros(N)

    for n in range(len(Wn)):
        bps_b += k[n] * fir_bp(N, Wn[n], bw[n], width)

    return bps_b


def fir_pks(N, Wn, bw, k, width=pi):
    """fir_pks(N, Wn, bw, k, width=pi)

    Peaking bank FIR Filter Design using windowed ideal filter method.

    Note: this algorithm doesn't perform well for even orders.
    
    Inputs:
    
      N      -- order of filter (number of taps)
      Wn -- an array of center frequencies of filter (normalized so that
                 1 corresponds to Nyquist or pi radians / sample)
    
      bw -- an array of cutoff bandwidths of filter (normalized so that
                 1 corresponds to Nyquist or pi radians / sample)
    
      k -- an array of scales at center frequencies
    
      width -- beta for Kaiser window FIR design.
                  pi = minimum ripple for steepest cutoff.
        
    Outputs:
    
      b      -- coefficients of length N FIR filter.
    """
    bps_b = fir_bps(N, Wn, bw, 1. - k, width)

    pks_b = invf(bps_b)

    return pks_b


# fn to generate hilbert coeficients
# **************************************
# Gibson, D. (1996, April). "Desigining an SSB Outphaser, Part 1."
# Electronics World, 306-310.
# Gibson, D. (1996, May). "Desigining an SSB Outphaser, Part 2."
# Electronics World, 392-394.
# **************************************
def fir_hb(N, beta=5):
    """fir_hb(N, beta=5)

    Hilbert FIR Filter Design using method demonstrated by Gibson,
    windowed with the Kaiser window.

    Gibson, D. (1996, April). "Desigining an SSB Outphaser, Part 1."
    Electronics World, 306-310.
    Gibson, D. (1996, May). "Desigining an SSB Outphaser, Part 2."
    Electronics World, 392-394.
    
    Inputs:
    
      N  -- order of filter (number of taps), should be odd
      beta -- beta for Kaiser window FIR design.
                  5 = similiar to Hamming.
    
    Outputs:
    
      b      -- coefficients of length N FIR filter.

    """
    # check if even or odd
    if N % 2 is 0:
        raise ValueError, ("N should be odd!!")

    else:
        # first make real response
        hilreal = zeros(N, complex)
        hilreal[(N -1 )/2] = 1.

        # then make imag response & window with kaiser
        hilimag = []
        for n in range(N):
            if n == (N - 1) / 2:
                hilimag.append(complex(0, 0))
            else:
                hilimag.append(
                    complex(
                        0,
                        (1 - (cos((n - (N - 1) / 2) * pi)))
                        /
                        ((n - (N - 1) / 2) * pi)
                        )
                    )
        hilimag *= kaiser(N, beta)

        # sum real and imag
        res = hilreal + hilimag

        return res


#=========================
# Convolution Function
#=========================

# may want to add a convolution function that
# takes kernel as a spectrum
def convfilt(x, kernel, mode = 'z', kind = 'fft', zi = None):
    """convfilt(x, kernel, mode = 'z', zi = None)

    Convolve input x by kernel. 
    
    Description
    
      Convolve input x by kernel along the 0 axis.
      Operates in two different modes, returning the complete
      convolution, or acting as a filter with state.

      Wraps convolve and fftconvolve.
    
    Inputs:
    
      x -- A N-dimensional input array.
      kernel -- A one or N-dimensional input array.
      mode -- 'z' or 'full'. If mode is 'z', acts as a filter
               with state 'z', and returns a vector of length len(x).
               If mode is 'full', returns the full convolution.
      kind -- 'direct' or 'fft', for direct or fft convolution
      zi -- Initial state.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            len(kernel) - 1.  If zi=None or is not given then initial
            rest is assumed.
    
    Outputs: (y, {zf})
    
      y -- The output of the delay.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            delay values.
    
      """
    if kind is 'direct':
        convfun = convolve
    else:
        convfun = fftconvolve

    x_chans = nchannels(x)
    k_chans = nchannels(kernel)

    # case 1: x and kernel are are both single channel
    if (x_chans is 1) and (k_chans is 1):
        y = convfun(x, kernel)

    # case 2: x is multichannel and kernel is single channel
    elif (x_chans > 1) and (k_chans is 1):
        kernel = interleave(kernel)
        y = convfun(x, kernel)

    # case 3: x is single channel and kernel is multichannel
    elif (x_chans is 1) and (k_chans > 1):
        x = interleave(x)
        y = convfun(x, kernel)

    # case 4: x and kernel are multichannel, test if equal
    elif x_chans == k_chans:

        y = empty([x_chans, nframes(x) + nframes(kernel) - 1]) # deinterleaved, empty y

        x_d = deinterleave(x)
        k_d = deinterleave(kernel)

        for n in range(x_chans):
            y[n] = convfun(x_d[n], k_d[n])
        y = interleave(y)

    else:                       # raise error here
        raise ValueError, ("Doh!!, x and kernel don't broadcast!")

    # now return the result. . .
    if mode is 'z':

        y, zf = split(y, [nframes(x)])

        if zi is None:
            return y

        else:
            if nframes(zi) == (nframes(kernel) - 1):
                over_dub(y, zi, write_over = True)
                return y, zf

            else:
                print nframes(zi), (nframes(kernel) - 1)
                raise ValueError, ("Doh!!, zi is wrong size!!")

    else:
        return y


#=========================
# IIR Filter Functions
#=========================


# consider adding:
#    ffilter_ar - accepts multi, channel b, a (following appropriate broadcast rules)
#    vfilter_ar - time varying b, a (built on vfilter_ar)
def ffilter(b, a, x, zi=None):
    """ffilter(b, a, x, zi=None)

    Filter data along one-dimension with an IIR or FIR filter.
    (ffilter is an lfilter wrapper to correct for 2-dimensional inputs.)
    N-dim >= 2. Filter along the 0 axis
    
    Description
    
      Filter a data sequence, x, using a digital filter.  This works for many
      fundamental data types (including Object type).  The filter is a direct
      form II transposed implementation of the standard difference equation
        (see "Algorithm").
    
    Inputs:
    
      b -- The numerator coefficient vector in a 1-D sequence.
      a -- The denominator coefficient vector in a 1-D sequence.  If a[0]
           is not 1, then both a and b are normalized by a[0].
      x -- An N-dimensional input array.
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See lfilter

      """
    axis = 0                    # filter along the 0 axis

    # test on input conditions
    if (x.ndim is 2) and (zi != None): # test for 2-dim case where lfilter fails
        
        x = deinterleave(x, False) # deinterleave x

        y = empty_like(x) # empty outputs
        zf = empty_like(zi)

        for (n, x_n, zi_n) in zip(range(shape(zi)[0]), x, zi): # iterate, by channel

            y[n], zf[n] = lfilter(b, a, x_n, axis, zi_n)

        y = interleave(y)   # deinterleave y

        return y, zf

    else:
        return lfilter(b, a, x, axis, zi)


# create a convenience / private function to do section filtering
# then ffos and fsos can use the section function
# **possibly use c-style indexing for coefs and states  

def _f_section_cascade(b, a, x, section_order = 1, zi=None):
    """_f_section_cascade(b, a, x, section_order = 1, zi=None)

    Filter data along one-dimension with an IIR or FIR filter.
    N-dim >= 2. Filter along the 0 axis

    Helper function to create a cascade of first or second order filters.
    See ffos or fsos.
        
    Algorithm:
      See ffilter & lfilter

      """
    # catch number of sections a == b
    if len(b) != len(a):
        raise ValueError, ("len(b) must equal len(a)")
    else:
        nos = len(b) / (section_order + 1) # number of sections

    # for convenience reshape b, a for iteration
    b.shape = (nos, section_order + 1)
    a.shape = (nos, section_order + 1)
    
    y = x.copy()             # set output to input, for cascading loop

    if zi is None:              # no zi
        for (b_n, a_n) in zip(b, a): # cascade
            y = ffilter(b_n, a_n, y) # filters

        return y
    else:
        if x.ndim is 1:
            zi.shape = (nos, section_order) # sections, section order
        else:
            zi = swapaxes(
                reshape(
                    zi,
                    (nos, shape(x)[1], section_order)), # nos, channels, section order
                0, 1)

        zf = zeros_like(zi)

        for (b_n, a_n, zi_n, n) in zip(b, a, zi, range(nos)): # cascade

            y, zf[n] = ffilter(b_n, a_n, y, zi_n)      # filters

        if x.ndim is 1:
            zf.shape = (section_order * nos,)
        else:
            zf = reshape(
                swapaxes(
                    zf, 0, 1),
                (nos, section_order * shape(x)[1])) # nos, order * channels

        return y, zf


def ffos(b, a, x, zi=None):
    """ffos(b, a, x, zi=None)

    Filter data along one-dimension with an IIR or FIR filter.
    N-dim >= 2. Filter along the 0 axis

    ffos is a cascade of first order sections.
    
    Description
    
      Filter a data sequence, x, using a digital filter.  This works for many
      fundamental data types (including Object type).  The filter is a direct
      form II transposed implementation of the standard difference equation
        (see "Algorithm").
    
    Inputs:
    
      b -- The collection of numerator coefficients in a 1-D sequence.
      a -- The collection of denominator coefficients in a 1-D sequence.
           len(a) must == len(b)
      x -- An N-dimensional input array.
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See ffilter & lfilter

      """
    return _f_section_cascade(b, a, x, 1, zi)


def fsos(b, a, x, zi=None):
    """fsos(b, a, x, zi=None)

    Filter data along one-dimension with an IIR or FIR filter.
    N-dim >= 2. Filter along the 0 axis

    fsos is a cascade of second order sections.
    
    Description
    
      Filter a data sequence, x, using a digital filter.  This works for many
      fundamental data types (including Object type).  The filter is a direct
      form II transposed implementation of the standard difference equation
        (see "Algorithm").
    
    Inputs:
    
      b -- The collection of numerator coefficients in a 1-D sequence.
      a -- The collection of denominator coefficients in a 1-D sequence.
           len(a) must == len(b)
      x -- An N-dimensional input array.
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See ffilter & lfilter

      """
    return _f_section_cascade(b, a, x, 2, zi)


# EXPECT NEED TO READDRESS THIS FUNCTION
def vfilter(b, a, x, zi=None):
    """vfilter(b, a, x, zi=None)

    Filter data along one-dimension with an IIR or FIR filter.
    vfilter is a time varying version of ffilter.
    N-dim >= 2. Filter along the 0 axis.
    
    Description
    
      Filter a data sequence, x, using a digital filter.  This works for many
      fundamental data types (including Object type).  The filter is a direct
      form II transposed implementation of the standard difference equation
      (see "Algorithm").

    Inputs:
    
      b -- The numerator coefficient vector in a 1-D sequence.
      a -- The denominator coefficient vector in a 1-D sequence.  If a[0]
           is not 1, then both a and b are normalized by a[0].
           Both b and a are time varying arrays of length order * sample length.
      x -- An N-dimensional input array.
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(shape(b)[1], shape(a)[1]).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See lfilter

      """
    # find order
    N = max(shape(b)[1], shape(a)[1]) - 1

    # find nframes
    nframes = shape(x)[0]

    # set initial/final state to zeros
    if zi is None:

        # set initial/final state to zeros
        if x.ndim is 1:
            zf = zeros(N)

        else:
            # find channels - only works for = 2-D input
            channels = shape(x)[1]
            zf = zeros((channels, N))

        zi_set = False

    # otherwise set to zi
    else:
        zf = zi
        zi_set = True

    y = empty_like(x)   # set empty y

    # iterate by frame
    for (n, b_n, a_n, x_n) in zip(range(nframes), b, a, x): # iterate, by sample frame
        y[n], zf = ffilter(b_n, a_n, array([x_n]), zf)

    y.shape = shape(x)          # this line is necessary for the 1-d case

    if zi_set:
        return y, zf
    else:
        return y


# **************************************
# IIR Filter Functions
# **************************************

def fiir_lp(x, N, Wn, zi = None):
    """fiir_lp(x, N, Wn, zi = None)

    Filter data along one-dimension with a fixed frequency butterworth
    low pass IIR filter. Filter along the 0 axis
    
    Description
    
      Filter a data sequence, x, using a low pass digital butterworth filter.
      The filter is a direct form II transposed implementation of the standard
      difference equation
      (see "Algorithm").
    
    Inputs:
    
      x -- An N-dimensional input array.
      N -- order
      Wn -- cutoff
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See butter and lfilter

      """
    b, a = butter(N, Wn, 'lowpass')

    y = ffilter(b, a, x, zi)
    
    return y


def fiir_hp(x, N, Wn, zi = None):
    """fiir_hp(x, N, Wn, zi = None)

    Filter data along one-dimension with a fixed frequency butterworth
    high pass IIR filter. Filter along the 0 axis
    
    Description
    
      Filter a data sequence, x, using a high pass digital butterworth filter.
      The filter is a direct form II transposed implementation of the standard
      difference equation
      (see "Algorithm").
    
    Inputs:
    
      x -- An N-dimensional input array.
      N -- order
      Wn -- cutoff
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See butter and lfilter

      """
    b, a = butter(N, Wn, 'highpass')

    y = ffilter(b, a, x, zi)
    
    return y


def fiir_bp(x, N, Wn, q = 1., zi = None):
    """fiir_bp(x, N, Wn, q = 1., zi = None)

    Filter data along one-dimension with a fixed frequency butterworth
    band pass IIR filter. Filter along the 0 axis
    
    Description
    
      Filter a data sequence, x, using a band pass digital butterworth filter.
      The filter is a direct form II transposed implementation of the standard
      difference equation
      (see "Algorithm").
    
    Inputs:
    
      x -- An N-dimensional input array.
      N -- order
      Wn -- center Wn
      q -- filter Q
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See butter and lfilter

      """
    bw = Wn / q

    Wn = array([Wn - .5 * bw, Wn + .5 * bw])

    b, a = butter(N, Wn, 'bandpass')

    y = ffilter(b, a, x, zi)
    
    return y


def fiir_bs(x, N, Wn, q = 1., zi = None):
    """fiir_bs(x, N, Wn, q = 1., zi = None)

    Filter data along one-dimension with a fixed frequency butterworth
    band stop IIR filter. Filter along the 0 axis
    
    Description
    
      Filter a data sequence, x, using a band stop digital butterworth filter.
      The filter is a direct form II transposed implementation of the standard
      difference equation
      (see "Algorithm").
    
    Inputs:
    
      x -- An N-dimensional input array.
      N -- order
      Wn -- center Wn
      q -- filter Q
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See butter and lfilter

      """
    bw = Wn / q

    Wn = array([Wn - .5 * bw, Wn + .5 * bw])

    b, a = butter(N, Wn, 'bandstop')

    y = ffilter(b, a, x, zi)
    
    return y


def diff_filt(x, zi = None):
    """diff_filt(x, zi = None)

    Filter data along one-dimension with a differentiator
    high pass IIR filter. Filter along the 0 axis
    
    Description
    
      Filter a data sequence, x, using a differentiator high pass filter.
      The filter is a direct form II transposed implementation of the standard
      difference equation
      (see "Algorithm").
    
    Inputs:
    
      x -- An N-dimensional input array.
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See butter and lfilter

      """
    b = array([1., -1.])
    a = array([1.])

    y = ffilter(b, a, x, zi)
    
    return y


def integ_filt(x, zi = None):
    """integ_filt(x, zi = None)

    Filter data along one-dimension with an integrator
    ow pass IIR filter. Filter along the 0 axis
    
    Description
    
      Filter a data sequence, x, using an integrator low pass filter.
      The filter is a direct form II transposed implementation of the standard
      difference equation
      (see "Algorithm").
    
    Inputs:
    
      x -- An N-dimensional input array.
      zi -- Initial conditions for the filter delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            max(len(a),len(b)).  If zi=None or is not given then initial
            rest is assumed.  SEE signal.lfiltic for more information.
    
    Outputs: (y, {zf})
    
      y -- The output of the digital filter.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            final filter delay values.
    
    Algorithm:
      See butter and lfilter

      """
    b = array([1.])             # integrator coeffs
    a = array([1., -1.])

    y = ffilter(b, a, x, zi)
    
    return y

# **************************************
# osc. . .
# **************************************

def phasor(Wn, phase = 0., zi = None):
    """phasor(Wn, phase = 0., zi = None)

    Args:
        - Wn    : Normalized frequency array (may be multichannel)
        - phase : In radians (may be an array of len(Wn)).
        - zi    : Initial conditions for the filter state. It is
        a vector (or array of vectors for an N-dimensional input)
        of length 1.  If zi=None or is not given then initial
        rest is assumed.  SEE signal.lfiltic for more information.

    Returns (y, {zf}).

        - y     : The output of the phasor (digital filter).
        - zf:   : If zi is None, this is not returned, otherwise,
                  zf holds the final filter delay values.

    Return len(Wn) of a variable frequency un-wrapped phasor.
    Wn is the normalized frequency (may be an array of nchannels, for multichannel).
    Phase in radians (constant, or may be an array of nframes of nchannels).

    """
    # the phasor is actually a scaled integrator

    b = array([0., 1.]) # integrator coeffs
    a = array([1., -1.])

    if zi is None:
        return ffilter(b, a, (pi * Wn)) + phase
    
    else:
        y, zf = ffilter(b, a, (pi * Wn), zi)
        return y + phase, zf


def sinosc(Wn, phase = 0., zi = None):
    """phasor(Wn, phase = 0., zi = None)

    Args:
        - Wn    : Normalized frequency array (may be multichannel)
        - phase : In radians (may be an array of len(Wn)).
        - zi    : Initial conditions for the filter state. It is
        a vector (or array of vectors for an N-dimensional input)
        of length 1.  If zi=None or is not given then initial
        rest is assumed.  SEE signal.lfiltic for more information.

    Returns (y, {zf}).

        - y     : The output of the oscillator.
        - zf:   : If zi is None, this is not returned, otherwise,
                  zf holds the final phasor filter delay values.

    Return len(Wn) of a variable frequency sine oscillator.
    Wn is the normalized frequency (may be an array of nchannels, for multichannel).
    Phase in radians (constant, or may be an array of nframes of nchannels).


    """
    if zi is None:
        return sin(phasor(Wn, phase, zi))
    else:
        y, zf = phasor(Wn, phase, zi)
        return sin(y), zf


# **************************************
# delays. . .
# **************************************

# NOTE FOR DELAYS:
# review DAFX for other delay algorithms--particularly for feedback delays!!

# similar to SC3's BufDelayN
# f means fixed, n means no interpolation
# consider adding vdelay, delayi, etc.
def fdelayn(x, nframes, axis = 0, zi = None):
    """fdelayn(x, nframes, axis = 0, zi=None)

    Delay input x by nframes. 
    
    Description
    
      Delay input x by nframes along the given axis.
      If nframes is negative, results in abs(nframes) advance.
      
      Note: max delay = size(x, axis)
    
    Inputs:
    
      x -- A N-dimensional input array.
      nframes -- Number of frames to delay by.
      axis -- axis of choice
      zi -- Initial conditions for the delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            nframes.  If zi=None or is not given then initial rest is assumed.
    
    Outputs: (y, {zf})
    
      y -- The output of the delay.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            delay values.
    
      """
    # delay / advance
    y = roll(x, nframes, axis)

    # extract zf, which has wrapped around
    if nframes < 0:
        zf = take(y, arange(size(y, axis) + nframes, size(y, axis)), axis) # advance
    else:
        zf = take(y, arange(nframes), axis) # delay

    # generate zeros if none exist
    if zi is None:
        zi = zeros(shape(zf))
        zi_init = False
    else:
        zi_init = True

    # put appropriate zi in place--using slice tuple
    # (the put function isn't appropriate)
    s_r = (zi.ndim * [Ellipsis])

    if nframes < 0:
        s_r[axis] = slice(size(y, axis) + nframes, size(y, axis)) # advance
    else:
        s_r[axis] = slice(0, nframes) # delay

    y[s_r] = zi

    if zi_init:
        return y, zf
    else:
        return y


def fadvancen(x, nframes, axis = 0, zi = None):
    """fdelayn(x, nframes, axis = 0, zi=None)

    Advance input x by nframes. 
    
    Description
    
      Advance input x by nframes along the given axis.
      If nframes is negative, results in abs(nframes) delay.
      
      Note: max advance = size(x, axis)
    
    Inputs:
    
      x -- A N-dimensional input array.
      nframes -- Number of frames to advance by.
      axis -- axis of choice
      zi -- Initial conditions for the delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            nframes.  If zi=None or is not given then initial rest is assumed.
    
    Outputs: (y, {zf})
    
      y -- The output of the advance.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            delay values.
    
      """
    return fdelayn(x, -nframes, axis, zi)


# comb filters. . . using circular delays

# f means fixed, n means no interpolation
# plan to add damped combs!
# consider adding vcomb, combi, etc.
def faz_combn(x, nframes, b0, b1, axis = 0, zi = None):
    """faz_combn(x, nframes, b0, b1, axis = 0, zi = None)

    Filter input x by ALL ZERO comb filter of length nframes. 
    
    Description
    
      Filter input x along the given axis.
    
    Inputs:
    
      x -- A N-dimensional input array.
      nframes -- Length of comb filter.
      b0 -- The direct feed-forward coefficient.
      b1 -- The delay feed-forward coefficient.
      axis -- axis of choice
      zi -- Initial conditions for the delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            nframes.  If zi=None or is not given then initial rest is assumed.
    
    Outputs: (y, {zf})
    
      y -- The output of the delay.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            delay values.
    
      """

    if axis is not 0:
        raise 'currently only supports axis = 0'

    else:

        y = zeros_like(x)       # empty output

        if zi is None:
            if x.ndim is 1:
                z = zeros(nframes)  # nframes of a delay
            else:
                z = zeros((nframes, nchannels(x)))
        else:
            z = copy(zi)

        if isscalar(b0) and isscalar(b1): # b0, b1 as scalars

            for n in range(size(x, axis)):
                                  # n is input read index
                n_z = n % nframes # n_z is z read/write index

                y[n] = b0 * x[n] + b1 * z[n_z]
                z[n_z] = x[n]

        else:                   # upgrade for time varying b0, b1
            if isscalar(b0):
                b0 = repeat(b0, size(x, axis))
            if isscalar(b1):
                b1 = repeat(b1, size(x, axis))

            for n in range(size(x, axis)):

                n_z = n % nframes

                y[n] = b0[n] * x[n] + b1[n] * z[n_z]
                z[n_z] = x[n]

        if zi is None:
            return y
        else:
            zf = roll(z, -n_z)[::-1]
            return y, zf


def fap_combn(x, nframes, b0, a1, axis = 0, zi = None):
    """fap_combn(x, nframes, b0, a1, axis = 0, zi = None)

    Filter input x by ALL POLE comb filter of length nframes. 
    
    Description
    
      Filter input x along the given axis.
    
    Inputs:
    
      x -- A N-dimensional input array.
      nframes -- Length of comb filter.
      b0 -- The direct feed-forward coefficient.
      a1 -- The delay feed-back coefficient. (neg, to conform to transfer fn)
      axis -- axis of choice
      zi -- Initial conditions for the delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            nframes.  If zi=None or is not given then initial rest is assumed.
    
    Outputs: (y, {zf})
    
      y -- The output of the delay.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            delay values.
    
      """

    if axis is not 0:
        raise 'currently only supports axis = 0'

    else:

        y = zeros_like(x)       # empty output

        if zi is None:
            if x.ndim is 1:
                z = zeros(nframes)  # nframes of a delay
            else:
                z = zeros((nframes, nchannels(x)))
        else:
            z = copy(zi)

        if isscalar(b0) and isscalar(a1): # b0, a1 as scalars

            for n in range(size(x, axis)):
                                  # n is input read index
                n_z = n % nframes # n_z is z read/write index

                xh = x[n] - a1 * z[n_z]
                y[n] = b0 * xh
                z[n_z] = xh

        else:                   # upgrade for time varying b0, b1
            if isscalar(b0):
                b0 = repeat(b0, size(x, axis))
            if isscalar(a1):
                a1 = repeat(a1, size(x, axis))

            for n in range(size(x, axis)):

                n_z = n % nframes

                xh = x[n] - a1[n] * z[n_z]
                y[n] = b0[n] * xh
                z[n_z] = xh

        if zi is None:
            return y
        else:
            zf = roll(z, -n_z)[::-1]
            return y, zf


def fpz_combn(x, nframes, b0, b1, a1, axis = 0, zi = None):
    """fpz_combn(x, nframes, b0, b1, a1, axis = 0, zi = None)

    Filter input x by POLE ZERO comb filter of length nframes. 
    
    Description
    
      Filter input x along the given axis.
    
    Inputs:
    
      x -- A N-dimensional input array.
      nframes -- Length of comb filter.
      b0 -- The direct feed-forward coefficient.
      a1 -- The delay feed-back coefficient. (neg, to conform to transfer fn)
      axis -- axis of choice
      zi -- Initial conditions for the delays.  It is a vector
            (or array of vectors for an N-dimensional input) of length
            nframes.  If zi=None or is not given then initial rest is assumed.
    
    Outputs: (y, {zf})
    
      y -- The output of the delay.
      zf -- If zi is None, this is not returned, otherwise, zf holds the
            delay values.
    
      """

    if axis is not 0:
        raise 'currently only supports axis = 0'

    else:

        y = zeros_like(x)       # empty output

        if zi is None:
            if x.ndim is 1:
                z = zeros(nframes)  # nframes of a delay
            else:
                z = zeros((nframes, nchannels(x)))
        else:
            z = copy(zi)

        if isscalar(b0) and isscalar(b1) and isscalar(a1): # b0, a1 as scalars

            for n in range(size(x, axis)):
                                  # n is input read index
                n_z = n % nframes # n_z is z read/write index

                xh = x[n] - a1 * z[n_z]
                y[n] = b1 * z[n_z] + b0 * xh
                z[n_z] = xh

        else:                   # upgrade for time varying b0, b1
            if isscalar(b0):
                b0 = repeat(b0, size(x, axis))
            if isscalar(b1):
                b1 = repeat(b1, size(x, axis))
            if isscalar(a1):
                a1 = repeat(a1, size(x, axis))

            for n in range(size(x, axis)):

                n_z = n % nframes

                xh = x[n] - a1[n] * z[n_z]
                y[n] = b1[n] * z[n_z] + b0[n] * xh
                z[n_z] = xh

        if zi is None:
            return y
        else:
            zf = roll(z, -n_z)[::-1]
            return y, zf


# ****************************************************************************
# REVISIT EVERYTHING BELOW HERE
# ****************************************************************************


# ******************************************************************************
# 
# Classes. . .
# 
# **********************

# CLASSES NEED TO BE UPDATED TO REMOVE CHANNELS--CONFORM TO GENERATORS

# ******************************************************************************
# osc objects: filters returning signal from a freq array
#    .ar() returns complete array
#          depends on freq array assigned

# consider adding table and tablei osc
# AS OSC_OBJ IS A SPECIALIZED CLASS DON'T BRING INTO FILT_OBJ
class OscObj(MusObj):

    def __init__(self, phase_init = None, sr = None):
        MusObj.__init__(self, sr) # Run superclass init

        self.z = None    # state of the integrator
        self.phase_init = phase_init  # phase init'ed?


    def _phase_init(self, freq, phase): # initializes phase appropriately
        if phase is None:       # init phase, if set
            if self.phase_init is None:
                phase = 0.
            else:
                phase = self.phase_init
        else:
            if self.phase_init is None:
                pass
            else:
                phase += self.phase_init

        return asarray(phase)


    def _zi(self, freq, phase): # initializes state of the integrator appropriately

        if self.z is None:      # set up the state if it is None

            # determine channels of freq and phase to generate

            # set z_chans
            z_chans = max(
                nchannels(freq), # frequency channels
                ((isscalar(phase) and [None]) or [nchannels(phase)])[0] # phase channels
                )

            # create zeros. . .
            z = zeros(z_chans)
            z.shape = (z_chans, 1)

            # set z
            self.z = z


class SinOsc(OscObj):

    def __init__(self, phase_init = None, sr = None):
        OscObj.__init__(self, phase_init, sr = None) # Run superclass init

    def ar(self, freq, phase = None):
        
        # check phase is init'ed, and assign if need be
        phase = self._phase_init(freq, phase)

        # check if state is set, and assign if need be
        self._zi(freq, phase)

        # run sinosc()
        y, self.z = sinosc(
            freq_to_Wn(freq, self.T),
            phase,
            self.z)
        return y



# ******************************************************************************
# Delay objects: filters returning signal from a signal array
#    .ar() returns complete array
# consider making state a tuple, so that states for internal filters (e.g., lp)
# can be held too!
# also--consider making delay_time possible to be an array
# class DelObj(MusObj):


# ADD A FILT_OBJ CLASS HERE?. . . WHICH WILL HANDLE MULTICHANNEL EXPANSION
# AS DOES GEN_OBJ??

class FDelObj(MusObj):

    def __init__(self, delay, zi = None, sr = None, asnframes = False):
        MusObj.__init__(self, sr) # Run superclass init

        if asnframes:           # convert and set nframes
            nframes = delay
        else:
            nframes = dur_to_nframes(delay, self.sr)

        if isscalar(nframes):
            self.nframes = nframes
        else:
            self.nframes = asarray(nframes)

        self.nchannels = nchannels(asarray([delay])) # store nchannels

        self.z = zi        # state of the delay, may be a tuple, as needed


    def ar(self, x): # array return

        # check if state is set, and assign if need be
        self._zi(x)

        if self.nchannels is 1: # run fdelayn()
            y, self.z = self.fun(
                x,
                self.nframes,
                0,
                self.z)

        else:                         # multichannel, run fdelayn()
            y = range(self.nchannels) # set up two empty lists to fill
            z = range(self.nchannels) # with results of delay

            for n, x_n in zip(y, deinterleave(x)): # count through nchannels
                y[n], z[n] = self.fun(
                    x_n,
                    self.nframes[n],
                    0,
                    self.z[n])
            y = interleave(asarray(y))
            self.z = z

        return y


    def _zi(self, x):   # initializes state of the delay appropriately

        if self.z is None:      # set up the state if it is None

            if self.nchannels is 1: # create zeros - as a block. . .
                zi = zeros((abs(self.nframes), nchannels(x))) # generate zi zeros
                self.z = zi

            else:               # create zeros - as an array of nchannel arrays. . .
                if self.nchannels != nchannels(x):
                    raise ValueError, 'delay argument nchannels != nchannels(x)'
                else:
                    zi = range(self.nchannels)
                    for n in range(self.nchannels):
                        zi[n] = zeros(abs(self.nframes[n]))
                    self.z = zi


class FDelay(FDelObj):

    def __init__(self, delay = 1., zi = None, sr = None, asnframes = False):
        self.fun = fdelayn      # define function
        FDelObj.__init__(self, delay, zi, sr, asnframes) # Run superclass init


# combs. . .
# might be good to work out how to combine DEL_OBJ and CMB_OBJ into one class
class FCmbObj(MusObj):

    def __init__(self, freq, zi = None, sr = None):
        MusObj.__init__(self, sr) # Run superclass init

        # set flags for cos or sin response
        self.sign = sign(freq)  # negative freq --> sin response

        # set up nframes
        nframes = dur_to_nframes(
            freq_to_period(abs(freq)),
            self.sr) # convert and set nframes
        
        self.nframes = nframes

        self.nchannels = nchannels(asarray([nframes])) # store nchannels

        self.z = zi        # state of the delay, may be a tuple, as needed


    def _ar(self, x, *args): # array return

        # check if state is set, and assign if need be
        self._zi(x)

        if self.nchannels is 1: # run comb()
            if self.fun is fpz_combn:
                y, self.z = self.fun(
                    x,
                    self.nframes,
                    args[0],
                    args[1],
                    args[2],
                    0,
                    self.z)
            else:
                y, self.z = self.fun(
                    x,
                    self.nframes,
                    args[0],
                    args[1],
                    0,
                    self.z)
        else:                         # multichannel, run comb()
            y = range(self.nchannels) # set up two empty lists to fill
            z = range(self.nchannels) # with results of delay

            for n, x_n in zip(y, deinterleave(x)): # count through nchannels
                if self.fun is fpz_combn:
                    y[n], z[n] = self.fun(
                        x_n,
                        self.nframes[n],
                        args[0][n],
                        args[1][n],
                        args[2][n],
                        0,
                        self.z[n])
                else:
                    y[n], z[n] = self.fun(
                        x_n,
                        self.nframes[n],
                        args[0][n],
                        args[1][n],
                        0,
                        self.z[n])
            y = interleave(asarray(y))
            self.z = z

        return y


    def _zi(self, x):   # initializes state of the delay appropriately

        if self.z is None:      # set up the state if it is None

            if self.nchannels is 1: # create zeros - as a block. . .
                zi = zeros((abs(self.nframes), nchannels(x))) # generate zi zeros
                self.z = zi

            else:               # create zeros - as an array of nchannel arrays. . .
                if self.nchannels != nchannels(x):
                    raise ValueError, 'delay argument nchannels != nchannels(x)'
                else:
                    zi = range(self.nchannels)
                    for n in range(self.nchannels):
                        zi[n] = zeros(abs(self.nframes[n]))
                    self.z = zi


class FAzComb(FCmbObj):

    def __init__(self, freq = 440., zi = None, sr = None):
        self.fun = faz_combn      # define function
        FCmbObj.__init__(self, freq, zi, sr) # Run superclass init

    def ar(self, x, gain):      # gain in db


        # CONSIDER MOVING THIS TO _AR, ABOVE
        # massage gain to broadcast correctly
        # may want to rework this to take advantage of
        # numpy broadcasting
        if self.nchannels is 1:
            if not isscalar(gain):  # is gain an array?
                gain = asarray(gain)

                if nframes(gain) is nchannels(x): # upgrade gain
                    gain = tile(gain, (nframes(x), self.nchannels))

        else:               # multichannel broadcasting--e.g., need to
                            # use more than one comb function call
            if isscalar(gain):
                gain = repeat(gain, self.nchannels)

            elif nchannels(asarray(gain)) is 1 and nframes(asarray(gain)) is nframes(x):
                gain = tile(gain, self.nchannels)


        k = db_to_amp(gain)     # calculate coeffs here!
        b0 = .5 * (1 + k)
        b1 = .5 * (1 - k) * self.sign

        # need to reshape for multichannel broadcasing
        if shape(k) == shape(x) and self.nchannels > 1:
            b0 = deinterleave(b0)
            b1 = deinterleave(b1)

        return self._ar(x, b0, b1)


class FApComb(FCmbObj):

    def __init__(self, freq = 440., zi = None, sr = None, asT60 = False):
        self.fun = fap_combn      # define function
        self.asT60 = asT60
        FCmbObj.__init__(self, freq, zi, sr) # Run superclass init

    def ar(self, x, gain):      # gain in db


        # CONSIDER MOVING THIS TO _AR, ABOVE
        # massage gain to broadcast correctly
        # may want to rework this to take advantage of
        # numpy broadcasting
        if self.nchannels is 1:
            if not isscalar(gain):  # is gain an array?
                gain = asarray(gain)

                if nframes(gain) is nchannels(x): # upgrade gain
                    gain = tile(gain, (nframes(x), self.nchannels))

        else:               # multichannel broadcasting--e.g., need to
                            # use more than one comb function call
            if isscalar(gain):
                gain = repeat(gain, self.nchannels)

            elif nchannels(asarray(gain)) is 1 and nframes(asarray(gain)) is nframes(x):
                gain = tile(gain, self.nchannels)

        # calculate coeffs here!
        if not self.asT60:      # as gain
            k = db_to_amp(gain)

            a1 = (k - 1.)/(k + 1.) * self.sign
            b0 = (1 - abs(a1))

            # need to reshape for multichannel broadcasing
            if shape(k) == shape(x) and self.nchannels > 1:
                b0 = deinterleave(b0)
                b1 = deinterleave(b1)

        else:                   # as T60
            
            a1 = -pow(10, -3 * nframes_to_dur(self.nframes, self.sr) / gain) * self.sign
            b0 = (1 - abs(a1))

        return self._ar(x, b0, a1)
