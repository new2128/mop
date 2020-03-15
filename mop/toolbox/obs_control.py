from tom_observations.facility import GenericObservationFacility, GenericObservationForm, get_service_class
from tom_observations.facilities import lco
from tom_observations.cadence import CadenceForm

from django.conf import settings





def submit_imaging_to_LCO(target,cadence,):
    
    obvserving_type  = 'IMAGING'
 
    request_obs =  lco.LCOBaseObservationForm(GenericObservationForm, lco.LCOBaseForm, CadenceForm)
    import pdb; pdb.set_trace()
