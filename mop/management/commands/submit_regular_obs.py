from django.core.management.base import BaseCommand
from tom_targets.models import Target
from mop.toolbox import obs_control
from astropy.time import Time
import datetime
class Command(BaseCommand):

    help = 'Submit Regular photomotry observations'
    
    def add_arguments(self, parser):
        parser.add_argument('target_name', help='name of the event to fit')

    
    def handle(self, *args, **options):

       target, created = Target.objects.get_or_create(name= options['target_name'])
       time_now = Time(datetime.datetime.now())
       time_end = time_now+7
       
       obs_control.submit_imaging_to_LCO(target,4)
