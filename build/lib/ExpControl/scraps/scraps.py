import numpy as np
import pandas as pd
import scraps as scr
import pickle
import pygtc
import pprint as pp
import numpy as np
from matplotlib import pyplot as plt
import csv
    
try: import simplejson as json
except ImportError: import json

class ScrapsWrapper:
    def __init__(self):
        return
    
    def pkl_to_s2p(self,pkl_file,s2p_file):
        pkl = pickle.load(open(pkl_file,'rb'))

        with open(s2p_file, 'w') as f:
            writer = csv.writer(f, delimiter='\t')
            writer.writerow(["Frequency", "I", "Q"])
            writer.writerows(zip(pkl.freq,pkl.ch1.values,pkl.ch2.values))

    def process_file(self,fileName,file, mask = None, meta_only=False, **loadtxt_kwargs):
        """Load Keysight PNA file data into dict."""
        #Find the temperature, power, and name locations from the filename
        tempLoc = fileName.find('TEMP') + 5
        pwrLoc = fileName.find('DBM') - 4
        
        sm = file.split('_')[0]
        smm = sm.split('-')
        fileName[0:fileName.find(smm[0])]
        nameNoDir = fileName.strip(fileName[0:fileName.find(smm[0])])

        resNameLoc = fileName.find(smm[0])

        if mask is None:
            mask = slice(None, None)
        else:
            assert type(mask) == slice, "mask must be of type slice."

        #Read the temp, pwr, and resName from the filename
        if(fileName[tempLoc + 1] == '.'):
            temp = np.float(fileName[tempLoc:tempLoc+5])

            if fileName[pwrLoc] == '_':
                pwr = np.float(fileName[pwrLoc+1:pwrLoc+3])
            else:
                pwr = np.float(fileName[pwrLoc:pwrLoc+3])

            resName = fileName[resNameLoc:resNameLoc+len(sm)]

            metaDict = {'name':resName,'temp':temp,'pwr':pwr}

            if meta_only:
                dataDict = {}
            else:
                #Grab frequency, I, and Q
                fileData = np.loadtxt(fileName, **loadtxt_kwargs)
                freqData = fileData[:,0][mask]
                IData = fileData[:,1][mask]
                QData = fileData[:,2][mask]

                dataDict = {'freq':freqData,'I':IData,'Q':QData}

            retVal = {}
            retVal.update(metaDict)
            retVal.update(dataDict)

            return retVal
        else:

            assert False, "Bad file? " + fileName
            
    def resonator_objects(self,fileDataDict):
        #Create a resonator object using the helper tool
        resObj1 = scr.makeResFromData(fileDataDict)

        #Create a resonator object using the helper tool and also fit the data
        #To do this, we pass a function that initializes the parameters for the fit, and also the fit function
        resObj2 = scr.makeResFromData(fileDataDict, paramsFn = scr.cmplxIQ_params, fitFn = scr.cmplxIQ_fit)

        #Check the temperature and power
        print('Temperature = ', resObj1.temp)
        print('Power = ', resObj1.pwr)

        #Check to see whether a results object exists
        print('Do fit results exist for the first object? ', resObj1.hasFit)
        print('Do fit results exist for the second object? ', resObj2.hasFit)


        #Explicitly call the fitter on the first object.
        #Here we will call it, and also override the guess for coupling Q with our own quess
        resObj1.load_params(scr.cmplxIQ_params)
        resObj1.do_lmfit(scr.cmplxIQ_fit, qc=5000)

        #Check to see whether a results object exists again, now they are both True
        print('Do fit results exist for the first object? ', resObj1.hasFit)
        print('Do fit results exist for the second object? ', resObj2.hasFit)

        #Compare the best guess for the resonant frequency (minimum of the curve) to the actual fit
        #Because we didn't specify a label for our fit, the results are stored in the lmfit_result
        #dict under the 'default' key. If we passed the optional label argument to the do_lmfit
        #method, it would store the results under whatever string is assigned to label.
        print('Guess = ', resObj2.fmin, ' Hz')
        print('Best fit = ', resObj2.lmfit_result['default']['result'].params['f0'].value, ' Hz')
        print('Best fit with different qc guess = ',
              resObj1.lmfit_result['default']['result'].params['f0'].value, ' Hz')

        #You can see the fit is not terribly sensitive to the guess for qc.
        return resObj1,resObj2
    
    def plot_ResListData(self,resObj):

        #When using inline plotting, you have to assign the output of the plotting functions to a figure, or it will plot twice

        #This function takes a list of resonators. It can handle a single one, just need to pass it as a list:
        figA = scr.plotResListData([resObj],
            plot_types = ['LogMag', 'Phase'], #Make two plots
            num_cols = 2, #Number of columns
            fig_size = 6, #Size in inches of each subplot
            show_colorbar = False, #Don't need a colorbar with just one trace
            force_square = True, #If you love square plots, this is for you!
            plot_fits = [True]*2) #Overlay the best fit, need to specify for each of the plot_types
        plt.show()
        
    def do_emcee(self,resObj,burn=200):
    
        #Call the emcee hook and pass it the fit function that calculates your residual.
        #Since we already ran a fit, emcee will use that fit for its starting guesses.
        resObj.do_emcee(scr.cmplxIQ_fit, nwalkers = 30, steps = 1000, burn=burn)

        #Check to see that a emcee result exists
        print('Does an emcee chain exist? ', resObj.hasChain)

        #Look at the first few rows of the output chain:
        chains = resObj.emcee_result['default']['result'].flatchain

        print('\nHead of chains:')
        pp.pprint(chains.head())

        #Compare withe the mle values (percent difference):
        #Maximum liklihood estimates (MLE) are stored in Resonator.mle_vals
        #lmfit best fit values for varied parameters are in Resonator.lmfit_vals
        diffs = list(zip(resObj.mle_labels, (resObj.mle_vals - resObj.lmfit_vals)*100/resObj.lmfit_vals))

        print('\nPerecent difference:')
        pp.pprint(diffs)

        return chains

    def plot_gtc(self,resObj,chains):
        #Plot the triangle plot, and overlay the best fit values with dashed black lines (default)
        #You can see that the least-squares fitter did a very nice job of getting the values right

        #You can also see that there is some strange non-gaussian parameter space that the MCMC
        #analysis maps out! This is kind of wierd, but not too worrisome. It is probably suggestive
        #that more care is needed in choosing good options for the MCMC engine.

        figGTC = pygtc.plotGTC(chains, truths = [resObj.lmfit_vals])
        plt.show()