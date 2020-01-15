# Motion Detection Using OpenCV for Raspberry Pi
# Written by Serena He and Chris Keilbart

import picamera
import numpy as np
import io
import cv2 as cv
import matplotlib.pyplot as plt
import numexpr as ne
import datetime
import os
import time

EPSILON = 1600 # Sensitivity level
WIDTH = 640
HEIGHT = 480
RATE = 0.5 # Rate of motion analysis, in seconds
STOP_LENGTH = 6 # Minimum time without motion to stop recording , in seconds

# Returns formatted date and time (YYYY-MM-DD_HHMMSS)
def getDatetime():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")

# Motion detection - returns True if motion detected
def isMotion(img1, img2):
    delta = ne.evaluate("sum((img1-img2) ** 2)")
    delta = abs(delta/float(WIDTH*HEIGHT)) # RGB change value
    print("delta: " + str(delta))
    if (delta > EPSILON):
        return True
    else:
        return False

# Moves file with motion to movement file
def saveMotion(img):
    os.rename(img, "movement/" + getDatetime() + ".jpg")
    return 0

def detectMotion():
    camera.capture("test1.jpg", use_video_port=True)
    while True:
        time.sleep(0.3)
        camera.capture("test2.jpg", use_video_port=True)
        # Convert to numpy/numexpr readable images
        test1 = cv.imread("test1.jpg", 1)
        test2 = cv.imread("test2.jpg", 1)

        # MOTION DETECTED
        if (isMotion(test1, test2)):
            print("Motion detected.\n")
            # TODO: Draw redbox around movement
            
            saveMotion("test2.jpg") # Save initial motion detected image
            # Record video of movement in splitter_port2
            camera.start_recording("movement/" + getDatetime() + ".h264")
            camera.capture("test1.jpg", use_video_port=True)
            time1 = time.time() # Initialize time
            while True:
                camera.wait_recording(RATE)
                camera.capture("test2.jpg", use_video_port=True)
                test1 = cv.imread("test1.jpg", 1)
                test2 = cv.imread("test2.jpg", 1)
                # MOTION - keep recording
                if (isMotion(test1, test2)):
                    os.rename("test2.jpg", "test1.jpg")
                    time1 = time.time() # Reset time
                # NO MOTION - stop recording
                else:
                    os.rename("test2.jpg", "test1.jpg")
                    time2 = time.time()
                    if ((time2 - time1) >= STOP_LENGTH):
                        camera.stop_recording()
                        break               
        else:
            os.rename("test2.jpg", "test1.jpg")
            print("No motion.\n")
    return 0

# START - motion detection   
with picamera.PiCamera(resolution = "640x480", framerate = 30) as camera:
    
    detectMotion()
