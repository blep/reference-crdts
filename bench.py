#!/usr/bin/env python3
"""Benchmarking script for CRDT operations, ported from bench.ts."""

import gzip
import json
import os
import time
import urllib.request
from reference_crdts.crdts import new_doc, get_array, local_insert, local_delete, yjs_mod, automerge, sync9


def download_if_missing(filename, url):
    """Download the file if it doesn't exist."""
    if not os.path.exists(filename):
        print(f"Downloading {filename}...")
        try:
            urllib.request.urlretrieve(url, filename)
            print(f"Downloaded {filename}")
        except Exception as e:
            print(f"Failed to download {filename}: {e}")
            return False
    return True


def bench(alg_name: str, alg):
    # filename = 'sveltecomponent'
    filename = 'automerge-paper'
    filepath = f'crdt-benchmarks/{filename}.json.gz'
    url = f'https://github.com/josephg/editing-traces/raw/master/sequential_traces/{filename}.json.gz'
    
    if not download_if_missing(filepath, url):
        print(f"Skipping {alg_name} benchmark due to download failure.")
        return
    
    try:
        with gzip.open(filepath, 'rt') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Failed to load {filepath}: {e}")
        return
    
    start_content = data['startContent']
    end_content = data['endContent']
    txns = data['txns']
    
    print(f"Starting {alg_name} {filename}")
    start_time = time.time()
    
    doc = new_doc()
    
    i = 0
    total_patches = 0
    for txn in txns:
        i += 1
        if i % 10000 == 0:
            print(i)
        for patch in txn['patches']:
            total_patches += 1
            pos, del_count, inserted = patch
            if inserted:
                alg.local_insert(doc, 'A', pos, inserted, alg)
            elif del_count:
                local_delete(doc, 'A', pos)
    
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"Time: {elapsed:.3f}s")
    print(f"Transactions: {len(txns)} ({len(txns)/elapsed:.1f}/s)")
    print(f"Patches: {total_patches} ({total_patches/elapsed:.1f}/s)")


def main():
    # Ensure the directory exists
    os.makedirs('crdt-benchmarks', exist_ok=True)
    
    bench('yjs mod', yjs_mod)
    bench('automerge', automerge)
    bench('sync9', sync9)


if __name__ == "__main__":
    main()