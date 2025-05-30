#!/usr/bin/python3

import logging
import os
import subprocess
import uuid
from flask import Flask, render_template, request, jsonify, render_template_string, redirect, url_for
from werkzeug.utils import secure_filename


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Initialize Flask application
app = Flask(__name__)
# Set the size limits for file uploads
FILE_LIMITS = {'file1': 100 * 1024 * 1024, 'file2': 100 * 1024 * 1024, 'reffile': 1 * 1024 * 1024}

# Serve the upload HTML page
@app.route("/", methods=["GET"])
def get_upload_page():
    logger.info("Serving index.html via render_template")
    try:
        return render_template("index.html")
    except Exception as e:
        logger.error(f"Error rendering index.html: {str(e)}")
        return jsonify({"error": "Internal server error: Failed to load index.html"}), 500

# Handle single or paired-end file upload, tool selection, and MAPQ
@app.route("/ngsqc", methods=["POST"])
def upload_files():
    logger.info("Received upload request")
    
    # Validate form data
    if "tool" not in request.form:
        logger.error("Missing tool selection")
        return jsonify({"error": "Tool selection is required"}), 400
    tool = request.form["tool"]
    if tool not in ["BWA", "Minimap2-sr", "Minimap2-lr:hq"]:
        logger.error(f"Invalid tool: {tool}")
        return jsonify({"error": "Invalid tool selected"}), 400
    
    if "mapq" not in request.form:
        logger.error("Missing MAPQ value")
        return jsonify({"error": "MAPQ value is required"}), 400
    try:
        mapq = int(request.form["mapq"])
        if not (0 <= mapq <= 60):
            logger.error(f"Invalid MAPQ: {mapq}")
            return jsonify({"error": "MAPQ must be between 0 and 60"}), 400
    except ValueError:
        logger.error(f"Invalid MAPQ format: {request.form['mapq']}")
        return jsonify({"error": "MAPQ must be an integer"}), 400
    
    if "file1" not in request.files:
        logger.error("Missing file1")
        return jsonify({"error": "Read 1 file is required"}), 400
    file1 = request.files["file1"]
    if not file1.filename:
        logger.error("No file1 selected")
        return jsonify({"error": "No file selected for Read 1"}), 400
    if not file1.filename.endswith((".fastq", ".fq", ".gz", ".fasta", ".fa", ".fas", ".fna")):
        logger.error(f"Invalid file1 format: {file1.filename}")
        return jsonify({"error": f"Invalid file format for {file1.filename}. Only .fastq, .fq, or .gz allowed"}), 400
    
    file2 = request.files.get("file2")
    if file2 and file2.filename and not file2.filename.endswith((".fastq", ".fq", ".gz", ".fasta", ".fa", ".fas", ".fna")):
        logger.error(f"Invalid file2 format: {file2.filename}")
        return jsonify({"error": f"Invalid file format for {file2.filename}. Only .fastq, .fq, or .gz allowed"}), 400
    
    reffile = request.files.get("reffile")
    if reffile and reffile.filename and not reffile.filename.endswith((".fasta", ".fa", ".fas", ".fna")):
        logger.error(f"Invalid reffile format: {reffile.filename}")
        return jsonify({"error": f"Invalid file format for {reffile.filename}. Only .fasta, .fa, or .fas allowed"}), 400

    # Check reference genome
    reference_path = "/app/reference/hxb2.fasta"
    if not os.path.exists(reference_path):
        logger.error(f"Reference genome not found at {reference_path}")
        return jsonify({"error": "Reference genome missing"}), 500
    
    # Generate job ID
    job_id = str(uuid.uuid4())

    # Save the uploaded files
    output_dir = f"/app/outputs/{job_id}"
    os.makedirs(output_dir, exist_ok=True)
    file1_filename = secure_filename(file1.filename)
    file1_path = os.path.join(output_dir, file1_filename)
    
    try:
        # Check file sizes and save files
        file1.seek(0, os.SEEK_END)  
        if file1.tell() > FILE_LIMITS['file1']:
            logger.error(f"File1 exceeds size limit: {file1.filename}")
            return render_template("index.html", message=f"File {file1.filename} exceeds size limit of 100MB")
        file1.seek(0)  # Reset file pointer after reading
        file1.save(file1_path)
        logger.info(f"Saved file1: {file1_path}")
        
        file2_path = None
        if file2 and file2.filename:
            # Check file sizes and save files
            file2.seek(0, os.SEEK_END)  
            if file2.tell() > FILE_LIMITS['file2']:
                logger.error(f"File2 exceeds size limit: {file2.filename}")
                return render_template("index.html", message=f"File {file2.filename} exceeds size limit of 100MB")
            file2.seek(0)  # Reset file pointer after reading
            file2_filename = secure_filename(file2.filename)
            file2_path = os.path.join(output_dir, file2_filename)
            file2.save(file2_path)
            logger.info(f"Saved file2: {file2_path}")

        #reffile_path = None
        if reffile and reffile.filename:
            # Check file sizes and save files
            reffile.seek(0, os.SEEK_END)  
            if reffile.tell() > FILE_LIMITS['reffile']:
                logger.error(f"Reffile exceeds size limit: {reffile.filename}")
                return render_template("index.html", message=f"File {reffile.filename} exceeds size limit of 1MB")
            reffile.seek(0)
            reffile_filename = secure_filename(reffile.filename)
            reference_path = os.path.join(output_dir, reffile_filename)
            reffile.save(reference_path)
            logger.info(f"Saved reffile: {reference_path}")

        if file2_path:
            logger.info(f"Processing paired-end files: {file1_path}, {file2_path}")
            process = subprocess.Popen(["/app/bin/ngsqc.sh", file1_path, reference_path, output_dir, str(mapq), tool, file2_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Spawned child process for job {job_id}, PID: {process.pid}")
        else:
            logger.info(f"Processing single-end file: {file1_path}")
            process = subprocess.Popen(["/app/bin/ngsqc.sh", file1_path, reference_path, output_dir, str(mapq), tool], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Spawned child process for job {job_id}, PID: {process.pid}")
        
        # Redirect to transition page
        return redirect(url_for("transition", job_id=job_id))

    except Exception as e:
        logger.error(f"Error spawning child process: {str(e)}")
        return jsonify({"error": f"Failed to start processing: {str(e)}"}), 500

# Transition page
@app.route("/transition/<job_id>")
def transition(job_id):
    logger.info(f"Serving transition page for job {job_id}")
    return render_template("transition.html", job_id=job_id)

# Check job status
@app.route("/status/<job_id>")
def check_status(job_id):
    done_path = os.path.join("outputs", job_id, "done")
    if os.path.exists(done_path):
        return jsonify({"status": "completed", "results_url": url_for("results", job_id=job_id)})
    return jsonify({"status": "running"})

# Render results
@app.route("/results/<job_id>")
def results(job_id):
    results_path = os.path.join("outputs", job_id, "multiqc_report.html")
    
    try:
        with open(results_path, "r") as f:
            template_content = f.read()
        return render_template_string(template_content)
    except Exception as e:
        logger.error(f"Error rendering results.html for job {job_id}: {str(e)}")
        return jsonify({"error": f"Failed to render results: {str(e)}"}), 500
