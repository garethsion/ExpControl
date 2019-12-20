import numpy as np
import pandas as pd
import datetime
from time import sleep
from matplotlib import pyplot as plt
from ExpControl.instrumentcontrol import InstrumentControl
from .interpolate_temp import interpolate_temp

class Measurements:
    def __init__(self,instr=['vna','gs','prx','keithley']):

        self.__ic = InstrumentControl()
        
        if 'vna' in instr:
            self.__vna = self.__ic.connect_to_vna()
        
        if 'prx' in instr:
            self.__prx = self.__ic.connect_to_er032m()
            self.set_zero_field()
        
        if 'gs' in instr:
            self.__gs = self.__ic.connect_to_gs200()
            self.__ic.set_zero_current(out='off')       
        
        if 'keithley' in instr:
            self.__keithley = self.__ic.connect_to_keithley_2400()
        
        return

    #def setup_vna(self,power=-30,avgs=1,measure='S21',format1='MLOG',format2='PHAS'):
    #    self.__ic.setup_vna(power=power,avgs=avgs,measure=measure,format1=format1,format2=format2)
        
    def setup_vna(self,power=-30,avgs=1,measure='S21',timeout=5000,format1='MLOG',format2='PHAS',format3='PHAS',format4='PHAS'):
        #self.__ic.setup_vna(power=power,avgs=avgs,measure=measure)
        self.__vna.set('power', power)
        self.__vna.set('avg', avgs)
        self.__vna.set('measure', measure)
        #self.__vna.set('format1',format1)
        #self.__vna.set('format2',format2)
        #self.__vna.set('format2',format3)
        #self.__vna.set('format3',format4)
        self.__vna.timeout.set(timeout)
     
    def setup_keithley(self,current=10e-06, complvoltage = 10e-03):
        self.__keithley_current = current
        self.__keithley_complvoltage = complvoltage
        self.__ic.setup_keithley()
    
    def resistance_measure(self):
        self.__keithley.curr(self.__keithley_current)
        self.__keithley.output(1)
        res1 = self.__keithley.resistance()
        self.__keithley.output(0)
        self.__keithley.curr(-self.__keithley_current)
        self.__keithley.output(1)
        res2 = self.__keithley.resistance()
        self.__keithley.output(0)
        resistance=(res1+res2)/2
        return resistance

    def get_temp(self):
        global data
        resistance=self.resistance_measure();
        temp=interpolate_temp(resistance);
        return temp
    
    def trace(self,start,stop,npts=1001,bandwidth=1000,background=None,plotting=True):
        self.__vna.set('npts', npts)
        self.__vna.set('bandwidth', bandwidth)

        freqs = np.linspace(start, stop, npts)
        self.__vna.set('start', start)
        self.__vna.set('stop', stop)
        
        t0 = datetime.datetime.now()
        data = self.__vna.trace()
        print('Trace took {}'.format(datetime.datetime.now() - t0))
        
        NoneType = type(None)
        if not isinstance(background, NoneType):
            data[0] -= background
        
        if plotting:
            plt.figure(figsize=(12,10))
            plt.plot(freqs/1e9, data[0],linewidth=3.0)
            # plt.plot(freqs/1e9, data[1])
            plt.xlabel('Frequency (GHz)',fontsize=28)
            plt.ylabel('$S_{21}$ (dB)',fontsize=28)
            plt.title('{:.4f} GHz - {:.4f} GHz'.format(start*1e-09,stop*1e-09),fontsize=30)
            plt.grid()
            plt.show()

        return freqs,data
        
    # def trace(self,start,stop,npts=1001,bandwidth=1000):
        # #self.__vna.timeout.set(5000)
        # self.__vna.set('npts', npts)
        # self.__vna.set('bandwidth', bandwidth)

        # freqs = np.linspace(start, stop, npts)
        # self.__vna.set('start', start)
        # self.__vna.set('stop', stop)
        
        # t0 = datetime.datetime.now()
        # data = self.__vna.trace()
        # print('Trace took {}'.format(datetime.datetime.now() - t0))
        
        # plt.figure(figsize=(12,10))
        # plt.plot(freqs/1e9, data[0],linewidth=3.0)
        # # plt.plot(freqs/1e9, data[1])
        # plt.xlabel('Frequency (GHz)',fontsize=28)
        # plt.ylabel('$S_{21}$ (dB)',fontsize=28)
        # plt.title('{:.4f} GHz - {:.4f} GHz'.format(start*1e-09,stop*1e-09),fontsize=30)
        # plt.grid()
        # plt.show()

        # return freqs,data
    
    def set_field_sweep_params(self, blow=0, bhigh=301, bit=2, field_limit=20002, flow=7e09, fhigh=8e09):
        self.__blow = blow
        self.__bhigh = bhigh
        self.__bit = bit
        self.__field_limit =field_limit
        self.__flow = flow
        self.__fhigh = fhigh
        
    def set_zero_field(self):
        self.__ic.set_zero_field()
        
    def set_field(self,field_gauss):
        caled_field = self.__ic.field_cal(field_gauss)
        self.__prx.open()
        self.__prx.write('CF+{}'.format(caled_field))
        self.__prx.close()
    
    def run_field_sweep(self, npts=2001, bw=1000, save='on', file='~\\'):
        
        field_arr = np.arange(self.__blow,self.__bhigh,self.__bit)

        t0 = datetime.datetime.now()
        for i in range(0,len(field_arr)):
            if field_arr[i] > self.__field_limit:
                raise Exception('Field = {:.3f}  mT- exceeds field limit ({:.3f} mT)'.format(field_arr[i]/10,self.__field_limit/10))
            else:
                self.__prx.open()
                self.__prx.write('CF+{}.00'.format(field_arr[i]))
                sleep(10)
                tr = self.trace(self.__flow,self.__fhigh,npts=npts,bandwidth=bw,background=None,plotting=True)
                self.__prx.close()
                print('B = {:.3f} mT'.format(field_arr[i]/10))
                
                if save:
                    filename = file + '{} mT.pkl'.format(field_arr[i]/10)
                    df = pd.DataFrame(data={'freq':tr[0],'ch1':tr[1][0],'ch2':tr[1][1]})
                    df.to_pickle(filename)
        
    def set_current_sweep_params(self, Ilow=0, Ihigh=1e-02, Iit = 500e-06, current_limit = 2e-01, flow=7.490e09, fhigh=7.494e09):
        self.__Ilow = Ilow
        self.__Ihigh = Ihigh
        self.__Iit = Iit
        self.__current_limit = current_limit
        self.__flow = flow
        self.__fhigh = fhigh
    
    def current_sweep(self, field=0, npts=2001, bw=1000, save='on', file='~\\'):
        current_arr = np.arange(self.__Ilow,self.__Ihigh,self.__Iit)

        self.__gs.output('on')    
        time.sleep(3)

        t0 = datetime.datetime.now()
        for i in range(0,len(current_arr)):
            current = current_arr[i]
            if current > self.__current_limit:
                raise Exception('Current = {:.3f}  uA- exceeds current limit ({:.3f} uA)'.format(current*1e06,self.__current_limit*1e06))
            else:
                self.__gs.current(current)
                print('Current = {:.3f} $\mu A$'.format(current*1e06))
                time.sleep(8)
                trace(self.__flow,self.__fhigh,field=field,current=current,npts=npts,bandwidth=bw,save=save,filedir=file)        
        
        print('Sweep took {}'.format(datetime.datetime.now() - t0))
        self.__gs.current(0)
        self.__gs.output('off')        
        return
