import yt_dlp
import os

def fetch_metadata(url):
    ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {'youtube': ['player_client=android']}
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'Unknown Title'),
                'uploader': info.get('uploader', 'Unknown Uploader'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', None),
                'formats': info.get('formats', []),
                'original_url': url
            }
        except Exception as e:
            raise Exception(f"Failed to fetch metadata: {str(e)}")

def download_media(url, format_choice, output_dir, is_audio=False):
    if is_audio:
        quality = format_choice.replace('kbps', '')
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'quiet': True,
            'restrictfilenames': True,
            'no_warnings': True,
            'extractor_args': {'youtube': ['player_client=android']}
        }
    else:
        if format_choice == "Best Available":
            format_str = 'bestvideo+bestaudio/best'
        else:
            res = format_choice.replace('p', '')
            format_str = f'bestvideo[height<={res}]+bestaudio/best[height<={res}]'
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
            'merge_output_format': 'mp4',
            'quiet': True,
            'restrictfilenames': True,
            'no_warnings': True,
            'extractor_args': {'youtube': ['player_client=android']}
        }
        
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(url, download=True)
            expected_filename = ydl.prepare_filename(info)
            base, _ = os.path.splitext(expected_filename)
            if is_audio:
                final_file = base + '.mp3'
            else:
                final_file = base + '.mp4'
            
            if os.path.exists(final_file):
                return final_file
            else:
                raise Exception("Downloaded file not found at expected path.")
        except Exception as e:
            raise Exception(f"Failed to download media: {str(e)}")
