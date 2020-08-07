from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target
from astropy.time import Time, TimezoneInfo
from mop.toolbox import fittools
from mop.brokers import gaia as gaia_mop
from django.conf import settings

import os
import json
import numpy as np
import datetime
import numpy as np
import requests
import csv

LOGIN_URL = "https://irsa.ipac.caltech.edu/account/signon/login.do"




class Command(BaseCommand):

    help = 'Clean a data product kind for a list of targets'
    
    def add_arguments(self, parser):
              parser.add_argument('events_to_harvest', help='all, alive, need or [years]')
    
    def handle(self, *args, **options):


       username =  os.getenv('IRSA_USERNAME')
       password = os.getenv('IRSA_PASSWORD')
       filters = {'zg': 'g_ZTF', 'zr': 'r_ZTF'}
       all_events = options['events_to_harvest']
       
       if all_events == 'all':
           list_of_targets = Target.objects.filter()
       if all_events == 'alive':
           list_of_targets = Target.objects.filter(targetextra__in=TargetExtra.objects.filter(key='Alive', value=True))
       if all_events[0] == '[':     
            
            years = all_events[1:-1].split(',')
            events = Target.objects.filter()
            list_of_targets = []
            for year in years:
 
                 list_of_targets =  [i for i in events if year in i.name]

       for target in list_of_targets:
       
            ra =    target.ra	
            dec =   target.dec
            radius = 0.0001 #arsec


            url = 'https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE '+str(ra)+' '+str(dec)+' '+str(radius)+'&FORMAT=CSV'
            response = requests.get(url,  timeout=20,auth=(username,password))


            content = list(csv.reader(response.content.decode('utf-8').splitlines(), delimiter=','))
            light = np.array(content)

            if target.name =='ZTF20aawpktr':
                import pdb; pdb.set_trace()

            if len(light)>1:
                #mjd, mag, magerr, filter
                lightcurve = np.c_[light[1:,3],light[1:,4],light[1:,5],light[1:,7]]

                for line in lightcurve:
                       try:
                              jd = Time(float(line[0])+2400000.5, format='jd', scale='utc')

                         
                              
                              mag = float(line[1])
                              emag = float(line[2])

                              filt = filters[line[-1]]
                              value = {
                                       'magnitude': mag,
                                       'filter': filt,
                                       'error': emag
                                       }
                                       
                              existing_point =   ReducedDatum.objects.filter(source_name='IRSA',timestamp=jd.to_datetime(timezone=TimezoneInfo()))

                                                                            
                              if existing_point.count() == 0:                                               
                                  rd, created = ReducedDatum.objects.get_or_create(
                                                timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                                                value=json.dumps(value),
                                                source_name='IRSA',
                                                data_type='photometry',
                                                target=target)
                                  rd.save()
                              else:
                                  rd, created = ReducedDatum.objects.update_or_create(
                                                timestamp=existing_point[0].timestamp,
                                                value=existing_point[0].value,
                                                source_name='IRSA',
                                                data_type='photometry',
                                                target=target,
                                                defaults={'value':json.dumps(value)})
                                  rd.save()
                                  
                       except:

                              pass












