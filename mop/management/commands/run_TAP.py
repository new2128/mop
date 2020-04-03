from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target,TargetExtra
from astropy.time import Time
from mop.toolbox import TAP
import datetime
import json
import numpy as np

class Command(BaseCommand):

    help = 'Sort events that need extra observations'
    
    def add_arguments(self, parser):
       
        pass
    
    def handle(self, *args, **options):





        
        list_of_events_alive = Target.objects.filter(targetextra__in=TargetExtra.objects.filter(key='Alive', value=True))  

        for event in list_of_events_alive[:]:

            try:

                ### Regular obs

                event_in_the_Bulge = event_in_the_Bulge(ra,dec)
                
                if event_in_the_Bulge:

                   pass
 
                else:
 
                   obs_control.build_and_submit_regular_phot(target)


                time_now = Time(datetime.datetime.now()).jd
                t0_pspl = event.extra_fields['t0']
                u0_pspl = event.extra_fields['u0']
                tE_pspl = event.extra_fields['tE']
            

                covariance = np.array(json.loads(event.extra_fields['Fit_covariance']))

                planet_priority = TAP.TAP_planet_priority(time_now,t0_pspl,u0_pspl,tE_pspl)
                planet_priority_error = TAP.TAP_planet_priority_error(time_now,t0_pspl,u0_pspl,tE_pspl,covariance)
 
                #psi_deriv = TAP.psi_derivatives_squared(time_now,t0_pspl,u0_pspl,tE_pspl) 
                #error = (psi_deriv[2] * covariance[2,2] + psi_deriv[1] * covariance[1,1] + psi_deriv[0] * covariance[0,0])**0.5
                ### need to create a reducedatum for planet priority
            
            
                data = {   'tap': planet_priority,
                       'tap_error': planet_priority_error
                   }

                rd, created = ReducedDatum.objects.get_or_create(
                          timestamp=datetime.datetime.utcnow(),
                          value=json.dumps(data),
                          source_name='MOP',
                          source_location=event.name,
                          data_type='TAP_priority',
                          target=event)
               
                if created:
                    rd.save()
            
                new_observing_mode = TAP.TAP_observing_mode(planet_priority,planet_priority_error,  
                                                    event.extra_fields['Observing_mode'])


                extras = {'TAP_priority':np.around(planet_priority,5),'Observing_mode':new_observing_mode}
                event.save(extras = extras)
                print(planet_priority,planet_priority_error)
            
            except:
                print('Can not perform TAP for this target')
