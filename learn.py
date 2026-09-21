import cv2
import time
from pathlib import Path
from collections import deque, Counter
from config import CONFIG
from watcher.inference.alpr import ALPRENGINE
from watcher.models.plateinfo import PlateInfo
from watcher.utils.platequeue import PlateQueue

def process():
    capture = cv2.VideoCapture(Path('test1.mp4'))
    if not capture.isOpened():
        raise Exception("Could not open video file")
    fps = capture.get(cv2.CAP_PROP_FPS) or 25
    frame_width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))

    pre_frame = max(1, int(fps * 2.5))  # 2.5 seconds
    post_frame = max(1, int(fps * 2.5))  # 2.5 seconds
    frames_buffer : deque = deque(maxlen=pre_frame)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    frame_count = 0
    engine = ALPRENGINE()
    plate_queue = PlateQueue(keep_time=30.0) 
    detected_plates: list[PlateInfo] = []
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frames_buffer.append(frame)
            if frame_count % 10 == 0: #samples every 10 frames
                timestamp = frame_count / fps
                for result in engine.detect(frame):
                    ocr = result.ocr
                    confidence = ocr.confidence
                    if isinstance(confidence, (list, tuple)):
                        confidence = sum(confidence) / len(confidence)
                    if not ocr.text or confidence < 0.99:
                        continue
                    plate = engine.normalise_plate(str(ocr.text))
                    if plate is None:
                            continue
                    detected_plates.append(PlateInfo(plate=plate, confidence=confidence, timestamp=timestamp, frame=frame.copy()))
                    if frame_count % 40 == 0:
                        plate_counts = Counter(plate.plate for plate in detected_plates)
                        most_common_plates = plate_counts.most_common(1)
                        common_plates = [plate for plate in detected_plates if plate.plate == most_common_plates[0][0]]
                        best_detection = max(common_plates, key=lambda x: x.confidence)
                        output_filename = f"output/most_common_{best_detection.plate}_{best_detection.timestamp:.1f}s.jpg"
                        if plate_queue.contains(best_detection.plate) is False: cv2.imwrite(output_filename, best_detection.frame)
                        best_detection.image = output_filename
                        best_detection.frame = None  # Clear the frame to save memory
                        plate_queue.add(best_detection)
                        #print(f"Detected plate: {most_common_plates[0][0]} with count: {most_common_plates[0][1]}")
                        detected_plates.clear()
                    print(f"plates in queue: {[plate.plate for plate in plate_queue.get_all()]}")
            frame_count += 1   
    except Exception as e:
        print(f"Error during video processing: {e}")
    finally:
        capture.release()


