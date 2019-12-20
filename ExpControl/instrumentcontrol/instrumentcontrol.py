import qcodes as qc
#from qcodes.instrument_drivers.Keysight.Keysight_E5071C import Keysight_E5071C
from qcodes.instrument_drivers.Keysight.Keysight_E5071C import Keysight_E5071C
from qcodes.instrument_drivers.yokogawa.GS200 import GS200
from .Keithley_2400 import Keithley_2400
from .RotatingStage import RotatingStage
import pyvisa
import visa

class InstrumentControl:
    def __init__(self):
        return
    
    def connect_to_vna(self,vna_address='169.254.71.72'):
        self.__vna = Keysight_E5071C('VNA','TCPIP0::'+vna_address+'::INSTR')
        return self.__vna
    
    def connect_to_gs200(self):
        self.__gs = GS200("gs200", 'USB0::0x0B21::0x0039::91L752855::INSTR', terminator="\n")
        return self.__gs

    def connect_to_keithley_2400(self,gpib_address = '25',GPIB='GPIB0'):
        self.__keithley = Keithley_2400('K2400',GPIB +'::'+gpib_address+'::INSTR')
        return self.__keithley
    
    def connect_to_er032m(self,com='COM21'):
        rm = pyvisa.ResourceManager()
        self.__prx = rm.open_resource('COM21')
        print('Connnected to:    Bruker ER 032M')
        self.__prx.write('++mode 1') # Controller
        self.__prx.write('++auto 0') # listen
        self.__prx.write('++addr '+'ASRL2')
        self.__prx.write('++addr')
        self.__prx.write('++eos 0') # CR/LF
        self.__prx.write('++eoi 1') # Enable EOI assertion
        self.__prx.write('++read eoi')
        self.__prx.write('CF+0.00')
        self.__prx.close()    
        return self.__prx
       
    def connect_to_rotating_stage(self):       
        serial_address = 'ASRL23::INSTR'
        self.__stage = RotatingStage('stage',serial_address)
        
    def fast_rotation(self,global_step=0,steps=0,direction='left'):
        rot_direction = 'direction'  # Right = clockwise viewed from above; left = counter clockwise
        stage.steps(steps)

        if rot_direction == 'left':
            stage.stepleft()
            step_global = step_global + steps
            
        if rot_direction == 'right':
            stage.stepright()
            step_global = step_global - steps
            
        print('Global Step = {}'.format(step_global))
    
    #def setup_vna(self,power=-30,avgs=1,measure='S21',format1='MLOG',format2='PHAS'):
    #    #power = -30
    #    #avgs = 1

    #    self.__vna.set('power', power)
    #    self.__vna.set('avg', avgs)
    #    self.__vna.set('measure', measure)
    #    self.__vna.set('format1',format1)
    #    self.__vna.set('format2',format2)
    #    self.__vna.timeout.set(5000)
    
    def setup_vna(self,power=-30,avgs=1,measure='S21',format1='MLOG',format2='PHAS',format3='PHAS',format4='PHAS'):
        #power = -30
        #avgs = 1

        self.__vna.set('power', power)
        self.__vna.set('avg', avgs)
        self.__vna.set('measure', measure)
        #self.__vna.set('format1',format1)
        #self.__vna.set('format2',format2)
        #self.__vna.set('format2',format3)
        #self.__vna.set('format3',format4)
        self.__vna.timeout.set(5000)
        
    def setup_keithley(self):
        self.__keithley.reset()
        self.__keithley.write('FUNC "RES"') #Measure resistance
        self.__keithley.write('RES:MODE MAN') #Set current and complvoltage manually
        #self.__keithley.write('RES:RANG 100')
        self.__keithley.write(':SENS:RES:NPLC 10') #Slow speed, high accuracy
        self.__keithley.write(':SYST:RSEN ON') #4-wire
        self.__keithley.write(':SYST:BEEP:STAT 0') #Turn off annoying beeping
        #self.__keithley.write(':FORM:ELEM RES')
        self.__keithley.curr(10e-6) #For safety set low current suring setup
        self.__keithley.compliancev(10e-3)

    def field_cal(self,field_gauss):
        cal = 1.371742112
        return field_gauss*cal # in Gauss
    
    def set_zero_field(self):
        self.__prx.open()
        self.__prx.write('CF+102.10') # Zero point is 102.10 Gauss
        self.__prx.close()
          
    def set_zero_current(self,out='off'):
        self.__gs.current(0)
        self.set_current_source_output(out=out)
        
    def set_current_source_output(self,out='off'):
        self.__gs.output(out)
