import matplotlib.pyplot as plt
import sys, re
import base64
from io import BytesIO

mapq = sys.argv[1]
tool = sys.argv[2]
ref = sys.argv[3]
if ref == "hxb2.fasta":
    ref = "HXB2"
# Read the mapping file content for HTML display
with open("read_mapping_flagstat.txt", 'r') as f:
    mapping_content = f.read().replace('\n', '<br>')  # Replace newlines with HTML breaks

# Read the mean depth file content for HTML display
with open("read_mean_depth.txt", 'r') as f:
    mean_depth_content = f.read().replace('\n', '<br>')  # Replace newlines with HTML breaks

# Read the breadth coverage file content for HTML display
with open("read_breadth_coverage.txt", 'r') as f:
    breadth_coverage_content = f.read().replace('\n', '%<br>')  # Replace newlines with HTML breaks

# Read the breadth coverage file content for HTML display
with open("consensus.fasta", 'r') as f:
    consensus_content = f.read().replace('\n', '<br>')  # Replace newlines with HTML breaks

x, y, fy = [], [], []
with open("read_depth.txt", "r") as dfp:
    for line in dfp:
        line = line.strip()
        if line:
            x.append(int(line.split("\t")[1]))
            y.append(int(line.split("\t")[2]))                        

with open("base_frequency.txt", "r") as bfp:
    for line in bfp:
        line = line.strip()
        maxfreq = 0.0
        if line:
            depth = int(line.split("\t")[2])           
            if depth == 0:
                fy.append(1.0)
            else:
                freq_str = line.split("\t")[3]
                fields = freq_str.split(" ")
                for field in fields:
                    freq = float(field.split(":")[1])
                    if freq > maxfreq:
                        maxfreq = freq
                fy.append(maxfreq)

# Create the XY line plot
fig, ax1 = plt.subplots(figsize=(10, 6))
ax1.plot(x, y, 'b-', label='read depth', linewidth=0.5)
ax1.set_xlabel('Reference Position')
ax1.set_ylabel('Number of Reads', color='b')
ax1.tick_params(axis='y', labelcolor='b')
ax1.grid(True)

# Create secondary (right) y-axis
ax2 = ax1.twinx()
ax2.plot(x, fy, 'r-', linewidth=0.5, label='base frequency')
ax2.set_ylabel('Maximum Base Frequency', color='r')
ax2.tick_params(axis='y', labelcolor='r')
ax2.set_ylim(0, 1)

# Add title and legend
#fig.suptitle('Read depth & base frequency')
#fig.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=2)

# Save plot to BytesIO and encode to base64
buffer = BytesIO()
plt.savefig(buffer, format='png')
buffer.seek(0)
img_read_depth_base_freq_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
plt.close()
img_read_depth_base_freq_src = f"data:image/png;base64,{img_read_depth_base_freq_base64}"

qx, qy = [], []
with open("mapq_distribution.txt", "r") as qfp:
    for line in qfp:
        line = line.strip()
        if line:
            fields = re.split(r"\s+", line)
            qx.append(int(fields[1]))
            qy.append(int(fields[0]))                

# Create the XY line plot
plt.figure(figsize=(10, 6))
plt.plot(qx, qy, 'b-', label='MAPQ distribution', linewidth=1)
#plt.title('Read Depth Plot')
plt.xlabel('MAPQ')
plt.ylabel('Number of Reads')
plt.legend()
plt.grid(True)
# Save plot to BytesIO and encode to base64
buffer = BytesIO()
plt.savefig(buffer, format='png')
buffer.seek(0)
img_mapq_distribution_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
img_mapq_distribution_src = f"data:image/png;base64,{img_mapq_distribution_base64}"
plt.close()                     

# Generate HTML content
html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mapping Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 50%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        img {{ max-width: 100%; height: auto; margin: 10px 0; }}
        pre {{ background-color: #f8f8f8; padding: 10px; border: 1px solid #ddd; }}
    </style>
</head>
<body>
    <p>Map to {ref} using {tool} with MAPQ >= {mapq}</p>
    <h3>Summary</h3>
    <pre>{mapping_content}</pre>

    <h3>Mean Depth</h3>
    <pre>{mean_depth_content}</pre>

    <h3>Breadth Coverage</h3>
    <pre>{breadth_coverage_content}</pre>

    <h3>Read Depth & Base Frequency Chart</h3>
    <img src="{img_read_depth_base_freq_src}" alt="Read Depth & Base Frequency Chart">
    <!--<h3>Base Frequency Chart</h3>
    <img src="base_frequency.png" alt="base Frequency Chart">-->
    <h3>MAPQ Distribution Chart</h3>
    <img src="{img_mapq_distribution_src}" alt="MAPQ Distribution Chart">
    <!--<h3>Consensus Sequence</h3>-->
</body>
</html>
"""

# Write HTML to file
with open('mapping_report_mqc.html', 'w') as f:
    f.write(html_content)

print("HTML file 'mapping_report_mqc.html' has been created.")