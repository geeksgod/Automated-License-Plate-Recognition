import cv2
import multiprocessing
import time
from learn import process
from main import main
def video_playback_worker(video_path, frame_queue, run_flag):
    """
    Process 1: Responsible ONLY for reading and displaying the video smoothly.
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("Error: Could not open video.")
        run_flag.value = False
        return

    while cap.isOpened() and run_flag.value:
        ret, frame = cap.read()
        if not ret:
            print("Video ended.")
            break

    #     # Send frame to the processing process if the queue isn't backed up.
    #     # This keeps the video fluid even if processing drops behind.
    #     if not frame_queue.full():
    #         try:
    #             frame_queue.put_nowait(frame)
    #         except Exception:
    #             pass

        # Display the video frame instantly
        cv2.imshow("Smooth Video Stream (Multiprocessed)", frame)

    #     # Handle exit key
    #     if cv2.waitKey(25) & 0xFF == ord('q'):
    #         break

    # # Signal the other process to shut down cleanly
    # run_flag.value = False
    # cap.release()
    # cv2.destroyAllWindows()


def image_processing_worker(frame_queue, run_flag):
    """
    Process 2: Runs on a separate CPU core. Handles heavy computation (AI, OCR, MongoDB).
    """
    print("Processing worker started on a separate CPU core...")
    
    while run_flag.value:
        try:
            # Wait for a frame (times out after 1 second to check if run_flag changed)
            frame = frame_queue.get(timeout=1)
        except Exception:
            continue

        # --- INSERT YOUR HEAVY CODE HERE ---
        # Example: Simulating a heavy CPU task like OCR plate recognition or MongoDB lookups
        print(f"[Processing Process] Analyzing frame shape: {frame.shape}")
        time.sleep(0.1)  # Simulates a slow 100ms processing delay
        # ------------------------------------

    print("Processing worker stopped.")


# --- Main Process execution guard (CRITICAL for multiprocessing) ---
if __name__ == "__main__":
    video_source = "test.mp4" # Replace with your file or 0 for webcam

    # 1. Create a Shared Queue (maxsize=2 stops it from bloating RAM)
    # 2. Create a shared Boolean flag to coordinate clean shutdowns
    ctx = multiprocessing.get_context("spawn") # Use 'spawn' for stability across OS platforms
    mp_queue = ctx.Queue(maxsize=2)
    shared_run_flag = ctx.Value('b', True) # 'b' represents a boolean/byte flag

    # Set up the processing worker process
    proc_process = ctx.Process(
        target=process, 
        daemon=True
    )
    proc_process.start()

    # Run the video playback on the main desktop process
    # (OpenCV GUI windows MUST run on the main process/thread on most OS platforms)
    main()

    # Wait for the processing process to terminate cleanly
    proc_process.join()
    print("All processes closed cleanly.")
