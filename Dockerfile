# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    unzip \
    zlib1g-dev \
    libbz2-dev \
    liblzma-dev \
    libncurses5-dev \
    libncursesw5-dev \
    tar \
    && rm -rf /var/lib/apt/lists/*

# Install FastQC
RUN wget https://www.bioinformatics.babraham.ac.uk/projects/fastqc/fastqc_v0.12.1.zip \
    && unzip fastqc_v0.12.1.zip \
    && chmod +x FastQC/fastqc \
    && mv FastQC /usr/local/bin/ \
    && ln -s /usr/local/bin/FastQC/fastqc /usr/local/bin/fastqc \
    && rm fastqc_v0.12.1.zip

# Install BWA
RUN wget https://github.com/lh3/bwa/archive/refs/tags/v0.7.19.zip \
    && unzip v0.7.19.zip \
    && cd bwa-0.7.19 \
    && make \
    && mv bwa /usr/local/bin/ \
    && cd .. \
    && rm -rf bwa-0.7.19 v0.7.19.zip

# Install SAMtools
RUN wget https://github.com/samtools/samtools/releases/download/1.21/samtools-1.21.tar.bz2 \
    && tar -xjf samtools-1.21.tar.bz2 \
    && cd samtools-1.21 \
    && ./configure \
    && make \
    && make install \
    && cd .. \
    && rm -rf samtools-1.21 samtools-1.21.tar.bz2

# Install Minimap2
RUN wget https://github.com/lh3/minimap2/releases/download/v2.29/minimap2-2.29.tar.bz2 \
    && tar -xjf minimap2-2.29.tar.bz2 \
    && cd minimap2-2.29 \
    && make \
    && mv minimap2 /usr/local/bin/ \
    && cd .. \
    && rm -rf minimap2-2.29 minimap2-2.29.tar.bz2

# Install OpenJDK 17 (Java)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Verify installations
RUN perl -v && java -version

# Copy and index reference genome
COPY reference/hxb2.fasta /app/reference/hxb2.fasta
RUN bwa index /app/reference/hxb2.fasta

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
RUN chmod +x /app/bin/*
RUN chmod -R 755 /app/outputs

# Expose port for web app
EXPOSE 8000

# Run the application with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]