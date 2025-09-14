#!/usr/bin/env python3
"""
Package entry point for ``image_analysis_sd``.

Running ``python -m image_analysis_sd`` will invoke the same CLI that
``shard-sd`` provides, delegating to :func:`image_analysis_sd.core.main`.
"""
from .core import main

if __name__ == "__main__":
    main()
