# NGS-QC - Next Generation Sequencing Quality Control

[NGS-QC](https://ngsqc.fredhutch.org/) is a Bioinformatics tool to perform quality control analysis of next-generation sequencing (NGS) data, including quality assessment, read mapping, coverrage analysis, and detailed reporting.

## Overview

NGS-QC performs end-to-end quality control analysis of FASTQ files by:
- Quality assessment using FastQC
- Read mapping against reference sequences using BWA
- Coverage analysis and consensus sequence generation
- Comprehensive HTML reporting with MultiQC integration

## Features

- **Quality Control**: FastQC analysis of raw sequencing data
- **Read Mapping**: BWA-MEM alignment with configurable MAPQ filtering
- **Coverage Analysis**: Depth, breadth, and mapping statistics
- **Consensus Generation**: Reference-based consensus sequences
- **Base Frequency Analysis**: Position-specific nucleotide frequencies

## Citation

If you use NGSQC in your research, please cite the individual tools:
- FastQC: Andrews, S. (2010). FastQC: a quality control tool for high throughput sequence data
- BWA: Li H. and Durbin R. (2009) Fast and accurate short read alignment with Burrows-Wheeler Transform
- SAMtools: Li H., Handsaker B., et al. (2009) The Sequence Alignment/Map format and SAMtools
- MultiQC: Ewels P., et al. (2016) MultiQC: summarize analysis results for multiple tools and samples

## Contact

For any questions, bugs and suggestions, please send email to cohnlabsupport@fredhutch.org and include a few sentences describing, briefly, the nature of your questions and include contact information.
