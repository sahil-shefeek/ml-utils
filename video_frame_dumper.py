import cv2
import os
import sys
import argparse
import time
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

def extract_frames_with_faces(video_path, similarity_threshold=0.95, draw_rectangles=True):
    """
    Extract frames with faces from a video while reducing duplicates.
    
    Args:
        video_path: Path to the video file
        similarity_threshold: Threshold for determining duplicate frames (0-1)
        draw_rectangles: Whether to draw rectangles around detected faces
        
    Returns:
        Number of frames extracted
    """
    print(f"Starting processing of video: {video_path}")
    print(f"Similarity threshold: {similarity_threshold}")
    print(f"Face rectangles: {'enabled' if draw_rectangles else 'disabled'}")
    
    # Check if the video file exists
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    # Get video filename without extension for output directory
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = os.path.join(os.getcwd(), "outputs", video_name)
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Load face detector
    try:
        print("Loading face detection model...")
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        if face_cascade.empty():
            raise ValueError("Failed to load face cascade classifier")
        print("Face detection model loaded successfully")
    except Exception as e:
        raise RuntimeError(f"Failed to load face detector: {str(e)}")
    
    # Open the video
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {video_path}")
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print("Video properties:")
        print(f"  - Dimensions: {frame_width}x{frame_height}")
        print(f"  - FPS: {fps:.2f}")
        print(f"  - Total frames: {total_frames}")
    except Exception as e:
        raise RuntimeError(f"Error opening video: {str(e)}")
    
    frame_count = 0
    processed_count = 0
    saved_count = 0
    prev_frame = None
    start_time = datetime.now()
    last_log_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break  # End of video
            
            frame_count += 1
            
            # Log progress periodically
            current_time = time.time()
            if current_time - last_log_time > 5:  # Log every 5 seconds
                elapsed = (datetime.now() - start_time).total_seconds()
                percent_done = (frame_count / total_frames * 100) if total_frames > 0 else 0
                print(f"Progress: {frame_count}/{total_frames} frames ({percent_done:.1f}%, {elapsed:.1f} seconds)")
                last_log_time = current_time
            
            # Process every 3rd frame for efficiency (adjust as needed)
            if frame_count % 3 != 0:
                continue
            
            processed_count += 1
            
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
            
            # Log face detection
            if len(faces) > 0 and frame_count % 30 == 0:
                print(f"Frame {frame_count}: Detected {len(faces)} faces")
            
            # Check if this frame is too similar to the previous saved frame
            if prev_frame is not None:
                try:
                    similarity = calculate_similarity(frame, prev_frame)
                    if similarity > similarity_threshold:
                        continue
                except Exception as e:
                    print(f"Warning: Failed to calculate similarity for frame {frame_count}: {str(e)}")
            
            # If we reach here, save the frame
            prev_frame = frame.copy()
            frame_filename = os.path.join(output_dir, f"frame_{frame_count:05d}_{len(faces)}_faces.jpg")
            
            # Draw rectangles around faces if enabled
            save_frame = frame.copy()
            if draw_rectangles:
                for (x, y, w, h) in faces:
                    cv2.rectangle(save_frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
            
            try:
                cv2.imwrite(frame_filename, save_frame)
                saved_count += 1
                
                # More detailed logging for saved frames
                if saved_count % 10 == 0:
                    elapsed = (datetime.now() - start_time).total_seconds()
                    print(f"Processed {frame_count} frames, saved {saved_count} with faces ({elapsed:.1f} seconds)")
            except Exception as e:
                print(f"Warning: Failed to save frame {frame_count}: {str(e)}")
    
    except KeyboardInterrupt:
        print("\nProcess interrupted by user")
    except Exception as e:
        print(f"Error processing video: {str(e)}")
    finally:
        # Release resources
        cap.release()
        
    elapsed = (datetime.now() - start_time).total_seconds()
    print(f"\nFinished processing {video_path}")
    print(f"Total frames in video: {total_frames}")
    print(f"Frames processed: {processed_count} (every 3rd frame)")
    print(f"Frames with faces saved: {saved_count}")
    print(f"Processing time: {elapsed:.1f} seconds")
    print(f"Output directory: {output_dir}")
    
    return saved_count

def main():
    parser = argparse.ArgumentParser(description='Extract frames with faces from a video.')
    parser.add_argument('video_path', help='Path to the video file')
    parser.add_argument('--similarity', type=float, default=0.95, 
                        help='Similarity threshold (0-1) for duplicate detection')
    parser.add_argument('--no-rectangles', action='store_true',
                        help='Disable drawing rectangles around detected faces')
    
    args = parser.parse_args()
    
    try:
        extract_frames_with_faces(args.video_path, args.similarity, not args.no_rectangles)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
