from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target,TargetExtra
from django.db import transaction
from django.db import models
from astropy.time import Time
from mop.toolbox import fittools
from mop.brokers import gaia as gaia_mop
from django.db.models import Q
import numpy as np

import traceback
import datetime
import random
import json
import sys
import os


def run_fit(target, cores):
    print(f'Working on {target.name}')

    try:
       if 'Gaia' in target.name:

           gaia_mop.update_gaia_errors(target)

       # Add photometry model

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

           t0_fit,u0_fit,tE_fit,piEN_fit,piEE_fit,mag_source_fit,mag_blend_fit,mag_baseline_fit,cov,model = fittools.fit_PSPL_parallax(target.ra, target.dec, photometry, cores = cores)

           # Add photometry model

           model_time = datetime.datetime.strptime('2018-06-29 08:15:27.243860', '%Y-%m-%d %H:%M:%S.%f')
           data = {'lc_model_time': model.lightcurve_magnitude[:,0].tolist(),
           'lc_model_magnitude': model.lightcurve_magnitude[:,1].tolist()
                   }
           existing_model =   ReducedDatum.objects.filter(source_name='MOP',data_type='lc_model',
                                                         timestamp=model_time,source_location=target.name)


           if existing_model.count() == 0:
               rd, created = ReducedDatum.objects.get_or_create(
                                                                   timestamp=model_time,
                                                                   value=json.dumps(data),
                                                                   source_name='MOP',
                                                                   source_location=target.name,
                                                                   data_type='lc_model',
                                                                   target=target)

               rd.save()

           else:
               rd, created = ReducedDatum.objects.update_or_create(
                                                                   timestamp=existing_model[0].timestamp,
                                                                   value=existing_model[0].value,
                                                                   source_name='MOP',
                                                                   source_location=target.name,
                                                                   data_type='lc_model',
                                                                   target=target,
                                                                   defaults={'value':json.dumps(data)})

               rd.save()


           time_now = Time(datetime.datetime.now()).jd
           how_many_tE = (time_now-t0_fit)/tE_fit


           if how_many_tE>2:

              alive = False

           else:

              alive = True

           last_fit = Time(datetime.datetime.utcnow()).jd


           extras = {'Alive':alive, 't0':np.around(t0_fit,3),'u0':np.around(u0_fit,5),'tE':np.around(tE_fit,3),
            'piEN':np.around(piEN_fit,5),'piEE':np.around(piEE_fit,5),
            'Source_magnitude':np.around(mag_source_fit,3),
            'Blend_magnitude':np.around(mag_blend_fit,3),
            'Baseline_magnitude':np.around(mag_baseline_fit,3),
            'Fit_covariance':json.dumps(cov.tolist()),
            'Last_fit':last_fit,
           }
           target.save(extras = extras)
    except:
        print(f'Job failed: {target.name}')
        traceback.print_exc()
        return None

class Command(BaseCommand):
    help = 'Fit events with PSPL and parallax, then ingest fit parameters in the db'

    def add_arguments(self, parser):
        parser.add_argument('--cores', help='Number of workers (CPU cores) to use', default=os.cpu_count(), type=int)
        parser.add_argument('--run-every', help='Run each Fit every N hours', default=4, type=int)

    def handle(self, *args, **options):


        #Adding Last_fit if dos not exist
        list_of_targets = Target.objects.filter()
        
        for target in list_of_targets:


            try:
                last_fit = target.extra_fields['Last_fit']
                
            except:
                last_fit = 2446756.50000


                extras = {'Last_fit':last_fit}
                target.save(extras = extras)


        # Run until all objects which need processing have been processed
        while True:
            # One instance of our database model to process (if found)
            element = None

            # Select the first available un-claimed object for processing. We indicate
            # ownership of the job by advancing the timestamp to the current time. This
            # ensures that we don't have two workers running the same job. A beneficial
            # side effect of this implementation is that a job which crashes isn't retried
            # for another four hours, which limits the potential impact.
            #
            # The only time this system breaks down is if a single processing fit takes
            # more than four hours. We'll instruct Kubernetes that no data processing Pod
            # should run for that long. That'll protect us against that overrun scenario.
            #
            # The whole thing is wrapped in a database transaction to protect against
            # collisions by two workers. Very unlikely, but we're good software engineers
            # and will protect against that.
            with transaction.atomic():

                # Cutoff date: N hours ago (from the "--run-every=N" hours command line argument)
                cutoff = Time(datetime.datetime.utcnow() - datetime.timedelta(hours=options['run_every'])).jd

                # Find any objects which need to be run
                # https://docs.djangoproject.com/en/3.0/ref/models/querysets/#select-for-update
                queryset = Target.objects.select_for_update(skip_locked=True)
                queryset = queryset.filter(targetextra__in=TargetExtra.objects.filter(key='Last_fit', value__lte=cutoff))
                queryset = queryset.filter(targetextra__in=TargetExtra.objects.filter(key='Alive', value=True))

                # Retrieve the first element which meets the condition
                element = queryset.first()

                # Element was found. Claim the element for this worker (mark the fit as in
                # the "RUNNING" state) by setting the Last_fit timestamp. This method has
                # the beneficial side effect such that if a fit crashes, it won't be re-run
                # (retried) for another N hours. This limits the impact of broken code on the cluster.
                if element is not None:
                    last_fit = Time(datetime.datetime.utcnow()).jd
                    extras = {'Last_fit':last_fit}
                    element.save(extras = extras)

            # If there are no more objects left to process, then the job is finished.
            # Inform Kubernetes of this fact by exiting successfully.
            if element is None:
                print('Job is finished, no more objects left to process! Goodbye!')
                sys.exit(0)

            # Now we know for sure we have an element to process, and we haven't locked
            # a row (object) in the database. We're free to process this for up to four hours.
            result = run_fit(element, cores=options['cores'])

if __name__ == '__main__':
    main()
