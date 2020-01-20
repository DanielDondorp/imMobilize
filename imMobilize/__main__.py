# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 13:20:50 2018

@author: ddo003
"""

from Interface.form import *
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets
import pyqtgraph

pyqtgraph.setConfigOption("background", "w")
pyqtgraph.setConfigOption("foreground", "k")

from pyqtgraph import PlotDataItem, LinearRegionItem, mkPen


# from functools import partial
import numpy as np
from threading import Thread
from StimuliManager.StimuliManager import StimuliManager
from MicroControllerCode.Arduino import Arduino
#from camera import Camera
from CameraModule.ThreadedCam import Camera
from datetime import datetime
import sys, time, os
import pandas as pd
import cv2
import socket

### trying to optimise according to Kushals instructions:

try:
    cv2.setNumThreads(1)
except:
    print("OpenCV is naturally single threaded or so I heard...")


# from PandasModel import PandasModel

class imMobilize(QtWidgets.QWidget):

    def __init__(self, parent=None, *args):

        # run the widget, get the form
        QtWidgets.QWidget.__init__(self, parent, *args)

        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.hostname = socket.gethostname()
        try:
            os.chdir("D:\\")
        except:
            os.chdir(f"/home/{os.getlogin()}")
        self.working_directory_selected = False
        """
        ==============================================================
        Connecting the buttons and labels in the serial control group
        ==============================================================
        """

        self.arduino = Arduino()
        # populate serial available combobox
        self.update_serial_available()
        # connect scan button
        self.ui.buttonSerialScan.clicked.connect(self.update_serial_available)

        # connect connect/disconnect button
        self.ui.buttonSerialConnect.clicked.connect(self.serial_connect_disconnect)
        # try:
        #     self.serial_connect_disconnect()
        # except:
        #     QtWidgets.QMessageBox.warning(self, "No controller found", "Could not connect to a suitable controller \n Connect Manually.")

        self.ui.lineeditWriteToSerial.editingFinished.connect(self.write_to_serial)
        self.ui.buttonWriteToSerial.clicked.connect(self.write_to_serial)

        self.ui.checkBoxReadSerialLive.clicked.connect(self.listen_to_serial)

        self.logged_temperature = np.array([])
        self.temp_plot_xvals = np.array([])





        """
        =====================================================================
        Connecting the buttons and controls in the light stim controls group
        =====================================================================
        """

        # connect the save_stim button
        self.ui.buttonSaveStim.clicked.connect(self.save_lightstim)

        # Style the three sliders (color the handles)
        # self.ui.sliderRed.setStyleSheet("QSlider::handle:vertical {background-color: red; border: 1px outset; border-radius: 3px;}")
        # self.ui.sliderGreen.setStyleSheet("QSlider::handle:vertical {background-color: lime; border: 1px outset; border-radius: 3px;}")
        # self.ui.sliderBlue.setStyleSheet("QSlider::handle:vertical {background-color: cyan; border: 1px outset; border-radius: 3px;}")

        self.ui.toggleWhiteColor.valueChanged.connect(self.toggle_lightstim_type)
        self.toggle_lightstim_type()

        """
        ====================================================================
        Connecting buttons and controls in vibration stimuli group
        ====================================================================
        """

        self.ui.buttonSaveVibrationStim.clicked.connect(self.save_vibration_stim)
        
        
        """
        =====================================================================
        Connecting the buttons and controls in the stimuli manager group
        =====================================================================
        """

        self.Stims = StimuliManager(arduino=self.arduino)
        self.set_experiment_view()
        self.set_lightstim_name_lineedit()
        self.set_vibrationstim_name_lineedit()
        self.ui.buttonDeleteSelectedStim.clicked.connect(self.delete_selected_stim)
        self.ui.buttonDeleteAllStims.clicked.connect(self.delete_all_stims)
        self.ui.buttonLoadStimulusProfile.clicked.connect(self.load_stimuli)
        self.ui.buttonSaveStimulusProfile.clicked.connect(self.save_stimuli)

        """
        =====================================================================
        Connecting the buttons and controls in the MetaData entry group
        =====================================================================
        """
        self.ui.buttonSetWorkingDirectory.clicked.connect(self.set_working_directory)

        self.ui.labelMetaDataDrugName.setVisible(False)
        self.ui.lineeditMetaDataDrugName.setVisible(False)

        self.ui.labelMetaDataGenetics.setVisible(False)
        self.ui.lineeditMetaDataGenetics.setVisible(False)

        self.ui.spinBoxExperimentDurationMinutes.valueChanged.connect(self.set_experiment_view)
        self.ui.spinBoxExperimentDurationSeconds.valueChanged.connect(self.set_experiment_view)

        self.ui.spinboxCrowdsize.setValue(1)
        
        self.ui.dateTimeEditHatching.setDateTime(QtCore.QDateTime.fromString(time.strftime("%Y/%m/%d %H:%M:%S"), "yyyy/M/d hh:mm:ss"))
        self.ui.dateTimeEditHatching.dateTimeChanged.connect(lambda: self.check_datetime(self.ui.dateTimeEditHatching))

        self.ui.checkBoxExperimentAutonaming.clicked.connect(self.set_experiment_autonaming)
        self.set_experiment_autonaming()

        self.experiment_live = False
        self.ui.buttonStartExperiment.clicked.connect(self.start_experiment)

        self.path = os.curdir
        self.experiment_name = self.ui.lineeditExperimentName.text()
        self.experiment_path = os.path.join(self.path, "Exp_" + self.experiment_name)
        
        self.ui.buttonLazyMode.clicked.connect(self.start_many)

        """
        ======================================================================
        Connecting buttons and controls to the camera manager group
        ======================================================================
        """


        self.detect_cameras()
        self.ui.buttonCameraConnectDisconnect.clicked.connect(self.camera_connect_disconnect)
        self.ui.buttonCameraPreview.clicked.connect(self.toggle_preview)
        self.ui.buttonScanForCameras.clicked.connect(self.detect_cameras)

        self.ui.spinBoxFramerate.valueChanged.connect(self.set_camera_framerate)

        for x in range(-2, -12, -1):
            self.ui.comboboxCameraExposure.addItem(str(2 ** x))

        self.ui.comboboxCameraExposure.currentTextChanged.connect(self.set_camera_exposure)
        self.ui.sliderCameraBrightness.sliderMoved.connect(self.set_camera_brightness)
        self.ui.sliderCameraGamma.sliderMoved.connect(self.set_camera_gamma)

        self.ui.buttonCameraResetProperties.clicked.connect(self.reset_camera_properties)

        #This is for IR light, so actually belongs to arduino, but it is located here in the GUI.
        self.ui.sliderIRLight.sliderReleased.connect(self.set_IR_light)

        """
        ======================================================================
        Connecting buttons and controls to the video manager
        ======================================================================
        """

        self.set_autonaming(True)

        self.ui.buttonSetPath.clicked.connect(self.set_path)

        self.ui.checkboxAutoNaming.toggled.connect(self.set_autonaming)
        self.ui.buttonRecordVideo.clicked.connect(self.record_video)


    def detect_cameras(self):
        self.ui.comboBoxConnectedCameras.clear()
        for ii in range(3):
            cap = cv2.VideoCapture(ii)
            if not cap.isOpened():
                pass
            else:
                cam = "Camera "+str(ii +1)
                self.ui.comboBoxConnectedCameras.addItem(cam)


    def camera_connect_disconnect(self):
        if not hasattr(self, "cam") or  not self.cam.cap.isOpened():
            camera_number = int(self.ui.comboBoxConnectedCameras.currentText().split(" ")[1])-1

            self.cam = Camera(camera=camera_number)
           
            if self.cam.cap.isOpened():
                self.ui.groupBoxCameraControls.setEnabled(True)
                self.ui.groupBoxVideoControls.setEnabled(True)
                self.ui.comboBoxConnectedCameras.setEnabled(False)

                self.ui.labelCameraConnectionStatus.setText("Connected to Camera "+str(camera_number+1))
                self.ui.labelCameraConnectionStatus.setStyleSheet("color: green")
                self.ui.buttonCameraConnectDisconnect.setText("Disconnect")
                self.ui.buttonCameraConnectDisconnect.setStyleSheet("color: red")

                t = self.ui.comboboxCameraExposure.findText(str(2 ** (self.cam.exposure)))
                self.ui.comboboxCameraExposure.setCurrentIndex(t)
                self.ui.sliderCameraBrightness.setValue(self.cam.brightness)
                self.ui.labelCameraBrighness.setNum(self.cam.brightness)
                self.ui.sliderCameraGamma.setValue(self.cam.gamma)
                self.ui.labelCameraGamma.setNum(self.cam.gamma / 100)
#                self.ui.sliderCameraGamma.setEnabled(False)
#                self.cam.signal_recording_finished.connect(self.recording_finished_receiver)
#                print("Signals have been conneted. Maybe. I dunno")
        else:
            self.toggle_preview(False)
            self.cam.stop()
            self.cam.cap.release()
            self.ui.buttonCameraPreview.setChecked(False)
            self.ui.groupBoxCameraControls.setEnabled(False)
            self.ui.groupBoxVideoControls.setEnabled(False)
            self.ui.comboBoxConnectedCameras.setEnabled(True)

            self.ui.buttonCameraConnectDisconnect.setText("Connect")
            self.ui.buttonCameraConnectDisconnect.setStyleSheet("color: black")
            self.ui.labelCameraConnectionStatus.setText("Status: Not Connected")
            self.ui.labelCameraConnectionStatus.setStyleSheet("color: black")

    def toggle_lightstim_type(self):
        val = self.ui.toggleWhiteColor.value()
        if val == 1:
            self.lightStimType = "White"
            self.ui.labelLightStimTypeLED.setEnabled(False)
            self.ui.labelLightStimTypeWhite.setEnabled(True)
            self.ui.widgetLEDSliders.setEnabled(False)

            self.ui.toggleWhiteColor.setStyleSheet(
                "QSlider::handle:horizontal {background-color: rgba(255,255,255,255); border: 2px outset; width: 10px; height: 10px; border-radius: 5px;}"
                "QSlider::groove:horizontal {height: 10px; width: 30px; background-color: rgba(255, 0,0, 100); border-radius: 5px; border: 1px solid;}")

            self.ui.sliderRed.setStyleSheet(
                "QSlider::handle:vertical {background-color: grey; border: 1px outset; border-radius: 3px;}")
            self.ui.sliderGreen.setStyleSheet(
                "QSlider::handle:vertical {background-color: grey; border: 1px outset; border-radius: 3px;}")
            self.ui.sliderBlue.setStyleSheet(
                "QSlider::handle:vertical {background-color: grey; border: 1px outset; border-radius: 3px;}")

        if val == 0:
            self.lightStimType = "LED"
            self.ui.labelLightStimTypeLED.setEnabled(True)
            self.ui.labelLightStimTypeWhite.setEnabled(False)
            self.ui.widgetLEDSliders.setEnabled(True)

            self.ui.toggleWhiteColor.setStyleSheet(
                "QSlider::handle:horizontal {background-color: rgba(255,100,0,100); border: 2px outset; width: 10px; height: 10px; border-radius: 5px;}"
                "QSlider::groove:horizontal {height: 10px; width: 30px; background-color: rgba(255, 255, 255,100); border-radius: 5px; border: 1px solid;}")

            self.ui.sliderRed.setStyleSheet(
                "QSlider::handle:vertical {background-color: red; border: 1px outset; border-radius: 3px;}")
            self.ui.sliderGreen.setStyleSheet(
                "QSlider::handle:vertical {background-color: lime; border: 1px outset; border-radius: 3px;}")
            self.ui.sliderBlue.setStyleSheet(
                "QSlider::handle:vertical {background-color: cyan; border: 1px outset; border-radius: 3px;}")

    def set_experiment_view(self):
        self.ui.graphicsView.clear()
        plot = PlotDataItem(pen="k")

        duration = (self.ui.spinBoxExperimentDurationMinutes.value() * 60) + self.ui.spinBoxExperimentDurationSeconds.value()
        xs = np.linspace(0, duration, 2)
        ys = [1, 1]
        plot.setData(xs, ys)
        self.ui.graphicsView.addItem(plot)

        for ii in range(len(self.Stims.df)):
            start = self.Stims.df.time_on.iloc[ii]
            stop = self.Stims.df.time_off.iloc[ii]

            if self.Stims.df.message_on.iloc[ii].startswith("w"):
                box = LinearRegionItem(values=(start, stop), brush=(255, 255, 250, 230), movable=False)
                self.ui.graphicsView.addItem(box)
            elif self.Stims.df.message_on.iloc[ii].startswith("n"):
                on = self.Stims.df.message_on.iloc[ii][1:]
                r = int(on[:3])
                g = int(on[3:6])
                b = int(on[6:])
                box = LinearRegionItem(values=(start, stop), brush=(r, g, b, 50), movable=False)
                self.ui.graphicsView.addItem(box)
            elif self.Stims.df.message_on.iloc[ii].startswith("v"):
                box = LinearRegionItem(values = (start, stop), brush="k", movable = False)
                self.ui.graphicsView.addItem(box)

        self.ui.comboBoxSelectStimId.clear()
        for stim_id in set(self.Stims.df.id):
            self.ui.comboBoxSelectStimId.addItem(stim_id)

    # def checkStimSafeguard(self):
    #     if self.ui.checkboxDirectStim.isChecked() is False:
    #         self.ui.listwidgetAllStims.itemDoubleClicked.disconnect(self.single_stim)
    #     elif self.ui.checkboxDirectStim.isChecked():
    #         self.ui.listwidgetAllStims.itemDoubleClicked.connect(self.single_stim)

    def update_serial_available(self):
        """Scans the available comports and updates the combobox with the resulst"""
        self.ui.comboboxSerialAvailable.clear()
        self.arduino.scan_comports()
        for port in list(self.arduino.port_dict.keys()):
            self.ui.comboboxSerialAvailable.addItem(port)

    def serial_connect_disconnect(self):
        """Connects to selected serial if disconnected and vice versa"""
        if self.ui.buttonSerialConnect.text().lower() == "connect":
            port = self.ui.comboboxSerialAvailable.currentText()
            self.arduino.connect(port)
            if self.arduino.ser.isOpen():
                self.ui.labelSerialConnected.setText("Connected: " + self.arduino.port)
                self.ui.labelSerialConnected.setStyleSheet("color: green")
                self.ui.buttonSerialConnect.setText("Disconnect")
                self.ui.checkBoxReadSerialLive.setEnabled(True)
                self.ui.sliderIRLight.setEnabled(True)

        elif self.ui.buttonSerialConnect.text().lower() == "disconnect":
            self.ui.checkBoxReadSerialLive.setChecked(False)
            self.arduino.disconnect()
            if self.arduino.ser.isOpen() == False:
                self.ui.labelSerialConnected.setText("Status: Not connected")
                self.ui.labelSerialConnected.setStyleSheet("color: black")
                self.ui.buttonSerialConnect.setText("Connect")
                self.ui.checkBoxReadSerialLive.setEnabled(False)
                self.ui.checkBoxReadSerialLive.setChecked(False)
                self.ui.sliderIRLight.setEnabled(False)

    def listen_to_serial(self):
        """Starts a thread that listens on the self.Arduino.ser serial connection and updates the GUI with incoming messages"""
        if self.ui.checkBoxReadSerialLive.isChecked():
            self.ui.graphicsViewSerial.clear()
            self.temperature_plot = PlotDataItem(pen = (0,153,153))
            self.temperature_plot_2 = PlotDataItem(pen = (255,128,0))
            self.temperature_plot.setDownsampling(auto=True, method = "mean")
            self.temperature_plot_2.setDownsampling(auto=True, method="mean")
            self.ui.graphicsViewSerial.addItem(self.temperature_plot)
            self.ui.graphicsViewSerial.addItem(self.temperature_plot_2)
            t = Thread(target=self.start_listening, args = ())
            t.start()

    def start_listening(self):
        """To be started in separate thread: listens to Serial port and updates gui via separate method if new message comes in"""
        self.arduino.ser.flushInput()
        self.logged_temperature = np.array([])
        self.logged_temperature_2 = np.array([])
        self.logged_temperature_time = np.array([])
        start = time.time()
        while self.ui.checkBoxReadSerialLive.isChecked() and self.arduino.ser.isOpen():
            if self.arduino.ser.in_waiting > 0:
                message = self.arduino.ser.readline().decode()
                elapsed_time = time.time() - start
                self.update_serial_display(message, np.round(elapsed_time,2))
            else:
                time.sleep(0.01)
        else:
            pass

    def update_serial_display(self, message, elapsed_time):
        temp1, temp2 = message.split(" ")
        self.ui.labelSerialLiveIncoming.setText(str(elapsed_time))
        self.ui.labelSerialLiveTemperature.setText(message)
        temp1 = float(temp1)
        temp2 = float(temp2)
        self.logged_temperature_time = np.hstack([self.logged_temperature_time, elapsed_time])
        self.logged_temperature = np.hstack([self.logged_temperature, temp1])
        self.logged_temperature_2 = np.hstack([self.logged_temperature_2, temp2])

        self.temperature_plot.setData(x=self.logged_temperature_time, y = self.logged_temperature)
        self.temperature_plot_2.setData(x=self.logged_temperature_time, y = self.logged_temperature_2)


    def write_to_serial(self):
        """Send message in the lineEdit widget to the serial port"""
        message = self.ui.lineeditWriteToSerial.text()
        self.arduino.write(message)
        self.ui.lineeditWriteToSerial.clear()

    def set_lightstim_name_lineedit(self):
        c = 1
        while "LightStim" + str(len(self.Stims.df) + c) in self.Stims.df.id:
            c += 1
        newname = "LightStim" + str(len(self.Stims.df) + c)
        self.ui.lineeditLightStimName.setText(newname)

    def save_lightstim(self):
        """Takes the current settings in the lightstim box and adds them to stim manager"""

        start_time = self.ui.spinboxStimStart.value()
        stop_time = self.ui.spinboxStimDuration.value() + start_time
        stim_id = self.ui.lineeditLightStimName.text()

        if self.lightStimType == "LED":
            start_message = "n"
            for slider in [self.ui.sliderRed, self.ui.sliderGreen, self.ui.sliderBlue]:
                start_message += str(slider.value()).zfill(3)
            stop_message = "nC"

        elif self.lightStimType == "White":
            start_message = "wS"
            stop_message = "wC"

        self.Stims.add_stimulus(start_time, stop_time, start_message, stop_message, stim_id)
        self.set_lightstim_name_lineedit()

        self.ui.comboBoxSelectStimId.clear()
        stim_ids = list(set(self.Stims.df.id))
        stim_ids.sort()
        for stim_id in stim_ids:
            self.ui.comboBoxSelectStimId.addItem(stim_id)
        self.set_experiment_view()


    def set_vibrationstim_name_lineedit(self):
        c = 1
        while "VibrationStim" + str(len(self.Stims.df) + c) in self.Stims.df.id:
            c += 1
        newname = "VibrationStim" + str(len(self.Stims.df) + c)
        self.ui.lineeditVibrationStimName.setText(newname)
        
    def save_vibration_stim(self):
        """takes the current settings in the vibration stim box and adds it to the stim manager"""
        start_time = self.ui.spinBoxVibrationStart.value()
        duration = self.ui.spinBoxVibrationDuration.value()
        freq = self.ui.spinBoxVibrationFrequency.value()
        start_message = "v"+str(freq).zfill(3)+str(int(duration*1000)).zfill(4)
        stop_message = "vC"
        stim_id = self.ui.lineeditVibrationStimName.text()
        self.Stims.add_stimulus(start_time, start_time+duration, start_message, stop_message, stim_id)
        self.set_vibrationstim_name_lineedit()
        self.ui.comboBoxSelectStimId.clear()
        stim_ids = list(set(self.Stims.df.id))
        stim_ids.sort()
        for stim_id in stim_ids:
            self.ui.comboBoxSelectStimId.addItem(stim_id)
        self.set_experiment_view()

    def delete_selected_stim(self):
        stim_id = self.ui.comboBoxSelectStimId.currentText()

        self.Stims.delete_stimulus(stim_id)
        self.set_experiment_view()


    def delete_all_stims(self):
        self.Stims.delete_all_stims()
        self.set_experiment_view()

    def load_stimuli(self):
        file = QtWidgets.QFileDialog.getOpenFileName(self, "Select a Stimuli File")
        file = file[0]
        if os.path.exists(file) and file.endswith(".txt"):
            df = pd.read_csv(file, delimiter = "\t")
            self.Stims.df = df
            self.set_experiment_view()
        elif not file:
            pass
        else:
            QtWidgets.QMessageBox.warning(self, "Invalid Filename", "Invalid Stimulus File selected.")
    
    def save_stimuli(self):
        filename_selected = False
        while not filename_selected:
            filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save Stimuli file as")[0]
            if not filename:
                break
            else:
                if not filename.endswith(".txt"):
                    filename += ".txt"
                self.Stims.df.to_csv(filename, sep = "\t")
                filename_selected = True

    def toggle_preview(self, event):
        if event:
            self.cam.preview()
            self.ui.buttonCameraPreview.setText("Stop")
            self.ui.buttonCameraPreview.setStyleSheet("color: red")
        else:
            self.ui.buttonCameraPreview.setText("Preview")
            self.ui.buttonCameraPreview.setStyleSheet("color: Black")
            self.cam.stop()

    def set_autonaming(self, bool):
        if bool:
            self.ui.lineeditVideoName.setText(time.strftime("%Y%m%d_%H%M%S_video"))

    def set_experiment_autonaming(self):
        if self.ui.checkBoxExperimentAutonaming.isChecked():
            name = time.strftime("%Y%m%d_%H%M%S")
            name += "_"
            name += str(self.ui.spinboxCrowdsize.value())
            name += "_"
            name += str(self.ui.spinBoxExperimentDurationMinutes.value()) + "m"
            name += str(self.ui.spinBoxExperimentDurationSeconds.value()) +"s_"
            if self.ui.checkboxMetaDataDrugs.isChecked():
                name += self.ui.lineeditMetaDataDrugName.text() + "_"
            else:
                name += "None_"
            if self.ui.checkboxMetaDataGenetics.isChecked():
                name += self.ui.lineeditMetaDataGenetics.text() + "_"
            else:
                name += "None_"
            if len(self.Stims.df) > 0:
                name += "Light"
            else:
                name += "None"
            self.ui.lineeditExperimentName.setText(name)
        else:
            pass

    def set_camera_framerate(self, fps):
        self.cam.framerate = fps

#        if self.cam.do_gamma == False:
#            self.ui.sliderCameraGamma.setVisible(False)
#            self.ui.labelCameraGamma.setVisible(False)
#        else:
#            self.ui.sliderCameraGamma.setVisible(True)
#            self.ui.labelCameraGamma.setVisible(True)

    def set_camera_brightness(self, brightness):
        self.cam.brightness = brightness


    def set_camera_gamma(self, gamma):
#        gamma = gamma * 10
        self.cam.gamma = gamma
        self.ui.labelCameraGamma.setNum(gamma/100)

    def set_camera_exposure(self, exp):
        # If set exposure is longer than framerate allows, then adjust framerate
        exp = float(exp)

        if exp > (1 / self.cam.framerate):
            print("\n WARNING: Adjusting framerate to accomodate for exposure \n")
            #            self.set_camera_framerate(1 / exp)
            self.ui.spinBoxFramerate.setValue(int(1 / exp))

        exp = np.log2(exp)
        self.cam.exposure = exp

    def set_IR_light(self):
        val = self.ui.sliderIRLight.value()
        self.arduino.write("i"+str(val).zfill(3))
        sys.stdout.write('\n IR Light set to {}. {}% of power'.format(val, (val/255)*100))

    def set_path(self):
        self.path = QtGui.QFileDialog.getExistingDirectory()
        print(self.path)

    def set_working_directory(self):
        self.working_directory_selected = False
        while not self.working_directory_selected:
            self.path = QtGui.QFileDialog.getExistingDirectory()
            if os.path.exists(self.path):
                os.chdir(self.path)
                self.working_directory_selected = True
            else:
                q = QtWidgets.QMessageBox.question(self, "No path selected", "Do you wish to not select a path? \n Path then defaults to C:\Experiments")
                if q == QtWidgets.QMessageBox.Yes:
                    self.path = "D:\\"
                    self.working_directory_selected = True

    def reset_camera_properties(self):
        self.cam.brightness = 0
        self.ui.sliderCameraBrightness.setValue(0)
        self.ui.labelCameraBrighness.setNum(0)

        self.cam.exposure = -5.0
        t = self.ui.comboboxCameraExposure.findText(str(2 ** -5))
        self.ui.comboboxCameraExposure.setCurrentIndex(t)

        self.cam.gamma = 1
        self.ui.sliderCameraGamma.setValue(10)
        self.ui.labelCameraGamma.setNum(1)

        self.cam.framerate = 30
        self.ui.spinBoxFramerate.setValue(30)

    def record_video(self, event):

        if event:
            self.ui.buttonRecordVideo.setText("Stop")
            self.ui.buttonRecordVideo.setStyleSheet("color:red")

            self.ui.groupBoxCameraControls.setEnabled(False)
            self.ui.groupBoxCameraConnection.setEnabled(False)

            if self.ui.checkboxAutoNaming.isChecked():
                self.ui.lineeditVideoName.setText(time.strftime("%Y%m%d_%H%M" + "_experiment"))

            name = os.path.join(self.path, self.ui.lineeditVideoName.text())

            duration = self.ui.spinBoxVideoTimeMinutes.value() * 60
            duration += self.ui.spinBoxVideoTimeSeconds.value()
            preview = self.ui.checkBoxPreviewWhileRecording.isChecked()
            self.cam.video(name, duration, preview)

            t = Thread(target=self.wait_for_recording_end)
            t.start()

        else:
            self.ui.groupBoxCameraControls.setEnabled(True)
            self.ui.groupBoxCameraConnection.setEnabled(True)
            self.ui.buttonRecordVideo.setText("Record")
            self.ui.buttonRecordVideo.setStyleSheet("color:Black")
            self.cam.stop()
#    
#    @QtCore.pyqtSlot()
#    def recording_finished_receiver(self):
#        self.ui.groupBoxCameraControls.setEnabled(True)
#        self.ui.groupBoxCameraConnection.setEnabled(True)
#        self.ui.buttonRecordVideo.setText("Record")
#        self.ui.buttonRecordVideo.setStyleSheet("color:Black")
#        self.cam.stop()

    def wait_for_recording_end(self):
        time.sleep(0.1)
        while self.cam.alive == True:
            time.sleep(0.1)
        else:
            self.record_video(False)

    #            self.ui.buttonRecordVideo.setChecked(False)
    #

    """
    ==========================================================================================
    METHODS TO RUN AN ENTIRE EXPERIMENT
    ==========================================================================================
    """
    
        
    
    def start_many(self):
        
        n_exp = self.ui.spinBoxLazyMode.value()
        for i in range(n_exp):
            sys.stdout.write("\n Experiment Sequence. recording "+str(i+1)+" of " + str(n_exp))
            self.start_experiment(True)
            while self.experiment_live:
                time.sleep(1)
                        
    
    def start_experiment(self, event):
        if event:
            if not hasattr(self, "cam"):
                QtWidgets.QMessageBox.warning(self, "Not Connected Warning", "No open connection with Camera")
                self.ui.buttonStartExperiment.setChecked(False)
            elif not self.cam.cap.isOpened():
                QtWidgets.QMessageBox.warning(self, "Not Connected Warning", "No open connection with Camera")
                self.ui.buttonStartExperiment.setChecked(False)
#            elif not self.arduino.connected:
#                QtWidgets.QMessageBox.warning(self, "Not Connected Warning", "No open connection with Controller")
#                self.ui.buttonStartExperiment.setChecked(False)
            else:
                if not self.working_directory_selected:
                    QtWidgets.QMessageBox.warning(self, "No valid working directory", "Select a directory to save your experiment")
                    self.set_working_directory()

                self.experiment_live = True
                self.ui.buttonStartExperiment.setStyleSheet('color: rgba(255,0,0,255)')
                self.ui.buttonStartExperiment.setText('Interrupt')

                self.set_experiment_autonaming()
                self.ui.widgetMetaData.setEnabled(False)
                self.experiment_name = self.ui.lineeditExperimentName.text()

                self.experiment_path = os.path.join(self.path, "Exp_" + self.experiment_name)
                if not os.path.exists(self.experiment_path) or not os.path.isdir(self.experiment_path):
                    os.mkdir(self.experiment_path)

                if self.ui.checkBoxReadSerialLive.isChecked():
                    self.ui.checkBoxReadSerialLive.setChecked(False)
                self.ui.checkBoxReadSerialLive.setChecked(True)
                self.listen_to_serial()

                duration = (self.ui.spinBoxExperimentDurationMinutes.value() * 60) + self.ui.spinBoxExperimentDurationSeconds.value()
                preview = self.ui.checkBoxPreviewWhileRecording.isChecked()
                self.cam.video(os.path.join(self.experiment_path, self.experiment_name), duration, preview)
                self.Stims.start_stimuli()
                t = Thread(target=self.wait_for_experiment_end, args=())
                t.start()
        else:
            self.experiment_live = False
            self.cam.stop()
            self.Stims.alive = False
            self.ui.checkBoxReadSerialLive.setChecked(False)
            self.ui.buttonStartExperiment.setStyleSheet("color: Black")
            self.ui.buttonStartExperiment.setText("Start Experiment")

            df = pd.DataFrame()
            df["date"] = [time.strftime("%Y%m%d")]
            df["time"] = [time.strftime("%H%M%S")]
            df["duration"] = [(self.ui.spinBoxExperimentDurationMinutes.value() * 60) + self.ui.spinBoxExperimentDurationSeconds.value()]
            
            if not self.ui.checkboxMetaDataDrugs.isChecked():
                self.ui.lineeditMetaDataDrugName.clear()
                self.ui.lineeditMetaDataDrugName.setText("none")
            if not self.ui.checkboxMetaDataGenetics.isChecked():
                self.ui.lineeditMetaDataGenetics.clear()
                self.ui.lineeditMetaDataGenetics.setText("none")
            
            df["drugs"] = [self.ui.lineeditMetaDataDrugName.text()]
            df["genetics"] = [self.ui.lineeditMetaDataGenetics.text()]
            seconds, readable, hph = self.get_ages()
            df["age"] = [hph] #legacy
            df["exact_age_seconds"] = [seconds]
            df["exact_age_readable"] = [readable]
            df["hatching_time"] = self.ui.dateTimeEditHatching.dateTime().toString("yyyyMMdd hh:mm:ss")
            
            df["crowdsize"] = [self.ui.spinboxCrowdsize.value()]
            df["framerate"] = [self.cam.framerate]
            df["dechorionated"] = [self.ui.checkboxMetaDataDechorionation.isChecked()]
            df["exposure"] = [float(self.ui.comboboxCameraExposure.currentText())]
            df["gamma"] = [self.cam.gamma]
            df["brightness"] = [self.cam.brightness]
            df["infrared"] = [self.ui.sliderIRLight.value()]
            df["camera"] = [self.ui.comboBoxConnectedCameras.currentText()]
            df["hostname"] = [self.hostname]


            df.to_csv(os.path.join(self.experiment_path, "metadata.txt"), sep="\t")

            self.Stims.df.to_csv(os.path.join(self.experiment_path, "stimuli_profile.txt"), sep="\t")
            df = pd.DataFrame(np.hstack([self.logged_temperature_time.reshape(-1,1), self.logged_temperature.reshape(-1,1), self.logged_temperature_2.reshape(-1,1)]), columns = ["time", "temperature", "temperature2"])
            df.set_index("time", inplace=True)
            df.to_csv(os.path.join(self.experiment_path, "logged_temperatures.txt"), sep="\t")
            self.ui.widgetMetaData.setEnabled(True)



    def wait_for_experiment_end(self):
        time.sleep(0.2)  # Give camera a chance to start.
        while self.cam.alive:
            time.sleep(0.2)
        else:
            if self.experiment_live:
                self.start_experiment(False)
                self.ui.buttonStartExperiment.setChecked(False)
                
    def get_ages(self, widget = "none"):
        if widget != "none":
            widget = widget
        else:
            widget = self.ui.dateTimeEditHatching
        hatching_time_qt = widget.dateTime()
        hatching_time = datetime.strptime(hatching_time_qt.toString("yyyyMMdd hh:mm:ss"), "%Y%m%d %H:%M:%S")
        
        age = datetime.now() - hatching_time
        return(age.total_seconds(), str(age), int(age.total_seconds()/3600))
        
    def check_datetime(self, widget = "none"):
        try:
            if widget != "none":
                widget = widget
            else:
                widget = self.ui.dateTimeEditHatching
            
            total_seconds, readable, hours = self.get_ages(widget)
            
            if total_seconds < 0:
                QtWidgets.QMessageBox.warning(self, "Negative Age Warning", "You are trying to set a hatching time in the future.")
            elif total_seconds >= (50 * 3600):
                QtWidgets.QMessageBox.warning(self, "Old Age Warning", "Are your animals really {0} hours old?".format(str(int(total_seconds/3600))))

        except Exception as e:
            print(str(e))


    def closeEvent(self, event):
        QtWidgets.QMessageBox.warning(self, "Closing", "Nothing you can do about it")
        self.arduino.ser.close()
        self.cam.cap.release()
        event.accept()
        print("yay")


if __name__ == "__main__":

    #    if not QtWidgets.QApplication.instance():
    #        app = QtWidgets.QApplication(sys.argv)
    #    else:
    #        app = QtWidgets.QApplication.instance()

    app = QtGui.QApplication([])

    projectWindow = QtGui.QMainWindow()
    projectWindow.resize(675, 510)
    projectWindow.setWindowTitle('imMobilize')
    immobilize = imMobilize()
    projectWindow.setCentralWidget(immobilize)
    projectWindow.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()
