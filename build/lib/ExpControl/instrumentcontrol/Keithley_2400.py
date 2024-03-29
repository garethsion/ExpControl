from qcodes import VisaInstrument
from qcodes.utils.validators import Strings


class Keithley_2400(VisaInstrument):

    def __init__(self, name, address, **kwargs):
        super().__init__(name, address, terminator='\n', **kwargs)

        self.add_parameter('rangev',
                           get_cmd='SENS:VOLT:RANG?',
                           get_parser=float,
                           set_cmd='SOUR:VOLT:RANG {:f}',
                           label='Voltage range')

        self.add_parameter('rangei',
                           get_cmd='SENS:CURR:RANG?',
                           get_parser=float,
                           set_cmd='SOUR:CURR:RANG {:f}',
                           label='Current range')

        self.add_parameter('compliancev',
                           get_cmd='SENS:VOLT:PROT?',
                           get_parser=float,
                           set_cmd='SENS:VOLT:PROT {:f}',
                           label='Voltage Compliance')

        self.add_parameter('compliancei',
                           get_cmd='SENS:CURR:PROT?',
                           get_parser=float,
                           set_cmd='SENS:CURR:PROT {:f}',
                           label='Current Compliance')

        self.add_parameter('volt',
                           get_cmd=':READ?',
                           get_parser=self._volt_parser, 
                           set_cmd=':SOUR:VOLT:LEV {:.8f}',
                           label='Voltage',
                           unit='V')

        self.add_parameter('curr', 
                           get_cmd=':READ?',
                           get_parser=self._curr_parser, 
                           set_cmd=':SOUR:CURR:LEV {:.8f}',
                           label='Current',
                           unit='A')

        self.add_parameter('mode',
                           vals=Strings(),
                           get_cmd=':SOUR:FUNC?',
                           set_cmd=self._set_mode_and_sense,
                           label='Mode')

        self.add_parameter('sense',
                           vals=Strings(),
                           get_cmd=':SENS:FUNC?',
                           set_cmd=':SENS:FUNC "{:s}"',
                           label='Sense mode')

        self.add_parameter('output',
                           get_parser=int,
                           set_cmd=':OUTP:STAT {:d}',
                           get_cmd=':OUTP:STAT?')

        self.add_parameter('nplcv',
                           get_cmd='SENS:VOLT:NPLC?',
                           get_parser=float,
                           set_cmd='SENS:VOLT:NPLC {:f}',
                           label='Voltage integration time')

        self.add_parameter('nplci',
                           get_cmd='SENS:CURR:NPLC?',
                           get_parser=float,
                           set_cmd='SENS:CURR:NPLC {:f}',
                           label='Current integration time')

        self.add_parameter('resistance',
                           get_cmd=':READ?',
                           get_parser=self._resistance_parser, 
                           label='Voltage',
                           unit='V')

    def _set_mode_and_sense(self, msg):
        # This helps set the correct read out curr/volt
        if msg == 'VOLT':
            self.sense('CURR')
        elif msg == 'CURR':
            self.sense('VOLT')
        else:
            raise AttributeError('Mode does not exist')
        self.write(':SOUR:FUNC {:s}'.format(msg))
           
    def reset(self):
        self.write(':*RST')

    def _volt_parser(self, msg):
        MerlinSmiler = [float(x) for x in msg.split(',')]
        return MerlinSmiler[0]

    def _curr_parser(self, msg):
        MerlinSmilerIkke = [float(x) for x in msg.split(',')]
        return MerlinSmilerIkke[1]

    def _resistance_parser(self, msg):
        JohanSmiler = [float(x) for x in msg.split(',')]
        return JohanSmiler[0]/JohanSmiler[1]
