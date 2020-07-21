from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target,TargetExtra
from astropy.time import Time
from mop.toolbox import fittools
from mop.brokers import gaia as gaia_mop
import json
import numpy as np
import datetime

class Command(BaseCommand):

    help = 'Fit an event with PSPL and parallax, then ingest fit parameters in the db'
    
    def add_arguments(self, parser):

        parser.add_argument('events_to_fit', help='all, alive, need or [years]')

    
    def handle(self, *args, **options):

       all_events = options['events_to_fit']
       
       if all_events == 'all':
           list_of_targets = Target.objects.filter()
       if all_events == 'alive':
           list_of_targets = Target.objects.filter(targetextra__in=TargetExtra.objects.filter(key='Alive', value=True))
       if all_events == 'need':
           list_of_targets = Target.objects.filter(targetextra__in=TargetExtra.objects.filter(key='t0', float_value=0.0))
       if all_events[0] == '[':     
	    
            years = all_events[1:-1].split(',')
            events = Target.objects.filter()
            list_of_targets = []
            for year in years:
 
                 list_of_targets =  [i for i in events if year in i.name]

       for target in list_of_targets:

           if 'Gaia' in target.name:

               gaia_mop.update_gaia_errors(target)
           
           if 'Microlensing' not in target.extra_fields['Classification']:
               alive = False

               extras = {'Alive':alive}
               target.save(extras = extras)
           
           else:

               datasets = ReducedDatum.objects.filter(target=target)
               time = [Time(i.timestamp).jd for i in datasets if i.data_type == 'photometry']
            
               phot = []
               for data in datasets:
                   if data.data_type == 'photometry':
                      try:
                           phot.append([json.loads(data.value)['magnitude'],json.loads(data.value)['error'],json.loads(data.value)['filter']])
           
                      except:
                           # Weights == 1
                           phot.append([json.loads(data.value)['magnitude'],1,json.loads(data.value)['filter']])
               

               photometry = np.c_[time,phot]

               t0_fit,u0_fit,tE_fit,piEN_fit,piEE_fit,mag_source_fit,mag_blend_fit,mag_baseline_fit,cov,model = fittools.fit_PSPL_parallax(target.ra, target.dec, photometry)
               #Add photometry model
               data = {'lc_model_time': model.lightcurve_magnitude[:,0].tolist(),
               'lc_model_magnitude': model.lightcurve_magnitude[:,1].tolist()
                        }

               rd, created = ReducedDatum.objects.get_or_create(
                  timestamp=datetime.datetime.utcnow(),
                  value=json.dumps(data),
                  source_name='MOP',
                  source_location=target.name,
                  data_type='lc_model',
                  target=target)
       
               if created:
                  rd.save()

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
                 'Baseline_magnitude':np.around(mag_baseline_fit,3),
                 'Fit_covariance':json.dumps(cov.tolist())}
               target.save(extras = extras)
