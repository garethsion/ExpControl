import os
from qcodes import ParamSpec
from qcodes.instrument.parameter import ManualParameter
from qcodes.dataset.measurements import Measurement
import qcodes.dataset.database as database
import qcodes.dataset.experiment_container as exc
from qcodes import initialise_or_create_database_at

class DatabaseHandler:
    def __init__(self):
        return
        
    def create_directory(self,parent_dir,directory):
        path = os.path.join(parent_dir, directory)

        try: 
            os.makedirs(path, exist_ok = True) 
            print("Directory '%s' created successfully" %directory) 
        except OSError as error: 
            print("Directory '%s' can not be created") 
    
        return path
        
    def create_database(self,filename,experiment_name,sample_name):
        #database.initialise_database()
        initialise_or_create_database_at(filename)

        try:
            experiment = exc.load_experiment_by_name(name=experiment_name,sample=sample_name)
        except ValueError:
            experiment = exc.new_experiment(name=experiment_name,sample_name=sample_name)
            print('new_experiment')
        
    def create_dataset(self,dataset_name):
        self.data_set = exc.new_data_set(dataset_name,
                                specs=[ParamSpec('caled_field', 'numeric', unit='G'),
                                       ParamSpec('frequency', 'array', unit='Hz'),
                                       ParamSpec('magnitude', 'array', unit='dB'),
                                       ParamSpec('phase', 'array', unit='deg'),
                                       ParamSpec('temp', 'numeric', unit='K'),
                                       ParamSpec('set_power', 'numeric', unit='dB')])
        self.data_set.mark_started()
        
        return self.data_set

        #meas = Measurement(data_set)
        #meas.register_parameter(vna.center)
        #meas.register_parameter(vna.trace.setpoints, setpoints=(vna.center))
        #meas.register_parameter(vna.trace.raw_value[0], setpoints=(vna.center))
        #meas.register_parameter(vna.trace.raw_value[1], setpoints=(vna.center))      
        
        #data_set.add_parameter(ParamSpec(name = 'caled_field',unit='G',paramtype='numeric'))
        #data_set.add_parameter(ParamSpec(name = 'power',unit='dBm',paramtype='numeric'))
        #data_set.add_parameter(ParamSpec(name = 'CenterFreq',unit='Hz',paramtype='numeric'))
        #data_set.add_parameter(ParamSpec(name = 'phase',unit='deg',paramtype='array'))
        #data_set.add_parameter(ParamSpec(name = 'magnitude',unit='dB',paramtype='array'))
        #data_set.add_parameter(ParamSpec(name = 'frequency',unit='Hz',paramtype='array'))