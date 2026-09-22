import streamlit as st
import os
import tempfile
import shutil
import re
from utils.downloader import fetch_metadata, download_media
from utils.editor import process_media

# Page config
st.set_page_config(layout="wide", page_title="Universal Media Studio")

# State initialization
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if 'media_info' not in st.session_state:
    st.session_state.media_info = None
if 'downloaded_file' not in st.session_state:
    st.session_state.downloaded_file = None
if 'processed_file' not in st.session_state:
    st.session_state.processed_file = None
if 'is_audio' not in st.session_state:
    st.session_state.is_audio = False

def reset_download_state():
    st.session_state.downloaded_file = None
    st.session_state.processed_file = None

def sanitize_filename(name):
    """Sanitizes filename for cross-platform downloads."""
    clean = re.sub(r'[\\/*?:"<>|]', "", name)
    return clean.strip() or "media_file"

st.title("Universal Media Studio")
st.markdown("Download, edit, and export online media easily.")

st.divider()

# Stage 1: URL Ingestion
st.header("1. Fetch Media")
url = st.text_input("Enter media URL (YouTube, Vimeo, etc.)")
if st.button("Fetch Metadata"):
    if url.strip():
        with st.spinner("Fetching metadata..."):
            try:
                reset_download_state()
                info = fetch_metadata(url.strip())
                st.session_state.media_info = info
                st.success("Metadata fetched successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
    else:
        st.warning("Please enter a valid URL.")

if st.session_state.media_info:
    st.divider()
    
    # Stage 2: Preview & Format Configuration
    st.header("2. Preview & Configuration")
    
    info = st.session_state.media_info
    
    col1, col2 = st.columns([1, 2])
    with col1:
        if info.get('thumbnail'):
            # Fixed deprecated use_column_width argument
            st.image(info['thumbnail'], use_container_width=True)
            
        dur = info.get('duration', 0)
        dur_str = f"{int(dur // 60)}m {int(dur % 60)}s" if dur else "Live/Unknown"
        st.write(f"**Duration:** {dur_str}")
        
    with col2:
        st.subheader(info.get('title', 'Unknown Title'))
        st.write(f"**Creator:** {info.get('uploader', 'Unknown')}")
        
        media_type = st.radio("Select Output Type", ["Video (MP4)", "Audio Only (MP3)"])
        is_audio = media_type == "Audio Only (MP3)"
        st.session_state.is_audio = is_audio
        
        if is_audio:
            format_choice = st.selectbox("Select Audio Bitrate", ["320kbps", "256kbps", "192kbps", "128kbps"])
        else:
            format_choice = st.selectbox("Select Video Quality", ["Best Available", "1080p", "720p", "480p", "360p"])
            
        if st.button("Download Raw Media"):
            with st.spinner("Downloading media... this might take a while."):
                try:
                    target_url = info.get('original_url') or url.strip()
                    downloaded_path = download_media(target_url, format_choice, st.session_state.temp_dir, is_audio=is_audio)
                    st.session_state.downloaded_file = downloaded_path
                    st.session_state.processed_file = None  # Reset processed state
                    st.success("Downloaded successfully!")
                except Exception as e:
                    st.error(f"Download failed: {e}")

if st.session_state.downloaded_file and os.path.exists(st.session_state.downloaded_file):
    st.divider()
    
    # Stage 3: In-Browser Editor
    st.header("3. Editor")
    
    # Preview
    st.subheader("Raw Media Preview")
    if st.session_state.is_audio:
        st.audio(st.session_state.downloaded_file)
    else:
        st.video(st.session_state.downloaded_file)
        
    st.subheader("Edit Controls")
    
    # Trim Tool
    duration = float(st.session_state.media_info.get('duration') or 60.0)
    if duration <= 0:
        duration = 60.0
        
    st.markdown("##### Trim Tool")
    start_time, end_time = st.slider(
        "Select Start and End Time (s)", 
        0.0, 
        duration, 
        (0.0, duration), 
        step=1.0
    )
    
    # Resize Tool
    resolution = None
    if not st.session_state.is_audio:
        st.markdown("##### Video Resizing")
        resolution = st.selectbox("Select Target Resolution", ["Original", "1080p", "720p", "480p", "360p"])
        
    if st.button("Apply & Render"):
        with st.spinner("Applying edits..."):
            try:
                base, ext = os.path.splitext(st.session_state.downloaded_file)
                output_path = os.path.join(st.session_state.temp_dir, f"edited_{os.path.basename(base)}{ext}")
                
                processed_path = process_media(
                    input_path=st.session_state.downloaded_file,
                    start_time=start_time,
                    end_time=end_time,
                    resolution=resolution,
                    is_audio=st.session_state.is_audio,
                    output_path=output_path
                )
                st.session_state.processed_file = processed_path
                st.success("Media processed successfully!")
            except Exception as e:
                st.error(f"Processing failed: {e}")

if st.session_state.processed_file and os.path.exists(st.session_state.processed_file):
    st.divider()
    
    # Stage 4: Export & Download
    st.header("4. Export")
    
    st.subheader("Processed Preview")
    if st.session_state.is_audio:
        st.audio(st.session_state.processed_file)
    else:
        st.video(st.session_state.processed_file)
        
    safe_title = sanitize_filename(st.session_state.media_info.get('title', 'media'))
    ext = ".mp3" if st.session_state.is_audio else ".mp4"
    mime = "audio/mpeg" if st.session_state.is_audio else "video/mp4"

    with open(st.session_state.processed_file, "rb") as file:
        st.download_button(
            label="Download Final Media",
            data=file,
            file_name=f"edited_{safe_title}{ext}",
            mime=mime,
            type="primary"
        )
elif st.session_state.downloaded_file and os.path.exists(st.session_state.downloaded_file):
    st.divider()
    st.header("4. Export (Raw)")
    
    safe_title = sanitize_filename(st.session_state.media_info.get('title', 'media'))
    ext = ".mp3" if st.session_state.is_audio else ".mp4"
    mime = "audio/mpeg" if st.session_state.is_audio else "video/mp4"

    with open(st.session_state.downloaded_file, "rb") as file:
        st.download_button(
            label="Download Raw Media",
            data=file,
            file_name=f"raw_{safe_title}{ext}",
            mime=mime
        )