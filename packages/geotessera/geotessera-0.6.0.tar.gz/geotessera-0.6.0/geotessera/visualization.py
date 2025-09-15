"""Simplified visualization utilities for GeoTessera.

This module provides core visualization functions for coverage analysis
and mosaic creation. Web/tile generation functions are in the web submodule.
"""

from pathlib import Path
from typing import Union, List, Tuple, Optional, Dict, Callable

import numpy as np
import geopandas as gpd
import pandas as pd


def analyze_geotiff_coverage(geotiff_paths: List[str]) -> Dict:
    """Analyze coverage and metadata of GeoTIFF files.

    Args:
        geotiff_paths: List of GeoTIFF file paths

    Returns:
        Dictionary with coverage statistics and metadata
    """
    try:
        import rasterio
    except ImportError:
        raise ImportError("rasterio required: pip install rasterio")

    if not geotiff_paths:
        return {"error": "No files provided"}

    coverage_info = {
        "total_files": len(geotiff_paths),
        "tiles": [],
        "bounds": {
            "min_lon": float("inf"),
            "min_lat": float("inf"),
            "max_lon": float("-inf"),
            "max_lat": float("-inf"),
        },
        "band_counts": {},
        "years": set(),
        "crs": set(),
    }

    for path in geotiff_paths:
        try:
            with rasterio.open(path) as src:
                bounds = src.bounds

                # Convert bounds to lat/lon if needed
                if src.crs and src.crs != "EPSG:4326":
                    from rasterio.warp import transform_bounds

                    # Transform bounds to WGS84 (lat/lon)
                    lon_min, lat_min, lon_max, lat_max = transform_bounds(
                        src.crs,
                        "EPSG:4326",
                        bounds.left,
                        bounds.bottom,
                        bounds.right,
                        bounds.top,
                    )
                else:
                    # Already in lat/lon
                    lon_min, lat_min, lon_max, lat_max = (
                        bounds.left,
                        bounds.bottom,
                        bounds.right,
                        bounds.top,
                    )

                # Update overall bounds
                coverage_info["bounds"]["min_lon"] = min(
                    coverage_info["bounds"]["min_lon"], lon_min
                )
                coverage_info["bounds"]["min_lat"] = min(
                    coverage_info["bounds"]["min_lat"], lat_min
                )
                coverage_info["bounds"]["max_lon"] = max(
                    coverage_info["bounds"]["max_lon"], lon_max
                )
                coverage_info["bounds"]["max_lat"] = max(
                    coverage_info["bounds"]["max_lat"], lat_max
                )

                # Track band counts
                band_count = src.count
                coverage_info["band_counts"][band_count] = (
                    coverage_info["band_counts"].get(band_count, 0) + 1
                )

                # Extract metadata
                tags = src.tags()
                if "TESSERA_YEAR" in tags:
                    coverage_info["years"].add(tags["TESSERA_YEAR"])

                coverage_info["crs"].add(str(src.crs))

                # Tile info (use lat/lon bounds)
                coverage_info["tiles"].append(
                    {
                        "path": path,
                        "bounds": [lon_min, lat_min, lon_max, lat_max],
                        "bands": band_count,
                        "year": tags.get("TESSERA_YEAR", "unknown"),
                        "tile_lat": tags.get("TESSERA_TILE_LAT", "unknown"),
                        "tile_lon": tags.get("TESSERA_TILE_LON", "unknown"),
                    }
                )

        except Exception as e:
            print(f"Warning: Failed to read {path}: {e}")
            continue

    # Convert sets to lists for JSON serialization
    coverage_info["years"] = sorted(list(coverage_info["years"]))
    coverage_info["crs"] = list(coverage_info["crs"])

    return coverage_info


def visualize_global_coverage(
    tessera_client,
    output_path: str = "tessera_coverage.png",
    year: Optional[int] = None,
    width_pixels: int = 2000,
    show_countries: bool = True,
    tile_color: str = "red",
    tile_alpha: float = 0.6,
    tile_size: float = 1.0,
    progress_callback: Optional[Callable] = None,
    multi_year_colors: bool = True,
    region_bbox: Optional[Tuple[float, float, float, float]] = None,
    region_file: Optional[str] = None,
) -> str:
    """Create a world map visualization showing Tessera embedding coverage.

    This is the recommended first step before downloading data - use it to check
    what data is available in your region of interest before proceeding with downloads.

    Generates a PNG map with available tiles overlaid to help users understand 
    data availability for their regions of interest. Can focus on a specific 
    region for detailed coverage analysis.

    Args:
        tessera_client: GeoTessera instance with loaded registries
        output_path: Output filename for the PNG map
        year: Specific year to show coverage for. If None, shows all years with multi-year coloring
        width_pixels: Width of output image in pixels (height calculated automatically)
        show_countries: Whether to show country boundaries
        tile_color: Color for tile rectangles (ignored when multi_year_colors=True)
        tile_alpha: Transparency of tile rectangles (0=transparent, 1=opaque)
        tile_size: Size multiplier for tile rectangles (1.0 = actual size)
        progress_callback: Optional callback function(current, total, status) for progress tracking
        multi_year_colors: When True and year=None, uses three colors: green (all years), 
                          blue (latest year only), orange (partial years)
        region_bbox: Optional bounding box (min_lon, min_lat, max_lon, max_lat) to focus on
        region_file: Optional path to region file (GeoJSON/Shapefile) for overlay

    Returns:
        Path to the created PNG file

    Typical workflow:
        >>> from geotessera import GeoTessera
        >>> gt = GeoTessera()
        >>> from geotessera.visualization import visualize_global_coverage
        >>> 
        >>> # STEP 1: Check coverage for your region
        >>> visualize_global_coverage(gt, "my_region_coverage.png", 
        ...                          region_file="my_study_area.geojson")
        >>> # STEP 2: Review the coverage map, then proceed to download data
        >>> 
        >>> # Other examples:
        >>> visualize_global_coverage(gt, "coverage_2024.png", year=2024)
        >>> visualize_global_coverage(gt, "coverage_all.png", width_pixels=3000)  # High-res global view
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.collections import PatchCollection
        import geodatasets
    except ImportError:
        raise ImportError(
            "Please install required packages: pip install matplotlib geodatasets"
        )

    # Import tile_to_bounds from registry module
    from .registry import tile_to_bounds

    # Load world countries from geodatasets only if needed
    world = None
    if show_countries:
        if not progress_callback:
            print("Loading world map data...")
        world = gpd.read_file(geodatasets.get_path("naturalearth.land"))
        
        # Clip world data to region if needed before plotting
        if region_bbox:
            from shapely.geometry import box
            min_lon, min_lat, max_lon, max_lat = region_bbox
            region_box = box(min_lon, min_lat, max_lon, max_lat)
            world = world.clip(region_box)

    # Ensure we have embeddings loaded
    tessera_client.registry.ensure_all_blocks_loaded(
        progress_callback=progress_callback
    )

    # Get available embeddings
    available_embeddings = tessera_client.registry.get_available_embeddings()
    
    # Get all available years for legend use
    all_years = set(y for y, _, _ in available_embeddings)
    latest_year = max(all_years) if all_years else None

    # Filter tiles by region if specified
    def is_tile_in_region(lon, lat, region_bbox):
        """Check if a tile intersects with the region bounding box."""
        if not region_bbox:
            return True
        min_lon, min_lat, max_lon, max_lat = region_bbox
        # Get tile bounds
        from .registry import tile_to_bounds
        west, south, east, north = tile_to_bounds(lon, lat)
        # Check for bounding box intersection
        return not (west > max_lon or east < min_lon or south > max_lat or north < min_lat)
    
    # Filter embeddings by year if specified
    if year is not None:
        tiles = [(lon, lat) for y, lon, lat in available_embeddings 
                if y == year and is_tile_in_region(lon, lat, region_bbox)]
        tile_colors = [tile_color] * len(tiles)  # Single color for specific year
        title = f"Tessera Embedding Coverage - Year {year}"
        if region_bbox:
            title += " (Region View)"
    else:
        # Multi-year analysis when no specific year requested
        if multi_year_colors:
            # Group tiles by location and analyze year coverage
            tiles_by_location = {}
            for y, lon, lat in available_embeddings:
                if is_tile_in_region(lon, lat, region_bbox):
                    if (lon, lat) not in tiles_by_location:
                        tiles_by_location[(lon, lat)] = set()
                    tiles_by_location[(lon, lat)].add(y)
            
            # Categorize tiles by year coverage
            tiles = []
            tile_colors = []
            
            for (lon, lat), years in tiles_by_location.items():
                tiles.append((lon, lat))
                
                if len(years) == len(all_years):
                    # All years present - green
                    tile_colors.append("darkgreen")
                elif latest_year in years and len(years) == 1:
                    # Only latest year - blue  
                    tile_colors.append("darkblue")
                else:
                    # Partial years coverage - orange
                    tile_colors.append("darkorange")
            
            title = "Tessera Embedding Coverage - Multi-Year Analysis"
            if region_bbox:
                title += " (Region View)"
        else:
            # Get unique tile locations across all years (original behavior)
            tile_set = set((lon, lat) for _, lon, lat in available_embeddings
                          if is_tile_in_region(lon, lat, region_bbox))
            tiles = list(tile_set)
            tile_colors = [tile_color] * len(tiles)
            title = "Tessera Embedding Coverage - All Available Years"
            if region_bbox:
                title += " (Region View)"

    if not progress_callback:
        print(f"Found {len(tiles)} tiles to visualize")

    # Calculate figure dimensions
    if progress_callback:
        progress_callback(0, 100, "Creating figure...")
    
    # Determine aspect ratio based on region or global view
    if region_bbox:
        min_lon, min_lat, max_lon, max_lat = region_bbox
        lon_range = max_lon - min_lon
        lat_range = max_lat - min_lat
        aspect_ratio = lat_range / lon_range if lon_range > 0 else 1.0
    else:
        # Global view: 180 degrees lat / 360 degrees lon = 0.5
        aspect_ratio = 0.5
    
    # Calculate dimensions in inches (matplotlib still needs this internally)
    # Use a fixed DPI of 100 for simplicity
    dpi = 100
    fig_width = width_pixels / dpi
    fig_height = fig_width * aspect_ratio
    
    fig, ax = plt.subplots(1, 1, figsize=(fig_width, fig_height), dpi=dpi)

    # Plot world map
    if show_countries and world is not None:
        if progress_callback:
            progress_callback(10, 100, "Plotting world map...")
        world.plot(ax=ax, color="lightgray", edgecolor="darkgray", linewidth=0.5)

    # Create rectangles for each tile (more accurate representation)
    if progress_callback:
        progress_callback(20, 100, f"Creating {len(tiles)} tile rectangles...")

    rectangles = []
    total_tiles = len(tiles)

    for i, (lon, lat) in enumerate(tiles):
        # Update progress every 100 tiles or at the end
        if progress_callback and (i % 100 == 0 or i == total_tiles - 1):
            progress = 20 + int((i / total_tiles) * 50)  # 20% to 70%
            progress_callback(
                progress, 100, f"Processing tile {i + 1}/{total_tiles}..."
            )

        # Get tile bounds using the helper function
        west, south, east, north = tile_to_bounds(lon, lat)

        # Apply size multiplier if needed
        if tile_size != 1.0:
            center_lon, center_lat = lon, lat
            half_width = (east - west) / 2 * tile_size
            half_height = (north - south) / 2 * tile_size
            west = center_lon - half_width
            east = center_lon + half_width
            south = center_lat - half_height
            north = center_lat + half_height

        # Create rectangle patch with individual color
        rect = mpatches.Rectangle(
            (west, south),
            east - west,
            north - south,
            linewidth=0,
            facecolor=tile_colors[i],
            alpha=tile_alpha,
        )
        rectangles.append(rect)

    # Add all rectangles as a collection for better performance
    if progress_callback:
        progress_callback(70, 100, "Adding tiles to map...")
    collection = PatchCollection(rectangles, match_original=True)
    ax.add_collection(collection)

    # Set axis properties - focus on region if specified
    if progress_callback:
        progress_callback(75, 100, "Setting up map properties...")
    
    if region_bbox:
        # Zoom to region bounds with small buffer for better visualization
        min_lon, min_lat, max_lon, max_lat = region_bbox
        # Add 5% buffer on each side
        lon_buffer = (max_lon - min_lon) * 0.05
        lat_buffer = (max_lat - min_lat) * 0.05
        ax.set_xlim(min_lon - lon_buffer, max_lon + lon_buffer)
        ax.set_ylim(min_lat - lat_buffer, max_lat + lat_buffer)
    else:
        # Global view
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
    
    ax.set_xlabel("Longitude", fontsize=12)
    ax.set_ylabel("Latitude", fontsize=12)
    ax.set_title(title, fontsize=14, fontweight="bold")

    # Add region file overlay if provided
    if region_file and progress_callback:
        progress_callback(77, 100, "Adding region overlay...")
    elif region_file:
        print("Adding region overlay...")
    
    if region_file:
        try:
            region_gdf = gpd.read_file(region_file)
            # Plot region boundary with distinctive styling
            region_gdf.plot(ax=ax, facecolor='none', edgecolor='red', 
                          linewidth=2, alpha=0.8, linestyle='--')
        except Exception as e:
            if progress_callback:
                progress_callback(77, 100, f"Warning: Could not load region file: {e}")
            else:
                print(f"Warning: Could not load region file: {e}")

    # Add grid
    ax.grid(True, alpha=0.3, linestyle="--")

    # Add statistics text with timestamp and manifest info
    if progress_callback:
        progress_callback(80, 100, "Adding statistics...")
    
    from datetime import datetime
    current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    stats_text = f"Total tiles: {len(tiles):,}"
    if year is None:
        years = sorted(set(y for y, _, _ in available_embeddings))
        if years:
            stats_text += f"\nYears: {min(years)}-{max(years)}"
    stats_text += f"\nGenerated: {current_timestamp}"
    
    git_hash, repo_url = tessera_client.registry.get_manifest_info()
    if "github.com" in repo_url:
        repo_name = repo_url.split("github.com/")[-1].replace(".git", "")
        stats_text += f"\nRepo: {repo_name}"
    if git_hash:
        stats_text += f"\nHash: {git_hash}"

    ax.text(
        0.02,
        0.5,
        stats_text,
        transform=ax.transAxes,
        fontsize=10,
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8),
    )

    # Add legend
    if progress_callback:
        progress_callback(85, 100, "Adding legend...")
    
    legend_elements = []
    if year is None and multi_year_colors:
        # Multi-year legend with three categories
        if all_years:  # Check if we have year data
            legend_elements.extend([
                mpatches.Patch(color="darkgreen", alpha=tile_alpha, label=f"All years ({len(all_years)} years)"),
                mpatches.Patch(color="darkblue", alpha=tile_alpha, label=f"Latest year only ({latest_year})"),
                mpatches.Patch(color="darkorange", alpha=tile_alpha, label="Partial years coverage"),
            ])
    else:
        # Single color legend (specific year or multi_year_colors=False)
        legend_elements.append(
            mpatches.Patch(color=tile_color, alpha=tile_alpha, label="Available tiles")
        )
    
    if show_countries and world is not None:
        legend_elements.append(mpatches.Patch(color="lightgray", label="Land masses"))
    
    if region_file:
        legend_elements.append(mpatches.Patch(facecolor="none", edgecolor="red", 
                                            label="Region boundary"))
    
    ax.legend(handles=legend_elements, loc="lower left", fontsize=10)

    # Save figure
    if progress_callback:
        progress_callback(90, 100, "Saving image to disk...")
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close()

    if progress_callback:
        progress_callback(100, 100, "Done!")
    else:
        print(f"Coverage map saved to: {output_path}")
    return output_path


def create_rgb_mosaic(
    geotiff_paths: List[str],
    output_path: str,
    bands: Tuple[int, int, int] = (0, 1, 2),
    target_crs: str = "EPSG:3857",
    progress_callback: Optional[Callable] = None,
) -> str:
    """Create an RGB visualization mosaic from multiple GeoTIFF files.
    
    This function merges tiles and then extracts RGB bands.
    
    Args:
        geotiff_paths: List of paths to GeoTIFF files
        output_path: Output path for RGB mosaic
        bands: Three band indices to map to RGB channels
        target_crs: Target CRS for the merged mosaic
        progress_callback: Optional callback function(current, total, status) for progress tracking
        
    Returns:
        Path to created RGB mosaic file
    """
    try:
        import rasterio
        from rasterio.enums import ColorInterp
        import tempfile
    except ImportError:
        raise ImportError("rasterio required: pip install rasterio")
    
    if not geotiff_paths:
        raise ValueError("No GeoTIFF files provided")
        
    if len(bands) != 3:
        raise ValueError(f"Must specify exactly 3 bands for RGB, got {len(bands)}")
    
    # First merge all tiles into a single mosaic using the core function
    if progress_callback:
        progress_callback(10, 100, f"Merging {len(geotiff_paths)} tiles...")
    
    with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
        temp_mosaic = tmp.name
    
    try:
        # Use GeoTessera to merge files
        from .core import GeoTessera
        gt = GeoTessera()
        gt.merge_geotiffs_to_mosaic(
            geotiff_paths=geotiff_paths,
            output_path=temp_mosaic,
            target_crs=target_crs,
        )
        
        if progress_callback:
            progress_callback(50, 100, f"Extracting RGB bands {bands}...")
        
        # Now extract RGB bands from the merged mosaic
        with rasterio.open(temp_mosaic) as src:
            # Check we have enough bands
            if src.count < max(bands) + 1:
                raise ValueError(
                    f"Not enough bands in mosaic. Requested bands {bands}, "
                    f"but only {src.count} available"
                )
            
            # Read the selected bands
            rgb_data = np.zeros((3, src.height, src.width), dtype=np.float32)
            for i, band_idx in enumerate(bands):
                rgb_data[i] = src.read(band_idx + 1)  # rasterio uses 1-based indexing
            
            # Always normalize to 0-1 for consistent visualization
            if progress_callback:
                progress_callback(70, 100, "Normalizing RGB bands...")
            
            for i in range(3):
                band = rgb_data[i]
                band_min, band_max = np.nanmin(band), np.nanmax(band)
                if band_max > band_min:
                    rgb_data[i] = (band - band_min) / (band_max - band_min)
                else:
                    rgb_data[i] = 0
            
            if progress_callback:
                progress_callback(80, 100, "Converting to RGB format...")
            
            # Convert to uint8
            rgb_uint8 = (np.clip(rgb_data, 0, 1) * 255).astype(np.uint8)
            
            if progress_callback:
                progress_callback(90, 100, f"Writing RGB mosaic to {Path(output_path).name}...")
            
            # Write RGB GeoTIFF
            profile = src.profile.copy()
            profile.update({
                'count': 3,
                'dtype': 'uint8',
                'compress': 'lzw',
                'photometric': 'RGB',
            })
            
            with rasterio.open(output_path, 'w', **profile) as dst:
                dst.write(rgb_uint8)
                dst.colorinterp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue]
                dst.update_tags(
                    TIFFTAG_ARTIST="GeoTessera",
                    TIFFTAG_IMAGEDESCRIPTION=f"RGB visualization using bands {bands}",
                )
    
    finally:
        # Clean up temp file
        import os
        if os.path.exists(temp_mosaic):
            os.unlink(temp_mosaic)
    
    if progress_callback:
        progress_callback(100, 100, f"Completed RGB mosaic: {Path(output_path).name}")
    
    return output_path


def calculate_bbox_from_file(
    filepath: Union[str, Path],
) -> Tuple[float, float, float, float]:
    """Calculate bounding box from a geometry file.

    Args:
        filepath: Path to GeoJSON, Shapefile, etc.

    Returns:
        Bounding box as (min_lon, min_lat, max_lon, max_lat)
    """
    gdf = gpd.read_file(filepath)
    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    return tuple(bounds)


def calculate_bbox_from_points(
    points: Union[List[Dict], pd.DataFrame], buffer_degrees: float = 0.1
) -> Tuple[float, float, float, float]:
    """Calculate bounding box from point data.

    Args:
        points: List of dicts with 'lon'/'lat' keys or DataFrame with lon/lat columns
        buffer_degrees: Buffer around points in degrees

    Returns:
        Bounding box as (min_lon, min_lat, max_lon, max_lat)
    """
    if isinstance(points, list):
        df = pd.DataFrame(points)
    else:
        df = points

    if "lon" not in df.columns or "lat" not in df.columns:
        raise ValueError("Points must have 'lon' and 'lat' columns")

    min_lon = df["lon"].min() - buffer_degrees
    max_lon = df["lon"].max() + buffer_degrees
    min_lat = df["lat"].min() - buffer_degrees
    max_lat = df["lat"].max() + buffer_degrees

    return (min_lon, min_lat, max_lon, max_lat)


def create_pca_mosaic(
    geotiff_paths: List[str],
    output_path: str,
    n_components: int = 3,
    target_crs: str = "EPSG:3857",
    progress_callback: Optional[Callable] = None,
    balance_method: str = "histogram",
    percentile_range: Tuple[float, float] = (2, 98),
) -> str:
    """Create PCA mosaic using combined-data approach.
    
    This function combines all embedding data across tiles, applies a single PCA
    transformation to the combined dataset, then creates a unified RGB mosaic.
    This ensures consistent principal components across the entire region,
    eliminating tiling artifacts.
    
    Args:
        geotiff_paths: List of paths to GeoTIFF files containing embeddings
        output_path: Output path for the PCA mosaic
        n_components: Number of PCA components to compute (only first 3 used for RGB)
        target_crs: Target CRS for the output mosaic
        progress_callback: Optional callback function(current, total, status) for progress tracking
        balance_method: Method for balancing RGB channels: "histogram" (default), "percentile", or "adaptive"
        percentile_range: Tuple of (lower, upper) percentiles for "percentile" method
        
    Returns:
        Path to created PCA mosaic file
        
    Raises:
        ImportError: If scikit-learn or rasterio are not available
        ValueError: If no GeoTIFF files are provided
    """
    try:
        import rasterio
        from rasterio.enums import ColorInterp
        import numpy as np
        import os
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        import tempfile
        import shutil
    except ImportError as e:
        raise ImportError(f"Required packages missing: {e}")
    
    if not geotiff_paths:
        raise ValueError("No GeoTIFF files provided")
    
    # Step 1: Read all embedding data from GeoTIFF files
    if progress_callback:
        progress_callback(1, 5, "Reading embedding data...")
    
    tiles_data = []
    all_pixels = []  # For combined PCA
    
    for i, geotiff_path in enumerate(geotiff_paths):
        with rasterio.open(geotiff_path) as src:
            # Read all bands: (bands, height, width) -> (height, width, bands)
            data = np.transpose(src.read(), (1, 2, 0))
            
            tiles_data.append({
                'path': geotiff_path,
                'data': data,
                'crs': src.crs,
                'transform': src.transform,
                'bounds': src.bounds,
                'height': src.height,
                'width': src.width
            })
            
            # Flatten spatial dimensions for PCA: (height*width, bands)
            pixels = data.reshape(-1, data.shape[2])
            all_pixels.append(pixels)
            
            # Progress update
            if progress_callback:
                read_progress = 1 + (i / len(geotiff_paths))
                progress_callback(read_progress, 5, f"Reading tile {i+1}/{len(geotiff_paths)}")
    
    # Step 2: Combine all pixel data and apply PCA
    if progress_callback:
        progress_callback(2, 5, "Applying PCA to combined data...")
    
    # Combine all pixels from all tiles
    combined_pixels = np.vstack(all_pixels)
    print(f"Combined data shape: {combined_pixels.shape}")
    
    # Standardize the combined data
    scaler = StandardScaler()
    combined_pixels_scaled = scaler.fit_transform(combined_pixels)
    
    # Apply PCA to the combined dataset
    pca = PCA(n_components=n_components)
    combined_pca = pca.fit_transform(combined_pixels_scaled)
    
    explained_variance = pca.explained_variance_ratio_
    total_variance = explained_variance.sum()
    print(f"PCA explained variance: {explained_variance[:3]} (total: {total_variance:.3f})")
    
    # Step 3: Split PCA results back into tiles and create temporary GeoTIFFs
    if progress_callback:
        progress_callback(3, 5, "Creating PCA tiles...")
    
    temp_dir = tempfile.mkdtemp(prefix="pca_tiles_")
    pca_geotiff_paths = []
    pixel_idx = 0
    
    # Apply selected balancing method for better color distribution
    component_scales = []
    
    if balance_method == "percentile":
        # Use percentile-based scaling for better color balance
        # Each component gets independently scaled to maximize its dynamic range
        for j in range(min(n_components, 3)):
            component_data = combined_pca[:, j]
            # Use specified percentiles to avoid outliers
            p_low = np.percentile(component_data, percentile_range[0])
            p_high = np.percentile(component_data, percentile_range[1])
            component_scales.append((p_low, p_high))
            print(f"PC{j+1} percentile scaling: [{p_low:.2f}, {p_high:.2f}]")
    
    elif balance_method == "histogram":
        # Apply histogram equalization to the combined PCA data first
        try:
            from skimage import exposure
        except ImportError:
            raise ImportError("scikit-image required for histogram balance: pip install scikit-image")
        
        # Apply histogram equalization globally to each component
        for j in range(min(n_components, 3)):
            component_data = combined_pca[:, j]
            # Normalize to 0-1 first
            p_low = np.percentile(component_data, 0.5)
            p_high = np.percentile(component_data, 99.5)
            if p_high > p_low:
                normalized = (component_data - p_low) / (p_high - p_low)
                normalized = np.clip(normalized, 0, 1)
                # Apply histogram equalization to the entire component
                equalized = exposure.equalize_hist(normalized)
                # Update the combined PCA data with equalized values
                combined_pca[:, j] = equalized
            
            # Store the new min/max after equalization
            new_min = combined_pca[:, j].min()
            new_max = combined_pca[:, j].max()
            component_scales.append((new_min, new_max))
            print(f"PC{j+1} histogram equalized: [{new_min:.2f}, {new_max:.2f}]")
    
    elif balance_method == "adaptive":
        # Adaptive scaling based on variance
        for j in range(min(n_components, 3)):
            component_data = combined_pca[:, j]
            mean = np.mean(component_data)
            std = np.std(component_data)
            # Scale to ±2.5 standard deviations
            p_low = mean - 2.5 * std
            p_high = mean + 2.5 * std
            component_scales.append((p_low, p_high))
            print(f"PC{j+1} adaptive scaling (μ±2.5σ): [{p_low:.2f}, {p_high:.2f}]")
    
    else:
        raise ValueError(f"Unknown balance_method: {balance_method}")
    
    for i, tile_info in enumerate(tiles_data):
        height, width = tile_info['height'], tile_info['width']
        n_pixels = height * width
        
        # Extract this tile's PCA results
        tile_pca_pixels = combined_pca[pixel_idx:pixel_idx + n_pixels]
        pixel_idx += n_pixels
        
        # Reshape back to image: (pixels, components) -> (height, width, components)
        tile_pca_image = tile_pca_pixels.reshape(height, width, n_components)
        
        # Normalize to 0-255 for visualization with per-component scaling
        pca_normalized = np.zeros((height, width, min(n_components, 3)), dtype=np.float32)
        
        for j in range(min(n_components, 3)):
            component = tile_pca_image[:, :, j]
            # Use per-component scaling for better balance
            p_low, p_high = component_scales[j]
            if p_high > p_low:
                normalized = (component - p_low) / (p_high - p_low)
                pca_normalized[:, :, j] = normalized
            else:
                pca_normalized[:, :, j] = 0.5
        
        # Convert to uint8
        output_data = (np.clip(pca_normalized, 0, 1) * 255).astype(np.uint8)
        
        # Write temporary PCA tile
        temp_path = os.path.join(temp_dir, f"pca_tile_{i}.tif")
        
        with rasterio.open(
            temp_path, 'w',
            driver='GTiff',
            height=height,
            width=width,
            count=min(n_components, 3),
            dtype='uint8',
            crs=tile_info['crs'],
            transform=tile_info['transform'],
            compress='lzw',
        ) as dst:
            for band_idx in range(min(n_components, 3)):
                dst.write(output_data[:, :, band_idx], band_idx + 1)
                variance_pct = explained_variance[band_idx] * 100
                dst.set_band_description(band_idx + 1, f"PC{band_idx + 1} ({variance_pct:.1f}%)")
        
        pca_geotiff_paths.append(temp_path)
    
    # Step 4: Merge PCA tiles into final mosaic
    if progress_callback:
        progress_callback(4, 5, "Merging PCA mosaic...")
    
    def merge_progress_callback(current: int, total: int, status: str = None):
        if progress_callback:
            step_progress = 4 + (current / max(total, 1)) * 0.9
            progress_callback(step_progress, 5, status or "Merging tiles...")
    
    # Import and use GeoTessera directly
    from .core import GeoTessera
    gt = GeoTessera()
    gt.merge_geotiffs_to_mosaic(
        geotiff_paths=pca_geotiff_paths,
        output_path=output_path,
        target_crs=target_crs,
        progress_callback=merge_progress_callback,
    )
    
    # Add PCA-specific metadata
    with rasterio.open(output_path, 'r+') as dst:
        dst.colorinterp = [ColorInterp.red, ColorInterp.green, ColorInterp.blue][:min(n_components, 3)]
        dst.update_tags(
            TIFFTAG_ARTIST="GeoTessera",
            TIFFTAG_IMAGEDESCRIPTION=f"Combined PCA visualization ({n_components} components, {balance_method} balanced)",
            PCA_COMPONENTS=str(n_components),
            PCA_STANDARDIZED="True",
            PCA_BALANCE_METHOD=balance_method,
            PCA_EXPLAINED_VARIANCE=str(explained_variance.tolist()),
            PCA_TOTAL_VARIANCE=f"{total_variance:.3f}",
            GEOTESSERA_TARGET_CRS=target_crs,
        )
    
    # Step 5: Clean up temporary files
    if progress_callback:
        progress_callback(5, 5, "Cleaning up...")
    
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    return output_path
