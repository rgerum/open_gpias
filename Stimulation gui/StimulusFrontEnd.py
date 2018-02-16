# -*- coding: utf-8 -*-
"""
Created on Wed Nov  8 12:56:07 2017

@author: rahlfshh
"""

import StimulusBackend
import numpy as np
import sys
from PyQt5.QtWidgets import (QMessageBox, QFileDialog, QPushButton,
     QApplication)
from threading import Thread
import time
import os
from PyQt5.uic import loadUiType
import Plot_Klasse
Ui_MainWindow, QMainWindow = loadUiType('Startle_Stimulation.ui')
import re

Playlist_Directory = "C:/Users/Setup/Desktop/Playlists"
Measurement_Directory= "C:/Users/Setup/Desktop/Messungen"
Backup_Measurement_Directory = "C:/Users/Setup/Backup_messungen"
    
class LoadAndPlayKonfig(QMainWindow, Ui_MainWindow):
    def __init__(self,parent=None):
        super().__init__()
        self.timeString = ""
        self.shutDown = 0
        QMainWindow.__init__(self, parent)
        self.setupUi(self)
        self.initUI()
        self.thisplot = None #TODO MS
        self.backup_plot_count = 0
        self.lcdNumber.display(0)

    def stop(self): #stop button pushed
        """
        Callback function for stop button, stops and resets mesurement
        """
        self.pauseButton.setEnabled(False)
        self.startButton.setEnabled(False)

        if self.measurement_thread is not None:
            self.textEdit_out.setText('Stopping Measurement. Please wait')
            self.measurement_thread.stop = True
            self.measurement_thread.pause = False  #In case it was previously paused
        #self.timer.stop()

    def pause(self):    #pause button pushed
        """
        Callback function for pause button
        """
        if self.measurement_thread is not None:
            if self.measurement_thread.pause:
                self.pauseButton.setText("Pause")
                self.measurement_thread.pause = False
            else:
                self.pauseButton.setText("Resume")
                self.pauseButton.setEnabled(False)
                self.textEdit_out.setText('Pausing Measurement. Please wait')
                self.measurement_thread.pause = True
        
    def startStimulation(self):
        if not self.check_input():
            return
        if self.measurement_thread is not None and self.measurement_thread.pause:
            self.measurement_thread.pause = False
            return
        
        #reset this to notify save_data
        self.timeString = ""
        try:
            konfigFile = open(self.lineEdit_Path.text(),"rb")
        except IOError:
            msg = QMessageBox(parent = self)
            msg.setIcon(QMessageBox.Warning)    
            msg.setText("Die geladenen Konfig File funktioniert nicht")
            msg.setWindowTitle("Warnung")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            return
        konfig = np.load(konfigFile, allow_pickle = False, fix_imports = False)
        if self.lineEdit_Path.text()[-11:] == "_TURNER.npy":
            self.turner = True
            self.hearingThreshold = False


            for a in konfig[5:]:
                 if a[4] !=0 or a[5] !=0 or a[6] !=0 or len(a) != 8:
                     msg = QMessageBox(parent = self)
                     msg.setIcon(QMessageBox.Warning)    
                     msg.setText("Die geladene Datei ist beschädigt.")
                     msg.setWindowTitle("Warnung")
                     msg.setStandardButtons(QMessageBox.Ok)
                     msg.exec_()
                     raise RuntimeError
        elif self.lineEdit_Path.text()[-32:] == "_TURNER_AND_HEARINGTHRESHOLD.npy":
            self.turner = True
            self.hearingThreshold = True
            for a in konfig:
                if len(a) != 8:
                    msg = QMessageBox(parent = self)
                    msg.setIcon(QMessageBox.Warning)    
                    msg.setText("Die geladene Datei ist beschädigt.")
                    msg.setWindowTitle("Warnung")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                    raise RuntimeError
        elif self.lineEdit_Path.text()[-21:] == "_HEARINGTHRESHOLD.npy":
            self.turner = False
            self.hearingThreshold = True
            for a in konfig:
                if a[0] !=0 or a[1] !=0 or a[2] !=0 or a[3] !=0:
                    msg = QMessageBox(parent = self)
                    msg.setIcon(QMessageBox.Warning)    
                    msg.setText("Die geladene Datei ist beschädigt.")
                    msg.setWindowTitle("Warnung")
                    msg.setStandardButtons(QMessageBox.Ok)
                    msg.exec_()
                    raise RuntimeError
        else:
            msg = QMessageBox(parent = self)
            msg.setIcon(QMessageBox.Warning)    
            msg.setText("Der Name der Datei ist nicht regelkonform.")
            msg.setWindowTitle("Warnung")
            msg.setStandardButtons(QMessageBox.Ok)
            msg.exec_()
            raise RuntimeError
        #StimulusBackend.startStimulation(konfig)
        self.textEdit_out.clear()     #clears output text
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.pauseButton.setEnabled(True)
        
        self.pauseButton.setText("Pause")

        
        self.measurement_thread = StimulusBackend.Measurement(konfig,10000)
        self.measurement_thread.plot_data.connect(self.plot_it)
        self.measurement_thread.backup.connect(self.save_backup)
        self.measurement_thread.finished.connect(self.m_finished)
        self.measurement_thread.paused.connect(self.m_paused)
        self.measurement_thread.stopped.connect(self.m_stopped)
        self.measurement_thread.resumed.connect(self.m_resumed)
        self.measurement_thread.update_timer.connect(self.update_timer)
        
        Thread(target=self.measurement_thread.run_thread, args=()).start() #start Measurement
        time.sleep(1)
        
    def initUI(self):
        self.dir_measurements = Measurement_Directory 
        self.openButton = QPushButton("Open...")
        def selectFile():
            self.lineEdit_Path.setText(QFileDialog.getOpenFileName(
                    directory = Playlist_Directory,
                    filter = "byteType (*_HEARINGTHRESHOLD.npy *_TURNER.npy *_TURNER_AND_HEARINGTHRESHOLD.npy)")[0])
        self.browseButton.clicked.connect(selectFile)
        self.startButton.clicked.connect(self.startStimulation)
        self.stopButton.clicked.connect(self.stop)   #program stops
        self.pauseButton.clicked.connect(self.pause) #program pauses
        
        self.measurement_thread = None
        self.plot_window = None
        
        
        self.setWindowTitle('Load Konfig File')
        self.show()

    def update_timer(self,konfigArray,idx):
        print("hallo1")
        min_left = self.calculate_time_left(konfigArray,idx)
        print(2)
        self.lcdNumber.display(min_left)
        print(3)
        
    def calculate_time_left(self,konfigArray,idx):
        print("hallo3")
        print(StimulusBackend.noiseTimeIDX)
        print(konfigArray)
        print(idx)
        noisetimes = konfigArray[idx:,StimulusBackend.noiseTimeIDX]
        ISIs = konfigArray[idx:,StimulusBackend.ISIIDX]
        print("hallo4")
        msleft = np.sum(ISIs) + np.sum(noisetimes) + 2000*len(ISIs)
        print("hallo5")
        return int(msleft/(1000*60)) + 1
        
    def save_backup(self,data_extracted,all_data):
        if self.backup_plot_count>=10:
            self.save_data(data_extracted, all_data, finished = False)
            self.backup_plot_count = 0
        else:
            self.backup_plot_count += 1
        
        
    #TODO MS    
    def plot_it(self,data,idx):
        if self.thisplot is None:
            self.thisplot = Plot_Klasse.plotWidget(data[idx,:,:], idx)
            #saves maximum of acceleration calculated by plot
            self.thisplot.plot()
            data[idx][6][0] = self.thisplot.get_max()
        #from Plot_Klasse import plot
        
        else:
            #data = np.copy(data)
            self.thisplot.esc()
            #self.thisplot.deleteLater()

            self.thisplot = Plot_Klasse.plotWidget(data[idx,:,:], idx)
            #saves maximum of acceleration calculated by plot
            self.thisplot.plot()
            data[idx][6][0] = self.thisplot.get_max()
            
        self.thisplot.show()
        
        
    def m_finished(self, data_extracted, all_data):
        self.save_data(data_extracted, all_data)
        self.textEdit_out.setText('Measurement ended')
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        self.MessageBox('Measurement Completed', mtype='information')
        self.measurement_thread = None
        self.lcdNumber.display(0)
        self.measurement_thread= None
        
    def m_paused(self):
        #self.timer.stop()
        self.startButton.setEnabled(False)
        self.pauseButton.setEnabled(True)
        self.MessageBox("The door can be opened.", 'information', title='Paused')
        self.textEdit_out.setText('Measurement paused')
    
    def m_resumed(self):
        self.pauseButton.setEnabled(True)
        self.textEdit_out.setText('')
    
    
    def m_stopped(self):
        self.textEdit_out.setText('Measurement stopped')
        self.startButton.setEnabled(True)
        self.pauseButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        if self.measurement_thread is not None:
            self.measurement_thread.pause = False #reset in case pause button was pressed
        self.MessageBox("Measurement stopped", mtype='information', title='info' )
        self.lcdNumber.display(0)
        self.measurement_thread= None
        if self.shutDown:
            self.shutDown = 2
            self.close()


 
    def save_data(self, data_extracted, all_data, finished = True):
        
        if self.timeString == "":
            self.timeString = time.strftime("%Y-%m-%d_%H-%M")
        
        
        if self.turner and self.hearingThreshold:
            fileNameEnding = "_turner_and_threshold"
        elif self.turner:
            fileNameEnding = "_turner"
        elif self.hearingThreshold:
            fileNameEnding = "_threshold"
        else:
            raise RuntimeError
        dirname = os.path.join(self.textEdit_Experimenter.toPlainText(), self.textEdit_Mousname.toPlainText(),self.textEdit_status.toPlainText(), self.timeString)
        filename = "UNFINISHED_" + self.textEdit_Experimenter.toPlainText() + '_' + self.textEdit_Mousname.toPlainText() + '_'+ self.textEdit_status.toPlainText() + "_" + fileNameEnding + "_"  + self.timeString
        directory = os.path.join(self.dir_measurements, dirname)



        if not os.path.exists(directory):
            os.makedirs(directory)

        np.save(os.path.join(directory, filename + '_extracted_data.npy'),data_extracted)

        
        if finished:
            time.sleep(3)
            #print(data_extracted[0])
            #os.rename(os.path.join(directory, filename + '_raw_data.npy'), os.path.join(directory, filename.replace("UNFINISHED_","") + '_raw_data.npy'))
            os.rename(os.path.join(directory, filename + '_extracted_data.npy'), os.path.join(directory, filename.replace("UNFINISHED_","") + '_extracted_data.npy'))
            self.timeString = ""
            only_amplitudes = self.raw_to_amplitude(data_extracted)
            np.save(os.path.join(directory, filename.replace("UNFINISHED_","") + '_amplitudes.npy'),only_amplitudes)
            directory_backup = directory.replace(Measurement_Directory,Backup_Measurement_Directory)
            if not os.path.exists(directory_backup):
                os.makedirs(directory_backup)
            
            np.save(os.path.join(directory_backup, filename.replace("UNFINISHED_","") + '_extracted_data.npy'),data_extracted)
            
    def raw_to_amplitude(self, extracted_data):
        only_amplitude = np.zeros((len(extracted_data),10))
        for i,item in enumerate(extracted_data):
            only_amplitude[i] = item[6][:10]
#        local_amplitudeIDX = 0
#        local_noiseIDX = 1
#        local_noiseGapIDX = 2
        local_noiseFreqMinIDX = 3
        local_noiseFreqMaxIDX = 4
        local_preStimAttenIDX = 5
#        local_preStimFreqIDX = 6
#        local_ISIIDX = 7
#        local_noiseTimeIDX = 8
        local_noiseFreqMidIDX = 9
        noise_atten = 60
        for i in range(len(only_amplitude)):
            if only_amplitude[i][local_noiseFreqMinIDX]!= 0:
                only_amplitude[i][local_noiseFreqMidIDX] = int(only_amplitude[i][local_noiseFreqMinIDX]*(only_amplitude[i][local_noiseFreqMaxIDX]/only_amplitude[i][local_noiseFreqMinIDX])**(1/2)+1)
                only_amplitude[i][local_preStimAttenIDX] = noise_atten
        return only_amplitude
                
                
        
        ############code from bera##############
    def MessageBox(self, msg, mtype='error', title=None):
        """
        opens a Message Box and displays a message

        Parameters
        ----------
        mtype: the message type: 'error', 'warning' | 'information' (default: 'error')

        """

        mbox = QMessageBox()
        mbox.setStandardButtons(QMessageBox.Ok)
        mbox.setText(msg)

        if type == 'error':
            mbox.setIcon(QMessageBox.Error)
            if title:
                mbox.setWindowTitle(title)
            else:
                mbox.setWindowTitle("Error")
        elif type == 'information':
            mbox.setIcon(QMessageBox.Info)
            if title:
                mbox.setWindowTitle(title)
            else:
                mbox.setWindowTitle("")
        elif type == 'warning':
            mbox.setIcon(QMessageBox.Warning)
            if title:
                mbox.setWindowTitle(title)
            else:
                mbox.setWindowTitle("Warning")

        mbox.exec_()
        
              ############end code from bera##############  

    
    #our owen close event to prevent the user from closing without intention
    #further more the measurment thread is closed
    def closeEvent(self, event):
        if self.shutDown == 1:
            event.ignore()
            return
        if self.shutDown == 2:
            self.thisplot.esc()#MS
            return

        if self.measurement_thread is not None:
            msg = QMessageBox(QMessageBox.Warning, "warning", 
                      "Sind sie sich sicher, dass Sie die Messung schließen"+
                      " möchten? Es ist nicht möglich die Messung zu einem"+
                      " späteren Zeitpunkt fortzuführen!")
            msg.addButton(QMessageBox.Ok)
            msg.addButton(QMessageBox.Cancel)
            ret = msg.exec_()
            if ret == QMessageBox.Ok:
           
                self.textEdit_out.setText('Stopping Measurement. Please wait')
                self.measurement_thread.stop = True
                self.measurement_thread.pause = False
                self.shutDown = 1
                event.ignore()
            else:
                event.ignore()
        else:
            self.thisplot.esc()#MS
            
            
            
    #taken from BERA-Messung.py
    def check_input(self):
        """
        Checks the entries of the textEdit Fields
        and shows Error Message if it is not correct"

        Returns
        -------
            False: Exception/Error while reading testEdit Field
            True: Entries correct
        """

        try:
            self.mousename=self.textEdit_Mousname.toPlainText()
            if self.mousename == 'Maus':
                raise ValueError('Mousename not changed')
        except:
            self.MessageBox("Please fill in Mousename")
            return False

        try:
            self.experimenter=self.textEdit_Experimenter.toPlainText()
            if self.experimenter == 'Experimenter':
                raise ValueError('Experimenter not changed')
        except:
            self.MessageBox("Please fill in Experimenter")
            return False

        try:
            self.status=self.textEdit_status.toPlainText()
            if self.status == 'pre_or_post':
                raise ValueError('Status not changed')
        except:
            self.MessageBox("Please fill in Status")
            return False
        
        #######End Code From Bera    
        try:
            self.status=self.textEdit_status.toPlainText()
            #check for whitespaces
            if re.search(r"\s", self.status):
                raise ValueError('Wrong Status')
            #check for correct form (pre/post (+ number))
            if self.status[:3] == 'pre':
                if len(self.status)!= 3:
                    int(self.status[3:])
            elif self.status[:4] == 'post':
                if len(self.status)!= 4:
                    int(self.status[4:])
            else:
                raise ValueError("Wrong Status")
        except:
            self.MessageBox("Please fill in Correct Status")
            return False

        return True


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LoadAndPlayKonfig()
    app.exec_()
