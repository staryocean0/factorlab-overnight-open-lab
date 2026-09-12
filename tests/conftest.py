"""Default QA is synthetic/metadata only, including during module collection."""
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def maintenance_io_barrier(event, args):
    if event in {'socket.connect', 'socket.getaddrinfo', 'socket.bind'}:
        raise RuntimeError('maintenance_network_forbidden')
    if event == 'open' and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).resolve()
        if path.is_relative_to(ROOT):
            rel = path.relative_to(ROOT).as_posix()
            if path.suffix.lower() in {'.csv', '.parquet', '.feather', '.pkl', '.pickle', '.pt', '.npz'} or rel.startswith(('output/', 'artifacts/')):
                raise RuntimeError('maintenance_market_or_account_rows_forbidden: ' + rel)


sys.addaudithook(maintenance_io_barrier)
