from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target
from astropy.time import Time
from mop.toolbox import fittools

import json
import numpy as np
import datetime

class Command(BaseCommand):

    help = 'Fit an event with PSPL and parallax, then ingest fit parameters in the db'
    
    def add_arguments(self, parser):
        parser.add_argument('target_name', help='name of the event to fit')

    
    def handle(self, *args, **options):

       target, created = Target.objects.get_or_create(name= options['target_name'])

       
       datasets = ReducedDatum.objects.filter(target=target)
       time = [Time(i.timestamp).jd for i in datasets]
       phot = [[json.loads(i.value)['magnitude'],json.loads(i.value)['error'],json.loads(i.value)['filter']] for i in datasets]
       photometry = np.c_[time,phot]
       
       if 'MOA' in target.name:

             emag_limit = 0.25

       else:
            
             emag_limit = None

       t0_fit,u0_fit,tE_fit,piEN_fit,piEE_fit,mag_source_fit,mag_blend_fit,mag_baseline_fit = fittools.fit_PSPL_parallax(target.ra, target.dec, photometry,emag_limit)

       time_now = Time(datetime.datetime.now()).jd
       how_many_tE = (time_now-t0_fit)/tE_fit
      

       if how_many_tE>2:

          alive = False

       else:
 
          alive = True
       

       extras = {'Alive':alive, 't0':np.around(t0_fit,3),'u0':np.around(u0_fit,5),'tE':np.around(tE_fit,3),
                 'piEN':np.around(piEN_fit,5),'piEE':np.around(piEE_fit,5),
                 'Source_magnitude':np.around(mag_source_fit,3),
                 'Blend_magnitude':np.around(mag_blend_fit,3),
                 'Baseline_magnitude':np.around(mag_baseline_fit,3)}
       target.save(extras = extras)

      
