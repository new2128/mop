from tom_observations.facility import GenericObservationFacility, GenericObservationForm, get_service_class
from tom_observations.facilities import lco
from tom_observations.cadence import CadenceForm
from mop.toolbox import TAP
import datetime 
from django.conf import settings
import copy
import numpy as np

def build_and_submit_regular_phot(target):

       #Defaults
       observing_type  = 'IMAGING'
       instrument_type = '1M0-SCICAM-SINISTRO'
       proposal =  'LCO2020A-002'
       facility = 'LCO'
       observation_mode = 'NORMAL'
       ipp = 1
       max_airmass = 2


       #Probably gonna need a MUSCAT exception

       start = datetime.datetime.utcnow().isoformat()
       end  = (datetime.datetime.utcnow()+datetime.timedelta(days=7)).isoformat()
    


      
       obs_name = target.name+'_'+'REG_phot'
       cadence = 20/target.extra_fields['tE']  #points/days
      
       if cadence<0.5:
      
          cadence = 0.5
       
       if cadence>4:
           
          cadence = 4

       cadence = 24/cadence #delta_hours/points 
       jitter = cadence

       mag_now = TAP.TAP_mag_now(target)
       mag_exposure = mag_now

       exposure_time_ip = TAP.calculate_exptime_omega_sdss_i(mag_exposure)


       telescope_class = TAP.TAP_telescope_class(mag_now)

       if telescope_class == '2m':
 
          instrument_type = '2M0-SCICAM-SPECTRAL'
          exposure_time_ip /= 2 # area ratio (kind of...)

       if telescope_class == '0.4m':
 
          instrument_type = '0M4-SCICAM-SBIG'  
          exposure_time_ip *= 4 # area ratio

       exposure_time_gp = exposure_time_ip+50 
   
       # ip alone
       obs_dic = {}

        
       obs_dic['name'] = obs_name
       obs_dic['target_id'] = target.id
       obs_dic['start'] = start
       obs_dic['end'] = end
       obs_dic['observation_mode'] = observation_mode

       obs_dic['ipp_value'] = ipp
       obs_dic['exposure_count'] = 1
       obs_dic['exposure_time'] = exposure_time_ip
       obs_dic['period'] = cadence
       obs_dic['jitter'] = jitter
       obs_dic['max_airmass'] = max_airmass
       obs_dic['proposal'] = proposal
       obs_dic['filter'] = "ip"
       obs_dic['instrument_type'] = instrument_type
       obs_dic['facility'] = facility
       obs_dic['observation_type'] = observing_type 
       
       request_obs =  lco.LCOBaseObservationForm(obs_dic)
       request_obs.is_valid()
       the_obs = request_obs.observation_payload()

       telescope = lco.LCOFacility()    
       telescope.submit_observation(the_obs)
       # gp,ip 

       delta_time = cadence/2

       start = (datetime.datetime.utcnow()+datetime.timedelta(hours=delta_time)).isoformat()
       end  = (datetime.datetime.utcnow()+datetime.timedelta(days=7)+datetime.timedelta(hours=delta_time)).isoformat()
       
       obs_dic = {}
       obs_dic['name'] = obs_name
       obs_dic['target_id'] = target.id
       obs_dic['start'] = start
       obs_dic['end'] = end
       obs_dic['observation_mode'] = observation_mode

       obs_dic['ipp_value'] = ipp
       obs_dic['exposure_count'] = 1
       obs_dic['exposure_time'] = exposure_time_ip
       obs_dic['period'] = cadence + exposure_time_gp/60./24*2 # Hack
       obs_dic['jitter'] = jitter + exposure_time_gp/60./24*2  #Hack 
       obs_dic['max_airmass'] = max_airmass
       obs_dic['proposal'] = proposal
       obs_dic['filter'] = "ip"
       obs_dic['instrument_type'] = instrument_type
       obs_dic['facility'] = facility
       obs_dic['observation_type'] = observing_type 
       request_obs =  lco.LCOBaseObservationForm(obs_dic)
       request_obs.is_valid()
       the_obs = request_obs.observation_payload()
       
       #Hacking the LCO TOM form to add several filters 
       instument_config =   the_obs['requests'][0]['configurations'][0]['instrument_configs'][0]
       exposure_times = [exposure_time_ip,exposure_time_gp]

       for ind_req,req in enumerate(the_obs['requests']):
           for ind_fil,fil in enumerate(["ip","gp"]):
               
               if ind_fil>0:
                   new_instrument_config =  copy.deepcopy(instument_config)
                   new_instrument_config['optical_elements']['filter'] = fil
                   new_instrument_config['exposure_time'] = exposure_time_gp
                   
                   the_obs['requests'][ind_req]['configurations'][0]['instrument_configs'].append(new_instrument_config)
           
       telescope = lco.LCOFacility()    
       telescope.submit_observation(the_obs)


def build_and_submit_priority_phot(target):

       #Defaults
       observing_type  = 'IMAGING'
       instrument_type = '1M0-SCICAM-SINISTRO'
       proposal =  'LCO2020A-002'
       facility = 'LCO'
       observation_mode = 'NORMAL'
       ipp = 1.1
       max_airmass = 2
       priority_duration = 3 #days

       #Probably gonna need a MUSCAT exception

       start = datetime.datetime.utcnow().isoformat()
       end  = (datetime.datetime.utcnow()+datetime.timedelta(days=priority_duration)).isoformat()
    


      
       obs_name = target.name+'_'+'PRI_phot'
       
       cadence = 1 #delta_hours/points 
       jitter = cadence

       mag_now = TAP.TAP_mag_now(target)
       mag_exposure = mag_now

       exposure_time_ip = TAP.calculate_exptime_omega_sdss_i(mag_exposure)


       telescope_class = TAP.TAP_telescope_class(mag_now)

       if telescope_class == '2m':
 
          instrument_type = '2M0-SCICAM-SPECTRAL'
          exposure_time_ip /= 2 # diameter ratio (kind of...)

       if telescope_class == '0.4m':
 
          instrument_type = '0M4-SCICAM-SBIG'  
          exposure_time_ip *= 4 # diameter ratio

       exposure_time_gp = exposure_time_ip+50
       # ip alone
       obs_dic = {}

        
       obs_dic['name'] = obs_name
       obs_dic['target_id'] = target.id
       obs_dic['start'] = start
       obs_dic['end'] = end
       obs_dic['observation_mode'] = observation_mode

       obs_dic['ipp_value'] = ipp
       obs_dic['exposure_count'] = 1
       obs_dic['exposure_time'] = exposure_time_ip
       obs_dic['period'] = cadence
       obs_dic['jitter'] = jitter
       obs_dic['max_airmass'] = max_airmass
       obs_dic['proposal'] = proposal
       obs_dic['filter'] = "ip"
       obs_dic['instrument_type'] = instrument_type
       obs_dic['facility'] = facility
       obs_dic['observation_type'] = observing_type 
       
       request_obs =  lco.LCOBaseObservationForm(obs_dic)
       request_obs.is_valid()
       the_obs = request_obs.observation_payload()

       telescope = lco.LCOFacility()    
       telescope.submit_observation(the_obs)
       # gp,ip 

       delta_time = cadence/2

       start = (datetime.datetime.utcnow()+datetime.timedelta(hours=delta_time)).isoformat()
       end  = (datetime.datetime.utcnow()+datetime.timedelta(days=priority_duration)+datetime.timedelta(hours=delta_time)).isoformat()
       
       obs_dic = {}
       obs_dic['name'] = obs_name
       obs_dic['target_id'] = target.id
       obs_dic['start'] = start
       obs_dic['end'] = end
       obs_dic['observation_mode'] = observation_mode

       obs_dic['ipp_value'] = ipp
       obs_dic['exposure_count'] = 1
       obs_dic['exposure_time'] = exposure_time_ip
       obs_dic['period'] = cadence + exposure_time_gp/60./24*2 # Hack
       obs_dic['jitter'] = jitter + exposure_time_gp/60./24*2  #Hack 
       obs_dic['max_airmass'] = max_airmass
       obs_dic['proposal'] = proposal
       obs_dic['filter'] = "ip"
       obs_dic['instrument_type'] = instrument_type
       obs_dic['facility'] = facility
       obs_dic['observation_type'] = observing_type 
       request_obs =  lco.LCOBaseObservationForm(obs_dic)
       request_obs.is_valid()
       the_obs = request_obs.observation_payload()


       #Hacking the LCO TOM form to add several filters 
       instument_config =   the_obs['requests'][0]['configurations'][0]['instrument_configs'][0]
       exposure_times = [exposure_time_ip,exposure_time_gp]

       for ind_req,req in enumerate(the_obs['requests']):
           for ind_fil,fil in enumerate(["ip","gp"]):
        
               if ind_fil>0:
                   new_instrument_config =  copy.deepcopy(instument_config)
                   new_instrument_config['optical_elements']['filter'] = fil
                   new_instrument_config['exposure_time'] = exposure_time_gp
                   



                   the_obs['requests'][ind_req]['configurations'][0]['instrument_configs'].append(new_instrument_config)
       
                 
       telescope = lco.LCOFacility()    
       telescope.submit_observation(the_obs)

