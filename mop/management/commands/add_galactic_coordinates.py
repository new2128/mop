from django.core.management.base import BaseCommand
from tom_targets.models import Target
from mop.brokers import gaia as gaia_mop
from astropy import units as u
from astropy.coordinates import SkyCoord


class Command(BaseCommand):

    help = 'Compute galactic coordinates l and b for all targets'
    def add_arguments(self, parser):
        parser.add_argument('target_name', help='name of the event to compute errors')

    
    def handle(self, *args, **options):
       
       list_of_targets = Target.objects.filter()
    
       for target in list_of_targets:

           cible = SkyCoord(ra=target.ra*u.degree, dec=target.dec*u.degree, frame='icrs')
             
           galactic = {'galactic_lng' : cible.galactic.l.value, 'galactic_lat':cible.galactic.b.value}

           target.save(extras=galactic)

