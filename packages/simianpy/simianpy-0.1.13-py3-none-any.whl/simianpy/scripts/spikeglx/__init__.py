import click

from simianpy.scripts.spikeglx.extract_waveforms import main as extract_waveforms

@click.group()
def SpikeGLX():
    pass

SpikeGLX.add_command(extract_waveforms)
