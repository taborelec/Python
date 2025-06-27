import os
import sys

srcpath = os.path.realpath('SourceFiles')
sys.path.append(srcpath)

from tevisainst import TEVisaInst

import numpy as np

ncoFreq = 2E9

#Set rates for DAC 
sampleRateDAC = 2E9
sampleDuration = 1/sampleRateDAC

dcSamples = 256
pulseWidth = 0.1E-6
prf =1000
pri = 1/prf
rotation = (1/35)*60 # RPM * 60 (Seconds)
print('Radar Rotation Speed: {0}s'.format(rotation))
pulsesPerRotation = round(rotation/pri / 1.0)
print('Pulses per Rotataion: {0}'.format(pulsesPerRotation))
numNoPulseSamples = (pri-pulseWidth)/sampleDuration
numNoPulseSamples = round(numNoPulseSamples / 256) * 256
numberDCLoops = numNoPulseSamples/dcSamples
print('DC Loops: {0}'.format(numberDCLoops))
numPulseSamples = pulseWidth/sampleDuration
numPulseSamples = round(numPulseSamples / 256) * 256

#waveform parameters
max_dac=(2**16)-1 # Max Dac
half_dac=max_dac/2 # DC Level
min_dac = 0
data_type = np.uint16 # DAC data type


'''
# Connect to instrument(PXI)
sid = 7 #PXI slot of AWT on chassis <------------ SLOT NUMBER HERE
from teproteus import TEProteusAdmin as TepAdmin
admin = TepAdmin() #required to control PXI module
inst = admin.open_instrument(slot_id=sid) 
resp = inst.send_scpi_query("*IDN?") # Get the instrument's *IDN
print('connected to: ' + resp) # Print *IDN

'''

# Connect to instrument(LAN)
inst_addr = 'TCPIP::192.168.1.8::5025::SOCKET' #Proteus Lan
#inst_addr = 'TCPIP::127.0.0.1::5025::SOCKET' #Proteus Local 
inst_addr = 'TCPIP::169.254.124.21::5025::SOCKET' #Proteus Lan
inst = TEVisaInst(inst_addr) # get instruent pointer
resp = inst.send_scpi_query("*IDN?")
print('Connected to: ' + resp) # print insturmrnt ID

resp = inst.send_scpi_query("*OPT?")
print('Options: ' + resp) # print insturmrnt ID

# initialize DAC
inst.send_scpi_cmd('*CLS; *RST')

#AWG channel
ch = 1 # everythinf after relates to CH 1
cmd = ':INST:CHAN {0}'.format(ch)
inst.send_scpi_cmd(cmd)

inst.send_scpi_cmd(':FREQ:RAST {0}'.format(sampleRateDAC)) 
inst.send_scpi_cmd(':INIT:CONT ON')
inst.send_scpi_cmd(':TRAC:DEL:ALL')

amplitudeUp = np.arange(0.5, 1.0, (1.0-0.5)/(pulsesPerRotation/2))
amplitudeDown = np.arange(1.0, 0.5, (-1*(1.0-0.5)/(pulsesPerRotation/2)))                        
antPatern = np.concatenate((amplitudeUp, amplitudeDown))

print(antPatern)

for pulses in range(1, pulsesPerRotation+1):
    # Define segment memory
    print(antPatern[pulses-1])
    dacWaveOn = np.ones(numPulseSamples)
    dacWaveOn = dacWaveOn * (max_dac) 
    dacWaveOn = dacWaveOn * antPatern[pulses-1]
    dacWaveOn = dacWaveOn.astype(data_type)
    arr_tuple = (dacWaveOn, dacWaveOn)
    dacWaveOnIQ = np.vstack(arr_tuple).reshape((-1,), order='F')

    cmd = ':TRAC:DEF {0}, {1}'.format(pulses, len(dacWaveOnIQ))
    inst.send_scpi_cmd(cmd)
    
    # Select the segment
    cmd = ':TRAC:SEL {0}'.format(pulses)
    inst.send_scpi_cmd(cmd)
    
    # Increase the timeout before writing binary-data:
    inst.timeout = 30000
    # Send the binary-data with *OPC? added to the beginning of its prefix.
    inst.write_binary_data('*OPC?; :TRAC:DATA', dacWaveOnIQ)
    # Set normal timeout
    inst.timeout = 10000
    
    resp = inst.send_scpi_query(':SYST:ERR?')
    print("Trace {0} Download Error = ".format(pulses))
    print(resp)

DCSegNum = pulsesPerRotation + 1

dacWaveOff = np.ones(dcSamples)
dacWaveOff = dacWaveOff * half_dac 
dacWaveOff = dacWaveOff.astype(data_type)   
arr_tuple = (dacWaveOff, dacWaveOff)
dacWaveOffIQ = np.vstack(arr_tuple).reshape((-1,), order='F')

cmd = ':TRAC:DEF {0}, {1}'.format(DCSegNum, len(dacWaveOffIQ))
inst.send_scpi_cmd(cmd)

# Select the segment
cmd = ':TRAC:SEL {0}'.format(DCSegNum)
inst.send_scpi_cmd(cmd)

# Increase the timeout before writing binary-data:
inst.timeout = 30000
# Send the binary-data with *OPC? added to the beginning of its prefix.
inst.write_binary_data('*OPC?; :TRAC:DATA', dacWaveOffIQ)
# Set normal timeout
inst.timeout = 10000

resp = inst.send_scpi_query(':SYST:ERR?')
print("Trace {0} Download Error = ".format(DCSegNum))
print(resp)
    

#Direct RF Output CH
cmd = ':INST:CHAN {0}'.format(ch)
inst.send_scpi_cmd(cmd)

cmd = ':TASK:COMP:LENG {0}'.format((pulsesPerRotation*2))
inst.send_scpi_cmd(cmd)

taskCounter = 1 
for pulses in range(1, (pulsesPerRotation+1)):
    
    print('Task: {0} Pulse: {1}'.format(taskCounter, pulses))
    cmd = ':TASK:COMP:SEL {0}'.format(taskCounter)
    inst.send_scpi_cmd(cmd)
    cmd = ':TASK:COMP:SEGM {0}'.format(pulses)
    inst.send_scpi_cmd(cmd)
    cmd = ':TASK:COMP:LOOP 1'
    inst.send_scpi_cmd(cmd)
    cmd = ':TASK:COMP:NEXT1 {0}'.format(taskCounter+1)
    inst.send_scpi_cmd(cmd)

    numberDCLoops1 = 20
    cmd = ':TASK:COMP:SEL {0}'.format(taskCounter+1)
    inst.send_scpi_cmd(cmd)
    cmd = ':TASK:COMP:SEGM {0}'.format(DCSegNum)
    inst.send_scpi_cmd(cmd)
    cmd = ':TASK:COMP:LOOP {0}'.format(numberDCLoops1)
    inst.send_scpi_cmd(cmd)
    if pulses == pulsesPerRotation:
        cmd = ':TASK:COMP:NEXT1 1'
        inst.send_scpi_cmd(cmd)
    else:
        cmd = ':TASK:COMP:NEXT1 {0}'.format(taskCounter+2)
        inst.send_scpi_cmd(cmd)
    taskCounter = taskCounter + 2

cmd = ':TASK:COMP:WRITE'
inst.send_scpi_cmd(cmd)
cmd = ':SOUR:FUNC:MODE TASK'
inst.send_scpi_cmd(cmd)

resp = inst.send_scpi_query(':SYST:ERR?')
print("End of Task, Gen Error = ")
print(resp)

cmd = ':SOUR:MODE DUC'
resp = inst.send_scpi_cmd(cmd)

cmd = ':SOUR:INT X4'
resp = inst.send_scpi_cmd(cmd)

cmd = ':SOUR:IQM ONE'
resp = inst.send_scpi_cmd(cmd)

sampleRateDACInt = sampleRateDAC * 4
print('Sample Clk Freq {0}'.format(sampleRateDACInt))
cmd = ':FREQ:RAST {0}'.format(sampleRateDACInt)
resp = inst.send_scpi_cmd(cmd)

resp = inst.send_scpi_query(':SYST:ERR?')
print("IQ Set Error = ")
print(resp)

cmd = ':SOUR:NCO:CFR1 {0}'.format(ncoFreq)
resp = inst.send_scpi_cmd(cmd)

cmd = ':VOLT MAX'
rc = inst.send_scpi_cmd(cmd)

cmd = ':VOLT:OFFS 0'
rc = inst.send_scpi_cmd(cmd)
    
cmd = ':OUTP ON'
rc = inst.send_scpi_cmd(cmd)

resp = inst.send_scpi_query(':SYST:ERR?')
print("End of CH1, Gen Error = ")
print(resp)

print('Radar Rotation Speed: {0}s'.format(rotation))
print('Pulses per Rotataion: {0}'.format(pulsesPerRotation))
print('DC Loops: {0}'.format(numberDCLoops))
































