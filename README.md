# ML Utils

A collection of machine learning utilities for various tasks.

## Video Frame Dumper

A Python utility to extract frames from videos, detect faces, and reduce duplicate frames.

### Features
- Face detection in video frames
- Duplicate frame reduction using structural similarity
- Configurable similarity threshold
- Option to draw face detection rectangles
- Error handling for robust operation

### Requirements
- Python 3.6+
- OpenCV (cv2)
- NumPy
- scikit-image

### Setup Guide for Beginners

#### 1. Install Python

If you don't have Python installed:
- **Windows**: Download and install from [python.org](https://www.python.org/downloads/). During installation, make sure to check "Add Python to PATH".
- **macOS**: 
  - Using Homebrew: `brew install python`
  - Or download from [python.org](https://www.python.org/downloads/)
- **Linux**: Use your package manager, e.g., `sudo apt install python3 python3-pip` for Ubuntu/Debian

#### 2. Set up a virtual environment (recommended)

A virtual environment keeps your dependencies isolated from other projects.

Open a terminal/command prompt and navigate to the project directory:

```bash
cd /path/to/ml-utils
```

Create a virtual environment:
```bash
# Windows
python -m venv venv

# macOS/Linux
python3 -m venv venv
```

Activate the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

When activated, you'll see `(venv)` at the beginning of your terminal prompt.

#### 3. Install required packages

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

This might take a few minutes to download and install all the dependencies.

### How to Use the Video Frame Dumper

#### Basic Usage

1. Make sure your virtual environment is activated (see above)

2. Run the script with a video file:
   ```bash
   python video_frame_dumper.py /path/to/your/video.mp4
   ```

   Replace `/path/to/your/video.mp4` with the actual path to your video file.

3. The script will create an `output` directory in the current folder, with a subdirectory named after your video file, containing the extracted frames.

#### Command-line Options

- `--similarity THRESHOLD`: 
  - Adjusts how the script determines duplicate frames
  - Value range: 0.0 to 1.0
  - Default: 0.95
  - Lower values mean stricter duplicate detection
  - Example: `--similarity 0.85`

- `--no-rectangles`: 
  - Disables drawing blue rectangles around detected faces
  - Example: `--no-rectangles`

#### Example Commands

Process a video with default settings:
```bash
python video_frame_dumper.py my_video.mp4
```

Process a video with fewer duplicates allowed:
```bash
python video_frame_dumper.py my_video.mp4 --similarity 0.85
```

Process a video without drawing rectangles around faces:
```bash
python video_frame_dumper.py my_video.mp4 --no-rectangles
```

Combine multiple options:
```bash
python video_frame_dumper.py my_video.mp4 --similarity 0.90 --no-rectangles
```

### Understanding the Output

- All frames will be saved in `output/[video_name]/` directory
- Each image is named: `frame_XXXXX_N_faces.jpg`
  - `XXXXX`: The frame number in the video
  - `N`: The number of faces detected in that frame
- Only frames containing faces are extracted
- Similar consecutive frames are skipped to reduce duplicates

### Troubleshooting

1. **"Module not found" errors**:
   - Make sure you've activated the virtual environment
   - Verify that you've installed all requirements with `pip install -r requirements.txt`

2. **"Video file not found" error**:
   - Double-check the path to your video file
   - Try using an absolute path instead of a relative path

3. **No frames extracted**:
   - The video might not contain detectable faces
   - Try adjusting the similarity threshold: `--similarity 0.8`
