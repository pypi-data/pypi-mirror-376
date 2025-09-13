from pathlib import Path

def read_glx_meta(meta_path):
    meta_path = Path(meta_path)
    meta_dict = {}
    with meta_path.open() as f:
        lines = f.read().splitlines()
        for line in lines:
            key, data = line.split(sep='=')
            key = key.strip('~')
            meta_dict[key] = data

    return meta_dict
