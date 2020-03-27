from django.core.management.base import BaseCommand
from tom_targets.models import Target
from mop.toolbox import obs_control
from astropy.time import Time
import datetime

class Command(BaseCommand):

    help = 'Submit Regular photometry observations'
    
    def add_arguments(self, parser):
        parser.add_argument('target_name', help='name of the event to observe')

    
    def handle(self, *args, **options):
      
        target, created = Target.objects.get_or_create(name= options['target_name'])
        obs_control.build_and_submit_regular_phot(target)
