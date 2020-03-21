from tom_observations.facility import GenericObservationFacility, GenericObservationForm, get_service_class
from tom_observations.facilities import lco
from tom_observations.cadence import CadenceForm
import datetime 
from django.conf import settings





def submit_imaging_to_LCO(target,cadence,filters,instrument):
    

    obs_dic = {}

    observing_type  = 'IMAGING'
 
    
    start = datetime.datetime.utcnow().isoformat()
    end  = (datetime.datetime.utcnow()+datetime.timedelta(days=7)).isoformat()
    obs_dic['name'] = target.name+'_'+'REG_phot'
    obs_dic['target_id'] = target.id
    obs_dic['start'] = start
    obs_dic['observation_mode'] = 'NORMAL'
    obs_dic['end'] = end
    obs_dic['ipp_value'] = 1.0
    obs_dic['exposure_count'] = 1
    obs_dic['exposure_time'] = 300
    obs_dic['period'] = 24
    obs_dic['jitter'] = 24
    obs_dic['max_airmass'] = 2
    obs_dic['proposal'] = 'LCO2020A-002'
    obs_dic['filter'] = filters[0]
    obs_dic['instrument_type'] = '1M0-SCICAM-SINISTRO'
    obs_dic['facility'] = 'LCO'
    obs_dic['observation_type'] = observing_type
    request_obs =  lco.LCOBaseObservationForm(obs_dic)
    request_obs.is_valid()
    the_obs = request_obs.observation_payload()
    telescope = lco.LCOFacility()    
    telescope.submit_observation(the_obs)

    import pdb; pdb.set_trace()
