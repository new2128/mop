from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target,TargetExtra
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
import random

LOGIN_URL = "https://irsa.ipac.caltech.edu/account/signon/login.do"




class Command(BaseCommand):

    help = 'Download ZTF DR3 for MOP targets'
    
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

       list_of_targets = list(list_of_targets)
       random.shuffle(list_of_targets)
       
       for target in list_of_targets:
       
            ra =    target.ra	
            dec =   target.dec
            radius = 0.0001 #arsec

            try:
                times = [Time(i.timestamp).jd for i in ReducedDatum.objects.filter(target=target) if i.data_type == 'photometry']
            except: 
                times = []

            try:
                url = 'https://irsa.ipac.caltech.edu/cgi-bin/ZTF/nph_light_curves?POS=CIRCLE '+str(ra)+' '+str(dec)+' '+str(radius)+'&FORMAT=CSV'
                response = requests.get(url,  timeout=20,auth=(username,password))


                content = list(csv.reader(response.content.decode('utf-8').splitlines(), delimiter=','))
                light = np.array(content)


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
                                  
                                  jd.to_datetime(timezone=TimezoneInfo())

                                  if  (jd.value not in times):
                                    
                                         rd, _ = ReducedDatum.objects.get_or_create(
                                                timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                                                value=json.dumps(value),
                                                source_name=self.name,
                                                source_location=alert_url,
                                                data_type='photometry',
                                                target=target)
                                        
                                        rd.save()
                                  
                                  else:
                                  
                                        pass          
                          
                           except:

                                  pass
                                 
                 
            except:
                print('Can not connect to IRSA')
                pass











