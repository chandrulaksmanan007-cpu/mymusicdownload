from moviepy.editor import VideoFileClip, AudioFileClip
import os

def process_media(input_path, start_time, end_time, resolution=None, is_audio=False, output_path=None):
    if not output_path:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_edited{ext}"

    clip = None
    try:
        if is_audio:
            clip = AudioFileClip(input_path)
        else:
            clip = VideoFileClip(input_path)
            
        # Trimming
        if start_time is not None and end_time is not None:
            if start_time >= end_time:
                raise ValueError("Start time must be less than end time.")
            clip = clip.subclip(start_time, end_time)
            
        # Resizing (only for video)
        if not is_audio and resolution and resolution != "Original":
            height = int(resolution.split('p')[0])
            clip = clip.resize(height=height)
            
        # Write output
        if is_audio:
            clip.write_audiofile(output_path, logger=None)
        else:
            clip.write_videofile(output_path, codec="libx264", audio_codec="aac", logger=None)
            
        if clip:
            clip.close()
            
        return output_path
    except Exception as e:
        if clip:
            clip.close()
        raise Exception(f"Failed to process media: {str(e)}")
