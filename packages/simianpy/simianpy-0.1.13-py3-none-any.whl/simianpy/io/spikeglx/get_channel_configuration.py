from simianpy.io.spikeglx.read_glx_meta import read_glx_meta
import re
import json

def get_channel_configuration(meta_path):
    meta_dict = read_glx_meta(meta_path)
    ap,lf,sy = list(map(int, meta_dict['snsApLfSy'].split(',')))
    channel_geom = list(re.findall(r'\((\d+):(\d+):(\d+):(\d+)\)', meta_dict['snsGeomMap']))
    assert len(channel_geom) == ap, "Mismatch between snsApLfSy and snsGeomMap?"
    data = {
        'chanMap': [],
        'kcoords': [],
        'xc': [],
        'yc': []
    }
    for idx, (shank, x, y, active) in enumerate(channel_geom):
        data['chanMap'].append(idx)
        data['kcoords'].append(int(shank))
        data['xc'].append(int(x))
        data['yc'].append(int(y))
    data['n_chan'] = int(meta_dict['nSavedChans'])
    return data
