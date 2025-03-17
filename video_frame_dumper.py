#!/usr/bin/env python3

import cv2
import numpy as np
import os
import sys
import argparse
from skimage.metrics import structural_similarity as ssim
from datetime import datetime

def calculate_similarity(img1, img2):
    """Calculate structural similarity between two images."""
    # Convert to grayscale
    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
    
    # Resize images if they have different dimensions
    if gray1.shape != gray2.shape:
        width = min(gray1.shape[1], gray2.shape[1])
        height = min(gray1.shape[0], gray2.shape[0])
        gray1 = cv2.resize(gray1, (width, height))
        gray2 = cv2.resize(gray2, (width, height))
    
    # Calculate SSIM
    score, _ = ssim(gray1, gray2, full=True)
    return score

def extract_frames_with_faces(video_path, similarity_threshold=0.95):
    """
    Extract frames with faces from a video while reducing duplicates.
    
    Args:
        video_path: Path to the video file
        similarity_threshold: Threshold for determining duplicate frames (0-1)
        
    Returns:
        Number of frames extracted
    """
    # Check if the video file exists
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Get video filename without extension for output directory
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(os.getcwd(), video_name)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Load face detector
    try:
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            raise ValueError("Failed to load face cascade classifier")
    except Exception as e:
        raise RuntimeError(f"Failed to load face detector: {str(e)}")
    
    # Open the video
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
    except Exception as e:
        raise RuntimeError(f"Error opening video: {str(e)}")
    
    frame_count = 0
    saved_count = 0
    prev_frame = None
    start_time = datetime.now()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # End of video
            
            frame_count += 1
            
            # Process every 3rd frame for efficiency (adjust as needed)
            if frame_count % 3 != 0:
                continue
            
            # Detect faces
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(
                    gray, 
                    scaleFactor=1.1, 
                    minNeighbors=5, 
                    minSize=(30, 30)
                )
            except Exception as e:
                print(f"Warning: Failed to detect faces in frame {frame_count}: {str(e)}")
                continue
            
            # If no faces found, skip this frame
            if len(faces) == 0:
                continue
            
            # Check if this frame is too similar to the previous saved frame
            if prev_frame is not None:
                try:
                    if calculate_similarity(frame, prev_frame) > similarity_threshold:
                        continue
                except Exception as e:
                    print(f"Warning: Failed to calculate similarity for frame {frame_count}: {str(e)}")
            
            # If we reach here, save the frame
            prev_frame = frame.copy()
            frame_filename = os.path.join(output_dir, f"frame_{frame_count:05d}_{len(faces)}_faces.jpg")
            
            # Draw rectangles around faces
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            try:
                cv2.imwrite(frame_filename, frame)
                saved_count += 1
            except Exception as e:
                print(f"Warning: Failed to save frame {frame_count}: {str(e)}")
            
            # Print progress every 20 saved frames
            if saved_count % 20 == 0:
                elapsed = (datetime.now() - start_time).total_seconds()
                print(f"Processed {frame_count} frames, saved {saved_count} with faces ({elapsed:.1f} seconds)")
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error processing video: {str(e)}")
    finally:
        # Release resources
        cap.release()
        
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\nFinished processing {video_path}")
    print(f"Total frames processed: {frame_count}")
    print(f"Frames with faces saved: {saved_count}")
    print(f"Processing time: {elapsed:.1f} seconds")
    print(f"Output directory: {output_dir}")
    
    return saved_count

def main():
    parser = argparse.ArgumentParser(description='Extract frames with faces from a video.')
    parser.add_argument('video_path', help='Path to the video file')
    parser.add_argument('--similarity', type=float, default=0.95, 
                        help='Similarity threshold (0-1) for duplicate detection')
    
    args = parser.parse_args()
    
    try:
        extract_frames_with_faces(args.video_path, args.similarity)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
