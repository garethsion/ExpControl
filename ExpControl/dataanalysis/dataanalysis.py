import numpy as np
import pandas as pd 
import lmfit
from lmfit.models import BreitWignerModel,LinearModel
from matplotlib import pyplot as plt

class DataAnalysis:
    def __init__(self):
        return
        
    def LorentzianFit(self,freq,trace, plot = True):
        
        if np.any(np.iscomplex(trace)):
            trace = trace.real
        
        #print (len(trace))
        start,stop = None, None                                         #Specifies the window within the data to analyse.
        Lin_mod = LinearModel()                                         #Linear lmfit model for background offset and slope
        BW_mod = BreitWignerModel()                                     #Breit-Wigner-Fano model
        mod = BW_mod+Lin_mod
        
        x = freq[start:stop]/1E6                                        #Convert frequencies to MHz
        trace = (10**(trace/10))                                        #Convert decibel data to linear
        y = trace[start:stop]
        
        pars = BW_mod.guess(y, x=x)                                     #Initialize fit params
        pars += Lin_mod.guess(y,x=x, slope = 0, vary = False)           
        pars['center'].set(value=x[np.argmax(y)], vary=True, expr='')   #Find the highest transmission value. Corresponding frequency is used as a guess for the centre frequency
        pars['sigma'].set(value=0.05, vary=True, expr='')               #Linewidth
        pars['q'].set(value=0, vary=True, expr='')                      #Fano factor (asymmetry term). q=0 gives a Lorentzian
        pars['amplitude'].set(value=-0.03, vary=True, expr='')          #Amplitude

        out  = mod.fit(y,pars,x=x)
        sigma = out.params['sigma']
        centre = out.params['center']
        
        dic = {'x':x,'y':y,'fit':out.best_fit,'out':out,'sigma':sigma.value,
               'centre':centre.value,'Q':centre.value/sigma.value}
        
        df = pd.DataFrame(data=dic)

        if plot == True:
            print(out.params['amplitude'],out.params['q'],out.params['sigma'])
            plt.plot(x,y, color = 'orange', label = 'Data')
            plt.plot(x, out.best_fit, color = 'darkslateblue',label = 'Fano resonance fit')
        return df

    def fit_3dB(self,freq,trace,freqbounds=()):

        if np.any(np.iscomplex(trace)):
                trace = trace.real
        
        if not any(freqbounds):
            freqbounds = (min(freq),max(freq))

        fcutl = [abs(i-freqbounds[0]) for i in freq]
        fcutl = fcutl.index(min(fcutl))
        fcuth = [abs(i-freqbounds[1]) for i in freq]
        fcuth = fcuth.index(min(fcuth))

        f = freq[fcutl:fcuth]
        s = trace[fcutl:fcuth]

        # Find resonant frequency
        max_s = np.where(s==max(s))[0][0]
        fo = f[max_s]
        so = s[max_s]

        # Split data into LHS and RHS components
        flhs = f[0:max_s+1]
        frhs = f[max_s:]

        slhs = s[0:max_s+1]
        srhs = s[max_s:]

        # Get peak indices for LHS and RHS
        so_lhs_idx = slhs[max_s]
        so_rhs_idx = srhs[0]

        low_3dB = slhs.flat[np.abs(slhs - (so_lhs_idx-3)).argmin()]
        up_3dB = srhs.flat[np.abs(srhs - (so_lhs_idx-3)).argmin()]

        flow = f[np.where(s==low_3dB)[0][0]]
        fup = f[np.where(s==up_3dB)[0][0]]

        BW = fup - flow

        Q = fo / BW

        dic = [{'center':fo,'fwhm':BW,'Q':Q}]
        df = pd.DataFrame(data=dic)

        return df
    
    def loaded_quality_factor(self):
        fit = self.LorentzianFit(self.__freq,self.__s21,plot=False)
        return fit.Q.values[0]
        