from django.core.management.base import BaseCommand
from tom_alerts.brokers import gaia
from astropy.coordinates import SkyCoord
import astropy.units as unit
from tom_targets.models import Target
from mop.brokers import gaia as gaia_mop
class Command(BaseCommand):

    help = 'Downloads Gaia data for all events marked as microlensing candidate'
    def add_arguments(self, parser):
        pass
       
    def handle(self, *args, **options):
        
        Gaia = gaia.GaiaBroker()
        list_of_alerts = Gaia.fetch_alerts({'target_name':None,'cone':None})
        
        for alert in list_of_alerts:
          
             if 'microlensing' in alert['comment']:    
 
                   #Create or load

                   clean_alert = Gaia.to_generic_alert(alert)
                   try: 
                       target, created = Target.objects.get_or_create(name=clean_alert.name,ra=clean_alert.ra,dec=clean_alert.dec,type='SIDEREAL',epoch=2000)
                   #seems to bug with the ra,dec if exists
                   except:
                          target, created = Target.objects.get_or_create(name=clean_alert.name) 
                 
                   Gaia.process_reduced_data(target)
                   gaia_mop.update_gaia_errors(target)

