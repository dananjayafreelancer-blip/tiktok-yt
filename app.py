import os
import requests
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
from pytube import YouTube as PyTubeVideo  # Windows 7 යූටියුබ් ලෙඩේ සුව කරන්න

app = Flask(__name__)
# ඩෙස්ක්ටොප් එකෙන් එන රික්වෙස්ට් බ්ලොක් නොවී වැඩ කරන්න CORS
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Local Desktop එකේදී විතරක් වැඩ කරන්න V2Ray Proxy එක සෙට් කරනවා
V2RAY_PROXY = "http://127.0.0.1:10809"

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

    url_lower = url.lower()

    # =========================================================================
    # 1. TIKTOK සඳහා විශේෂිත ලොජික් එක (Video / Slideshow වෙන් කිරීම)
    # =========================================================================
    if 'tiktok.com' in url_lower:
        tk_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'nocheckcertificate': True,
            'proxy': V2RAY_PROXY  # Local Desktop එකේදී වැඩ කරන්න
        }
        try:
            with yt_dlp.YoutubeDL(tk_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if not info:
                    return jsonify({'error': 'TikTok දත්ත ලබාගන්න බැරි වුණා!'}), 400
                
                title = info.get('title', 'TikTok Content')
                thumbnail = info.get('thumbnail', 'https://placehold.co/600x338/png')
                
                # --- A. ටික්ටොක් එක SLIDESHOW (PHOTOS) එකක් නම් ---
                if "entries" in info or info.get('_type') == 'playlist' or info.get('extractor') == 'TikTokPhoto':
                    images = [entry.get('url') for entry in info.get('entries', []) if entry.get('url')]
                    return jsonify({
                        'title': title,
                        'thumbnail': thumbnail,
                        'formats': [],  # Slideshow හින්දා වීඩියෝ ෆෝමැට් නැත
                        'jpg_url': thumbnail,
                        'is_slideshow': True,
                        'images': images
                    })
                
                # --- B. ටික්ටොක් එක NORMAL VIDEO එකක් නම් (FB වගේම එක බටන් එකයි + MP3) ---
                tiktok_formats = []
                video_url = info.get('url')
                if not video_url:
                    for f in reversed(info.get('formats', [])):
                        if f.get('url') and f.get('vcodec') != 'none':
                            video_url = f.get('url')
                            break
                            
                if video_url:
                    tiktok_formats.append({
                        'resolution': 'Normal Quality',
                        'size': 'Best Size',
                        'url': video_url,
                        'height': 0
                    })
                
                # MP3 Audio එක වෙන් කරගැනීම
                audio_url = None
                for f in info.get('formats', []):
                    if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                        audio_url = f.get('url')
                        break
                if not audio_url and video_url:
                    audio_url = video_url
                    
                if audio_url:
                    tiktok_formats.append({
                        'resolution': 'MP3 Audio',
                        'size': 'Best Size',
                        'url': audio_url,
                        'height': -1
                    })
                    
                return jsonify({
                    'title': title,
                    'thumbnail': thumbnail,
                    'formats': tiktok_formats,
                    'jpg_url': thumbnail,
                    'is_slideshow': False
                })
        except Exception as tk_err:
            return jsonify({'error': f'TikTok Error: {str(tk_err)}'}), 400

    # =========================================================================
    # 2. YOUTUBE සඳහා විශේෂිත ලොජික් එක (Windows 7 බකල් නොගහන ස්ටේබල් ක්‍රමය)
    # =========================================================================
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        try:
            # Pytube එකෙන් Local Desktop එකේදී Proxy සහිතව ලස්සනට අදිනවා
            yt = PyTubeVideo(url, proxies={"http": V2RAY_PROXY, "https": V2RAY_PROXY})
            title = yt.title
            thumbnail = yt.thumbnail_url
            
            yt_formats = []
            streams = yt.streams.filter(progressive=True)
            for stream in streams:
                res = stream.resolution
                if res in ["720p", "480p", "360p"]:
                    yt_formats.append({
                        'resolution': res,
                        'size': 'Best Size',
                        'url': stream.url,
                        'height': int(res.replace('p', ''))
                    })
                    
            if not yt_formats:
                best_s = yt.streams.get_highest_resolution()
                if best_s:
                    res_val = best_s.resolution or '720p'
                    yt_formats.append({
                        'resolution': res_val,
                        'size': 'Best Size',
                        'url': best_s.url,
                        'height': int(res_val.replace('p', '')) if 'p' in res_val else 720
                    })
            
            # MP3 Audio එක එකතු කිරීම
            try:
                audio = yt.streams.filter(only_audio=True).first()
                if audio:
                    yt_formats.append({
                        'resolution': 'MP3 Audio',
                        'size': 'Best Size',
                        'url': audio.url,
                        'height': -1
                    })
            except:
                pass
                
            yt_formats.sort(key=lambda x: x['height'], reverse=True)
            return jsonify({
                'title': title,
                'thumbnail': thumbnail,
                'formats': yt_formats[:3],
                'jpg_url': thumbnail,
                'is_slideshow': False
            })
        except Exception as yt_err:
            return jsonify({'error': f'YouTube Error: {str(yt_err)}'}), 400

    # =========================================================================
    # 3. FB, INSTAGRAM සහ වෙනත් ඕනෑම එකක් (උඹේ පරණ ඔරිජිනල් කෝඩ් එක - වෙනස් කර නැත!)
    # =========================================================================
    else:
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
                    if f.get('url') and f.get('acodec') != 'none' and f.get('vcodec') != 'none':
                        height = f.get('height')
                        format_note = str(f.get('format_note', '')).lower()
                        
                        resolution = ""
                        if 'facebook' in extractor or 'instagram' in extractor or 'youtube' in extractor:
                            if height:
                                resolution = f"{height}p"
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
                
                unique_formats = {}
                for f in raw_formats:
                    res = f['resolution']
                    if res not in unique_formats:
                        unique_formats[res] = f
                
                final_formats = list(unique_formats.values())
                final_formats.sort(key=lambda x: x['height'], reverse=True)
                
                if not final_formats and info.get('url'):
                    final_formats.append({
                        'resolution': 'Default Quality',
                        'size': 'Best Size',
                        'url': info.get('url')
                    })

                return jsonify({
                    'title': title,
                    'thumbnail': thumbnail,
                    'formats': final_formats[:3],
                    'jpg_url': thumbnail,
                    'is_slideshow': False
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
