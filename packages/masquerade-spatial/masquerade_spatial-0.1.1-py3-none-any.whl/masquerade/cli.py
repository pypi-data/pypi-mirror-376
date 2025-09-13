#!/usr/bin/env python3
"""
Command Line Interface for Masquerade package.

This script provides a command-line interface for processing spatial imaging data
with the Masquerade package.
"""

import sys
import re
import argparse
import numpy as np
from pathlib import Path

from masquerade import Masquerade


def str_to_bool(value):
    """Convert string representation to boolean."""
    if isinstance(value, bool):
        return value
    if value.lower() in ('true', '1', 'yes', 'on'):
        return True
    elif value.lower() in ('false', '0', 'no', 'off'):
        return False
    else:
        raise ValueError(f"Cannot convert '{value}' to boolean")


def str_to_none_or_str(value):
    """Convert string 'None' to None, otherwise return the string."""
    return None if value == 'None' else value


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Process spatial imaging data with Masquerade",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        "image_source",
        help="Path to input TIFF image file"
    )
    parser.add_argument(
        "spatial_metadata", 
        help="Path to CSV file with spatial annotations"
    )
    parser.add_argument(
        "output_path",
        help="Path for output file"
    )
    
    # Optional arguments
    parser.add_argument(
        "--marker-metadata",
        default="None",
        help="Path to CSV file with relevant markers (or 'None')"
    )
    parser.add_argument(
        "--adjust-coords",
        type=str_to_bool,
        default=True,
        help="Whether to adjust coordinates to image bounds"
    )
    parser.add_argument(
        "--compress",
        type=str_to_bool,
        default=False,
        help="Whether to compress the output"
    )
    parser.add_argument(
        "--radius",
        type=int,
        default=10,
        help="Radius for circular masks"
    )
    parser.add_argument(
        "--filled",
        type=str_to_bool,
        default=True,
        help="Generate filled circles (True) or outlines (False)"
    )
    parser.add_argument(
        "--num-points",
        type=int,
        default=100,
        help="Number of points for circle outlines"
    )
    parser.add_argument(
        "--pre-filter-masks",
        type=str_to_bool,
        default=False,
        help="Whether to pre-filter masks during compression"
    )
    parser.add_argument(
        "--target-size",
        type=float,
        default=4.0,
        help="Target output size in GB"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    
    args = parser.parse_args()
    
    # Print configuration if verbose
    if args.verbose:
        print("Masquerade Configuration:")
        print(f"  Image source: {args.image_source}")
        print(f"  Spatial annotations: {args.spatial_metadata}")
        print(f"  Output path: {args.output_path}")
        print(f"  Marker metadata: {args.marker_metadata}")
        print(f"  Adjust coordinates: {args.adjust_coords}")
        print(f"  Compress: {args.compress}")
        print(f"  Radius: {args.radius}")
        print(f"  Fill circles: {args.filled}")
        print(f"  Number of points: {args.num_points}")
        print(f"  Pre-filter masks: {args.pre_filter_masks}")
        print(f"  Target size: {args.target_size} GB")
        print()
    
    # Validate input files
    if not Path(args.image_source).exists():
        print(f"Error: Image source file not found: {args.image_source}")
        sys.exit(1)
    
    if not Path(args.spatial_metadata).exists():
        print(f"Error: Spatial metadata file not found: {args.spatial_metadata}")
        sys.exit(1)
    
    if args.marker_metadata != "None" and not Path(args.marker_metadata).exists():
        print(f"Error: Marker metadata file not found: {args.marker_metadata}")
        sys.exit(1)
    
    try:
        # Initialize Masquerade
        masquerade = Masquerade()
        
        # Set parameters
        masquerade.image_source = args.image_source
        masquerade.spatial_anno = args.spatial_metadata
        masquerade.relevant_markers = str_to_none_or_str(args.marker_metadata)
        masquerade.adjust_coords = args.adjust_coords
        masquerade.compress = args.compress
        masquerade.radius = args.radius
        masquerade.filled = args.filled
        masquerade.num_points = args.num_points
        masquerade.filter_img = args.pre_filter_masks
        masquerade.target_size = args.target_size
        
        if args.verbose:
            print("Processing image...")
            print(f"Initial raw size: {masquerade.raw_size} GB")
        
        # Process the image
        image, set_subset_x, set_subset_y, spatial_metadata = masquerade.PreProcessImage()
        
        if args.verbose:
            print(f"Raw size after preprocessing: {masquerade.raw_size} GB")
            print(f"Compression factor: {masquerade.compression_factor}")
            print("Generating circle masks...")
        
        # Generate masks
        channels = masquerade.get_circle_masks(
            image=image,
            metadata=spatial_metadata,
            set_subset_x=set_subset_x,
            set_subset_y=set_subset_y
        )
        
        # Handle compression or continuous channels
        if args.compress:
            if args.verbose:
                print(f"Compressing masks to {masquerade.target_size} GB")
                print(f"Using compression factor: {masquerade.compression_factor}")
            
            channels, channel_names = masquerade.compress_marker_channels(
                channels, spatial_metadata=spatial_metadata
            )
            
            if args.verbose:
                print(f"Channel names: {channel_names}")
                for k in channels.keys():
                    print(f"  {k}: {channels[k].shape}")
            
            # Modify output path with compression factor
            out_path_parts = re.split('[.]', args.output_path)
            output_path = f"{out_path_parts[0]}_{np.round(masquerade.compression_factor, 3)}_.{out_path_parts[1]}"
        else:
            channels, channel_names = masquerade.get_continuous_channels(
                channels, 
                set_subset_x=set_subset_x, 
                set_subset_y=set_subset_y
            )
            output_path = args.output_path
        
        if args.verbose:
            print(f"Writing output to: {output_path}")
        
        # Write output
        masquerade.write_ome_bigTiff(
            channels=channels,
            out=output_path,
            channels_to_keep=list(channels.keys())
        )
        
        if args.verbose:
            print("Processing completed successfully!")
        
    except Exception as e:
        print(f"Error during processing: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def legacy_main():
    """
    Legacy CLI function that mimics the original sys.argv parsing.
    
    This maintains compatibility with existing scripts that call the tool
    with positional arguments in the original order.
    """
    if len(sys.argv) != 12:
        print("Legacy usage: masquerade-legacy <image> <metadata> <output> <marker_metadata> "
              "<adjust_coords> <compress> <radius> <filled> <num_points> <prefilter> <target_size>")
        sys.exit(1)
    
    # Parse arguments in original order
    image_source = sys.argv[1]
    metadata = sys.argv[2]
    out_path = sys.argv[3]
    marker_metadata = sys.argv[4]
    adjust_coords = sys.argv[5]
    compress = sys.argv[6]
    radius = sys.argv[7]
    filled = sys.argv[8]
    num_points = sys.argv[9]
    preFilter_masks = sys.argv[10]
    target_size = sys.argv[11]
    
    # Convert string parameters to appropriate types
    masquerade = Masquerade()
    masquerade.adjust_coords = True if adjust_coords == 'True' else False
    masquerade.relevant_markers = None if marker_metadata == 'None' else marker_metadata
    masquerade.compress = True if compress == 'True' else False
    masquerade.filter_img = True if preFilter_masks == 'True' else False
    masquerade.filled = True if filled == 'True' else False
    
    masquerade.spatial_anno = metadata
    masquerade.image_source = image_source
    masquerade.target_size = float(target_size)
    masquerade.radius = int(radius)
    masquerade.num_points = int(num_points)
    
    print('image source --> ' + image_source)
    print('spatial annos --> ' + metadata)
    print('out path --> ' + out_path)
    print('marker metadata --> ' + str(marker_metadata))
    print('adjust coords: ' + str(masquerade.adjust_coords))
    print('compress: ' + str(masquerade.compress))
    print('radius: ' + str(masquerade.radius))
    print('fill circle: ' + str(masquerade.filled))
    print('num points: ' + str(masquerade.num_points))
    print('pre-filter masks: ' + str(masquerade.filter_img))
    print('target size --> ' + str(masquerade.target_size))
    
    print('raw size: ' + str(masquerade.raw_size))
    
    image, set_subset_x, set_subset_y, spatial_metadata = masquerade.PreProcessImage()
    
    print('raw size: ' + str(masquerade.raw_size))
    print('compression factor: ' + str(masquerade.compression_factor))
    
    channels = masquerade.get_circle_masks(
        image=image,
        metadata=spatial_metadata,
        set_subset_x=set_subset_x,
        set_subset_y=set_subset_y
    )
    
    if masquerade.compress:
        print('compressing masks to ' + str(masquerade.target_size) + 'GB')
        print('compression factor: ' + str(masquerade.compression_factor))
        
        channels, channel_names = masquerade.compress_marker_channels(
            channels, spatial_metadata=spatial_metadata
        )
        print(channel_names)
        for k in channels.keys():
            print(channels[k].shape)
        
        out_path_p = re.split('[.]', out_path)
        out_path = f"{out_path_p[0]}_{np.round(masquerade.compression_factor, 3)}_.{out_path_p[1]}"
    else:
        channels, channel_names = masquerade.get_continuous_channels(
            channels, set_subset_x=set_subset_x, set_subset_y=set_subset_y
        )
    
    masquerade.write_ome_bigTiff(
        channels=channels,
        out=out_path,
        channels_to_keep=list(channels.keys())
    )


if __name__ == "__main__":
    main()
