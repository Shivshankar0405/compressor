import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from compressor import compress_file

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024 # 50 MB max

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

STATS_FILE = 'stats.json'
INITIAL_STATS = {'views': 10, 'pdfs': 5, 'images': 3}

def get_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r') as f:
                data = json.load(f)
                for k, v in INITIAL_STATS.items():
                    if k not in data:
                        data[k] = v
                return data
        except:
            pass
    return INITIAL_STATS.copy()

def save_stats(stats):
    try:
        with open(STATS_FILE, 'w') as f:
            json.dump(stats, f)
    except:
        pass

def increment_stat(stat_name):
    stats = get_stats()
    stats[stat_name] = stats.get(stat_name, 0) + 1
    save_stats(stats)
    return stats

@app.route('/')
def index():
    return jsonify({"status": "API is running"}), 200

@app.route('/api/stats', methods=['GET', 'POST'])
def stats():
    if request.method == 'POST':
        s = increment_stat('views')
    else:
        s = get_stats()
    return jsonify(s)

@app.route('/api/compress', methods=['POST'])
def compress():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    target_size_kb = request.form.get('targetSizeKB', type=float)
    if not target_size_kb:
        return jsonify({'error': 'Target size not provided'}), 400
    
    target_size_bytes = int(target_size_kb * 1024)
    
    if file:
        filename = secure_filename(file.filename)
        input_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(input_path)
        
        try:
            output_path = compress_file(input_path, target_size_bytes)
            if output_path is None:
                return jsonify({'error': 'Failed to compress file to target size.'}), 500
            
            # Increment stats based on file type
            ext = os.path.splitext(filename)[1].lower()
            if ext == '.pdf':
                increment_stat('pdfs')
            elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
                increment_stat('images')
            
            return send_file(output_path, as_attachment=True)
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            # Clean up input file after processing
            if os.path.exists(input_path):
                try:
                    os.remove(input_path)
                except:
                    pass
            # Output file is removed automatically by OS or a cronjob ideally, but we could try to handle it.
            # Currently send_file locks it, so we can't remove it synchronously.

if __name__ == '__main__':
    app.run(debug=True, port=5000)
