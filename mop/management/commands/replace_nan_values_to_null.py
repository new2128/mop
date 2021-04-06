from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target
from astropy.time import Time
from mop.toolbox import fittools
from mop.brokers import gaia as gaia_mop
from django.conf import settings

import random
import numpy as np
import datetime
import json

def clean_lc_model(target):

    #import pdb; pdb.set_trace()

    try:
    
        existing_model =   ReducedDatum.objects.filter(source_location=target.name,data_type='lc_model',)
        model = json.loads(existing_model[0].value)

        if True in np.isnan(model['lc_model_magnitude']):

            data = {'lc_model_time': [],
                    'lc_model_magnitude': []}
            
            rd, created = ReducedDatum.objects.update_or_create(timestamp=existing_model[0].timestamp,
                                                                value=json.dumps(data),
                                                                source_name='MOP',
                                                                source_location=target.name,
                                                                data_type='lc_model',
                                                                target=target)   
            rd.save()         
    except:
    
        pass

class Command(BaseCommand):

    help = 'Replace nan with null for dDB/Django complience'
    
    def add_arguments(self, parser):
       pass
    
    def handle(self, *args, **options):


       list_of_targets = Target.objects.filter()
       list_of_targets = list(list_of_targets)
       random.shuffle(list_of_targets)


       for target in list_of_targets:
            print(target.name, ' Start cleaning')
            extras = target.extra_fields
            
            for key in extras.keys():
            
                try:
                
                    if extras[key] is None:
                    
                        extras[key] = 'null'
                    
                    if np.isnan(extras[key]):
                    
                        extras[key] = 'null'
                except:
                
                    pass
                    
            target.save(extras = extras)
            clean_lc_model(target)
            
            print(target.name, ' : Clean!') 

