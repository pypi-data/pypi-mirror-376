import os
import tempfile
import shutil
import cv2
import yt_dlp
import base64
import subprocess
from datetime import datetime, timedelta
from .openai_helper import get_api_key
from openai import OpenAI

client = OpenAI(api_key=get_api_key())

def download_youtube_video(url, start_time=None, end_time=None, ensure_audio=False):
    """Download YouTube video segment, optionally ensuring audio is included.
    If a local file path is provided instead of a URL, it will be used directly."""
    # Check if the input is a local file path
    if os.path.isfile(url):
        print(f"Using local file: {url}")
        # For local files, we don't need to download anything
        # Just create a temp directory to maintain the same return signature
        temp_dir = tempfile.mkdtemp()
        return url, temp_dir
        
    # Original YouTube download logic for URLs
    temp_dir = tempfile.mkdtemp()
    # Use a more descriptive temporary filename
    base_filename = 'video'
    output_tmpl = os.path.join(temp_dir, f'{base_filename}.%(ext)s')
    final_output_path = os.path.join(temp_dir, f'{base_filename}.mp4') # Expected final path after merge
    
    def parse_time(time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    
    # --- Format Selection --- 
    # Prioritize MP4 video and M4A/AAC audio, but ensure *some* audio is included if ensure_audio=True.
    # Fallback to best available video+audio if specific formats fail.
    # Request merge to MP4 container.
    if ensure_audio:
        # Explicitly request best video (prefer mp4) + best audio (prefer m4a), merge into mp4
        # The /best ensures it falls back if the preferred combo isn't available.
        ydl_format = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best'
    else:
        # Video only, prefer mp4
        ydl_format = 'bestvideo[ext=mp4]/bestvideo/best'

    ydl_opts = {
        'format': ydl_format,
        'outtmpl': output_tmpl,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [lambda d: print(f"Download progress: {d['_percent_str']}") if '_percent_str' in d else None],
        # Ensure the final merged file is MP4
        'merge_output_format': 'mp4' 
    }
    
    # Determine download section based on provided times
    download_section = None
    if start_time and end_time:
        start_seconds = parse_time(start_time)
        end_seconds = parse_time(end_time)
        download_section = f'*{start_seconds}-{end_seconds}'
    elif start_time:
        start_seconds = parse_time(start_time)
        download_section = f'*{start_seconds}-inf' # Use 'inf' for end
    elif end_time:
        end_seconds = parse_time(end_time)
        download_section = f'*0-{end_seconds}' # Use 0 for start

    if download_section:
        # Use 'download_sections' which is generally more reliable
        ydl_opts.update({
            'download_sections': download_section,
            # Force keyframes at cuts for accuracy, might increase download size slightly
            'force_keyframes_at_cuts': True 
        })
        # Remove postprocessor args if using download_sections
        if 'postprocessor_args' in ydl_opts:
            del ydl_opts['postprocessor_args']
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            
        # Check if the expected merged file exists
        if not os.path.exists(final_output_path):
            # Fallback: maybe only video downloaded, try finding any mp4
            found_files = [f for f in os.listdir(temp_dir) if f.endswith('.mp4')]
            if found_files:
                # Rename the first found mp4 to the expected name
                os.rename(os.path.join(temp_dir, found_files[0]), final_output_path)
            else:
                 raise Exception("yt-dlp did not produce the expected mp4 file.")
                    
        return final_output_path, temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise Exception(f"Error downloading video: {str(e)}")

def extract_frames(video_path, fps=1):
    """Extract frames from video at specified FPS"""
    frames_dir = tempfile.mkdtemp()
    frames = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_original = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps_original / fps) if fps_original else 1
        
        frame_count = 0
        saved_count = 0
        
        while frame_count < total_frames:
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_count)
            success, frame = cap.read()
            
            if success:
                frame_path = os.path.join(frames_dir, f'frame_{saved_count}.jpg')
                cv2.imwrite(frame_path, frame)
                frames.append(frame_path)
                saved_count += 1
                print(f"\rExtracting frames: {saved_count} ({(frame_count/total_frames)*100:.1f}%)", end="", flush=True)
            
            frame_count += frame_interval
        
        print()
        cap.release()
        return frames, frames_dir
    except Exception as e:
        shutil.rmtree(frames_dir)
        raise Exception(f"Error extracting frames: {str(e)}")

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_frames(url, start_time=None, end_time=None, model="gpt-4o"):
    """Download YouTube video, extract frames, and analyze with GPT-4 Vision"""
    try:
        print("\n1. Downloading video...")
        video_path, video_dir = download_youtube_video(url, start_time, end_time)
        
        print("\n2. Extracting frames...")
        frames, frames_dir = extract_frames(video_path)
        total_frames = len(frames)
        print(f"Extracted {total_frames} frames")
        
        print("\n3. Analyzing frames with GPT-4 Vision...")
        analysis = []
        
        for i, frame_path in enumerate(frames, 1):
            print(f"\rAnalyzing frame {i}/{total_frames} ({(i/total_frames)*100:.1f}%)", end="", flush=True)
            base64_image = encode_image(frame_path)
            
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Describe this frame in detail, including any notable objects, actions, or events."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500
            )
            
            timestamp = str(timedelta(seconds=i))
            frame_analysis = f"[{timestamp}] {response.choices[0].message.content}\n\n"
            analysis.append(frame_analysis)
        
        print("\n\n4. Cleaning up temporary files...")
        shutil.rmtree(video_dir)
        shutil.rmtree(frames_dir)
        
        print("\nAnalysis complete!")
        return "".join(analysis)
        
    except Exception as e:
        if 'video_dir' in locals():
            shutil.rmtree(video_dir)
        if 'frames_dir' in locals():
            shutil.rmtree(frames_dir)
        return f"Error analyzing video: {str(e)}"

# Function to transcribe video and save as SRT
def transcribe_video_to_srt(video_path, model="whisper-1", start_time=None, end_time=None):
    """Transcribe video audio to SRT format using Whisper and save to a temp file."""
    srt_file = None
    temp_audio = None
    try:
        # More robust check for *any* audio stream using ffprobe
        # Gets the index of the first audio stream. Errors/returns empty if none.
        print(f"\\nChecking for audio stream in: {video_path}")
        probe_cmd = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a',   # Select *any* audio stream
            '-show_entries', 'stream=index', # Show index(es)
            '-of', 'csv=p=0', # Output index(es) separated by newline
            video_path
        ]
        
        try:
            # Check if ffprobe finds *any* audio stream index
            result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, timeout=30)
            if not result.stdout.strip(): 
                print("Warning: No audio stream index found by ffprobe - skipping subtitles.")
                return None
            # We just care that *an* audio stream exists, don't need the index here
            print(f"Audio stream(s) found. Proceeding with extraction.")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Warning: ffprobe failed or timed out (likely no audio stream) - skipping subtitles. Error: {e}")
            return None

        # Proceed with audio extraction if check passed
        print("\\nExtracting audio for transcription...")
        temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_audio.close()

        # Base ffmpeg command arguments
        ffmpeg_cmd_base = ['ffmpeg', '-y']

        # Add time arguments if provided (placed before -i for faster seeking)
        if start_time:
            ffmpeg_cmd_base.extend(['-ss', start_time])
        if end_time:
             # Use -to instead of -t for absolute end time if start_time is also present
             ffmpeg_cmd_base.extend(['-to', end_time])

        ffmpeg_cmd = ffmpeg_cmd_base + [
            '-i', video_path,
            '-vn',                          # No video
            '-map', '0:a?',                 # Map first *available* audio stream (optional)
            '-acodec', 'pcm_s16le',         # Convert to PCM WAV
            '-ar', '16000',                 # 16kHz sample rate
            '-ac', '1',                     # Mono
            '-hide_banner', '-loglevel', 'error', # Quieter logs
            temp_audio.name
        ]

        print(f"Running audio extraction: {' '.join(ffmpeg_cmd)}")
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True) # Removed check=True for manual check

        if result.returncode != 0:
            # Log stderr for debugging before raising
            print(f"FFmpeg Error (Return Code: {result.returncode}):\\n{result.stderr}")
            # Clean up temp audio file before raising
            if temp_audio and os.path.exists(temp_audio.name):
                 os.remove(temp_audio.name)
            raise Exception(f"Failed to extract audio. FFmpeg stderr logged above.")

        print("\\nTranscribing extracted audio (Whisper)...")
        with open(temp_audio.name, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file,
                response_format="srt"
            )

        # Save the SRT content to a temporary file
        srt_file = tempfile.NamedTemporaryFile(mode='w+', suffix='.srt', delete=False)
        srt_file.write(response)
        srt_file.flush()
        print(f"Temporary SRT file created: {srt_file.name}")
        return srt_file

    except Exception as e:
        # Clean up temp files if created before error
        if srt_file and os.path.exists(srt_file.name):
            srt_file.close()
            os.remove(srt_file.name)
        # temp_audio is cleaned up in the finally block now
        # Re-raise the original exception for clarity
        raise e # Removed redundant message wrapping
    finally:
        # Clean up temp audio file in success or specific failure cases
        if temp_audio and os.path.exists(temp_audio.name):
            os.remove(temp_audio.name)
            print(f"Temporary audio file removed: {temp_audio.name}")

def convert_to_gif(video_path, output_path, fps=10, speed=1.0, 
                   burn_subtitles=False, start_time=None, end_time=None):
    """Convert video to high-quality GIF or MP4 video, optionally with subtitles.
    
    Detects output format based on file extension (.gif vs .mp4, etc.)
    """
    temp_srt_file = None
    try:
        # Validate speed parameter
        if not 0.25 <= speed <= 2.0:
            raise ValueError("Speed must be between 0.25 and 2.0")
            
        # Determine output format based on file extension
        output_ext = os.path.splitext(output_path)[1].lower()
        is_gif_output = output_ext == '.gif'
        is_video_output = output_ext in ['.mp4', '.mkv', '.mov', '.avi']
        
        if not (is_gif_output or is_video_output):
            print(f"Warning: Unrecognized output extension '{output_ext}'. Defaulting to GIF workflow.")
            is_gif_output = True
            is_video_output = False
            
        print(f"Output format: {'GIF' if is_gif_output else 'Video'} ({output_ext})")
            
        # --- Subtitle Generation (if requested) ---
        srt_path_for_ffmpeg = None
        if burn_subtitles:
            # Pass time args to transcription function
            temp_srt_file = transcribe_video_to_srt(video_path, start_time=start_time, end_time=end_time)
            # Only proceed if transcription was successful (returned a file object)
            if temp_srt_file:
                srt_path_for_ffmpeg = temp_srt_file.name
                # Ensure the file is closed so ffmpeg can access it if needed, 
                # but keep the path. It will be deleted in finally.
                temp_srt_file.close()
            else:
                # transcribe_video_to_srt already printed a warning
                pass # Keep srt_path_for_ffmpeg as None
            
        # --- Base FFmpeg Arguments ---
        # Base ffmpeg args for input and seeking
        ffmpeg_input_args = []
        if start_time:
            ffmpeg_input_args.extend(['-ss', start_time])
        # IMPORTANT: -i must come AFTER -ss/-to for accurate seeking
        ffmpeg_input_args.extend(['-i', video_path]) 
        # Add duration limit using -t if end_time and start_time are known
        # Or use -to if only end_time is known (less common usage)
        if end_time:
            if start_time:
                # Calculate duration if both start and end are given
                try:
                    from datetime import datetime, timedelta
                    t_start = datetime.strptime(start_time, '%H:%M:%S')
                    t_end = datetime.strptime(end_time, '%H:%M:%S')
                    duration = (t_end - t_start).total_seconds()
                    if duration > 0:
                         ffmpeg_input_args.extend(['-t', str(duration)])
                    else:
                        print("Warning: End time is not after start time, ignoring end time.")
                except ValueError:
                    print("Warning: Could not parse start/end time for duration calculation.")
                    ffmpeg_input_args.extend(['-to', end_time]) # Fallback to -to
            else:
                 ffmpeg_input_args.extend(['-to', end_time]) # Use -to if only end time
                 
        # --- Different workflows for GIF vs MP4 ---
        if is_gif_output:
            # --- GIF WORKFLOW ---
            # Generate palette for better quality
            palette_path = tempfile.NamedTemporaryFile(suffix='_palette.png', delete=False).name
            
            # Base filters for GIF
            vf_filters = []
            if speed != 1.0:
                vf_filters.append(f'setpts={1/speed}*PTS')
            vf_filters.append(f'fps={fps}')
            vf_filters.append('scale=720:-1:flags=lanczos')
            
            # Add subtitle filter if path exists
            if srt_path_for_ffmpeg:
                subtitle_filter = f"subtitles={srt_path_for_ffmpeg}:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF&,Outline=1,BorderStyle=3,Alignment=2,MarginV=40'"
                vf_filters.append(subtitle_filter)
                print("Subtitle filter added to GIF conversion.")
                
            # Build palette generation command
            palette_cmd = ['ffmpeg', '-y', '-nostdin'] + ffmpeg_input_args + [
                '-vf', ",".join(vf_filters) + ',palettegen',
                palette_path
            ]
            print(f"Running FFmpeg palette generation...")
            subprocess.run(palette_cmd, check=True, capture_output=True)
    
            # Build final GIF generation command
            gif_cmd = ['ffmpeg', '-y', '-nostdin'] + ffmpeg_input_args + [
                 '-i', palette_path,
                '-lavfi', ",".join(vf_filters) + ' [x]; [x][1:v] paletteuse',
                output_path
            ]
            print(f"Running FFmpeg GIF generation...")
            subprocess.run(gif_cmd, check=True, capture_output=True)
            
            # Clean up palette file
            if os.path.exists(palette_path):
                os.remove(palette_path)
                
        elif is_video_output:
            # --- MP4/VIDEO WORKFLOW ---
            # Base filters for video
            vf_filters = []
            if speed != 1.0:
                vf_filters.append(f'setpts={1/speed}*PTS')
                # Also adjust audio tempo if speed is changed
                audio_filter = f'atempo={speed}'
            else:
                audio_filter = None
                
            # Add subtitle filter if path exists
            if srt_path_for_ffmpeg:
                subtitle_filter = f"subtitles={srt_path_for_ffmpeg}:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF&,Outline=1,BorderStyle=3,Alignment=2,MarginV=40'"
                vf_filters.append(subtitle_filter)
                print("Subtitle filter added to video.")
                
            # Build a more efficient one-pass command for video
            video_cmd = ['ffmpeg', '-y', '-nostdin'] + ffmpeg_input_args
            
            # Add video filters if any
            if vf_filters:
                video_cmd.extend(['-vf', ','.join(vf_filters)])
                
            # Add audio filter if any
            if audio_filter:
                video_cmd.extend(['-af', audio_filter])
                
            # Set output quality and format
            video_cmd.extend([
                '-c:v', 'libx264',  # Use H.264 codec
                '-preset', 'medium', # Balance between speed and quality
                '-crf', '23',        # Reasonable quality (lower = better)
                '-c:a', 'aac',       # AAC audio codec
                '-b:a', '128k',      # 128kbps audio bitrate
                output_path
            ])
            
            print(f"Running FFmpeg video conversion...")
            result = subprocess.run(video_cmd, check=True, capture_output=True)
            print(f"Video conversion complete!")
            
        return True
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        # If ffmpeg failed, print stderr
        if isinstance(e, subprocess.CalledProcessError):
            print("FFmpeg stderr:", e.stderr.decode())
        return False
    finally:
        # --- Cleanup --- 
        # Clean up temporary SRT file only if it was successfully created
        if temp_srt_file and hasattr(temp_srt_file, 'name') and os.path.exists(temp_srt_file.name):
            print(f"Cleaning up temporary SRT file: {temp_srt_file.name}")
            # File object might already be closed, just remove the path
            os.remove(temp_srt_file.name)

def transcribe_video(url, model="whisper-1", start_time=None, end_time=None):
    """Download YouTube video and transcribe audio"""
    try:
        print("\n1. Downloading video...")
        video_path, video_dir = download_youtube_video(url, start_time, end_time)
        
        print("\n2. Transcribing audio...")
        with open(video_path, 'rb') as audio_file:
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
        
        print("\n3. Cleaning up temporary files...")
        shutil.rmtree(video_dir)
        
        return response.text
        
    except Exception as e:
        if 'video_dir' in locals():
            shutil.rmtree(video_dir)
        return f"Error transcribing video: {str(e)}"