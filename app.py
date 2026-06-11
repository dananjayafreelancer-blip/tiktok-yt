import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# ඩෙස්ක්ටොප් එකෙන් එන රික්වෙස්ට් බ්ලොක් නොවී වැඩ කරන්න CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

@app.route('/')
def home():
    return "Temporary Name Downloader API is Running Successfully! 🔥"

@app.route('/api/extract', methods=['POST'])
def extract_video():
    data = request.json
    if not data:
        return jsonify({'error': 'No data received!'}), 400
        
    url = data.get('url')
    if not url:
        return jsonify({'error': 'කරුණාකර URL එකක් ඇතුළත් කරන්න මචන්!'}), 400

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Social Media Video')
            thumbnail = info.get('thumbnail', 'https://placehold.co/600x338/png')
            extractor = info.get('extractor', '').lower()
            
            raw_formats = []
            formats = info.get('formats', [])
            
            for f in formats:
                # Video සහ Audio තියෙන ලින්ක්ස් විතරක් ගමු
                if f.get('url') and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                    height = f.get('height')
                    format_note = str(f.get('format_note', '')).lower()
                    
                    resolution = ""
                    
                    # FB, Insta, YT සඳහා HD/SD සහ p කොලිටි වෙන් කිරීම
                    if 'facebook' in extractor or 'instagram' in extractor or 'youtube' in extractor:
                        if height:
                            resolution = f"{height}p"  # උස තියෙනව නම් 1080p, 720p විදිහටම ගනියි (විශේෂයෙන් YT වලට)
                        elif 'hd' in format_note:
                            resolution = "HD Quality"
                        elif 'sd' in format_note:
                            resolution = "SD Quality"
                        else:
                            resolution = "Normal Quality"
                    else:
                        resolution = f"{height}p" if height else "Normal Quality"
                    
                    filesize = f.get('filesize') or f.get('filesize_approx')
                    size_str = f"{round(filesize / (1024 * 1024), 1)} MB" if filesize else "Best Size"
                    
                    raw_formats.append({
                        'resolution': resolution,
                        'size': size_str,
                        'url': f.get('url'),
                        'height': height or 0
                    })
            
            # එකම කොලිටි එක දෙපාරක් එන එක වළක්වන්න (Deduplication)
            unique_formats = {}
            for f in raw_formats:
                res = f['resolution']
                if res not in unique_formats:
                    unique_formats[res] = f
            
            final_formats = list(unique_formats.values())
            # ලොකු කොලිටි එකේ ඉඳන් පහළට Sort කරනවා
            final_formats.sort(key=lambda x: x['height'], reverse=True)
            
            # මොකුත්ම ෆෝමැට් සෙට් වුණේ නැත්නම් Fallback එක
            if not final_formats and info.get('url'):
                final_formats.append({
                    'resolution': 'Default Quality',
                    'size': 'Best Size',
                    'url': info.get('url')
                })

            return jsonify({
                'title': title,
                'thumbnail': thumbnail,
                'formats': final_formats[:3], # උපරිම හොඳම කොලිටි 3ක් යවමු
                'jpg_url': thumbnail
            })

    except Exception as e:
        return jsonify({'error': f'වීඩියෝ විස්තර ගන්න බැරි වුණා: {str(e)}'}), 500

@app.route('/api/download')
def download_file():
    file_url = request.args.get('url')
    filename = request.args.get('filename', 'download.mp4')
    
    if not file_url:
        return "URL එක අඩුයි මචන්", 400
        
    try:
        req = requests.get(file_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
        response = Response(req.iter_content(chunk_size=1024*1024), content_type=req.headers.get('Content-Type'))
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return f"Download Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
