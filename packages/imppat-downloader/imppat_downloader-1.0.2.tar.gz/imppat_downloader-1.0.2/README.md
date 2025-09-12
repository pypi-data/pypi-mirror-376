# IMPPAT Downloader

**IMPPAT Downloader** is a Python command-line tool to fetch **all available structure formats** (MOL, SDF, PDB, etc.) from the [IMPPAT database](https://cb.imsc.res.in/imppat/).

For each IMPHY ID, it creates a folder and saves all available files there. It also generates a manifest CSV summarizing the results.

## Features
- Downloads multiple chemical structure formats automatically.
- Organizes files per compound in separate folders.
- Generates a timestamped manifest CSV for tracking.
- Supports skipping already downloaded files.

## Installation
```bash
pip install imppat-downloader


##Usage

imppat-downloader --start 1 --end 5 --delay 2 --skip-existing

Arguments
--start: Start IMPHY ID (integer)

--end: End IMPHY ID (integer, exclusive)

--delay: Delay between requests (seconds, default 2.0)

--skip-existing: Skip files that are already downloaded