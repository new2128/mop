import numpy as np
from pyLIMA import event
from pyLIMA import telescopes
from pyLIMA import microlmodels


def flux_to_mag(flux):
      
        ZP_pyLIMA = 27.4
        magnitude = ZP_pyLIMA -2.5*np.log10(flux)
        return magnitude

def fit_PSPL(photometry, emag_limit = None):

       current_event = event.Event()
       current_event.name = 'MOP_to_fit'
       filters = np.unique(photometry[:,-1]) 

       for ind,filt in enumerate(filters):

           if emag_limit:

               mask = (photometry[:,-1] == filt) & (np.abs(photometry[:,-2].astype(float))<emag_limit)
           
           else:
 
               mask = (photometry[:,-1] == filt) 
           lightcurve = photometry[mask,:-1].astype(float)

           telescope = telescopes.Telescope(name='Tel_'+str(ind), camera_filter=filt,
                                            light_curve_magnitude=lightcurve,
                                            light_curve_magnitude_dictionnary={'time': 0, 'mag': 1, 'err_mag': 2},
                                            clean_the_lightcurve='Yes')


           current_event.telescopes.append(telescope)

       Model = microlmodels.create_model('PSPL', current_event, parallax=['None', 0])
       Model.parameters_boundaries[0] = [Model.parameters_boundaries[0][0],Model.parameters_boundaries[0][-1]+500]
       Model.parameters_boundaries[1] = [0,2]
       current_event.fit(Model, 'DE',DE_population_size=10)

       t0_fit =  current_event.fits[-1].fit_results[0]
       u0_fit =  current_event.fits[-1].fit_results[1]
       tE_fit =  current_event.fits[-1].fit_results[2]
       chi2_fit = current_event.fits[-1].fit_results[-1]

       mag_source_fit = flux_to_mag( current_event.fits[-1].fit_results[3])

       try:
           mag_blend_fit = flux_to_mag( current_event.fits[-1].fit_results[3]*current_event.fits[-1].fit_results[4])
           mag_baseline_fit = flux_to_mag( current_event.fits[-1].fit_results[3]*(1+current_event.fits[-1].fit_results[4]))
       except:
           mag_blend_fit = 0
           mag_baseline_fit = mag_source

       return [t0_fit,u0_fit,tE_fit,mag_source_fit,mag_blend_fit,mag_baseline_fit,chi2_fit]

def fit_PSPL_parallax(ra,dec,photometry, emag_limit = None):
 

       t0_fit,u0_fit,tE_fit,mag_source_fit,mag_blend_fit,mag_baseline_fit,chi2_fit = fit_PSPL(photometry, emag_limit = None)

       current_event = event.Event()
       current_event.name = 'MOP_to_fit'

       current_event.ra = ra
       current_event.dec = dec

       filters = np.unique(photometry[:,-1])

       for ind,filt in enumerate(filters):

           if emag_limit:

               mask = (photometry[:,-1] == filt) & (np.abs(photometry[:,-2].astype(float))<emag_limit)
           
           else:
 
               mask = (photometry[:,-1] == filt) 
           lightcurve = photometry[mask,:-1].astype(float)

           telescope = telescopes.Telescope(name='Tel_'+str(ind), camera_filter=filt,
                                            light_curve_magnitude=lightcurve,
                                            light_curve_magnitude_dictionnary={'time': 0, 'mag': 1, 'err_mag': 2},
                                            clean_the_lightcurve='Yes')


           current_event.telescopes.append(telescope)

       t0_par = t0_fit

       Model_parallax = microlmodels.create_model('PSPL', current_event, parallax=['Full', t0_par])
       Model_parallax.parameters_boundaries[0] = [t0_fit-10,t0_fit+10]
      
       Model_parallax.parameters_boundaries[1] = [0,2]
       Model_parallax.parameters_boundaries[2] = [0.1,500]
       #Model_parallax.parameters_boundaries[3] = [-1,1]
       #Model_parallax.parameters_boundaries[4] = [-1,1]
       Model_parallax.parameters_guess = [ t0_fit,u0_fit,tE_fit,0,0]
       current_event.fit(Model_parallax, 'DE',DE_population_size=10,flux_estimation_MCMC = 'polyfit')

       #if (chi2_fit-current_event.fits[-1].fit_results[-1])/current_event.fits[-1].fit_results[-1]<0.1:
       
            #return [t0_fit,u0_fit,tE_fit,None,None,mag_source_fit,mag_blend_fit,mag_baseline_fit]

       t0_fit =  current_event.fits[-1].fit_results[0]
       u0_fit =  current_event.fits[-1].fit_results[1]
       tE_fit =  current_event.fits[-1].fit_results[2]
       piEN_fit =  current_event.fits[-1].fit_results[3]
       piEE_fit =  current_event.fits[-1].fit_results[4]

       mag_source_fit = flux_to_mag( current_event.fits[-1].fit_results[5])

       try:
           mag_blend_fit = flux_to_mag( current_event.fits[-1].fit_results[5]*current_event.fits[-1].fit_results[6])
           mag_baseline_fit = flux_to_mag( current_event.fits[-1].fit_results[5]*(1+current_event.fits[-1].fit_results[6]))
       except:
           mag_blend_fit = 0
           mag_baseline_fit = mag_source
       
       return [t0_fit,u0_fit,tE_fit,piEN_fit,piEE_fit,mag_source_fit,mag_blend_fit,mag_baseline_fit]
