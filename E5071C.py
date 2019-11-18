from qcodes import VisaInstrument
from qcodes.utils import validators as vals
from cmath import phase
import numpy as np
from qcodes import MultiParameter, Parameter


class FrequencySweep(MultiParameter):
    """
    Hardware controlled parameter class for Rohde Schwarz RSZNB20 trace.

    Instrument returns an list of transmission data in the form of a list of
    complex numbers taken from a frequency sweep.

    TODO:
      - ability to choose for abs or db in magnitude return
    """
    def __init__(self, name, instrument, start, stop, npts):
        super().__init__(name, names=("", ""), shapes=((), ()))
        self._instrument = instrument
        self.set_sweep(start, stop, npts)
        self.names = ('magnitude', 'phase')
        self.units = ('dB', 'deg')
        self.setpoint_names = (('frequency',), ('frequency',))

    def set_sweep(self, start, stop, npts):
        #  needed to update config of the software parameter on sweep chage
        # freq setpoints tuple as needs to be hashable for look up
        f = tuple(np.linspace(int(start), int(stop), num=npts))
        self.setpoints = ((f,), (f,))
        self.shapes = ((npts,), (npts,))

    def get(self):
        self._instrument.cont_meas_off()
        self._instrument.write('FORM:DATA ASC')
        self._instrument.write('SENS1:AVER ON')
        self._instrument.write('SENS1:AVER:CLE')

        # instrument averages over its last 'avg' number of sweeps
        # need to ensure averaged result is returned
        for avgcount in range(self._instrument.avg()):
            self._instrument.write(':TRIG:SING; *WAI')
        self._instrument.write('CALC1:PAR1:SEL')
        mag_str = self._instrument.ask('CALC1:DATA:FDATA?').split(',')[::2] 
        mag_list = [float(v) for v in mag_str]
        self._instrument.write('CALC1:PAR2:SEL') #CALC2 does PORT2!
        phas_str = self._instrument.ask('CALC1:DATA:FDATA?').split(',')[::2]
        phas_list = [float(v) for v in phas_str]
        
        self._instrument.cont_meas_on()
        return np.array(mag_list), np.array(phas_list)


class Keysight_E5071C(VisaInstrument):
    """
    qcodes driver for the Rohde & Schwarz ZNB20 virtual network analyser

    Requires FrequencySweep parameter for taking a trace

    TODO:
    - centre/span settable for frequwncy sweep
    - check initialisation settings and test functions
    - S11/S12 ... selection
    - set correct timeout
    """
    def __init__(self, name, address, **kwargs):

        super().__init__(name=name, address=address, **kwargs)

        self.add_parameter(name='power',
                           label='Power',
                           unit='dBm',
                           get_cmd='SOUR:POW?',
                           set_cmd='SOUR:POW {:.4f}',
                           get_parser=float,
                           vals=vals.Numbers(-150, 10))

        self.add_parameter(name='bandwidth',
                           label='Bandwidth',
                           unit='Hz',
                           get_cmd='SENS:BAND?',
                           set_cmd='SENS:BAND {:.4f}',
                           get_parser=int,
                           vals=vals.Numbers(1, 1e6))

        self.add_parameter(name='avg',
                           label='Averages',
                           unit='',
                           get_cmd='SENS:AVER:COUN?',
                           set_cmd='SENS:AVER:COUN {:.4f}',
                           get_parser=int,
                           vals=vals.Numbers(1, 999))

        self.add_parameter(name='start',
                           get_cmd='SENS:FREQ:START?',
                           set_cmd=self._set_start,
                           get_parser=float)

        self.add_parameter(name='stop',
                           get_cmd='SENS:FREQ:STOP?',
                           set_cmd=self._set_stop,
                           get_parser=float)
        
        self.add_parameter(name='center',
                           get_cmd='SENS:FREQ:CENTER?',
                           set_cmd=self._set_center,
                           get_parser=float)
    
        self.add_parameter(name='span',
                           get_cmd='SENS:FREQ:SPAN?',
                           set_cmd=self._set_span,
                           get_parser=float)

        self.add_parameter(name='npts',
                           get_cmd='SENS:SWE:POIN?',
                           set_cmd=self._set_npts,
                           get_parser=int)

        self.add_parameter(name='trace',
                           start=self.start(),
                           stop=self.stop(),
                           npts=self.npts(),
                           parameter_class=FrequencySweep)
                           
        self.add_parameter('measure',
                           get_cmd='CALC:PAR:DEF?',
                           vals=vals.Enum('S11','S12','S21','S22'),
                           set_cmd=self._set_measure,
                           label='Sxy measurement parameter')

        self.add_function('reset', call_cmd='*RST')
        #self.add_function('tooltip_on', call_cmd='SYST:ERR:DISP ON')
        #self.add_function('tooltip_off', call_cmd='SYST:ERR:DISP OFF')
        self.add_function('cont_meas_on', call_cmd='TRIG:SOUR INT')
        self.add_function('cont_meas_off', call_cmd='TRIG:SOUR BUS')
        #self.add_function('update_display_once', call_cmd='SYST:DISP:UPD ONCE')
        #self.add_function('update_display_on', call_cmd='SYST:DISP:UPD ON')
        #self.add_function('update_display_off', call_cmd='SYST:DISP:UPD OFF')
        self.add_function('rf_off', call_cmd='OUTP OFF')
        self.add_function('rf_on', call_cmd='OUTP ON')

        self.initialise()
        self.connect_message()
        
    def _set_measure(self, val):
        Sxy = val;
        self.write('CALC1:PAR1:DEF {}'.format(Sxy))
        self.write('CALC1:PAR2:DEF {}'.format(Sxy))

    def _set_start(self, val):
        self.write('SENS:FREQ:START {:.4f}'.format(val))
        # update setpoints for FrequencySweep param
        self.trace.set_sweep(val, self.stop(), self.npts())

    def _set_stop(self, val):
        self.write('SENS:FREQ:STOP {:.4f}'.format(val))
        # update setpoints for FrequencySweep param
        self.trace.set_sweep(self.start(), val, self.npts())
        
    def _set_center(self, val):
        self.write('SENS:FREQ:CENTER {:.4f}'.format(val))
        # update setpoints for FrequencySweep param
        f1 = val-self.span()/2
        f2 = val+self.span()/2
        self.trace.set_sweep(f1, f2, self.npts())
        
    def _set_span(self, val):
        self.write('SENS:FREQ:SPAN {:.4f}'.format(val))
        # update setpoints for FrequencySweep param
        f1 = self.center()-val/2
        f2 = self.center()+val/2
        self.trace.set_sweep(f1, f2, self.npts())

    def _set_npts(self, val):
        self.write('SENS:SWE:POIN {:.4f}'.format(val))
        # update setpoints for FrequencySweep param
        self.trace.set_sweep(self.start(), self.stop(), val)

    def initialise(self):
        self.write('*RST')
        self.write('SENS1:SWE:TYPE LIN') #linear sweep SENS1?
        self.write('SENS1:SWE:TIME:AUTO ON') 
        self.write('TRIG:SOUR INT') #trig immediately when INIT:CON ON
        self.write('SENS1:AVER ON') #averaging ON

        self.write('CALC1:PAR:COUN 2') #add ampl 
        self.write('CALC1:PAR1:DEF S11') #make this a parameter! Do i need to change CALC1 SENS1 etc when measuring S22?
        self.write('CALC1:PAR1:SEL')
        self.write('CALC1:FORM MLOG')
        
        self.write('CALC1:PAR2:DEF S11')
        self.write('CALC1:PAR2:SEL')
        self.write('CALC1:FORM PHAS')
        
        self.write('INIT1:CONT ON') #maybe INIT2 too?
        self.start(1e6)
        self.stop(20e9)
        self.npts(201)
        self.power(-50)

