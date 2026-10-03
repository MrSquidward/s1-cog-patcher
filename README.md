# Sentinel-1 COG Patcher

A Python script that patches the `manifest.safe` of a Sentinel-1 **COG_SAFE** product (Cloud Optimized GeoTIFF), distributed by the Copernicus Data Space Ecosystem so that ESA SNAP reads the correct processor (IPF) version.

Without the patch, SNAP misreads the IPF version of every COG_SAFE product as **1.0**. As a result, some of the SNAP operators (like Remove-GRD-Border-Noise) fails, calibration shows a warning, and thermal noise removal runs code meant for pre-2018 data.

## Usage

Give the script the product's `.SAFE` folder or its `manifest.safe` file:

```bash
python3 s1-cog-patcher.py S1C_IW_GRDH_1SDV_20260306T000637_20260306T000702_006636_00D653_EAE1_COG.SAFE
```

The script is safe to run more than once. The original `manifest.safe` is copied and saved as `manifest.safe.orig`. 

## The problem

### Symptoms

Recent SNAP versions open COG_SAFE products, but processing them gives one or more of these:

- **Remove-GRD-Border-Noise fails:**
  ```
  [NodeId: Remove-GRD-Border-Noise] Cannot invoke "org.esa.snap.core.datamodel.MetadataElement.getAttributeString(String)" because "noiseVectorListElem" is null
  ```
- **Calibration warns:**
  ```
  The calibration LUT for this product could be incorrect and therefore the calibration result may not be reliable.
  ```
- **No error, but different results.** The same scene processed as COG_SAFE and as the original SAFE gives different calibrated values.

### Root cause

When CDSE converts a product to COG, it adds a new top-level `COG Conversion` processing entry to `manifest.safe`. The original ESA processing chain is nested inside it:

```xml
<safe:processing name="COG Conversion" ...>
  <safe:facility organisation="CloudFerro" ...>
    <safe:software name="Sentinel-1 COGifier" version="001.00"/>   <!-- SNAP reads this -->
  </safe:facility>
  <safe:resource ...>
    <safe:processing name="GRD Post Processing" ...>
      <safe:facility organisation="ESA" ...>
        <safe:software name="Sentinel-1 IPF" version="004.03"/>    <!-- the real IPF version -->
      </safe:facility>
      ...
```

SNAP's Sentinel-1 reader takes only the outermost `safe:processing` element. From it, the reader builds `Processing_system_identifier`, here `CloudFerro Sentinel-1 COGifier 001.00`. The operators treat the last word of that string as the IPF version, so they see **1.0**, not the real version (e.g. 4.03).

## The fix

The script changes **one attribute** in `manifest.safe`. It copies the real IPF version from the nested ESA entry onto the COGifier entry:

```diff
- <safe:software name="Sentinel-1 COGifier" version="001.00"/>
+ <safe:software name="Sentinel-1 COGifier" version="004.03"/>
```

SNAP then reads `CloudFerro Sentinel-1 COGifier 004.03`, and every operator gets the correct version (4.03). Nothing else in the product is changed. Each product's own IPF version is read from its manifest, not hard-coded, so the script works on products from any IPF version.

## Requirements

- Python 3.6 or newer. Standard library only, nothing to install.
- SNAP 10 or newer. Older versions cannot open COG_SAFE products at all, because they don't support the Zstandard compression the COGs use (error `Unsupported compression type (tag number = 50000)`). This script does not change that.
- The product must be unzipped (a `.SAFE` folder, not a `.zip`).

### Reverting

To restore the original manifest:

```bash
mv PRODUCT.SAFE/manifest.safe.orig PRODUCT.SAFE/manifest.safe
```

## Issues
If you encounter any problems, feel free to reach out or open an issue.
