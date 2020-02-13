from django.core.management.base import BaseCommand
from mop.brokers import moa


class Command(BaseCommand):

    help = 'Downloads MOA data for all events for a given years list'

    def add_arguments(self, parser):
        parser.add_argument('years', help='years you want to harvest, spearted by ,')

    def handle(self, *args, **options):
        
        Moa = moa.MOABroker()
        list_of_targets = Moa.fetch_alerts('./data/',[options['years']])
        Moa.find_and_ingest_photometry(list_of_targets)


   
