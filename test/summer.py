import cv2
import os
import subprocess
import random

def encode_video(input_path, output_path):
    try:
        command = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264',
            '-preset', 'medium',
            '-crf', '23',
            '-c:a', 'aac',
            '-strict', '-2',
            '-movflags', '+faststart',
            '-y',
            output_path
        ]

        process = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        if process.returncode != 0:
            print(f"FFmpeg encoding failed: {process.stderr.decode()}")
            return None

        return output_path

    except Exception as e:
        print(f"Error during video encoding: {e}")
        return None
    

def add_audio(video_no_audio, audio_source, output_with_audio):
    command = [
        'ffmpeg',
        '-i', video_no_audio,
        '-i', audio_source,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        '-shortest',
        '-y',
        output_with_audio
    ]
    
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if process.returncode != 0:
        print(f"FFmpeg audio merge failed: {process.stderr.decode()}")
        return None
    return output_with_audio


def merge_videos(video_paths, output_path):
    """
    Merges multiple videos by taking clips of calculated duration from the video to create an output video.

    Args:
        video_paths (list): List of paths to input video files.
        output_path (str): Path to save the output merged video.
    """
    random.shuffle(video_paths)  # Shuffle the video paths for randomness
    
    num_videos = len(video_paths)

    cap = cv2.VideoCapture(video_paths[0])
    if not cap.isOpened():
        raise ValueError("Failed to open video to compute duration.")
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    total_duration = frame_count / fps
    cap.release()
    clip_duration = total_duration / num_videos


    # Initialize video properties
    video_caps = []
    fps_list = []
    frame_counts = []
    widths, heights = [], []

    # Validate video files and collect properties
    for i, path in enumerate(video_paths):
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise ValueError(f"Video file {path} is invalid or unsupported.")
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            cap.release()
            raise ValueError(f"Video {path} has invalid FPS.")
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if frame_count == 0:
            cap.release()
            raise ValueError(f"Video {path} has no frames.")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            cap.release()
            raise ValueError(f"Video {path} has invalid dimensions.")

        # Check if video has enough frames for its clip
        required_duration = (i + 1) * clip_duration
        if frame_count / fps < required_duration:
            cap.release()
            raise ValueError(f"Video {path} is too short. Needs at least {required_duration:.2f} seconds for clip {i * clip_duration:.2f}-{(i + 1) * clip_duration:.2f} seconds.")

        video_caps.append(cap)
        fps_list.append(fps)
        frame_counts.append(frame_count)
        widths.append(width)
        heights.append(height)

    # Ensure all videos have the same resolution
    if len(set(zip(widths, heights))) > 1:
        for cap in video_caps:
            cap.release()
        raise ValueError("All videos must have the same resolution (width and height).")

    # Use first video's properties for output
    out_fps = fps_list[0]
    out_width, out_height = widths[0], heights[0]
    expected_duration = clip_duration * num_videos

    # Initialize output video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, out_fps, (out_width, out_height))
    if not out.isOpened():
        for cap in video_caps:
            cap.release()
        raise ValueError("Failed to initialize output video writer.")

    # Process each video clip
    for i, cap in enumerate(video_caps):
        start_time = i * clip_duration
        start_frame = int(start_time * fps_list[i])
        end_frame = int((start_time + clip_duration) * fps_list[i])

        # Set to start frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # Read and write frames
        for _ in range(start_frame, min(end_frame, frame_counts[i])):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        cap.release()

    out.release()

    # Verify final video duration
    final_cap = cv2.VideoCapture(output_path)
    if not final_cap.isOpened():
        raise ValueError("Failed to open output video for verification.")
    final_frame_count = int(final_cap.get(cv2.CAP_PROP_FRAME_COUNT))
    final_fps = final_cap.get(cv2.CAP_PROP_FPS)
    final_duration = final_frame_count / final_fps if final_fps > 0 else 0
    final_cap.release()

    if abs(final_duration - expected_duration) > 0.5:
        raise ValueError(f"Final video duration ({final_duration}s) does not match expected ({expected_duration}s).")


def check_length(video_path):
    """
    Checks if the video at video_path has the expected duration.

    Args:
        video_path (str): Path to the video file.
        expected_duration (float): Expected duration in seconds.

    Returns:
        bool: True if the video has the expected duration, False otherwise.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Failed to open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    actual_duration = frame_count / fps if fps > 0 else 0

    cap.release()
    
    print(f"Video {video_path} has duration: {actual_duration:.2f} seconds")


if __name__ == "__main__":
    try:
        # Define your 4 videos
        video_paths = [
            'deepfake.mp4',
            'heart.mp4',
            'speech.mp4',
            'spo2.mp4',
            'audio_tone.mp4',
        ]

        temp_video = "merged_output_temp.mp4"
        merge_videos(video_paths, temp_video)
        encoded_video = encode_video(temp_video, "encoded_merged_output.mp4")
        output_with_audio = "final_output_with_audio.mp4"
        final_video = add_audio(encoded_video, video_paths[0], output_with_audio)
        print(f"Final video with audio saved as: {final_video}")

    except Exception as e:
        print(f"Error: {str(e)}")

    


    