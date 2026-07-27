# satview

Predicts when satellites will be visible from one or more ground locations. For
each configured NORAD ID and site, it reports rise/peak/set times with
azimuth, elevation, and ground-to-satellite range, whether the pass is
actually optically visible (sunlit satellite + dark sky), and an estimated
peak visual magnitude.

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

First run will download and cache two things into `cache/` (not committed to
git): a JPL ephemeris file (`de421.bsp`, ~17MB, used for sun-position
calculations) and each satellite's TLE. These are fetched automatically, no
manual step needed.

## Usage

1. Copy `config.example.yaml` to your own config file and edit it (see
   [Config reference](#config-reference) below).
2. Run:

```bash
python -m satview.run your_config.yaml
```

If your shell session doesn't already have `.venv` activated, use one of
these instead, which activate it and run in one line:

```powershell
# Windows PowerShell
.venv\Scripts\python.exe -m satview.run your_config.yaml
```

(Calling the venv's `python.exe` directly has the same effect as activating
and works even when PowerShell's script execution policy is `Restricted` —
the default on many machines, which blocks `Activate.ps1` from running at
all. If you'd rather actually activate it in PowerShell, run
`.venv\Scripts\Activate.ps1` first and, if that errors, allow scripts for
just that process with
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.)

```bat
:: Windows cmd.exe
.venv\Scripts\activate.bat && python -m satview.run your_config.yaml
```

```bash
# Git Bash on Windows
source .venv/Scripts/activate && python -m satview.run your_config.yaml

# macOS/Linux
source .venv/bin/activate && python -m satview.run your_config.yaml
```

This prints a per-site, per-satellite pass table to the console. If the
config has an `output` section, it also writes the same data to a CSV or
JSON file.

## Config reference

```yaml
sites:
  - name: Home
    latitude: 40.7580
    longitude: -73.9855
    elevation_m: 10        # optional, defaults to 0

satellites:
  - norad_id: 25544         # ISS

search:
  start: now                 # "now", or an ISO8601 timestamp like "2026-07-23T00:00:00Z"
  hours: 48                  # how far ahead to search

elevation_mask_deg: 0        # minimum elevation to count as a line-of-sight pass

output:                       # optional; omit to only print to the console
  path: passes.csv            # format inferred from .csv/.json extension, or set 'format' explicitly
```

Multiple `sites` and `satellites` entries are all run against each other (a
config with 2 sites and 3 satellites produces 6 site/satellite reports).

Timezone for each site's printed/exported times is resolved automatically
from its latitude/longitude — no need to specify it.

## What "visible" means here

Every pass is evaluated two ways:

- **Line-of-sight (LOS)**: the satellite is above the elevation mask,
  regardless of lighting. This is the rise/peak/set always reported.
- **Optical visibility**: the sub-window (if any) within the LOS pass where
  the satellite is sunlit *and* the sky is dark enough to see it (sun more
  than 6° below the horizon). Only passes with a nonzero optical window get
  an estimated magnitude.

## Magnitude estimation

Peak magnitude is estimated from a satellite's intrinsic ("standard")
brightness, adjusted for range and solar phase angle, plus a standard
atmospheric extinction correction for passes low on the horizon. Not every
satellite has a known standard magnitude — in that case magnitude is
reported as `N/A (no catalog data)` rather than guessed.

The catalog used (`satview/data/qsmag.txt`) is a static, bundled snapshot of
Mike McCants' Quicksat intrinsic-magnitude list (dated 2020), retrieved from
a Wayback Machine archive since the live source is no longer reliably
hosted. It won't include newly launched satellites, and any given estimate
is realistically only accurate to within about half a magnitude — actual
brightness also depends on a satellite's real-time attitude and panel
orientation, which no static catalog captures.

## Running tests

```bash
python -m pytest
```

Tests cover config validation, TLE fetch/cache-fallback logic, timezone
resolution, and output formatting. They run offline — no live network calls.
