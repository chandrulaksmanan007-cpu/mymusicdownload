import streamlit as st
import os
import tempfile
import shutil
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

st.title("Universal Media Studio")
st.markdown("Download, edit, and export online media easily.")

st.divider()

# Stage 1: URL Ingestion
st.header("1. Fetch Media")
url = st.text_input("Enter media URL (YouTube, Vimeo, etc.)")
if st.button("Fetch Metadata"):
    if url:
        with st.spinner("Fetching metadata..."):
            try:
                reset_download_state()
                info = fetch_metadata(url)
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
        if info['thumbnail']:
            st.image(info['thumbnail'], use_column_width=True)
        st.write(f"**Duration:** {info['duration']} seconds")
        
    with col2:
        st.subheader(info['title'])
        st.write(f"**Creator:** {info['uploader']}")
        
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
                    downloaded_path = download_media(info['original_url'], format_choice, st.session_state.temp_dir, is_audio=is_audio)
                    st.session_state.downloaded_file = downloaded_path
                    st.session_state.processed_file = None # Reset processed
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
    duration = st.session_state.media_info.get('duration', 0)
    if duration == 0:
        duration = 1000 # Fallback if duration is unknown
        
    st.markdown("##### Trim Tool")
    start_time, end_time = st.slider("Select Start and End Time (s)", 0.0, float(duration), (0.0, float(duration)), step=1.0)
    
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
        
    with open(st.session_state.processed_file, "rb") as file:
        st.download_button(
            label="Download Final Media",
            data=file,
            file_name=f"edited_{st.session_state.media_info['title']}{'.mp3' if st.session_state.is_audio else '.mp4'}",
            mime="audio/mpeg" if st.session_state.is_audio else "video/mp4",
            type="primary"
        )
elif st.session_state.downloaded_file and os.path.exists(st.session_state.downloaded_file):
    st.divider()
    st.header("4. Export (Raw)")
    
    with open(st.session_state.downloaded_file, "rb") as file:
        st.download_button(
            label="Download Raw Media",
            data=file,
            file_name=f"raw_{st.session_state.media_info['title']}{'.mp3' if st.session_state.is_audio else '.mp4'}",
            mime="audio/mpeg" if st.session_state.is_audio else "video/mp4"
        )
