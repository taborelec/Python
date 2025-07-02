# -*- coding: utf-8 -*-
"""
Created on Tue Jul  1 13:57:41 2025

@author: marka
"""
import os
import sys

srcpath = os.path.realpath('SourceFiles')
sys.path.append(srcpath)

import warnings # this is for GUI warnings
warnings.filterwarnings("ignore")

import numpy as np
from tevisainst import TEVisaInst

# Downloaded waveform to Proteus must be a multiple of 64?

def round_up_64(n):
    """Round up to the nearest multiple of 64."""
    return ((n + 63) // 64) * 64

# --- Parameters ---
sampleRateDAC = 1e9  # 1 GS/s
segment_us = 100     # Total segment length in microseconds
pulse_us = 10        # Pulse width in microseconds

# --- Calculate lengths ---
desired_segment_len = int(segment_us * 1e-6 * sampleRateDAC)
segment_len = round_up_64(desired_segment_len)  # Must be multiple of 64

desired_pulse_len = int(pulse_us * 1e-6 * sampleRateDAC)
pulse_len = min(desired_pulse_len, segment_len)  # Pulse fits in segment

# --- Create waveform: 10us pulse, rest zeros ---
waveform = np.zeros(segment_len)
# Example: 5 cycles in 10us, amplitude 0.8
t = np.arange(pulse_len)
waveform[:pulse_len] = 0.8 * np.ones(pulse_len)

# --- Scale for DAC (unsigned 16-bit) ---
max_dac = 65535
half_dac = max_dac / 2
segment = ((waveform + 1.0) * half_dac).astype(np.uint16)

# --- Connect to Proteus and upload ---
inst_addr = 'TCPIP::192.168.1.12::5025::SOCKET'
inst = TEVisaInst(inst_addr)

inst.send_scpi_cmd('*CLS; *RST')
inst.send_scpi_cmd(':INST:CHAN 1')
inst.send_scpi_cmd(f':FREQ:RAST {sampleRateDAC}')
inst.send_scpi_cmd(':TRAC:DEL:ALL')
inst.send_scpi_cmd(f':TRAC:DEF 1, {segment_len}')
inst.send_scpi_cmd(':TRAC:SEL 1')
inst.write_binary_data('*OPC?; :TRAC:DATA', segment)

#the command :FUNC:MODE:SEGM is required the play the waveform when not using TASK
inst.send_scpi_cmd(':FUNC:MODE:SEGM 1')
inst.send_scpi_cmd(':OUTP ON')
inst.send_scpi_cmd(':INIT:CONT ON')

# --- Optional: check for errors ---
resp = inst.send_scpi_query(':SYST:ERR?')
print("Instrument Error Status:", resp)
