import cv2
import time
from pathlib import Path
from collections import deque, Counter
from config import CONFIG
from watcher.inference.alpr import ALPRENGINE
from watcher.models.plateinfo import plateInfo
from watcher.utils.platequeue import plateQueue

from PyQt6.QtCore import QThread, pyqtSignal

class BowserWatchWorker(QThread):
    plate_detected = pyqtSignal(object)
    alert_triggered = pyqtSignal(dict)

    def __init__(self,mongo, parent=None):
        super().__init__(parent)
        self.running = True
        self.mongo = mongo

    def run(self):
        self.__process_video()
        
    def __process_video(self, video_path: Path = Path('watcher/data/test1.mp4'), poll_every_frames: int = 40):
            capture = cv2.VideoCapture(video_path)
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
            plate_queue = plateQueue(keep_time=10.0) 
            detected_plates: list[plateInfo] = []
            try:
                while self.running:
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
                            detected_plates.append(plateInfo(plate=plate, confidence=confidence, timestamp=timestamp, frame=frame.copy()))
                            if frame_count % poll_every_frames == 0:                         
                                best_detection = self._poll_plates(detected_plates)                               
                                best_detection.image = self._save_image(best_detection, plate_queue)  
                                best_detection.frame = None  # Clear the frame to save memory
                                plate_queue.add(best_detection)
                                watchlist_entry = self._has_watchlist_entry(best_detection.plate)
                                #print(f"Detected plate: {most_common_plates[0][0]} with count: {most_common_plates[0][1]}")
                                detected_plates.clear()
                            if watchlist_entry:
                                self.alert_triggered.emit(watchlist_entry)    
                            self.plate_detected.emit(plate_queue)

                    frame_count += 1   
            except Exception as e:
                print(f"Error during video processing: {e}")
            finally:
                capture.release()

    def _poll_plates(self,detected_plates: list[plateInfo]):
        plate_counts = Counter(plate.plate for plate in detected_plates)
        most_common_plates = plate_counts.most_common(1)
        common_plates = [plate for plate in detected_plates if plate.plate == most_common_plates[0][0]]
        return max(common_plates, key=lambda x: x.confidence)  

    def _save_image(self, best_detection: plateInfo, plate_queue: plateQueue):
        output_filename = f"watcher/output/most_common_{best_detection.plate}_{best_detection.timestamp:.1f}s.jpg"
        if plate_queue.contains(best_detection.plate) is False: 
            print(best_detection.frame.shape)
            cv2.imwrite(output_filename, best_detection.frame)
            print(f"Saved image for plate: {best_detection.plate} at {output_filename}")
            return output_filename
        else:
            return None

    def _has_watchlist_entry(self, plate: str):
            return self.mongo.check_watchlist(plate)

    def stop(self):
            self.running = False
            self.wait()
    