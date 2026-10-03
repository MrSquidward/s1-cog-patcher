#!/usr/bin/env python3
"""
Patch Sentinel-1 COG_SAFE manifest so SNAP reads the real IPF version.

Copies the nested "Sentinel-1 IPF" version onto the "Sentinel-1 COGifier"
entry (e.g. 001.00 -> 004.03). The original is kept as manifest.safe.orig.

Usage:
    python3 s1-cog-patcher.py PRODUCT.SAFE
    python3 s1-cog-patcher.py PRODUCT.SAFE/manifest.safe
"""
import re
import shutil
import sys
from pathlib import Path

if len(sys.argv) != 2:
    sys.exit(__doc__)

path = Path(sys.argv[1])
manifest = path / "manifest.safe" if path.is_dir() else path
if not manifest.is_file():
    sys.exit(f"Error: {manifest} not found (zipped products must be unzipped first)")

text = manifest.read_text(encoding="utf-8")
tags = list(re.finditer(r'<(?:\w+:)?software\b[^>]*>', text))

cog = next((t for t in tags if 'COGifier' in t.group(0)), None)
ipf = next((t for t in tags if 'name="Sentinel-1 IPF"' in t.group(0)), None)
if cog is None:
    sys.exit("Nothing to do: no COG Conversion entry (not a COG_SAFE product?)")
if ipf is None:
    sys.exit("Error: no Sentinel-1 IPF version found in manifest")

ipf_version = re.search(r'\bversion="([^"]+)"', ipf.group(0)).group(1)
old = re.search(r'\bversion="([^"]*)"', cog.group(0))
if old and old.group(1) == ipf_version:
    sys.exit(f"Already patched (IPF {ipf_version})")

new_tag = (re.sub(r'\bversion="[^"]*"', f'version="{ipf_version}"', cog.group(0)) if old
           else cog.group(0).replace("software", f'software version="{ipf_version}"', 1))

backup = manifest.with_name("manifest.safe.orig")
if not backup.exists():
    shutil.copy2(manifest, backup)
manifest.write_text(text[:cog.start()] + new_tag + text[cog.end():], encoding="utf-8")
print(f"Patched: COGifier {old.group(1) if old else '(none)'} -> IPF {ipf_version}")
print(f"Backup:  {backup}")
