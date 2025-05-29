#!/bin/bash

# Check if enough arguments
if [ $# -lt 5 ]; then
	echo "At least 5 arguments needed: $0 <fq1> <ref> <outdir> <MAPQ> <tool> [fq2]"
	exit 1
fi

# Set default MAPQ value
DEFAULT_FQ2=''

fq1="$1"  # R1 fastq(.gz) file
ref="$2"  # reference fasta file to map to
outdir="$3"  # output directory to hold all output files
MAPQ="$4"  # MAPQ cutoff value
tool="$5"  # tool to use for mapping (default: bwa)
fq2=${6:-$DEFAULT_FQ2}  # fq2

# Validate MAPQ (ensure it's a non-negative integer)
if ! [[ "$MAPQ" =~ ^[0-9]+$ ]]; then
    echo "Error: MAPQ must be a non-negative integer (got '$MAPQ')"
    exit 1
fi

SCRIPT_PATH="$(readlink -f "$0")"
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

# Check if directory exists
if [ -d "$outdir" ]; then
	echo "Directory '$outdir' already exists"
else
	# Create directory
	mkdir -p "$outdir"
	echo "Directory '$outdir' created"
fi

refname=$(basename "$ref")

# run FastQC on fq1 and fq2
if [ -z "$fq2" ]; then
	echo "Running FastQC with single-end reads"
	fastqc "$fq1"
else
	echo "Running FastQC with paired-end reads"
	fastqc "$fq1" "$fq2"
fi	

if [ "$ref" != "/app/reference/hxb2.fasta" ]; then
	if [ "$tool" == "BWA" ]; then
		echo "Indexing reference genome"
		bwa index "$ref"	
	fi
fi

# run bwa mem or minimap2 to map fq1 and fq2 to ref
if [ -z "$fq2" ]; then
	if [ "$tool" == "BWA" ]; then
		echo "Running bwa mem with single-end reads"
		bwa mem -t 8 "$ref" "$fq1" > "$outdir/map.sam"
	elif [ "$tool" == "Minimap2-sr" ]; then
		echo "Running minimap2 with single-end short reads"
		minimap2 -ax sr -t 8 "$ref" "$fq1" > "$outdir/map.sam"
	elif [ "$tool" == "Minimap2-lr:hq" ]; then
		echo "Running minimap2 with single-end long reads"
		minimap2 -ax lr:hq -t 8 "$ref" "$fq1" > "$outdir/map.sam"
	else
		echo "Unknown tool: $tool. Please use bwa, minimap2-sr or minimap2-lr:hq."
		exit 1
	fi
else
	if [ "$tool" == "BWA" ]; then
		echo "Running bwa mem with pair-end reads"
		bwa mem -t 8 "$ref" "$fq1" "$fq2" > "$outdir/map.sam"
	elif [ "$tool" == "Minimap2-sr" ]; then
		echo "Running minimap2 with pair-end short reads"
		minimap2 -ax sr -t 8 "$ref" "$fq1" "$fq2" > "$outdir/map.sam"
	elif [ "$tool" == "Minimap2-lr:hq" ]; then
		echo "Running minimap2 with pair-end long reads"
		minimap2 -ax lr:hq -t 8 "$ref" "$fq1" "$fq2" > "$outdir/map.sam"
	else
		echo "Unknown tool: $tool. Please use BWA, Minimap2-sr or Minimap2-lr:hq."
		exit 1
	fi
fi	

# change working directory to output
cd $outdir

# convert sam to bam
samtools view -bS map.sam > map.bam

# sort and index bam file
samtools sort map.bam -o map_sorted.bam
samtools index map_sorted.bam

# Check MAPQ distribution
#echo "MAPQ distribution in BAM:"
samtools view map_sorted.bam | cut -f 5 | sort -n | uniq -c > mapq_distribution.txt

# Filter BAM by MAPQ
if [ "$MAPQ" -eq 0 ]; then
    cp map_sorted.bam map_sorted_filtered.bam
else
    samtools view -b -q "$MAPQ" map_sorted.bam > map_sorted_filtered.bam
fi

# generate consensus
samtools consensus -f fasta -o consensus.fasta map_sorted_filtered.bam

# calculate read depth
samtools depth -a map_sorted_filtered.bam > read_depth.txt

# calculate read mean depth
samtools depth -a map_sorted_filtered.bam | awk '{c++;s+=$3}END{print s/c}' > read_mean_depth.txt

# calculate breadth of coverage
samtools depth -a map_sorted_filtered.bam | awk '{c++;if($3>0) total+=1}END{print(total/c)*100}' > read_breadth_coverage.txt

# get mapping rate
samtools flagstat map_sorted_filtered.bam > read_mapping_flagstat.txt

# create pileup via samtools
#samtools mpileup -aa -f $ref -q $MAPQ map_sorted.bam > pileup_all.txt
samtools mpileup -aa -f "$ref" map_sorted_filtered.bam > pileup_all_filtered.txt

# count base frequency at each positon
python $SCRIPT_DIR/count_base_frequency.py

# create a html summary report
python $SCRIPT_DIR/create_html_report.py "$MAPQ" "$tool" "$refname"

cat <<EOF > multiqc_config.yaml
read_count_multiplier: 1
read_count_prefix: ''
read_count_desc: 'reads'
EOF

# create MultiQC report
multiqc . -c multiqc_config.yaml

#cp multiqc_report.html report.html

touch done