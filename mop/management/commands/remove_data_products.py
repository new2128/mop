from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target
from astropy.time import Time
from mop.toolbox import fittools
from mop.brokers import gaia as gaia_mop


import json
import numpy as np
import datetime

class Command(BaseCommand):

    help = 'Clean a data product kind for a list of targets'
    
    def add_arguments(self, parser):
        parser.add_argument('--targets_name', nargs='+', help='name of the events to clean')
        parser.add_argument('--data_type', nargs='+', help='name of the data king to remove')
    
    def handle(self, *args, **options):
       import pdb; pdb.set_trace()
       name = options['targets_name']
       data_type = options['data_type']
       
       if name == 'all':
           list_of_targets = Target.objects.filter()
       else:
           list_of_targets = Target.objects.filter(target__name__contains=name)
             
       for target in list_of_targets:
           
           ReducedDatum.objects.filter(target=target, data_type=settings.DATA_PRODUCT_TYPES[data_type][0]).delete()
           print(target.name, ' : Clean!') 

