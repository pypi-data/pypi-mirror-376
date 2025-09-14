from openai import OpenAI
import os
import json
import tempfile
import subprocess
import shutil
import base64
from datetime import datetime

def get_api_key():
    """Get OpenAI API key from config file"""
    config_path = os.path.expanduser('~/.dt_config.json')
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            return config.get('openai_token')
    except FileNotFoundError:
        raise Exception(f"Config file not found at {config_path}")
    except json.JSONDecodeError:
        raise Exception(f"Invalid JSON in config file at {config_path}")
    except Exception as e:
        raise Exception(f"Error reading config: {str(e)}")

# Initialize client with API key from config
client = OpenAI(api_key=get_api_key())

def list_models():
    """List available OpenAI models"""
    try:
        models = client.models.list()
        for model in models:
            print(f"- {model.id}")
    except Exception as e:
        print(f"Error listing models: {e}")

def get_command_suggestion(text, context, model="gpt-4"):
    """Get command suggestion based on text description and current directory context"""
    try:
        prompt = f"""
Based on the following context and request, suggest an appropriate command:

Context:
{context}

Request: {text}

Provide only the command, no explanations."""

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful command-line assistant. Provide only the command that would accomplish the user's request, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Error getting suggestion: {e}" 

def execute_command(command, auto_confirm=False):
    """Execute the suggested command with optional confirmation"""
    if not command:
        print("No command to execute")
        return
        
    if auto_confirm:
        print(f"Executing: {command}")
        os.system(command)
    else:
        confirm = input(f"Execute command '{command}'? [y/N] ")
        if confirm.lower() == 'y':
            os.system(command)
        else:
            print("Command execution cancelled")

def extract_audio(video_path):
    """Extract audio from video file using ffmpeg"""
    temp_dir = tempfile.gettempdir()
    audio_path = os.path.join(temp_dir, 'audio_extract.mp3')
    
    try:
        cmd = f'ffmpeg -i "{video_path}" -q:a 0 -map a "{audio_path}" -y'
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return audio_path
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error extracting audio: {e.stderr.decode()}")

def transcribe_video(video_path, model="whisper-1"):
    """Transcribe video by extracting audio and using Whisper API"""
    try:
        # Extract audio
        print("Extracting audio...")
        audio_path = extract_audio(video_path)
        
        # Open audio file
        print("Transcribing audio...")
        with open(audio_path, 'rb') as audio_file:
            # Call Whisper API
            response = client.audio.transcriptions.create(
                model=model,
                file=audio_file
            )
        
        # Clean up temporary audio file
        os.remove(audio_path)
        
        return response.text
        
    except Exception as e:
        if 'audio_path' in locals():
            try:
                os.remove(audio_path)
            except:
                pass
        return f"Error transcribing video: {str(e)}"

def download_youtube_video(url, start_time=None, end_time=None):
    """Download YouTube video segment"""
    temp_dir = tempfile.mkdtemp()
    output_path = os.path.join(temp_dir, 'video.mp4')
    
    # Convert time strings to seconds for yt-dlp
    def parse_time(time_str):
        h, m, s = map(int, time_str.split(':'))
        return h * 3600 + m * 60 + s
    
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # More flexible format selection
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [lambda d: print(f"Download progress: {d['_percent_str']}") if '_percent_str' in d else None],
        'merge_output_format': 'mp4'
    }
    
    # Add time range if specified
    if start_time and end_time:
        start_seconds = parse_time(start_time)
        end_seconds = parse_time(end_time)
        
        ydl_opts.update({
            'download_ranges': lambda _: [[start_seconds, end_seconds]],
            'force_keyframes_at_cuts': True,
            'postprocessor_args': {
                'ffmpeg': [
                    '-ss', str(start_seconds),
                    '-t', str(end_seconds - start_seconds)
                ]
            }
        })
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return output_path, temp_dir
    except Exception as e:
        shutil.rmtree(temp_dir)
        raise Exception(f"Error downloading video: {str(e)}")

def extract_frames(video_path, fps=1):
    """Extract frames from video at specified FPS"""
    import yt_dlp
    import cv2
    
    frames_dir = tempfile.mkdtemp()
    frames = []
    
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps_original = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps_original / fps)
        
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
        
        print()  # New line after progress
        cap.release()
        return frames, frames_dir
    except Exception as e:
        shutil.rmtree(frames_dir)
        raise Exception(f"Error extracting frames: {str(e)}")

def encode_image(image_path):
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def analyze_youtube_video(url, start_time=None, end_time=None, model="gpt-4o"):
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
            
            timestamp = str(datetime.timedelta(seconds=i))  # Approximate timestamp
            frame_analysis = f"[{timestamp}] {response.choices[0].message.content}\n\n"
            analysis.append(frame_analysis)
        
        print("\n\n4. Cleaning up temporary files...")
        shutil.rmtree(video_dir)
        shutil.rmtree(frames_dir)
        
        print("\nAnalysis complete!")
        return "".join(analysis)
        
    except Exception as e:
        # Clean up on error
        if 'video_dir' in locals():
            shutil.rmtree(video_dir)
        if 'frames_dir' in locals():
            shutil.rmtree(frames_dir)
        return f"Error analyzing video: {str(e)}"

def split_audio(input_file: str, chunk_duration: int = 600) -> list:
    """Split audio file into chunks using ffmpeg.
    
    Args:
        input_file: Path to input audio file
        chunk_duration: Duration of each chunk in seconds (default: 10 minutes)
    
    Returns:
        List of temporary chunk file paths
    """
    import tempfile
    import subprocess
    import os
    
    # Create temp directory for chunks
    temp_dir = tempfile.mkdtemp()
    chunk_paths = []
    
    try:
        # Get duration of input file
        probe_cmd = [
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', input_file
        ]
        duration = float(subprocess.check_output(probe_cmd).decode().strip())
        
        # Calculate number of chunks needed
        num_chunks = int(duration / chunk_duration) + 1
        
        print(f"\nSplitting {os.path.basename(input_file)} into {num_chunks} chunks...")
        
        # Split file into chunks
        for i in range(num_chunks):
            chunk_path = os.path.join(temp_dir, f'chunk_{i}.mp3')
            start_time = i * chunk_duration
            
            cmd = [
                'ffmpeg', '-y', '-i', input_file,
                '-ss', str(start_time),
                '-t', str(chunk_duration),
                '-acodec', 'libmp3lame',  # Convert to MP3
                '-ab', '128k',  # Reduce bitrate to help with file size
                '-ac', '1',  # Convert to mono
                '-ar', '44100',  # Standard sample rate
                chunk_path
            ]
            
            subprocess.run(cmd, capture_output=True)
            if os.path.exists(chunk_path):
                chunk_paths.append(chunk_path)
                print(f"Created chunk {i+1}/{num_chunks}")
        
        return temp_dir, chunk_paths
        
    except Exception as e:
        print(f"Error splitting audio: {str(e)}")
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        return None, []

def transcribe_local_audio(audio_path: str, model: str = "whisper-1"):
    """Transcribe local audio file using OpenAI's Whisper API.
    
    Args:
        audio_path: Path to the audio file
        model: Whisper model to use (whisper-1)
    """
    import os
    
    try:
        # Check file size
        file_size = os.path.getsize(audio_path)
        max_size = 25 * 1024 * 1024  # 25MB
        
        if file_size > max_size:
            print(f"\nAudio file is {file_size/1024/1024:.1f}MB (limit is 25MB)")
            print("Splitting into smaller chunks...")
            
            temp_dir, chunk_paths = split_audio(audio_path)
            if not chunk_paths:
                return None
                
            # Transcribe each chunk
            transcripts = []
            for i, chunk_path in enumerate(chunk_paths, 1):
                print(f"\nTranscribing chunk {i}/{len(chunk_paths)}...")
                with open(chunk_path, "rb") as audio_file:
                    response = client.audio.transcriptions.create(
                        model=model,
                        file=audio_file
                    )
                transcripts.append(response.text)
            
            # Clean up temp files
            import shutil
            shutil.rmtree(temp_dir)
            
            # Combine transcripts
            return "\n\n".join(transcripts)
        else:
            print(f"Transcribing audio file: {audio_path}")
            with open(audio_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model=model,
                    file=audio_file
                )
            return response.text
        
    except Exception as e:
        print(f"Error transcribing audio: {str(e)}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)
        return None