# extract_keyframes.py

import cv2
import numpy as np
import os
from tqdm import tqdm
import argparse # Import the library for command-line arguments

def extract_keyframes(video_path, output_folder, threshold=35):
    """
    Extracts keyframes from a video based on significant changes between frames.

    This function works with various video formats supported by OpenCV/FFmpeg,
    including .mp4, .mkv, and .webm.

    Args:
        video_path (str): Path to the input video file.
        output_folder (str): Path to the folder where keyframes will be saved.
        threshold (int): The threshold for scene change detection. A higher value
                         means less sensitivity and fewer keyframes.
    """
    # --- 1. Pre-flight Checks and Setup ---
    print(f"Starting keyframe extraction for: {video_path}")
    print(f"Difference threshold set to: {threshold}")

    # Check if the input video file exists
    if not os.path.exists(video_path):
        print(f"Error: Input video file not found at '{video_path}'")
        return

    # Open the video file
    video_capture = cv2.VideoCapture(video_path)
    if not video_capture.isOpened():
        print("Error: Could not open video file. This might be due to missing codecs for the format.")
        return

    # Create the output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"Created output folder: {output_folder}")

    # --- 2. Initialization ---
    success, prev_frame = video_capture.read()
    if not success:
        print("Error: Could not read the first frame from the video.")
        video_capture.release()
        return

    prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)

    # Save the very first frame
    first_frame_path = os.path.join(output_folder, "keyframe_00000001.jpg")
    cv2.imwrite(first_frame_path, prev_frame)
    
    frame_count = 1
    keyframe_count = 1

    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

    # Initialize progress bar
    pbar = tqdm(total=total_frames, unit="frames", desc="Processing Video")
    pbar.update(1)

    # --- 3. Main Loop for Frame Extraction ---
    while success:
        success, current_frame = video_capture.read()
        if not success:
            break

        frame_count += 1
        pbar.update(1)

        current_frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
        
        # Calculate the absolute difference between frames
        frame_diff = cv2.absdiff(current_frame_gray, prev_frame_gray)
        mean_diff = np.mean(frame_diff)

        # If the difference is significant, save the frame
        if mean_diff > threshold:
            keyframe_count += 1
            filename = f"keyframe_{keyframe_count:08d}.jpg"
            output_path = os.path.join(output_folder, filename)
            cv2.imwrite(output_path, current_frame)
            
            # The new keyframe becomes the reference for the next comparison
            prev_frame_gray = current_frame_gray

    # --- 4. Cleanup ---
    pbar.close()
    video_capture.release()
    print("\n------------------------------------")
    print("Keyframe extraction complete.")
    print(f"Total frames processed: {frame_count}")
    print(f"Total keyframes extracted: {keyframe_count}")
    print(f"Keyframes saved in: '{output_folder}'")
    print("------------------------------------")


if __name__ == '__main__':
    # --- Use argparse to handle command-line arguments ---
    parser = argparse.ArgumentParser(
        description="Extracts keyframes from a video (.mp4, .mkv, .webm, etc.) based on scene changes."
    )
    
    # Required argument for the input video file
    parser.add_argument(
        "input_video",
        help="Path to the input video file."
    )
    
    # Optional argument for the output folder
    parser.add_argument(
        "-o", "--output_folder",
        default="extracted_keyframes",
        help="Folder to save the keyframes (default: 'extracted_keyframes')."
    )
    
    # Optional argument for the threshold
    parser.add_argument(
        "-t", "--threshold",
        type=int,
        default=35,
        help="Integer threshold for scene change detection (default: 35). Higher is less sensitive."
    )
    
    # Parse the arguments from the command line
    args = parser.parse_args()
    
    # Call the main function with the parsed arguments
    extract_keyframes(
        video_path=args.input_video,
        output_folder=args.output_folder,
        threshold=args.threshold
    )