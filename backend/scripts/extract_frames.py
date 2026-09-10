import os # Import os module to manage directory creations and file iterations.
import cv2 # Import OpenCV library for reading videos and extracting frames.

def extract_frames(root_folder: str = "videos") -> None: # Define frame extraction function with root videos folder parameter.
    real_videos_dir = os.path.join(root_folder, "real") # Build path to directory containing authentic videos.
    fake_videos_dir = os.path.join(root_folder, "fake") # Build path to directory containing manipulated videos.
    
    for category, videos_dir in [("real", real_videos_dir), ("fake", fake_videos_dir)]: # Loop over real and fake video categories.
        if not os.path.exists(videos_dir): # Skip if the source video directory does not exist on disk.
            continue # Continue to next category loop iteration.
            
        output_dir = os.path.join("frames", category) # Build output directory path mirroring category under frames folder.
        os.makedirs(output_dir, exist_ok=True) # Create output directory if it does not already exist.
        
        video_files = [f for f in os.listdir(videos_dir) if f.lower().endswith(".mp4")] # List all files ending in .mp4 in category folder.
        total_files = len(video_files) # Get the count of total video files.
        print(f"Found {total_files} videos in {category} folder. Starting extraction...") # Print initial extraction status.
        
        for idx, file in enumerate(video_files): # Iterate over mp4 files with index.
            video_path = os.path.join(videos_dir, file) # Construct full path to current video.
            cap = cv2.VideoCapture(video_path) # Open the video file using OpenCV Capture.
            if not cap.isOpened(): # Check if video file could not be opened.
                print(f"Error opening video: {video_path}") # Print error message for current video.
                continue # Skip to next video file.
                
            frame_count = 0 # Initialize video frame counter.
            saved_count = 0 # Initialize saved frames counter.
            
            while True: # Loop through frames of current video file.
                ret, frame = cap.read() # Read next frame from video capture.
                if not ret: # Break loop if frame could not be read or video ended.
                    break # Terminate loop.
                    
                if frame_count % 10 == 0: # Check if current frame index is multiple of 10.
                    output_file_name = f"{os.path.splitext(file)[0]}_frame_{frame_count}.jpg" # Construct output image filename.
                    output_path = os.path.join(output_dir, output_file_name) # Construct full output filepath.
                    cv2.imwrite(output_path, frame) # Write the extracted frame to disk using OpenCV.
                    saved_count += 1 # Increment saved frame counter.
                    
                frame_count += 1 # Increment total frame counter.
                
            cap.release() # Release OpenCV video capture resources.
            print(f"[{idx+1}/{total_files}] Extracted {saved_count} frames from {file}") # Print extraction progress for current video.

if __name__ == "__main__": # Run when executing script directly.
    extract_frames() # Invoke the frame extraction function.
