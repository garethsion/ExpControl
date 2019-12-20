import qcodes as qc
from qcodes.instrument_drivers.Keysight.Keysight_E5071C import Keysight_E5071C
import pyvisa
import visa

class InstrumentControl:
    def __init__(self,vna_address='169.254.71.72')
        self.vna = Keysight_E5071C('VNA','TCPIP0::'+vna_address+'::INSTR')
    
    def setup_vna(self,power=-30,avgs=1,measure='S21'):
        self._power = power
        self._avgs = avgs
        self._measure = measure
        
        self.__vna.set('power', self._power)
        self.__vna.set('avg', self._avgs)
        self.__vna.set('measure', self._measure)
        self.__vna.timeout.set(5000)
        #self.__vna.set('format1',format1)
        #self.__vna.set('format2',format2)
        #self.__vna.set('format2',format3)
        #self.__vna.set('format3',format4)
        
    @property
    def power(self):
        return self._power
        
    @power.setter
    def power(self,power):
        self._power = power
        
    @property
    def avgs(self):
        return self._avgs
        
    @avgs.setter
    def avgs(self,avgs):
        self._avgs = avgs
        
    @property
    def measure(self):
        return self._measure
        
    @measure.setter
    def power(self,measure):
        self._measure = measure