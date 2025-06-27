# -*- coding: utf-8 -*-
"""
Created on Fri Jun 27 08:10:37 2025

@author: marka
"""
import os
import sys

srcpath = os.path.realpath('../SourceFiles')
sys.path.append(srcpath)

import warnings # this is for GUI warnings
warnings.filterwarnings("ignore")

from tevisainst import TEVisaInst

import numpy as np
from scipy.signal import decimate

import matplotlib.pyplot as plt
from matplotlib.widgets import Button

import keyboard
import time

class ScopeFFTDisplay:
    def __init__(self, inst_addr='TCPIP::192.168.1.12::5025::SOCKET', sample_rate=5.4E9, numframes=1, framelen=20*4800, decimation_factor=10):
        # ADC/Display parameters
        self.data_type = np.uint16
        self.breakVal = 0
        self.dcOff = 0
        self.spectrumInv = 0
        self.useWindow = True  # Blackman
        self.timeBase = 0

        # Set sample rates for ADC
        self.sampleRateADC = sample_rate
        
        # Set Decimation
        self.decimation_factor = decimation_factor

        # Set number of frames to be collected
        self.numframes = numframes
        self.framelen = framelen
        self.totlen = numframes * framelen
        
        # Set True to use fake data instead of real acquisition
        self.use_fake_data = False  # Set True to use fake data instead of real acquisition

        # Set globals for button presses (as instance attributes)
        self.grid_button_500 = None
        self.grid_button_800 = None
        self.grid_button_1000 = None
        self.grid_button_trig = None
        self.grid_button_exit = None

        if self.use_fake_data:
            print('Not connected to fake data mode')
        else:
            # Connect to instrument(LAN)
            self.inst_addr = inst_addr
            self.inst = TEVisaInst(self.inst_addr)
            
            resp = self.inst.send_scpi_query("*IDN?")
            print('connected to: ' + resp)

        # Initialize GUI attributes
        self.line1 = None
        self.line2 = None
        self.xT = None
        self.xF = None
        self.figure = None

    def vMax(self, val):
        if self.use_fake_data:
            range_ = 'High'
        else:
            cmd = ':DIG:CHAN:RANG HIGH'
            self.inst.send_scpi_cmd(cmd)
            range_ = self.inst.send_scpi_query(':DIG:CHAN:RANG?')
        print('Range ' + range_)

    def vMed(self, val):
        if self.use_fake_data:
            range_ = 'Med'
        else:
            cmd = ':DIG:CHAN:RANG MED'
            self.inst.send_scpi_cmd(cmd)
            range_ = self.inst.send_scpi_query(':DIG:CHAN:RANG?')
        print('Range ' + range_)

    def vMin(self, val):
        if self.use_fake_data:
            range_ = 'Low'
        else:
            cmd = ':DIG:CHAN:RANG LOW'
            self.inst.send_scpi_cmd(cmd)
            range_ = self.inst.send_scpi_query(':DIG:CHAN:RANG?')
        print('Range ' + range_)

    def freeRun(self, val):
        cmd = ':DIG:TRIG:SOURCE CPU'
        self.inst.send_scpi_cmd(cmd)
        range_ = self.inst.send_scpi_query(':DIG:TRIG:SOURCE?')
        print('Trigger ' + range_)

    def trigExt(self, val):
        # Uncomment for external trigger commands, for now just set timeBase
        # cmd = ':DIG:TRIG:SOURCE TASK1'
        # self.inst.send_scpi_cmd(cmd)
        # range_ = self.inst.send_scpi_query(':DIG:TRIG:SOURCE?')
        # print('Trigger ' + range_)
        self.timeBase = 1

    def exitLoop(self, val):
        self.breakVal = 1
        
    def decimate_waveform(self, wav):
        if self.decimation_factor > 1:
            return decimate(wav, self.decimation_factor, ftype='fir', zero_phase=True)
        else:
            return wav

    def initADC(self):
        # initialize ADC
        if self.use_fake_data:
            print('Fake Data Mode')
        else:
            self.inst.send_scpi_cmd(':DIG:MODE SING')
    
            print('ADC Clk Freq {0}'.format(self.sampleRateADC))
            cmd = ':DIG:FREQ  {0}'.format(self.sampleRateADC)
            self.inst.send_scpi_cmd(cmd)
    
            # Enable capturing data from channel 1
            self.inst.send_scpi_cmd(':DIG:CHAN:SEL 1')
            self.inst.send_scpi_cmd(':DIG:CHAN:STATE ENAB')
            # Select the internal-trigger as start-capturing trigger:
            self.inst.send_scpi_cmd(':DIG:TRIG:SOURCE CPU')
    
            cmd = ':DIG:ACQuire:FRAM:DEF {0},{1}'.format(self.numframes, self.framelen)
            self.inst.send_scpi_cmd(cmd)
    
            # Select the frames for the capturing 
            capture_first, capture_count = 1, self.numframes
            cmd = ':DIG:ACQuire:FRAM:CAPT {0},{1}'.format(capture_first, capture_count)
            self.inst.send_scpi_cmd(cmd)
    
            # Start the digitizer's capturing machine
            self.inst.send_scpi_cmd(':DIG:INIT ON')
            self.inst.send_scpi_cmd(':DIG:TRIG:IMM')
            self.inst.send_scpi_cmd(':DIG:INIT OFF')
    
            # Choose which frames to read (all in this example)
            self.inst.send_scpi_cmd(':DIG:DATA:SEL ALL')
    
            # Choose what to read 
            self.inst.send_scpi_cmd(':DIG:DATA:TYPE FRAM')
    
            # Get the total data size (in bytes)
            resp = self.inst.send_scpi_query(':DIG:DATA:SIZE?')
            print('Total read size in bytes: ' + resp)
            print()

    def freqDomain(self, wav, spectrumInv=None, dcOff=None):
        if spectrumInv is None:
            spectrumInv = self.spectrumInv
        if dcOff is None:
            dcOff = self.dcOff

        wav = wav - dcOff
        if self.useWindow:
            win = np.blackman(len(wav))
            wavFFT = wav * win
        else:
            wavFFT = wav
        fourierTransform = np.fft.fft(wavFFT) / len(wav)
        fourierTransform = abs(fourierTransform[range(int(len(wav) / 2))])
        if spectrumInv == 1:
            fftPlot = np.log10(fourierTransform[::-1])
        else:
            fftPlot = np.log10(fourierTransform)
        return fftPlot

    def makeGUI(self):
        # Preallocate processing memory
        wav1 = np.ones(self.framelen, dtype=np.uint16) * 4096

        # Calculate Axis
        xT = np.linspace(0, self.numframes * self.framelen, self.numframes * self.framelen)
        xT = xT / self.sampleRateADC
        tpCount = len(wav1)
        timeStep = xT[1] - xT[0]
        xF = np.fft.fftfreq(tpCount, timeStep)
        xF = xF[range(int(len(wav1) / 2))]

        # Run GUI event loop
        plt.ion()

        # Create Plots and Sub Plots
        figure, ax1 = plt.subplots(2)
        line1, = ax1[0].plot(xT, wav1, color="yellow")
        line2, = ax1[1].plot(xF, self.freqDomain(wav1, 0, 0), color="yellow")

        ax1[0].set(xlabel='Time', ylabel='Amplitude (AU)')
        ax1[0].set_position([0.2, 0.55, 0.7, 0.35])
        ax1[0].set_ylim([0, 4096])
        ax1[0].set(facecolor="black")
        ax1[0].grid()

        ax1[1].set(xlabel='Frequency', ylabel='FFT Amplitude (AU)')
        ax1[1].set_position([0.2, 0.1, 0.7, 0.35])
        ax1[1].set_ylim([-5, 10])
        ax1[1].set(facecolor="black")
        ax1[1].grid()

        # Set buttons as instance attributes
        xAnchor = 0.04
        yAnchor = 0.33

        ax1_button_500 = plt.axes([xAnchor, 0.85, 0.03, 0.05])
        self.grid_button_500 = Button(ax1_button_500, 'Max', color='white', hovercolor='grey')
        self.grid_button_500.on_clicked(self.vMax)

        ax1_button_800 = plt.axes([xAnchor + 0.035, 0.85, 0.03, 0.05])
        self.grid_button_800 = Button(ax1_button_800, 'Med', color='white', hovercolor='grey')
        self.grid_button_800.on_clicked(self.vMed)

        ax1_button_1000 = plt.axes([xAnchor + (0.035 * 2), 0.85, 0.03, 0.05])
        self.grid_button_1000 = Button(ax1_button_1000, 'Min', color='white', hovercolor='grey')
        self.grid_button_1000.on_clicked(self.vMin)

        yAnchor = 0.7

        ax3_button_trig = plt.axes([0.04, yAnchor - 0.075, 0.1, 0.05])
        self.grid_button_trig = Button(ax3_button_trig, 'Trigger', color='white', hovercolor='grey')
        self.grid_button_trig.on_clicked(self.trigExt)

        ax3_button_exit = plt.axes([0.04, yAnchor - (0.075 * 3), 0.1, 0.05])
        self.grid_button_exit = Button(ax3_button_exit, 'Exit', color='white', hovercolor='grey')
        self.grid_button_exit.on_clicked(self.exitLoop)

        self.line1 = line1
        self.line2 = line2
        self.xT = xT
        self.xF = xF
        self.figure = figure

    def acquireData(self):
        if self.use_fake_data:
            t = np.arange(self.framelen) / self.sampleRateADC
            freq = 1e9  # 1000 MHz fake frequency
            wav1 = 2048 + 1000 * np.sin(2 * np.pi * freq * t)   # Sine wave
            wav1 += 200 * np.random.randn(self.framelen)        # Add noise
            wav1 = np.clip(wav1, 0, 4095).astype(np.uint16)     # Clip/saturate to ADC range
        else:
            wav1 = np.zeros(self.framelen, dtype=np.uint16)
    
            # Start the digitizer's capturing machine
            self.inst.send_scpi_cmd(':DIG:INIT ON')
            self.inst.send_scpi_cmd(':DIG:TRIG:IMM')
            self.inst.send_scpi_cmd(':DIG:INIT OFF')
    
            # Choose which frames to read (all in this example)
            self.inst.send_scpi_cmd(':DIG:DATA:SEL ALL')
    
            # Choose what to read 
            self.inst.send_scpi_cmd(':DIG:DATA:TYPE FRAM')
    
            # Get the total data size (in bytes)
            resp = self.inst.send_scpi_query(':DIG:DATA:SIZE?')
            num_bytes = np.uint32(resp)
    
            # Read the data that was captured by channel 1:
            self.inst.send_scpi_cmd(':DIG:CHAN:SEL 1')
            self.inst.read_binary_data(':DIG:DATA:READ?', wav1, num_bytes)
    
    
        wav1 = self.decimate_waveform(wav1)

        # Update axes based on decimation
        effective_sample_rate = self.sampleRateADC / self.decimation_factor
        num_samples = len(wav1)
        self.xT = np.arange(num_samples) / effective_sample_rate

        tpCount = num_samples
        timeStep = self.xT[1] - self.xT[0] if num_samples > 1 else 1.0/effective_sample_rate
        self.xF = np.fft.fftfreq(tpCount, timeStep)
        self.xF = self.xF[range(int(tpCount / 2))]

        # Plot the samples
        # Time
        self.line1.set_xdata(self.xT)
        self.line1.set_ydata(wav1)
        # Frequency
        self.line2.set_xdata(self.xF)
        self.line2.set_ydata(self.freqDomain(wav1))

        # draw updated values
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()

        time.sleep(0.1)
        del wav1

    def run(self):
        self.initADC()
        self.makeGUI()
        while True:
            try:
                if keyboard.is_pressed(' '):
                    print("Stop initiated...")
                    break
                if self.breakVal == 1:
                    print("Stop initiated...")
                    break

                self.acquireData()

            except Exception as e:
                print("Exception occurred:", e)
                break

        self.inst.close_instrument()


if __name__ == "__main__":
    scope_fft_display = ScopeFFTDisplay()
    scope_fft_display.use_fake_data = True  # <--- Enable fake data mode
    scope_fft_display.run()
