from simianpy.io.raw.extractbin import extract_windows_samples
from simianpy.io.spikeglx.get_channel_configuration import get_channel_configuration

from pathlib import Path
import warnings

import click
import numpy as np
import pandas as pd
import xarray as xr
from tqdm import tqdm

SAMPLE_RATE = 30000  # Hz
def extract_waveforms(
        spike_times, 
        spike_clusters, 
        cluster_info, 
        ap_bin, 
        ap_meta, 
        output_directory=None,
        pbar=True, 
        n_waveforms=400,
        Filter=None,
        chunk=True,
        aggregate=True
    ):
    if output_directory is None:
        output_directory = Path(spike_times).parent
    output_directory = Path(output_directory)
    output_directory.mkdir(parents=True, exist_ok=True)

    spike_times = np.load(spike_times)
    unitids = np.load(spike_clusters)
    chan_map = get_channel_configuration(ap_meta)
    n_chan = chan_map['n_chan']

    cluster_info = Path(cluster_info)
    if cluster_info.exists():
        cluster_info = pd.read_csv(cluster_info, sep='\t')
        good_units = cluster_info.query("group == 'good'")['cluster_id'].to_numpy()
        if len(good_units) > 0:
            mask = np.isin(unitids, good_units)
            spike_times = spike_times[mask]
            unitids = unitids[mask]
        else:
            warnings.warn("No good units found in cluster_info.tsv, Please sort the file using phy. Using all units")
    else:
        warnings.warn(f"cluster_info.tsv file not found at {cluster_info}. Please sort the file using phy. Using all units")

    unique_unitids = np.unique(unitids)
    wf_indices = []
    wf_unitids = []
    for unitid in tqdm(unique_unitids, desc='Selecting waveforms', disable=not pbar):
        mask = unitid == unitids
        unit_idx = np.where(mask)[0]
        if n_waveforms is not None:
            unit_idx = np.random.choice(unit_idx, min(n_waveforms, unit_idx.size), replace=False)
        wf_indices.append(spike_times[unit_idx])
        wf_unitids.append(np.repeat(unitid, n_waveforms))
    wf_indices = np.concatenate(wf_indices)
    wf_unitids = np.concatenate(wf_unitids)
    sortidx = np.argsort(wf_indices)
    wf_indices = wf_indices[sortidx]
    wf_unitids = wf_unitids[sortidx] 

    window = (-30, 30)  # 2 ms window
    wf = extract_windows_samples(
        ap_bin,
        wf_indices,
        window=window,
        n_channels=n_chan,
        pbar=pbar,
        dask=False
    )
    n_wfs, n_samples, n_chans = wf.shape
    wf = xr.DataArray(
        wf, 
        dims=['waveform', 'time', 'channels'], 
        coords={
            'waveform': np.arange(n_wfs),
            'channels': np.arange(n_chans),
            'time': (np.arange(n_samples) + window[0] / SAMPLE_RATE),
            'unitid': ('waveform', wf_unitids)
        }
    )
    wf = wf.isel(channels=slice(None, -1)) # drop the sync channel
    wf = wf.assign_coords(
        x=('channels', chan_map['xc']),
        y=('channels', chan_map['yc']),
    )
    if not aggregate:
        wf.to_netcdf(output_directory / 'waveforms.nc', engine='h5netcdf')
        return

    if Filter is not None:
        if chunk:
            wf = Filter.apply_xarray(wf.chunk(channels=12), 'time').compute()
        else:
            wf = Filter.apply_xarray(wf, 'time')
    wf_mean = wf.groupby('unitid').mean('waveform').astype(np.float32)
    peak_channel = np.abs(wf_mean).max('time').idxmax('channels').values.astype('int16')
    wf_mean = wf_mean.assign_coords(
        peak_channel = ('unitid', peak_channel)
    )
    wf_mean.to_netcdf(output_directory / 'mean_waveforms.nc', engine='h5netcdf')

    single_channel_waveforms = []
    for unitid, unitwf in wf_mean.groupby('unitid'):
        single_channel_waveforms.append(unitwf.sel(channels=unitwf['peak_channel'].item()))
    single_channel_waveforms = xr.concat(single_channel_waveforms,dim='unitid',coords='different',compat='equals')
    single_channel_waveforms.to_netcdf(output_directory / 'mean_waveforms_single_channel.nc', engine='h5netcdf')

@click.command("extract-waveforms")
@click.argument('phy_dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.argument('ap_bin', type=click.Path(exists=True, dir_okay=False, readable=True))
@click.option('-o', '--output_directory', type=click.Path(file_okay=False, dir_okay=True, writable=True), default=None, help='Directory to save the output files. Defaults to the directory containing the spike_times file.')
@click.option('-n', '--n-waveforms', type=int, default=400, help='Number of waveforms to extract per unit.')
@click.option('--pbar/--no-pbar', default=True, help='Show progress bar.')
@click.option('--chunk/--no-chunk', default=True, help='Chunk the data when filtering. Recommended for large datasets.')
@click.option('--aggregate/--raw', default=True, help='Aggregate waveforms across time.')
@click.option('-f', '--filter', 'Filter', default=None, help='Filter to apply to the waveforms. low:high:order, e.g., 300:6000:3 for a 3rd order Butterworth bandpass filter between 300 and 6000 Hz.')
def main(phy_dir, ap_bin, output_directory, n_waveforms, pbar, chunk, aggregate, Filter):
    """
    Extract waveforms from a SpikeGLX binary file based on spike times and cluster information from a Phy directory.

    PHY_DIR is the path to the Phy directory containing spike_times.npy, spike_clusters.npy, and cluster_info.tsv files.

    AP_BIN is the path to the SpikeGLX AP binary file.
    """
    phy_dir = Path(phy_dir)
    spike_times = phy_dir / 'spike_times.npy'
    spike_clusters = phy_dir / 'spike_clusters.npy'
    cluster_info = phy_dir / 'cluster_info.tsv'
    ap_meta = ap_bin.replace('.bin', '.meta')
    if Filter is not None:
        from simianpy.signal.sosfilter import sosFilter
        try:
            low, high, order = map(float, Filter.split(':'))
            order = int(order)
        except Exception as e:
            raise ValueError("Filter must be in the format low:high:order, e.g., 300:6000:3 for a 3rd order Butterworth bandpass filter between 300 and 6000 Hz.") from e
        Filter = sosFilter('bandpass', order, [low, high], SAMPLE_RATE)
    extract_waveforms(
        spike_times,
        spike_clusters,
        cluster_info,
        ap_bin,
        ap_meta,
        output_directory=output_directory,
        pbar=pbar,
        n_waveforms=n_waveforms,
        chunk=chunk,
        Filter=Filter,
        aggregate=aggregate
    )
