import qcodes as qc
import visa
import numpy as np
import matplotlib.pyplot as plt
from .Keithley_2400 import Keithley_2400
from interpolate_temp import interpolate_temp
from RepeatingTimer import RepeatingTimer
from os.path import join, exists
from os import makedirs
import time
import datetime

def setup_keithley():
    Keithley.reset()
    Keithley.write('FUNC "RES"') #Measure resistance
    Keithley.write('RES:MODE MAN') #Set current and complvoltage manually
    #Keithley.write('RES:RANG 100')
    Keithley.write(':SENS:RES:NPLC 10') #Slow speed, high accuracy
    Keithley.write(':SYST:RSEN ON') #4-wire
    Keithley.write(':SYST:BEEP:STAT 0') #Turn off annoying beeping
    #Keithley.write(':FORM:ELEM RES')
    Keithley.curr(10e-6) #For safety set low current suring setup
    Keithley.compliancev(10e-3)

def measure():
    Keithley.curr(current)
    Keithley.output(1)
    res1 = Keithley.resistance()
    Keithley.output(0)
    Keithley.curr(-current)
    Keithley.output(1)
    res2 = Keithley.resistance()
    Keithley.output(0)
    resistance=(res1+res2)/2
    return resistance

def getdata():
    global data
    posix=time.time();
    runtime=posix-starttime;
    resistance=measure();
    temp=interpolate_temp(resistance);
    data=np.append(data,[[runtime,posix,resistance,temp]],axis=0)
    print('Time: {:6.2f}s; POSIX: {:10.0f}; Resistance: {:6.2f}Ohm; Temp: {:6.3f}K'.format(runtime,posix,resistance,temp))

current = 10e-6; #Amps
complvoltage = 10e-3; #Volts

# #Keithley = Keithley_2400('K2400','COM2')
# #setup_keithley()
# #Keithley.curr(current)
# #Keithley.compliancev(complvoltage)

# Setup Keithley
gpib_address = '25';
Keithley = Keithley_2400('K2400','GPIB0::'+gpib_address+'::INSTR')
setup_keithley()
Keithley.curr(current)
Keithley.compliancev(complvoltage)

# Set up data storage
global data
data = np.empty([0,4])#Time,Res,Temp
filename=input('Enter a filename (optional): ')
if not filename: filename='data'+datetime.datetime.now().replace(microsecond=0).isoformat().replace(':','-')
folder=join('data','')
if not exists(folder): makedirs(folder);
fullpath=join(folder,filename+'.csv');

# Ask for time interval
usertime = input('Enter time interval >2sec: ')
timeinterval=(float(usertime) if usertime else 2.0);
if timeinterval<2.0: timeinterval=2.0;

# Run experiment
print('Starting experiment, press ENTER to stop...')
starttime=time.time();
rt = RepeatingTimer(timeinterval,getdata) #Do not set below 2s
input() # Wait for press enter
rt.stop()
np.savetxt(fullpath,data,delimiter=',',header='Time\tPOSIX\tResistance\tTemperature')
print('Data saved to '+fullpath)

# And a quick plot
plt.plot(data[:,0],data[:,3])
plt.xlabel('Time (s)')
plt.ylabel('Temperature (K)')
plt.title(filename)
plt.savefig(fullpath.replace('csv','png'))
plt.show()