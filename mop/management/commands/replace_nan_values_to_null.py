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
                
                    if (np.isnan(extras[key])) or (extras[key] is None):
                    
                        extras[key] = 'null'
                except:
                
                    pass
                    
            target.save(extras = extras)
            print(target.name, ' : Clean!') 

