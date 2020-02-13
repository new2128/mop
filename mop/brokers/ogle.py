from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from tom_alerts.alerts import GenericBroker, GenericQueryForm
from django import forms
from tom_targets.models import Target
from tom_observations import facility
from tom_dataproducts.models import ReducedDatum

from astropy.coordinates import SkyCoord
import astropy.units as unit
import ftplib
import os
import numpy as np
import json
from astropy.time import Time, TimezoneInfo


BROKER_URL = 'ftp.astrouw.edu.pl'


class OGLEQueryForm(GenericQueryForm):
    target_name = forms.CharField(required=False)
    cone = forms.CharField(
        required=False,
        label='Cone Search',
        help_text='RA,Dec,radius in degrees'
    )

    def clean(self):
        if len(self.cleaned_data['target_name']) == 0 and \
                        len(self.cleaned_data['cone']) == 0:
            raise forms.ValidationError(
                "Please enter either a target name or cone search parameters"
                )

class OGLEBroker(GenericBroker):
    name = 'OGLE'
    form = OGLEQueryForm

    def fetch_alerts(self, ogle_files_directories, years = []):
        
        #download from OGLE FTP
        ftp_tunnel = ftplib.FTP( BROKER_URL ) 
        ftp_tunnel.login()
        ftp_file_path = os.path.join( 'ogle', 'ogle4', 'ews' )
        ftp_tunnel.cwd(ftp_file_path)

        output_file = open(os.path.join(ogle_files_directories,'ogle_last.changed'),'wb')
        ftp_tunnel.retrbinary('RETR last.changed', output_file.write)
        output_file.close()

        for year in years:
            
            ftp_file_path = os.path.join( str(year) )
            ftp_tunnel.cwd(ftp_file_path)
            output_file = open(os.path.join(ogle_files_directories,'ogle_lenses_'+str(year)+'.par'), 'wb')
            ftp_tunnel.retrbinary('RETR lenses.par', output_file.write )
            output_file.close()
            ftp_tunnel.cwd('../')

        ftp_tunnel.quit()

        #ingest the TOM db
        list_of_targets = []
        for year in years:

            ogle_events = os.path.join(ogle_files_directories,'ogle_lenses_'+str(year)+'.par')
          

            events = np.loadtxt(ogle_events,dtype=str)

            for event in events[1:]:

                   name = 'OGLE-'+event[0]
                   #Create or load
                   coords = [event[3]+event[4]]
                   cible = SkyCoord(coords, unit=(unit.hourangle, unit.deg))
                   target, created = Target.objects.get_or_create(name=name,ra=cible.ra.degree[0],dec=cible.dec.degree[0],
                                   type='SIDEREAL',epoch=2000)
                   if created:

                       target.save()
                   
                   list_of_targets.append(target)


        return list_of_targets


    def find_and_ingest_photometry(self, targets):
        
        ftp_tunnel = ftplib.FTP( BROKER_URL ) 
        ftp_tunnel.login()
        ftp_file_path = os.path.join( 'ogle', 'ogle4', 'ews' )
        ftp_tunnel.cwd(ftp_file_path)

        previous_year = targets[0].name.split('-')[1]
        ftp_tunnel.cwd(previous_year)
        for target in targets:
            
            year = target.name.split('-')[1]
            event = target.name.split('-')[2]+'-'+target.name.split('-')[3]

            if year == previous_year:
        
               pass
        
            else:

               ftp_tunnel.cwd('../../')
               ftp_tunnel.cwd(year)
            
            ftp_tunnel.cwd(event.lower())
            ftp_tunnel.retrbinary('RETR phot.dat',open('./data/ogle_phot.dat', 'wb').write)
            photometry = np.loadtxt('./data/ogle_phot.dat')
            photometry = photometry[photometry[:,0].argsort()[::-1],] #going backward to save time on ingestion
            ftp_tunnel.cwd('../')
            for index,point in enumerate(photometry):
        
                jd = Time(point[0], format='jd', scale='utc')
                jd.to_datetime(timezone=TimezoneInfo())
                data = {   'magnitude': point[1],
                           'filter': 'OGLE_I',
                           'error': point[2]
                       }
                rd, created = ReducedDatum.objects.get_or_create(
                timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                value=json.dumps(data),
                source_name=target.name,
                source_location='OGLE EWS',
                data_type='photometry',
                target=target)
               
                if created:

                    rd.save()

                else:
                    # photometry already there (I hope!)
                    break
            os.remove('./data/ogle_phot.dat')

    def to_generic_alert(self, alert):
        pass
  
