"""
Simple Cloud Backup - Upload CSV to multiple free services
"""

import os
import shutil
from datetime import datetime

def backup_to_dropbox_folder():
    """Copy CSV to Dropbox folder if it exists"""
    csv_file = "backend/aviator_rounds_history.csv"
    if not os.path.exists(csv_file):
        return False
    
    # Common Dropbox paths
    dropbox_paths = [
        os.path.expanduser("~/Dropbox"),
        os.path.expanduser("~/OneDrive"), 
        "C:/Users/%s/Dropbox" % os.getenv('USERNAME'),
        "C:/Users/%s/OneDrive" % os.getenv('USERNAME')
    ]
    
    for path in dropbox_paths:
        if os.path.exists(path):
            backup_name = f"aviator_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            backup_path = os.path.join(path, backup_name)
            shutil.copy2(csv_file, backup_path)
            print(f"✅ Backed up to: {backup_path}")
            return True
    
    return False

def create_web_viewer():
    """Create HTML file to view CSV data"""
    csv_file = "backend/aviator_rounds_history.csv"
    if not os.path.exists(csv_file):
        return
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>Aviator Bot Data</title>
    <style>
        body { font-family: Arial; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .profit { color: green; }
        .loss { color: red; }
    </style>
</head>
<body>
    <h1>Aviator Bot Data</h1>
    <p>Last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    <div id="data"></div>
    
    <script>
        // Read CSV and display as table
        fetch('aviator_rounds_history.csv')
            .then(response => response.text())
            .then(data => {
                const lines = data.split('\\n');
                let html = '<table><tr>';
                
                // Header
                const headers = lines[0].split(',');
                headers.forEach(header => {
                    html += '<th>' + header + '</th>';
                });
                html += '</tr>';
                
                // Data rows (last 50)
                const dataLines = lines.slice(1).slice(-50);
                dataLines.forEach(line => {
                    if (line.trim()) {
                        const cells = line.split(',');
                        html += '<tr>';
                        cells.forEach((cell, index) => {
                            let className = '';
                            if (headers[index] === 'profit_loss' && parseFloat(cell) > 0) className = 'profit';
                            if (headers[index] === 'profit_loss' && parseFloat(cell) < 0) className = 'loss';
                            html += '<td class="' + className + '">' + cell + '</td>';
                        });
                        html += '</tr>';
                    }
                });
                
                html += '</table>';
                document.getElementById('data').innerHTML = html;
            });
    </script>
</body>
</html>"""
    
    with open("aviator_data_viewer.html", "w") as f:
        f.write(html_content)
    
    # Copy CSV to same folder
    shutil.copy2(csv_file, "aviator_rounds_history.csv")
    
    print("✅ Created web viewer: aviator_data_viewer.html")
    print("📊 Open in browser to view your data")

def main():
    print("☁️ Simple Cloud Backup Options")
    print("1. Copy to Dropbox/OneDrive folder")
    print("2. Create web viewer (HTML file)")
    print("3. Both")
    
    choice = input("Choice (1/2/3): ").strip()
    
    if choice in ["1", "3"]:
        if backup_to_dropbox_folder():
            print("✅ Backup successful!")
        else:
            print("❌ No cloud folder found")
    
    if choice in ["2", "3"]:
        create_web_viewer()
    
    print("\n🎯 Easy alternatives:")
    print("• Email CSV file to yourself")
    print("• Upload to Google Drive manually")
    print("• Copy to USB drive")

if __name__ == "__main__":
    main()