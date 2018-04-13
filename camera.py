# -*- coding: utf-8 -*-
"""
Created on Thu Mar  1 15:12:46 2018

@author: ddo003
"""

from multiprocessing import Process, Queue
from threading import Thread
import cv2
import time, sys
import numpy as np




class Camera:
    
    def __init__(self, camera: object = 0, framerate: object = 30, shape: object = (7680, 4320), gamma: object = 1, brightness: object = 0,
                 exposure: object = -5.0) -> object:
        """

        :param camera: Which connected camera to use.
        :param framerate:
        :param shape:
        :param gamma:
        :param brightness:
        :param exposure: negative values, get evaluates  as 2**param_val by camera.
        """
        self.camera = camera
        self.cap = cv2.VideoCapture(self.camera)
        self.alive = False
        self.framerate = framerate
        self.shape = shape
        
        self.brightness = self.cap.get(cv2.CAP_PROP_BRIGHTNESS)
        self.aperture = self.cap.get(cv2.CAP_PROP_APERTURE)
        self.gamma = gamma
        self.brightness = brightness
        self.exposure  = exposure
        
    
    @property
    def framerate(self):
        return self._framerate
    
    @framerate.setter
    def framerate(self, framerate):
        self._framerate = framerate
        self.cap.set(cv2.CAP_PROP_FPS, framerate)
        if framerate > 50:
            self.do_gamma = False
            print("\n Can not do calculations for gamma at framerates over 50 fps. Calculate corrected gamma on video later\n")
        else:
            self.do_gamma = True
        # print('Framerate set to: ' + str(framerate))
        
    @property
    def shape(self):
        return self._shape
    
    @shape.setter
    def shape(self, shape):
        self._shape = shape
        w, h = shape
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        # print("Video shape set to : ", w, h)
        
    @property
    def brightness(self):
        return self._brightness
    
    @brightness.setter
    def brightness(self, brightness):
        self._brightness = brightness
        self.cap.set(cv2.CAP_PROP_BRIGHTNESS, brightness)
    
    @property
    def exposure(self):
        return self._exposure
    
    @exposure.setter
    def exposure(self, exposure):
        self._exposure = exposure
        self.cap.set(cv2.CAP_PROP_EXPOSURE, exposure)
    
    
    def reconnect(self):
        self.cap.release()
        self.cap = cv2.VideoCapture(self.camera)
        
    def read(self):

        ret = False
        while ret == False:
            ret, frame = self.cap.read()

        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    def preview(self):
        p = Thread(target=self.start_preview, args = ())
        p.start()
    
    def video(self, name, duration):
        p = Thread(target=self.write_video, args = (name, duration,))
        p.start()
     
        
    def gamma_correction(self, img, correction):
        img = img/255.0
        img = cv2.pow(img, correction)
        return np.uint8(img*255)
    
    def start_preview(self):
        print("Preview Starting")

#        cap.set(cv2.CAP_PROP_FPS, self.framerate)
        self.alive = True
        
        frames = 0
        start_time = time.time()
        while self.alive == True:
             
            
            ret, frame = self.cap.read()
            
            if ret == True:
                                                   
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if self.do_gamma == True:
                    frame = self.gamma_correction(frame, self.gamma)
                cv2.imshow('preview',frame)
            
            frames += 1
            if frames == 10:
                end_time = time.time()
                total_time = (end_time - start_time)
                fps = frames / total_time              
                sys.stdout.write("\r fps = "+str(fps)+" time for 10 frames: "+str(total_time))
                frames = 0
                start_time = time.time()
          
        else:
            self.alive = False
            cv2.destroyWindow("preview")
#            cv2.destroyAllWindows()                  
        
    def write_video(self, name = "out", duration = 60):
        
        
        w=int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH ))
        h=int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT ))        
        framerate = self.framerate
        
        savepath  = name+".avi"
    
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(savepath,fourcc, framerate, (w,h), isColor = False)
                         
        
        start_time = time.time()
        end_time = start_time
        self.alive = True
        fc = 0
        while (end_time - start_time) < duration and self.alive == True:
             
            
            ret, frame = self.cap.read()
            
            if ret == True:
                                                   
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                if self.do_gamma == True:
                    frame = self.gamma_correction(frame, self.gamma)
                out.write(frame)
                fc +=1
                # cv2.imshow('Recording',frame)
            
            end_time = time.time()
            sys.stdout.write("\r Recording! "+str(np.round((end_time-start_time),2))+"/"+str(duration)+" seconds       ")
       
        else:
            sys.stdout.write("\n Recording Complete! Saved as "+name + "Framecount: "+str(fc))
            
            # cv2.destroyWindow("Recording")
            out.release()
            self.alive = False
    
    def stop(self):
        self.alive = False

        
        
            