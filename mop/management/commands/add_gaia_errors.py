from django.core.management.base import BaseCommand
from tom_targets.models import Target
from mop.brokers import gaia as gaia_mop



class Command(BaseCommand):

    help = 'Compute errorbars for Gaia'
    def add_arguments(self, parser):
        parser.add_argument('target_name', help='name of the event to compute errors')

    
    def handle(self, *args, **options):

       target, created = Target.objects.get_or_create(name= options['target_name'])
       gaia_mop.update_gaia_errors(target)
