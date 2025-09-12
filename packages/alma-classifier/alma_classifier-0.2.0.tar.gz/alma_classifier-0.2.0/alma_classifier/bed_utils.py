"""BED file processing utilities for ALMA classifier."""
import os
import gzip
from pathlib import Path
from typing import Union, Dict, List, Tuple

import numpy as np
import pandas as pd

def _get_data_dir() -> Path:
    """Resolve a readable data directory containing reference files.

    Priority:
    1) ALMA_DATA_DIR env var
    2) /app/data (Docker image)
    3) Package-adjacent ../data (site-packages sibling when installed from source)
    4) User data dir: $XDG_DATA_HOME or ~/.local/share/alma-classifier/data
    """
    # 1) Env override
    d = os.getenv("ALMA_DATA_DIR")
    if d:
        p = Path(d)
        if p.exists():
            return p
    # 2) Docker image location
    p = Path("/app/data")
    if p.exists():
        return p
    # 3) Package-adjacent data (do not create)
    p = Path(__file__).parent.parent / "data"
    if p.exists():
        return p
    # 4) User data dir
    xdg = os.getenv("XDG_DATA_HOME")
    if xdg:
        p = Path(xdg) / "alma-classifier" / "data"
    else:
        p = Path.home() / ".local" / "share" / "alma-classifier" / "data"
    return p

BED_COLUMNS = [
    "chrom", "start_position", "end_position", "modified_base_code", "score",
    "strand", "start_position2", "end_position2", "color", "Nvalid_cov",
    "fraction_modified", "Nmod", "Ncanonical", "Nother_mod", "Ndelete",
    "Nfail", "Ndiff", "Nnocall"
]

def read_cpg_coordinates_hg38(file_path: Union[str, Path]) -> Tuple[pd.DataFrame, Dict[str, List[str]]]:
    """Read CpG coordinates reference file and return CpG mapping."""
    ref_df = pd.read_csv(
        file_path, 
        sep='\t', 
        header=None,
        usecols=[0, 1, 3],
        names=['chrm', 'start', 'name'], 
        dtype={'chrm': str, 'start': int, 'name': str}
    )
    
    # Create coordinate column
    ref_df['coordinate'] = ref_df['chrm'] + ':' + ref_df['start'].astype(str)
    
    # Handle duplicate coordinates by creating a mapping dictionary
    coord_to_names = ref_df.groupby('coordinate')['name'].agg(list).to_dict()
    
    return ref_df[['name']].set_index('name'), coord_to_names

def read_bed_file(file_path: Union[str, Path]) -> pd.DataFrame:
    """Read a single BED file (compressed or uncompressed)."""
    file_path = Path(file_path)
    
    # Determine if file is compressed
    if file_path.suffix == '.gz':
        open_func = gzip.open
        encoding = 'utf-8'
    else:
        open_func = open
        encoding = None
    
    # Read the file
    with open_func(file_path, 'rt', encoding=encoding) as f:
        df = pd.read_csv(
            f,
            sep='\t', 
            header=None,
            usecols=[0, 1, 3, 10],  # chrom, start_position, modified_base_code, fraction_modified
            names=['chrom', 'start_position', 'modified_base_code', 'fraction_modified'],
            dtype={'chrom': str, 'start_position': int, 'modified_base_code': str, 'fraction_modified': float}
        )
    
    return df

def process_bed_to_methylation(
    bed_file: Union[str, Path],
    sample_name: str = None
) -> pd.DataFrame:
    """Convert a single BED file to methylation beta values format."""
    bed_file = Path(bed_file)
    
    if sample_name is None:
        # Remove .bed.gz or .bed extension to get sample name
        sample_name = bed_file.name.replace('.bed.gz', '').replace('.bed', '')
    
    print(f"Processing BED file: {bed_file.name}")
    
    # Get reference mapping
    data_dir = _get_data_dir()
    ref_path = data_dir / "cpg_coordinates_hg38.bed.gz"
    if not ref_path.exists():
        raise FileNotFoundError(
            "Reference file not found: {}. Set ALMA_DATA_DIR to the directory containing cpg_coordinates_hg38.bed.gz or mount it into /app/data.".format(ref_path)
        )
    
    ref_df, coord_to_names = read_cpg_coordinates_hg38(ref_path)
    
    # Read sample BED data
    sample_df = read_bed_file(bed_file)
    print(f"Read {len(sample_df):,} methylation sites from BED file")
    
    # Create coordinate column for sample
    sample_df['coordinate'] = sample_df['chrom'] + ':' + sample_df['start_position'].astype(str)
    
    # Create a dictionary to store beta values for all CpG names
    beta_values = {}
    sites_matched = 0
    
    # Process each coordinate in the sample
    for coord, frac_mod in zip(sample_df['coordinate'], sample_df['fraction_modified']):
        if coord in coord_to_names:
            # Get all CpG names for this coordinate
            cpg_names = coord_to_names[coord]
            beta = round(frac_mod / 100, 3)  # Convert percentage to fraction
            # Assign the same beta value to all CpGs at this coordinate
            for name in cpg_names:
                beta_values[name] = beta
            sites_matched += 1
    
    print(f"Matched {sites_matched:,} sites to reference CpGs")
    
    # Create a series with all reference CpGs
    result = pd.Series(beta_values, name=sample_name)
    result = result.reindex(ref_df.index)
    
    # Convert to DataFrame with sample as row
    result_df = pd.DataFrame([result], index=[sample_name])
    
    return result_df

def is_bed_file(file_path: Union[str, Path]) -> bool:
    """Check if a file is a BED file based on extension."""
    file_path = Path(file_path)
    return file_path.suffix.lower() in ['.bed'] or file_path.name.lower().endswith('.bed.gz')
