# Python OpenCV Motion Detection

import picamera
import argparse
import datetime
import numpy as np
import os
import cv2 as cv
import imutils
from imutils.video import VideoStream
import threading
import time
import logging
from threading import Event, Thread

# CONSTANTS
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
RESOLUTION = str(FRAME_WIDTH) + "x" + str(FRAME_HEIGHT)
HIGH_RES = "1080x720"
FRAMERATE = 30
GAUSS_BLUR_REGION = (25, 25)
MIN_AREA = 450
KERNEL = np.ones((15, 15), np.uint8)
FRAME_RESET = 0.5 #seconds
MOTION_TIMEOUT = 10 #seconds
DEFAULT_VID_NAME = "motion_video.avi"

first_frame_blurred = None
motion_detected = False
motion_detected_event = Event()
no_motion_detected_event = Event()

class Resource:
    """
    Variables shared between multiple threads. Uses a simple locking
    mechanism to avoid data loss or corruption.
    """
    def __init__(self, value):
        self.lock = threading.Lock()
        self.value = value
        
    def change_value(self, new_value):
        self.lock.acquire()
        try:
            self.value = new_value
        finally:
            self.lock.release()
            
    def get_value(self):
        self.lock.acquire()
        try:
            return self.value
        finally:
            self.lock.release()
        

def save_file(current_name, extension):
    """
    Rename file using the date and time, and move to the motion folder
    """
    if (not os.path.isdir("motion")):
        os.mkdir("motion")
    date_time = datetime.datetime.now().strftime("%d-%m-%Y_%H%M%S")
    os.rename(current_name, "motion/" + date_time + extension)
    return 0

def get_date_time():
    return datetime.datetime.now().strftime("%d-%m-%Y_%H:%M:%S")

def record_motion():
    while True:
        # Wait for motion to be detected
        motion_detected_event.wait()
        print("check_motion: motion")
        # Make directory ./motion
        if (not os.path.isdir("motion")):
            os.mkdir("motion")
        # Begin recording motion event
        motion_video_name = "./motion/" + get_date_time() + ".h264"
        camera.start_recording(motion_video_name, splitter_port=2, resize=HIGH_RES)
        print("check_motion: recording start")
        # Wait for no more motion to stop recording
        no_motion_detected_event.wait()
        print("check_motion: no motion")
        camera.stop_recording(splitter_port=2)
        print("check_motion: recording stop")
        # Clear events
        motion_detected_event.clear()
        no_motion_detected_event.clear()
        

def detect_motion():
    time.sleep(0.4)
    camera.capture("first.jpg", use_video_port=True, splitter_port=1)
    first_frame= cv.imread("first.jpg", cv.IMREAD_GRAYSCALE);
    first_frame_blurred = cv.GaussianBlur(first_frame, GAUSS_BLUR_REGION, 0)
    print("First frame taken")
    
    # Initialize variables
    init_frame_begin = time.time()
    motion_timeout_begin = 0
    motion_status_text = "NO MOTION"
    is_recording_motion = False

    while (not exit_flag.get_value()):
        # Reset motion
        motion_detected = False
        # Get new capture 
        camera.capture("capture.jpg", use_video_port=True, splitter_port=1)
        frame_colour = cv.imread("capture.jpg", cv.IMREAD_COLOR)
        frame_gray = cv.cvtColor(frame_colour, cv.COLOR_BGR2GRAY) # Grayscale
        frame_blurred = cv.GaussianBlur(frame_gray, GAUSS_BLUR_REGION, 0) # Apply blur

        # Get image delta between first and current frame
        delta_frame = cv.absdiff(first_frame_blurred, frame_blurred)
        # Filter delta image through a threshold
        threshold_frame = cv.threshold(delta_frame, 30, 255, cv.THRESH_BINARY)[1]
        # Dilate image delta 
        dilated_frame = cv.dilate(threshold_frame, KERNEL, iterations=3)
        # Find contour around the difference
        contours = cv.findContours(dilated_frame.copy(), cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)

        # Check contours
        if contours == None:
            motion_detected = False
        else:
            for contour in contours:
                # Check if contour is negligible
                if (cv.contourArea(contour) >= MIN_AREA):
                    # Get box size around contour
                    (x, y, w, h) = cv.boundingRect(contour)
                    cv.rectangle(frame_colour, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    motion_detected = True

        # Check motion status
        if (motion_detected):
            motion_status_text = "CHANGE DETECTED"
            motion_detected_event.set()
            motion_timeout_begin = time.time()
            # Start recording if not already
            if (not is_recording_motion):
                is_recording_motion = True
        # Stop recording if no motion and timeout has been reached
        elif (is_recording_motion and (time.time() - motion_timeout_begin) >= MOTION_TIMEOUT):
            motion_status_text = "NO CHANGE"
            no_motion_detected_event.set()
            is_recording_motion = False
        else:
            motion_status_text = "NO CHANGE"

        # Read from keyboard
        key = cv.waitKey(3)
        # Break if "q" pressed
        if (key == ord("q")):
            break
            
        # Reset first frame after a certain period
        time_now = time.time()
        if (time_now - init_frame_begin >= FRAME_RESET):
            init_frame_begin = time_now
            first_frame_blurred = frame_blurred
            
    print("end detect motion")
    return 0
    
def exit_on_q():
    while True:
        user_input = input()
        if (user_input == "q"):
            exit_flag.change_value(True)
            break
    print("Exiting")
    return 0
            

# ===== START =====
if __name__ == "__main__":
    exit_flag = Resource(False)    
    with picamera.PiCamera(resolution = RESOLUTION, framerate = FRAMERATE) as camera:
        # Start threads
        thread_motion = threading.Thread(target=detect_motion, args=())
        thread_record = threading.Thread(target=record_motion, args=(), daemon=True) # Daemon thread, killed on main exit
        thread_exit = threading.Thread(target=exit_on_q, args=())

        thread_motion.start()
        thread_exit.start()
        thread_record.start()

        thread_exit.join()
        thread_motion.join()
    exit()



                



