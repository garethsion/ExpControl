from qcodes import VisaInstrument
from qcodes.utils import validators as vals

class RotatingStage(VisaInstrument):
    """
    qcodes driver for Rotation Stage
    
    For Bi-polar stepper motor
    for power supply: 12V and 1.5A limit is required
    
    USAGE:
    
    Tell arduino number of motor steps to move with 'stepper_steps <int>',
    ask with 'stepper_steps?'
    50 steps is about 4.5deg
    
    Initiate rotation by stepper_steps using commands 'stepright' or 'stepleft'
    
    Ask current step position with 'position', reset with 'resetposition'
    
    Add 'verbose=True' when calling RotatingStage to print all outputs
    """
    def __init__(self, name, address, verbose=False, **kwargs):

        super().__init__(name=name, address=address, terminator='\r\n', **kwargs)
        
        self.verbose = verbose # Print the response from every command

        self.add_parameter(name='steps',
                           label='Number of steps',
                           get_cmd='stepper_steps?',
                           set_cmd=self._set_stepper_steps,
                           get_parser=self._only_int,
                           vals=vals.Ints())
                           
        self.add_parameter(name='position',
                           label='Current position in steps',
                           get_cmd='position?',
                           get_parser=self._only_int,
                           vals=vals.Ints())

        self.add_function('stepright', call_cmd=self._step_right)
        self.add_function('stepclockwise', call_cmd=self._step_right)
        
        self.add_function('stepleft', call_cmd=self._step_left)
        self.add_function('stepanticlockwise', call_cmd=self._step_left)
        self.add_function('stepcounterclockwise', call_cmd=self._step_left)
        
        self.add_function('resetposition', call_cmd=self._reset_position)

        self.connect_message()
        
    def _whoami(self):
        self.ask('*IDN?')
        
    def _set_stepper_steps(self,stepper_steps):
        msg = self.ask('stepper_steps {:d}'.format(stepper_steps))
        if self.verbose: print(msg)
        
    def _reset_position(self):
        msg = self.ask('resetposition')
        if self.verbose: print(msg)
        
    def _step_right(self):
        msg = self.ask('stepright')
        if self.verbose: print(msg)
        
    def _step_left(self):
        msg = self.ask('stepleft')
        if self.verbose: print(msg)
        
    def _only_int(self,msg):
        return int(''.join(c for c in msg if c.isdigit() or c=='-'))