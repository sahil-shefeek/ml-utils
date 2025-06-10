import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import cv2
import numpy as np
import os
import threading
from queue import Queue, Empty

# --- Core Extraction Logic (Modified for GUI Integration) ---

def extract_keyframes_worker(video_path, output_folder, threshold, status_queue):
    """
    This function runs in a separate thread to extract keyframes without freezing the GUI.
    It communicates its progress and status back to the main thread via a queue.
    """
    try:
        # --- 1. Setup ---
        status_queue.put(f"INFO: Starting extraction for: {video_path}")
        status_queue.put(f"INFO: Difference threshold set to: {threshold}")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Input video file not found at '{video_path}'")

        video_capture = cv2.VideoCapture(video_path)
        if not video_capture.isOpened():
            raise IOError("Could not open video file. Check path or video format/codecs.")

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)
            status_queue.put(f"INFO: Created output folder: {output_folder}")

        # --- 2. Initialization ---
        success, prev_frame = video_capture.read()
        if not success:
            raise IOError("Could not read the first frame from the video.")

        prev_frame_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        first_frame_path = os.path.join(output_folder, "keyframe_00000001.jpg")
        cv2.imwrite(first_frame_path, prev_frame)
        
        frame_count = 1
        keyframe_count = 1
        total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))

        # --- 3. Main Loop ---
        while success:
            success, current_frame = video_capture.read()
            if not success:
                break

            frame_count += 1
            
            # Update progress
            progress_percent = (frame_count / total_frames) * 100
            status_queue.put(f"PROGRESS:{progress_percent}")

            current_frame_gray = cv2.cvtColor(current_frame, cv2.COLOR_BGR2GRAY)
            frame_diff = cv2.absdiff(current_frame_gray, prev_frame_gray)
            mean_diff = np.mean(frame_diff)

            if mean_diff > threshold:
                keyframe_count += 1
                filename = f"keyframe_{keyframe_count:08d}.jpg"
                output_path = os.path.join(output_folder, filename)
                cv2.imwrite(output_path, current_frame)
                prev_frame_gray = current_frame_gray

        # --- 4. Final Status ---
        status_queue.put("\n------------------------------------")
        status_queue.put("INFO: Keyframe extraction complete.")
        status_queue.put(f"INFO: Total frames processed: {frame_count}")
        status_queue.put(f"INFO: Total keyframes extracted: {keyframe_count}")
        status_queue.put(f"INFO: Keyframes saved in: '{output_folder}'")
        status_queue.put("------------------------------------")

    except (FileNotFoundError, IOError, Exception) as e:
        status_queue.put(f"ERROR: {str(e)}")
    finally:
        if 'video_capture' in locals() and video_capture.isOpened():
            video_capture.release()
        status_queue.put("DONE") # Signal that the process is finished

# --- Tkinter GUI Application Class ---

class KeyframeExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Keyframe Extractor")
        self.root.geometry("600x550")
        self.root.minsize(550, 500)

        # Style
        self.style = ttk.Style(self.root)
        self.style.theme_use("clam")

        # Frame for input widgets
        self.frame = ttk.Frame(self.root, padding="10")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # --- Variables ---
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.threshold_var = tk.StringVar(value="35")
        self.status_queue = Queue()

        # --- UI Widgets ---
        self.create_widgets()

        # Start the queue processor
        self.process_queue()

    def create_widgets(self):
        # Configure grid layout
        self.frame.columnconfigure(1, weight=1)

        # Input Video Path
        ttk.Label(self.frame, text="Input Video:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.input_entry = ttk.Entry(self.frame, textvariable=self.input_path)
        self.input_entry.grid(row=0, column=1, sticky=tk.EW, padx=5, pady=5)
        self.browse_input_button = ttk.Button(self.frame, text="Browse...", command=self.select_input_file)
        self.browse_input_button.grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)

        # Output Folder Path
        ttk.Label(self.frame, text="Output Folder:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.output_entry = ttk.Entry(self.frame, textvariable=self.output_path)
        self.output_entry.grid(row=1, column=1, sticky=tk.EW, padx=5, pady=5)
        self.browse_output_button = ttk.Button(self.frame, text="Browse...", command=self.select_output_folder)
        self.browse_output_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)

        # Threshold
        ttk.Label(self.frame, text="Difference Threshold:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.threshold_entry = ttk.Entry(self.frame, textvariable=self.threshold_var, width=10)
        self.threshold_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Extract Button
        self.extract_button = ttk.Button(self.frame, text="Extract Keyframes", command=self.start_extraction_thread)
        self.extract_button.grid(row=3, column=0, columnspan=3, pady=15)

        # Progress Bar
        self.progress_bar = ttk.Progressbar(self.frame, orient="horizontal", length=100, mode="determinate")
        self.progress_bar.grid(row=4, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=5)

        # Status Area
        ttk.Label(self.frame, text="Status & Log:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.status_text = tk.Text(self.frame, height=10, bg="#f0f0f0", relief="solid", borderwidth=1, wrap=tk.WORD)
        self.status_text.grid(row=6, column=0, columnspan=3, sticky=tk.NSEW, padx=5, pady=5)
        self.frame.rowconfigure(6, weight=1) # Make the text area expandable

        # Configure tag for error messages
        self.status_text.tag_config("error", foreground="red", font=("TkDefaultFont", 9, "bold"))
        self.status_text.tag_config("info", foreground="blue")
        self.status_text.config(state=tk.DISABLED)

    def select_input_file(self):
        file_path = filedialog.askopenfilename(
            title="Select a Video File",
            filetypes=(("Video Files", "*.mp4 *.mkv *.webm *.avi"), ("All files", "*.*"))
        )
        if file_path:
            self.input_path.set(file_path)

    def select_output_folder(self):
        folder_path = filedialog.askdirectory(title="Select Output Folder")
        if folder_path:
            self.output_path.set(folder_path)

    def start_extraction_thread(self):
        # --- Input Validation ---
        video_path = self.input_path.get()
        output_folder = self.output_path.get()
        try:
            threshold = int(self.threshold_var.get())
            if threshold <= 0: raise ValueError("Threshold must be positive.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Threshold must be a positive integer.")
            return

        if not video_path:
            messagebox.showerror("Invalid Input", "Please select an input video file.")
            return
        if not output_folder:
            messagebox.showerror("Invalid Input", "Please select an output folder.")
            return

        # Clear previous status and disable button
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete('1.0', tk.END)
        self.status_text.config(state=tk.DISABLED)
        self.progress_bar["value"] = 0
        self.extract_button.config(state=tk.DISABLED)

        # --- Start the worker thread ---
        self.thread = threading.Thread(
            target=extract_keyframes_worker,
            args=(video_path, output_folder, threshold, self.status_queue)
        )
        self.thread.daemon = True # Allows main window to exit even if thread is running
        self.thread.start()

    def process_queue(self):
        """ Checks the queue for messages from the worker thread and updates the GUI. """
        try:
            while True:
                msg = self.status_queue.get_nowait()
                self.status_text.config(state=tk.NORMAL)

                if msg.startswith("PROGRESS:"):
                    progress = float(msg.split(":")[1])
                    self.progress_bar["value"] = progress
                elif msg.startswith("ERROR:"):
                    self.status_text.insert(tk.END, msg + "\n", "error")
                elif msg.startswith("INFO:"):
                    self.status_text.insert(tk.END, msg + "\n", "info")
                elif msg == "DONE":
                    self.extract_button.config(state=tk.NORMAL)
                else:
                    self.status_text.insert(tk.END, msg + "\n")
                
                # Scroll to the end
                self.status_text.see(tk.END)
                self.status_text.config(state=tk.DISABLED)

        except Empty:
            pass # No messages in the queue
        
        # Schedule this function to run again after 100ms
        self.root.after(100, self.process_queue)


if __name__ == '__main__':
    root = tk.Tk()
    app = KeyframeExtractorApp(root)
    root.mainloop()