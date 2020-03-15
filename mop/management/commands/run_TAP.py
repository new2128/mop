from django.core.management.base import BaseCommand
from tom_dataproducts.models import ReducedDatum
from tom_targets.models import Target
from astropy.time import Time
from mop.toolbox import TAP


class Command(BaseCommand):

    help = 'Sort events that need extra observations'
    
    def add_arguments(self, parser):
       

    
    def handle(self, *args, **options):





        
        list_of_events_alive = Target.objects.filter(targetextra__in=TargetExtra.objects.filter(key='Alive', value=True))  


        for event in list_of_events_alive:
            time_now = Time(datetime.datetime.now()).jd
            planet_priority = TAP_planet_priority(time_now,t0_pspl,u0_pspl,tE_pspl,fs_pspl,fb_pspl)
            ### need to create a reducedatum for planet priority
            print(planet_priority) 
            
          
