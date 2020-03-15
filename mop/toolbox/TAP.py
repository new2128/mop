from django.core.management.base import BaseCommand
from tom_observations.models import ObservationRecord
from tom_targets.models import Target
from astropy import units as u
from astropy.coordinates import Angle
import time
from jdcal import gcal2jd
from numpy import exp, log10
import requests


ZP = 27.4 #pyLIMA convention

def calculate_exptime_romerea(magin):
    """
    This function calculates the required exposure time
    for a given iband magnitude (e.g. OGLE I which also
    roughly matches SDSS i) based on a fit to the empiric
    RMS diagram of DANDIA light curves from 2016. The
    output is in seconds.
    """
    if magin < 14.7:
        mag = 14.7
    else:
        mag = magin
    lrms = 0.14075464 * mag * mag - 4.00137342 * mag + 24.17513298
    snr = 1.0 / exp(lrms)
    # target 4% -> snr 25
    return round((25. / snr)**2 * 300., 1)


def event_in_the_Bulge(ra,dec):

    Bulge_limits = [[255,275],[-36,-22]]

    if (ra>Bulge_limits[0][0]) & (ra<Bulge_limits[0][1]) & (dec>Bulge_limits[1][0]) & (dec<Bulge_limits[1][1]):
        in_the_Bulge = True
    else:
        
        in_the_Bulge = False

    return in_the_Bulge


def TAP_planet_priority(time_now,t0_pspl,u0_pspl,tE_pspl,fs_pspl,fb_pspl):
    """
    This function calculates the priority for ranking
    microlensing events based on the planet probability psi
    as defined by Dominik 2009 and estimates the cost of
    observations based on an empiric RMS estimate
    obtained from a DANDIA reduction of K2C9 Sinistro
    observations from 2016. It expects the overhead to be
    60 seconds and also return the current Paczynski
    light curve magnification.
    """
    usqr = u0_pspl**2 + ((time_requested - t0_pspl) / te_pspl)**2
    pspl_deno = (usqr * (usqr + 4.))**0.5
    if pspl_deno < 1e-10:
        pspl_deno = 10000.
    psip = 4.0 / (pspl_deno) - 2.0 / (usqr + 2.0 + pspl_deno)
    amp = (usqr + 2.) / pspl_deno
    mag = ZP-2.5 * log10(fs_pspl * amp + fb_pspl)
    # 60s overhead
    
    return psip / (calculate_exptime_romerea(mag) + 60.)




def TAP_regular_mode(in_the_Bulge,survey_cadence,sdssi_baseline,tE_fit):

    cadence =   20/tE_fit  #visits per day
    cadence = np.max(0.5,np.min(4,cadence)) # 0.5<cadence<4

    #Inside the Bulge?
    if not in_the_Bulge:
        return cadence 
    
    if survey_cadence<1:
          
       if sdssi_baseline<16.5:
       
          return cadence 

    return None


def TAP_priority_mode():

    cadence = 24 #pts/day
    duration = 3 
    return duration,cadence



def TAP_telescope_class(sdss_i_mag):

   telescope_class = '2m'

   if sdss_i_mag<14:
      
      telescope_class = '0.4m'

   if sdss_i_mag<17.5:
      
      telescope_class = '1m'

   return telescope_class
