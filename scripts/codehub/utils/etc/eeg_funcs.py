import warnings
import bct.algorithms.clustering as clust
import bct.algorithms.distance as dist
import bct.algorithms.degree as dg
from ieeg.auth import Session
from IPython.display import Image
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal as sig
import os
import pathlib
from scipy.fft import fft, fftfreq
import math
import sys
from scipy.integrate import simps
from joblib import Parallel, delayed
from sklearn.model_selection import LeaveOneOut
from sklearn.metrics import accuracy_score, confusion_matrix, roc_auc_score, roc_curve
from sklearn.decomposition import PCA


# Function to identify clip start/end pairs (in seconds) in iEEG annotations
def get_annotation_times(dataset, annotation_layer):
    """
    Obtains pairs of clip start and end times from iEEG annotations
    Input: 
      dataset (ieegpy Dataset object): Dataset object from which to extract clip start/end pairs
      annotation_layer (str): The annotation layer whose annotations to use to extract clip start/end pairs
    Returns:
      An ndarray with shape (num_clips, 2) whose ith element is an array of length 2 containing the start 
      and end times, respectively, of the ith clip
    """
    
    # Get metadata
    annotations = dataset.get_annotations(annotation_layer)
    ch_names    = dataset.get_channel_labels()
    details     = dataset.get_time_series_details(ch_names[0])
    
    # Get dimensionality
    num_annotations = len(annotations)
    num_clips       = int(num_annotations // 2)
    
    # Calculate duration
    data_end_time = (details.end_time - details.start_time) / 1e6
    pairs         = np.zeros((num_clips, 2))

    # Populate the time-pairs
    for i in range(1, num_annotations):
        ind = int(np.ceil(i / 2)) - 1
        pairs[ind][1 - i % 2] = annotations[i].start_time_offset_usec / 1e6
    pairs[-1][1] = data_end_time

    return pairs

# Function to compute number of windows
def num_windows(fs, winLen, winDisp, xLen):
    """
    Computes number of full sliding windows of size winLen in a certain signal
    Input:
      fs (float): Sampling frequency of the signal
      winLen (float): Length of window, in seconds
      winDisp (float): Stride of the window, in seconds
      xLen (int): Length of signal, in samples
    Returns:
      An int that is the number of possible full windows in the signal 
    """

    # Get window dimensions
    winLen  = winLen * fs
    winDisp = winDisp * fs
    return int(np.floor((xLen - winLen + winDisp) / winDisp))

# Function to compute values of a given function at each window in the signal
def moving_window_features(x, fs, winLen, winDisp, featFn):
    """
    Computes an array containing the value of featFn for each possible window in the given signal
    Input:
      x (ndarray): Input signal of either shape (num_channels, num_samples) or (num_samples)
      fs (float): Sampling frequency of the input signal, in Hz
      winLen (float): Length of window, in seconds
      winDisp (float): Stride of window, in seconds
      featFn (function): The function to apply on windows of the signal
    Returns:
      ndarray whose ith value is the value of featFn evaluated at the ith sliding window from the left.
      If input shape is (num_channels, num_samples), output shape is (num_channels, num_windows).
      If input shape is (num_samples), output shape is (num_windows).
    """

    # Number of complete windows in the signal
    num_wins = num_windows(fs, winLen, winDisp, x.shape[-1])
    winLen, winDisp = winLen * fs, winDisp * \
        fs  # Convert winLen, winDisp to samples

    if (len(x.shape) == 1):  # x has shape (num_samples)
        features = np.zeros((num_wins))  # Features array to be populated
        # For loop populates features array with the values of featFn evaluated at each of the windows
        for i in range(num_wins):
            features[i] = featFn(
                x[int(i * winDisp): int(i * winDisp + winLen)])
        return features
    # x has shape (num_channels, num_samples)
    num_channels = x.shape[0]
    # Features array to be populated
    features = np.zeros((num_channels, num_wins))
    # For loop populates features array with the values of featFn evaluated at each of the windows in each of the channels
    for i in range(num_channels):
        for j in range(num_wins):
            features[i][j] = featFn(
                x[i][int(j * winDisp): int(j * winDisp + winLen)])
    return features

# Function to take in data and split it into clips of arbitrary length with arbitrary overlap (in seconds)


def split_data(data, fs, clip_len, overlap, start_time=0):
    """
    Splits input data into clips of arbitrary length with arbitrary overlap
    Input:
      data (ndarray): Input data of shape (num_channels, num_samples)
      fs (float): Sampling frequency, in Hz
      clip_len (float): Desired length of clips, in seconds
      overlap (float): Desired overlap between consecutive clips, in seconds
      start_time (float, optional): Amount of time by which to shift over the start time of the first clip in
      the returned times array, in seconds. If value not given, start_time is by default 0.
    Returns:
      times, splitted (ndarray, ndarray): times has shape (num_clips) and contains the times, in seconds,
      corresponding to the returned clips (right aligned). splitted is an ndarray of shape (num_channels,
      num_clips, clip_len), containing the data split into clips for each channel. Note here clip_len is in
      samples, not seconds.
    """
    stride = clip_len - overlap
    num_clips = num_windows(fs, clip_len, stride, len(data[0]))
    times = np.arange(0, num_clips) * stride + start_time
    # Make times right aligned by shifting it over
    times += clip_len
    clip_len, overlap, stride = int(
        clip_len * fs), int(overlap * fs), int(stride * fs)
    num_channels = len(data)
    splitted = np.zeros((num_channels, num_clips, clip_len))
    for i in range(num_channels):
        for j in range(num_clips):
            splitted[i][j] = data[i][j*stride:j*stride+clip_len]

    return times, splitted

# Function to plot log of power spectrum of the data


def plot_psd(signal, sfreq, title=None):
    """
    Plots log of power spectrum of input signal
    Input:
      signal (ndarray): Input signal array of shape (num_samples)
      sfreq (float): Sampling frequency of input signal in Hz
      title (string / None): Optional string argument for title of the PSD plot
    Returns:
      None
    """
    N = len(signal)  # N is number of time samples in the signal clip
    T = 1 / sfreq  # T is time interval between adjacent samples
    y = fft(signal)  # Compute fft of signal
    # freqs is an array containing the DFT sample frequencies
    freqs = fftfreq(N, T)[:N//2]
    plt.plot(freqs, np.log(2.0/N * np.abs(y[0:N//2]) ** 2))
    if (title != None):
        plt.title(title)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Log(Power)')
    plt.show()


def psd(signal, sfreq, plot=False, log_psd=False, title=None):
    N = len(signal)  # N is number of time samples in the signal clip
    T = 1 / sfreq  # T is time interval between adjacent samples
    y = fft(signal)  # Compute fft of signal
    # freqs is an array containing the DFT sample frequencies
    freqs = fftfreq(N, T)[:N//2]
    spectrum = np.clip(2.0/N * np.abs(y[0:N//2]), a_min=0.00001, a_max=1e20)
    if (log_psd == True):
        spectrum = np.log(np.clip(spectrum), a_min=0.00001, a_max=1e20)
    if (plot == True):
        plt.plot(freqs, spectrum)
        if (title != None):
            plt.title(title)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Log(Power)')
        plt.show()

    return freqs, spectrum

# Function to make a butterworth notch filter


def create_notch_filter(order, low_cutoff, high_cutoff, fs):
    """
    Creates a butterworth notch filter with the desired parameters
    Input:
      order (int): Order of the filter
      low_cutoff (float): Lower critical frequency of the stop band, in Hz
      high_cutoff (float): Upper critical frequency of the stop band, in Hz
      fs (float): Sampling frequency of the signal the filter will be used on, in Hz
    Returns:
      b, a (ndarray, ndarray): b, a are the numerator and denominator polynomials of the filter, respectively
    """
    b, a = sig.butter(
        N=order, Wn=[low_cutoff, high_cutoff], btype='bandstop', fs=fs)
    return b, a

# Function to make a butterworth high pass filter


def create_high_pass_filter(order, cutoff, fs):
    """
    Creates butterworth high pass filter
    Input:
      order (int): Order of the filter
      cutoff (float): Critical frequency of the filter, in Hz
      fs (float): Sampling frequency of the signal the filter will be used on, in Hz
    Returns:
      b, a (ndarray, ndarray): b, a are the numerator and denominator polynomials of the filter, respectively
    """
    b, a = sig.butter(N=order, Wn=cutoff, btype='highpass', fs=fs)
    return b, a

# Function to apply a certain filter to a signal


def apply_filter(data: np.ndarray, filter) -> np.ndarray:
    """
    Applies the given filter to the given data. A filtered version of the data is returned. The original
    input data is not modified
    Input:
      data (ndarray): Input data to be filtered. Can either have shape (num_channels, num_samples) or (num_samples)
      filter (tuple): A tuple (b, a) of the filter to be applied. b, a are ndarrays that are the numerator and denominator polynomials of the filter, respectively
    Returns:
      ndarray of the filtered data with the same shape as the input data
    """
    b, a = filter[0], filter[1]
    return sig.filtfilt(b, a, data)

# Function to resample a given input signal


def resample(x, sfreq_original, sfreq_new):
    """
    Resamples the given signal to the given sampling frequency. A resampled version of the signal
    is returned without modifying the original input signal
    Input:
      x (ndarray): Input data to be resampled. Can either have shape (num_channels, num_samples) or (num_samples)
      sfreq_original (float): Original sampling frequency of the input signal, in Hz
      sfreq_new (float): New desired sampling frequency of the signal, in Hz
    Returns:
      ndarray of the resampled data with the same shape as the input data
    """

    # Length of time of the input signal is num_samples / sfreq
    time_len = x.shape[-1] / sfreq_original
    # Number of samples in resampled signal
    num_samples_new = int(time_len * sfreq_new)
    # Resample signal along last dimension of x.shape
    return sig.resample(x, num_samples, axis=-1)

# Function to compute line length


def line_length(x):
    """
    Computes line length of given input signal.
    Line length of a signal [x0,x1,...,xn] is given by |x1-x0| + |x2-x1| + ... + |xn-x(n-1)|
    Input:
      x (ndarray): Input signal of shape (num_channels, num_samples) or (num_samples)
    Returns:
      ndarray or float of the line lengths of the signals in each channel. For input shape of (num_channels, num_samples) output is
      ndarray of shape (num_channels). For input shape (num_samples) output is a float
    """

    return np.sum(np.abs(np.diff(x, axis=-1)), axis=-1)

# Function to compute area


def area(x):
    """
    Computes area of given input signal.
    Area of a signal [x0,x1,...,xn] is given by |x0| + |x1| + ... + |xn|
    Input:
      x (ndarray): Input signal of shape (num_channels, num_samples) or (num_samples)
    Returns:
      ndarray or float of the areas of the signals in each channel. For input shape of (num_channels, num_samples) output is
      ndarray of shape (num_channels). For input shape (num_samples) output is a float
    """

    return np.sum(np.abs(x), axis=-1)

# Function to compute energy


def energy(x):
    """
    Computes energy of given input signal.
    Energy of a signal [x0,x1,...,xn] is given by (x0)^2 + (x1)^2 + ... + (xn)^2
    Input:
      x (ndarray): Input signal of shape (num_channels, num_samples) or (num_samples)
    Returns:
      ndarray or float of the energies of the signals in each channel. For input shape of (num_channels, num_samples) output is
      ndarray of shape (num_channels). For input shape (num_samples) output is a float
    """
    return np.sum(x**2, axis=-1)

# Function to compute number of zero crossings


def zero_crossings(x):
    """
    Computes number of zero crossings of given input signal.
    Input:
      x (ndarray): Input signal of shape (num_channels, num_samples) or (num_samples)
    Returns:
      ndarray or int of the number of zero crossings of the signals in each channel. For input shape of (num_channels, num_samples)
      output is ndarray of shape (num_channels). For input shape (num_samples) output is an int
    """

    y = x - np.mean(x, axis=-1).reshape(-1, 1)
    return np.sum(np.abs(np.diff(np.where(y > 0, 1, 0), axis=-1)), axis=-1)

# Function to compute peak to peak


def peak_to_peak(x):
    """
    Computes peak to peak of given input signal x. Peak to peak is the (absolute value) difference between the highest and
    lowest values in the signal
    Input:
      x (ndarray): Input signal of shape (num_channels, num_samples) or (num_samples)
    Returns:
      ndarray or float of the peak to peak values for each of the signals in each channel. For input shape of (num_channels, num_samples)
      output is ndarray of shape (num_channels). For input shape (num_samples) output is a float
    """

    return np.amax(x, axis=-1) - np.amin(x, axis=-1)

# Function to extract univariate temporal measure features from array of input clips (clips has shape (num_channels, num_clips, num_samples))


def extract_utms(clips, funcs):
    """
    Extracts univariate temporal measures (utms) from an array of input clips
    Input:
      clips (ndarray): ndarray of shape (num_channels, num_clips, num_samples) of input data clips
      funcs (list): List of utm functions to run on the clips
    Returns:
      features (ndarray): ndarray of shape (len(funcs), num_channels, num_clips) that contains, for
      each function and channel, an array of floats of length num_clips which are the function outputs
      on each of the clips.
    """
    num_channels = len(clips)
    num_clips = len(clips[0])
    features = np.zeros((len(funcs), num_channels, num_clips))
    for i in range(len(funcs)):
        for j in range(num_clips):
            features[i, :, j] = funcs[i](clips[:, j])

    return features


# Function to compute relative power from 5 EEG frequency bands


def relative_power(x, start, end, sfreq):
    """
    Computes relative power of an input signal from 5 EEG frequency bands
    Input:
      x (ndarray): Input signal of shape (num_samples)
      start (float): Start time of the clip to be used for computing relative power, in seconds
      end (float): End time of the clip to be used for computing relative power, in seconds
      sfreq (float): Sampling frequency of the input signal, in Hz
    Returns:
      d,t,a,b,g (float,float,float,float,float): 5 values between 0 and 1 that sum to 1, which are the
      relative powers of the delta, theta, alpha, beta, and gamma bands, respectively
    """
    delta_low, delta_high = 0.5, 4
    theta_low, theta_high = 4, 8
    alpha_low, alpha_high = 8, 12
    beta_low, beta_high = 12, 30
    gamma_low, gamma_high = 30, 100

    start, end = int(start * sfreq), int(end * sfreq)

    x = x[start:end]

    N = len(x)  # N is number of time samples in the signal clip
    T = 1 / sfreq  # T is time interval between adjacent samples
    y = fft(x)  # Compute fft of signal
    psd = (2.0 / N) * np.abs(y[:N//2]) ** 2
    # freqs is an array containing the DFT sample frequencies
    freqs = fftfreq(N, T)[:N//2]

    # Frequency resolution of our power spectrum
    freq_res = freqs[1] - freqs[0]

    # Mask that is true only for those frequencies that are within the desired frequency band
    mask_delta = np.logical_and(freqs >= delta_low, freqs <= delta_high)
    mask_theta = np.logical_and(freqs >= theta_low, freqs <= theta_high)
    mask_alpha = np.logical_and(freqs >= alpha_low, freqs <= alpha_high)
    mask_beta = np.logical_and(freqs >= beta_low, freqs <= beta_high)
    mask_gamma = np.logical_and(freqs >= gamma_low, freqs <= gamma_high)

    # Calculate power by approximating area under the curve
    delta_power = simps(psd[mask_delta], dx=freq_res)
    theta_power = simps(psd[mask_theta], dx=freq_res)
    alpha_power = simps(psd[mask_alpha], dx=freq_res)
    beta_power = simps(psd[mask_beta], dx=freq_res)
    gamma_power = simps(psd[mask_gamma], dx=freq_res)

    total_power = delta_power + theta_power + \
        alpha_power + beta_power + gamma_power

    return delta_power / total_power, theta_power / total_power, alpha_power / total_power, beta_power / total_power, gamma_power / total_power


# Function to calculate phase locking value matrix between n signals
def plv(data):
    """
    Computes phase locking value (plv) matrix given n input signals
    Input:
      data (ndarray): Input data of shape (num_signals, num_samples)
    Returns:
      plvs (ndarray): Matrix of shape (num_signals, num_signals), whose (i,j)th entry is the phase locking
      value between input signal i and input signal j
    """
    hilbert = sig.hilbert(data)
    phases = hilbert / np.abs(hilbert)
    n = phases.shape[0]
    N = phases.shape[1]
    plvs = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            plvs[i][j] = (1 / N) * \
                np.abs(np.matmul(phases[i], np.conj(phases[j].T)))

    return plvs

# Function to plot plv/coherence matrix with channels labeled


def plot_matrix(matrix, ch_names, figsize=None):
    """
    Plots an input plv or coherence matrix
    Input:
      matrix (ndarray): Input plv or coherence matrix of shape (num_channels, num_channels)
      ch_names (list): List of the channel names of length (num_channels)
      figsize (tuple, optional): Optional parameter of the form (w, h), where w and h are floats that are the desired
      width and height, respectively, in inches. If no value given, figsize will be automatically chosen based on the size
      of the matrix
    Returns:
      None
    """
    if (not figsize):
        size = len(ch_names) * (4/15)
        size = max(5, size)
        figsize = (size, size)
    fig, ax = plt.subplots(figsize=figsize)
    plt.imshow(matrix)
    plt.colorbar()
    plt.show()

# Function to calculate coherence between data channels


def coherence(data, fs):
    """
    Calculated coherence between data channels
    Input:
      data (ndarray): Input data array of shape (num_channels, num_samples)
      fs (float): Sampling frequency, in Hz
    Returns:
      The coherence matrix of the data array. The (i,j)th entry is the coherence between channel i and channel j
    """
    N = len(data)
    matrix = np.zeros((N, N))
    for i in range(N):
        for j in range(i+1, N):
            f, c = sig.coherence(data[i], data[j], fs)
            res = f[1] - f[0]
            # Normalize area so it is between 0 and 1 (so diagonal entries will be 1's)
            matrix[i][j] = simps(c, dx=res) / (len(f) * res)

    # Currently matrix is strictly upper triangular, so we can obtain the final symmetric matrix with the following line
    matrix = matrix + matrix.T + np.identity(N)

    return matrix


# Function to calculate average node strengths of an array of undirected graphs


def avg_node_strength(graphs):
    """
    Computes average node strength for each graph, given an array of undirected, weighted graphs. The node strength of a given node is
    the sum of all the weights of its incident edges. The average node strength is the average of the node strengths
    of all the nodes in the graph
    Input:
      graphs (ndarray): Array of input graphs of shape (num_graphs, num_nodes, num_nodes)
    Returns:
      strengths (ndarray): Array of shape (num_graphs) that is an array of the average node strengths for each of the input
      graphs
    """
    num_graphs = len(graphs)
    N = len(graphs[0])
    strengths = np.zeros((num_graphs, N))
    for i in range(num_graphs):
        strengths[i] = dg.strengths_und(graphs[i])
    strengths = np.mean(strengths, axis=1)

    return strengths


# Function to calculate average global efficiencies of an array of input graphs


def global_efficiency(graphs):
    """
    Calculates global efficiency for each graph in an array of undirected, weighted graphs. Global efficiency
    is the average shortest inverse path length
    Input:
      graphs (ndarray): Array of input graphs of shape (num_graphs, num_nodes, num_nodes)
    Returns:
      efficiencies (ndarray): Array of shape (num_graphs) that is an array of the global efficiencies for
      each of the input graphs
    """
    num_graphs = len(graphs)
    efficiencies = np.zeros((num_graphs))
    for i in range(num_graphs):
        efficiencies[i] = dist.charpath(graphs[i])[1]

    return efficiencies


# Function to calculate average clustering coefficients of an array of input graphs


def avg_clustering_coef(graphs):
    """
    Calculates average clustering coefficient for each graph in an array of undirected, weighted graphs.
    The clustering coefficient is the average "intensity" of triangles around a node. The average clustering
    coefficient is the average of this across all nodes in the graph
    Input:
      graphs (ndarray): Array of input graphs of shape (num_graphs, num_nodes, num_nodes)
    Returns:
      clustering (ndarray): Array of shape (num_graphs) that is an array of the average clustering coefficients
      for each of the input graphs
    """
    num_graphs = len(graphs)
    N = len(graphs[0])
    clustering = np.zeros((num_graphs, N))
    for i in range(num_graphs):
        clustering[i] = clust.clustering_coef_wu(graphs[i])
    clustering = np.mean(clustering, axis=1)

    return clustering

# Function to calculate characteristic path lengths of an array of input graphs


def char_path_len(graphs):
    """
    Calculates characteristic path length for each graph in an array of undirected, weighted graphs.
    The characteristic path length is the average shortest path length in the graph
    Input:
      graphs (ndarray): Array of input graphs of shape (num_graphs, num_nodes, num_nodes)
    Returns:
      lens (ndarray): Array of shape (num_graphs) that is an array of the characteristic path length
      for each of the input graphs
    """
    num_graphs = len(graphs)
    lens = np.zeros((num_graphs))
    for i in range(num_graphs):
        lens[i] = dist.charpath(graphs[i])[0]

    return lens

# Function to calculate average eccentricities of an array of input graphs


def avg_eccentricity(graphs):
    """
    Calculates average eccentricity for each graph in an array of undirected, weighted graphs.
    The average eccentricity is the average of the eccentricities at each node, across all nodes in the graph
    Input:
      graphs (ndarray): Array of input graphs of shape (num_graphs, num_nodes, num_nodes)
    Returns:
      eccentricities (ndarray): Array of shape (num_graphs) that is an array of the average eccentricities
      for each of the input graphs
    """
    num_graphs = len(graphs)
    N = len(graphs[0])
    eccentricities = np.zeros((num_graphs, N))
    for i in range(num_graphs):
        eccentricities[i] = dist.charpath(graphs[i])[2]
    eccentricities = np.mean(eccentricities, axis=1)

    return eccentricities

# Function to extract graph metric features from input array of graphs


def extract_graph_metrics(graphs, funcs):
    """
    Extracts graph feature metrics from an input array of weighted, undirected graphs
    Input:
      graphs (ndarray): Array of input graphs of shape (num_graphs, num_nodes, num_nodes)
      funcs (list): List of functions for the desired graph metrics
    Output:
      features (ndarray): Array of shape (len(funcs), len(graphs)). Contains, for each function, an array of
      length len(graphs) that is the output of that function on each of the graphs in the input array graphs
    """
    features = np.zeros((len(funcs), len(graphs)))
    for i in range(len(funcs)):
        features[i] = funcs[i](graphs)

    return features

# Function to take in an array of clips and return an array of graphs that is either the coherence or plv of each clip


def data_to_graphs(clips, graph_func, fs):
    """
    Converts an array of clips to an array of graphs that is either the coherence or plv of each clip.
    Input:
      clips (ndarray): Input array of clips of shape (num_channels, num_clips, num_samples).
      graph_func (string): String that is either 'plv' or 'coherence', denoting the function with which to make the graphs
      fs (float): Sampling frequency of the clips, in Hz
    Returns:
      graphs (ndarray): Array of shape (num_clips, num_channels, num_channels) that is an array of either the
      plv or coherence matrices for each clip in clips
    """
    graphs = []
    if (graph_func == 'coherence'):
        graphs = Parallel(n_jobs=2)(delayed(coherence)(
            clips[:, i], fs) for i in range(len(clips[0])))
    elif (graph_func == 'plv'):
        graphs = Parallel(n_jobs=2)(delayed(plv)(
            clips[:, i]) for i in range(len(clips[0])))

    return graphs

# A function to, given an input array features of shape (num_functions, num_clips) and an input array times for the clips, plot the
# evolution over time of these features for each of the functions


def plot_metrics(features, times, names=None, grid_dims=None, figsize=(15, 15)):
    """
    Plots the evolution over time of an input array of graph metrics
    Input:
      features (ndarray): Array of shape (num_functions, num_clips) that contains, for each graph metric function,
      an array of length num_clips that is the output of the function on each graph resulting from the clips
      times (ndarray): Array of shape (num_clips) that is the array of right aligned times for each clip
      names (list, optional): Optional list of strings of length num_functions. If given, the strings in names
      will be used as the titles for the plots of each graph metric
      grid_dims(tuple, optional): Optional tuple of the form (r, c). If given, the resulting plots will be displayed
      in a grid with r rows and c columns. If not given, the plots will be displayed with 3 rows and an appropriate
      number of columns
      figsize (tuple, optional): Optional parameter of the form (w, h), where w and h are floats that are the desired
      width and height, respectively, in inches. If no value given, figsize will be set to (15, 15)
    """
    num_funcs = len(features)
    num_clips = len(features[0])
    if (not grid_dims):
        grid_dims = (3, int(np.ceil(num_funcs/3)))
    if (not names):
        names = ['' for i in range(num_funcs)]
    fig, axs = plt.subplots(grid_dims[0], grid_dims[1], figsize=figsize)
    for i in range(num_funcs):
        feats = features[i]
        row = int(np.floor(i/grid_dims[1]))
        col = i % grid_dims[1]
        axs[row, col].plot(times, feats)
        axs[row, col].set_title(names[i])
        axs[row, col].set_xlabel('Time (s)')
        axs[row, col].set_ylabel('Value')
    plt.show()


def common_average_reference(data):
    """
    Applies common average reference montage to the input data. The input data is not modified.
    Input:
      data (ndarray): Input signal to be common average referenced. Has shape (num_channels, num_samples)
    Returns:
      ndarray of same shape as input that is the input data with the common average reference montage applied to it.
    """
    return data - np.mean(data, axis=0)

# Function to obtain bipolar montage for 21 electrode EEG with 2 ekg channels


def create_bipolar_montage(data, ch_names):
    """
    Creates a dictionary that is the bipolar montage of an input EEG signal
    Input:
      data (ndarray): Input EEG data from which the bipolar montage is to be created. Has shape (num_channels, num_samples). Can have extra channels, but must
      have all channels that are required to create a bipolar montage.
      ch_names (list): The names of the channels corresponding to the channels in the data array. Is a list of strings of length num_channels
    Returns:
      Dictionary that is the bipolar montage of the input EEG. The keys are strings representing the name of a channel in the montage (eg: 'fp1-fp7'), and the
      values are ndarrays of shape (num_samples) that are the associated signal for that channel
    """
    name_to_index = {}  # Dictionary that gives, for a given channel name, its index in ch_indices
    # Keys are the channel names, in all lowercase (for convenience)
    for i in range(len(ch_names)):  # Populate the name_to_index dictionary
        name_to_index[ch_names[i].lower()] = i

    bipolar_montage = {}  # Dictionary containing the bipolar montage of the eeg data

    bipolar_montage['fp1-f7'] = data[name_to_index['fp1']] - \
        data[name_to_index['f7']]
    bipolar_montage['f7-t3'] = data[name_to_index['f7']] - \
        data[name_to_index['t3']]
    bipolar_montage['t3-t5'] = data[name_to_index['t3']] - \
        data[name_to_index['t5']]
    bipolar_montage['t5-o1'] = data[name_to_index['t5']] - \
        data[name_to_index['o1']]

    bipolar_montage['fp1-f3'] = data[name_to_index['fp1']] - \
        data[name_to_index['f3']]
    bipolar_montage['f3-c3'] = data[name_to_index['f3']] - \
        data[name_to_index['c3']]
    bipolar_montage['c3-p3'] = data[name_to_index['c3']] - \
        data[name_to_index['p3']]
    bipolar_montage['p3-o1'] = data[name_to_index['p3']] - \
        data[name_to_index['o1']]

    bipolar_montage['fp2-f4'] = data[name_to_index['fp2']] - \
        data[name_to_index['f4']]
    bipolar_montage['f4-c4'] = data[name_to_index['f4']] - \
        data[name_to_index['c4']]
    bipolar_montage['c4-p4'] = data[name_to_index['c4']] - \
        data[name_to_index['p4']]
    bipolar_montage['p4-o2'] = data[name_to_index['p4']] - \
        data[name_to_index['o2']]

    bipolar_montage['fp2-f8'] = data[name_to_index['fp2']] - \
        data[name_to_index['f8']]
    bipolar_montage['f8-t4'] = data[name_to_index['f8']] - \
        data[name_to_index['t4']]
    bipolar_montage['t4-t6'] = data[name_to_index['t4']] - \
        data[name_to_index['t6']]
    bipolar_montage['t6-o2'] = data[name_to_index['t6']] - \
        data[name_to_index['o2']]

    bipolar_montage['fz-cz'] = data[name_to_index['fz']] - \
        data[name_to_index['cz']]
    bipolar_montage['cz-pz'] = data[name_to_index['cz']] - \
        data[name_to_index['pz']]

    return bipolar_montage

# Function to plot multiple channels of an EEG (takes in either a dictionary or an array with an additional channel names array)


def plot_eeg(data, sfreq, start=0, end=15, indices=None, ch_names=None, padding=0, figsize=(24, 8)):
    """
    Plots multiple channels of an input EEG
    Input:
      data (ndarray or dict): Input EEG data that is either an array or a dict. If data is an ndarray, it will be of shape
      (num_channels, num_samples). If it is a dict, it will have num_channels elements. Each key is a string that is a channel name,
      and each value is the corresponding ndarray of shape (num_samples) that is the EEG signal for that channel
      sfreq (float): Sampling frequency of the data, in Hz
      start (float): The start time of the clip to be plotted, in seconds
      end (float): The end time of the clip to be plotted, in seconds
      indices (list, optional): List of indices of the channels to be plotted. If not given, all channels will be plotted
      labels (list, optional): Optional list of strings to be used as labels for the channels in the plot. If data is a dict,
      this parameter will not be used
      padding (float, optional): The amount of padding to be used between adjacent channels in the plot. If not given, the
      default value is 0
      figsize (tuple, optional): Optional parameter of the form (w, h), where w and h are floats that are the desired
      width and height, respectively, in inches. If no value given, figsize will be set to (24,8)
    Returns:
      None
    """
    fig, ax = plt.subplots(figsize=figsize)

    # arr is the variable for the copy of the data that will be used in the function
    arr = np.copy(data)

    # If data is a dictionary, obtain the keys and channel names from it
    if (type(data) == dict):
        arr = np.array(list(data.values()))
        ch_names = list(data.keys())

    # If an indices argument was not given, simply make indices [0,1,...,len(arr)] to display all channels
    if (not indices):
        indices = [i for i in range(len(arr))]

    # Remove all elements from arr and ch_names that are not in indices
    mask = [False for i in range(len(arr))]
    for ind in indices:
        mask[ind] = True
    arr = arr[mask]
    if (ch_names):
        ch_names = [ch_names[ind] for ind in indices]

    # Convert start, end from seconds to sample numbers
    start = int(start * sfreq)
    end = int(end * sfreq)

    # Keep only desired time clip from arr
    arr = arr[:, start:end]

    # Times array for plotting purposes. Has shape (len(data),), and in each index contains the time stamp of the sample
    # For example, index 0 is 0, index 1 is 1/sfreq, index 2 is 2/sfreq, etc
    # Thus times[i] gives the timestamp for the sample data[x][i]
    # Creates an array [0,1,2,...,len(data[0])]
    times = np.arange(0, len(arr[0]), 1)
    # Divide all entries in times by sample frequency to obtain the desired times array
    times = times / sfreq

    maxes = np.max(arr[:-1], axis=1)
    mins = np.min(arr, axis=1)
    maxes = np.insert(maxes, 0, 0)

    maxes += padding

    temp1 = np.cumsum(maxes)
    temp2 = np.cumsum(mins)
    offsets = temp1 - temp2

    # Array of means of each of the channels we are plotting (ie: means[i] is the mean value of arr[i] + offsets[i])
    # These means will be used as the locations for the y axis channel labels
    means = np.zeros(len(arr))

    for i in range(len(arr)):
        ax.plot(times, arr[i] + offsets[i], color='black')
        means[i] = np.mean(arr[i] + offsets[i])
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Channels')

    ax.set_yticks(means)
    if ch_names:
        ax.set_yticklabels(ch_names)

    plt.show()

# Function to plot bipolar montage of eeg. Input is a dictionary that is a bipolar montage of an eeg


def plot_bipolar_montage(data, sfreq, start=0, end=15, indices=None, padding=0, figsize=(24, 8)):
    """
    Plots bipolar montage given an input EEG bipolar montage dictionary
    Input:
      data (dictionary): Dictionary that is the EEG data in bipolar montage format. The keys are strings representing the name of a channel in the
      montage (eg: 'fp1-fp7'), and the values are ndarrays of shape (num_samples) that are the associated signal for that channel.
      sfreq (float): Sampling frequency of the input data, in Hz.
      start (float): Start time of clip from data to plot, in seconds
      end (float): End time of clip from data to plot, in seconds
      indices (list): A list of integers that are the indices of channels from the bipolar montage dictionary to plot. If no argument is given, the entire bipolar
      montage will be plotted
      padding (float): Amount of padding to add between vertically adjacent channels when plotting the montage
      figsize (tuple): Tuple of 2 integers that specifies the desired plot size. Default is (24, 8)
    Returns:
      None
    """
    fig, ax = plt.subplots(figsize=figsize)

    # arr is the variable for the copy of the data that will be used in the function
    arr = np.copy(data)

    arr = np.array(list(data.values()))
    ch_names = list(data.keys())

    # Reverse array and ch_names, and appropriately modify indices. This is so that when we plot the bipolar montage it will
    # plot with the appropriate top to bottom order (eg: fp1-fp7 on the top)
    arr = np.flip(arr, axis=0)
    ch_names.reverse()
    if (indices):
        for i in range(len(indices)):
            indices[i] = (len(arr) - 1) - i
        indices.sort()

    # If an indices argument was not given, simply make indices [0,1,...,len(arr)] to display all channels
    if (not indices):
        indices = [i for i in range(len(arr))]

    # Remove all elements from arr and ch_names that are not in indices
    mask = [False for i in range(len(arr))]
    for ind in indices:
        mask[ind] = True
    arr = arr[mask]
    if (ch_names):
        ch_names = [ch_names[ind] for ind in indices]

    # Convert start, end from seconds to sample numbers
    start = int(start * sfreq)
    end = int(end * sfreq)

    # Keep only desired time clip from arr
    arr = arr[:, start:end]

    # Times array for plotting purposes. Has shape (len(data),), and in each index contains the time stamp of the sample
    # For example, index 0 is 0, index 1 is 1/sfreq, index 2 is 2/sfreq, etc
    # Thus times[i] gives the timestamp for the sample data[x][i]
    # Creates an array [0,1,2,...,len(data[0])]
    times = np.arange(0, len(arr[0]), 1)
    # Divide all entries in times by sample frequency to obtain the desired times array
    times = times / sfreq

    maxes = np.max(arr[:-1], axis=1)
    mins = np.min(arr, axis=1)
    maxes = np.insert(maxes, 0, 0)

    maxes += padding

    # Add spacing between each chain of electrodes if plotting full bipolar montage
    # HOW TO IMPROVE THIS?
    if (len(arr) == 18):
        scale = 3
        maxes[2] += scale * padding
        maxes[6] += scale * padding
        maxes[10] += scale * padding
        maxes[14] += scale * padding

    temp1 = np.cumsum(maxes)
    temp2 = np.cumsum(mins)
    offsets = temp1 - temp2

    # Array of means of each of the channels we are plotting (ie: means[i] is the mean value of arr[i] + offsets[i])
    # These means will be used as the locations for the y axis channel labels
    means = np.zeros(len(arr))

    for i in range(len(arr)):
        ax.plot(times, arr[i] + offsets[i])
        means[i] = np.mean(arr[i] + offsets[i])

    ax.set_yticks(means)
    if ch_names:
        ax.set_yticklabels(ch_names)

    plt.show()


def load_full_channels(dataset, duration_secs, sampling_rate, chn_idx, offset_time=0):
    """
    Loads the entire channel from IEEG.org
    Input:
      dataset: the IEEG dataset object
      duration_secs: the duration of the channel, in seconds
      sampling_rate: the sampling rate of the channel, in Hz
      chn_idx: the indicies of the m channels you want to load, as an array-like object
    Returns:
      [n, m] ndarry of the channels' values.
    """
    # stores the segments of the channel's data
    chn_segments = []

    # how many segments do we expect?
    num_segments = int(np.ceil(duration_secs * sampling_rate / 1e5))

    # segment start times and the step
    seg_start, step = np.linspace(1 + offset_time*1e6, offset_time*1e6 +
                                  duration_secs*1e6, num_segments, endpoint=False, retstep=True)
    # get the segments
    for start in seg_start:
        chn_segments.append(dataset.get_data(start, step, chn_idx))

    # concatenate the segments vertically
    return np.vstack(chn_segments)


# Run clip through preprocessing
def preprocess(data_clip, sfreq):
    # Get clip with the start, end times
    clip = np.copy(data_clip)

    # Run filtering on the clip and common average reference it
    notch = create_notch_filter(4, 55, 65, sfreq)
    high_pass = create_high_pass_filter(4, 0.5, sfreq)
    # low_pass = create_low_pass_filter()
    b, a = sig.butter(N=4, Wn=5, btype='lowpass', fs=sfreq)

    padding_right = np.copy(clip)
    padding_left = np.copy(clip)
    clip = np.concatenate((clip, padding_right), axis=1)
    clip = np.concatenate((padding_left, clip), axis=1)

    clip = apply_filter(clip, notch)
    clip = apply_filter(clip, high_pass)
    clip = apply_filter(clip, (b, a))

    # Remove padding
    clip = clip[:, len(padding_left[0]):-len(padding_right[0])]

    # clip = common_average_reference(clip)

    return clip


# Function to return array of averagedPsd arrays (one per time window), based
# on the Kerr 2012 paper. Returns a numpy array of shape (numBands, numWindows),
# where each row is an array of a particular frequency for all time windows.
# Input signal is the original signal, not a power spectrum.
def averagePsds(signal, sfreq, timeWindow, numBands):
    averagedPsds = []
    ind = 0
    while (ind + timeWindow * sfreq <= len(signal)):
        # Calculate the psd for the current time window
        spectrum = psd(signal[int(ind): int(
            ind + timeWindow * sfreq)], sfreq)[1]
        N = timeWindow * sfreq
        # Variable that is the discrete frequency associated with real frequency of 1 Hz,
        # based on the formula k = N * f_k / f_s
        k = int(N * 1 / sfreq)
        # Get the averaged psd of spectrum
        averagedPsd = [0 for i in range(numBands)]
        for i in range(len(averagedPsd)):
            averagedPsd[i] = np.mean(spectrum[int(k * i): int(k * (i + 1))])
        # Append averagedPsd to averagedPsds
        averagedPsds.append(averagedPsd)
        # Increment ind
        ind += timeWindow * sfreq

    return np.array(averagedPsds).T


# Function to return all the runs in an ieeg file. Returns None on failure.
# On success, returns a tuple (dataClips, channels, sfreq). dataClips is a list of
# numpy arrays that are the runs, and channels is a list of the channels that were
# kept (only channels that are in channelsRef are retained)
def getRuns(session, file, channelsRef, printProgress=False):
    ## LOAD FILE ##
    try:
        dataset = session.open_dataset(file)
    except:
        return None, None, None
    # Get channel labels and put them in ch_names array
    ch_names = dataset.get_channel_labels()
    # Assign time_series_details object to details variable
    details = dataset.get_time_series_details(ch_names[0])
    sfreq = details.sample_rate
    # ch_indices array (array of indices for each channel)
    ch_indices = [i for i in range(len(ch_names))]
    pairs = get_annotation_times(dataset, 'EEG clip times')
    data_clips = []

    # Create mask for which channels to keep
    mask = []
    # Array of the retained channels
    channels = []
    for channelName in ch_names:
        channelName = channelName.lower()
        if (channelName in channelsRef):
            mask.append(True)
            channels.append(channelName)
        else:
            mask.append(False)

    # Assert that all the desired channels are present
    assert len(channels) == len(channelsRef)

    for i in range(len(pairs)):
        if (printProgress):
            print('-----', i)
        start, end = pairs[i][0], pairs[i][1]
        while (True):
            try:
                data = load_full_channels(
                    dataset, end-start, sfreq, ch_indices, offset_time=start)
                break
            except:
                continue
        data = data.T
        # Keep only the desired channels in data
        data = data[mask, :]
        # Add data to data_clips
        data_clips.append(data)

    ## Chop off NaNs from downloaded clips ##
    for i in range(len(data_clips)):
        clip = data_clips[i]
        max_first_num = 0
        min_last_num = len(clip[0])-1
        for j in range(len(clip)):
            first_num = 0
            last_num = len(clip[0])-1
            while (np.isnan(clip[j][first_num])):
                first_num += 1
            while (np.isnan(clip[j][last_num])):
                last_num -= 1
            max_first_num, min_last_num = max(
                max_first_num, first_num), min(min_last_num, last_num)
        # Adjust start/end times of the clip appropriately
        pairs[i][0] += max_first_num / sfreq
        pairs[i][1] -= (len(clip[0]) - 1 - min_last_num) / sfreq
        # Cut out nan segments of data
        data_clips[i] = data_clips[i][:, max_first_num:min_last_num+1]

        # Run clip through 0.5 Hz high pass filter
        high_pass = create_high_pass_filter(4, 0.5, sfreq)
        data_clips[i] = apply_filter(data_clips[i], high_pass)

    return (data_clips, channels, sfreq)

# Function to, given a list of lists of features, impute the missing values with
# -1


def impute(featureArr):
    # Step 1: Find the length of the longest list
    max_length = max(len(sub_list) for sub_list in featureArr)

    # Step 2: Extend each sub-list with -1 values to match the length of the longest list
    for sub_list in featureArr:
        sub_list.extend([-1] * (max_length - len(sub_list)))

    return featureArr


def warn(*args, **kwargs):
    pass


warnings.warn = warn

# Function to, given an input feature matrix (of shape (numDataPoints, numFeatures))
# X, and labels y, return a random subset of X and y of maximum size such that
# the number of data points in each class are equal


def balancedSubsample(X, y, size=None, random_state=None):
    if random_state is not None:
        np.random.seed(random_state)

    classes, class_counts = np.unique(y, return_counts=True)
    min_class_count = np.min(class_counts)

    if size is None or size > min_class_count:
        size = min_class_count

    X_balanced = []
    y_balanced = []

    for class_label in classes:
        class_indices = np.where(y == class_label)[0]
        selected_indices = np.random.choice(
            class_indices, size=size, replace=False)

        X_balanced.extend(X[selected_indices])
        y_balanced.extend(y[selected_indices])

    X_balanced = np.array(X_balanced)
    y_balanced = np.array(y_balanced)

    return X_balanced, y_balanced

# Function to, given an sklearn model, input feature matrix (of shape
# (numDataPoints, numFeatures)) X, and labels y, perform LOSO cross validation
# and return the average accuracy, sensitivity, and specificity


def losoCrossVal(model, X, y, balanceClasses=False, threshold=0.5):
    loo = LeaveOneOut()

    accuracies = []
    # True positive rate (sensitivity)
    tpr = []
    # True negative rate (specificity)
    tnr = []
    aucs = []
    cnt = 0
    for train_index, test_index in loo.split(X):
        cnt += 1
        print(cnt)
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]

        # Subsample X_train, y_train to make class balanced
        # if (balanceClasses) :
        #   X_train, y_train = balancedSubsample(X_train, y_train)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        accuracy = accuracy_score(y_test, y_pred)

        if (y_test[0] == 1):
            tpr.append(y_pred[0])
        else:
            tnr.append(1 - y_pred[0])

        accuracies.append(accuracy)

    # print(accuracies)
    # print(y)
    avg_accuracy = np.mean(accuracies)
    avg_sensitivity = np.mean(tpr)
    avg_specificity = np.mean(tnr)

    return avg_accuracy, avg_sensitivity, avg_specificity


# Function to, given an input feature matrix (of shape (numDataPoints, numFeatures))
# X, and labels y, perform sklearn PCA to reduce the dimensionality to 2
# dimensions, and then plot a scatter plot that is color coded based on the label
def plotPcaScatter(X, y):
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X)

    # Get unique labels for color coding
    unique_labels = np.unique(y)

    # Create a scatter plot with color-coded labels
    for label in unique_labels:
        plt.scatter(X_pca[y == label, 0],
                    X_pca[y == label, 1], label=str(label))

    # Customize the plot
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.title('PCA Scatter Plot')
    plt.legend()

    plt.savefig('scatter.png')

    # Show the plot
    plt.show()
