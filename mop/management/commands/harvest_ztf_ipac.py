from django.core.management.base import BaseCommand
from mop.brokers import ztfipac


class Command(BaseCommand):

    help = 'Downloads ZTF IPAC data for all events '

    def add_arguments(self, parser):
        #parser.add_argument('years', help='years you want to harvest, spearted by ,')
        pass
    def handle(self, *args, **options):

        ZTFIPAC = ztfipac.ZTFIPACBroker()
        ZTFIPAC.fetch_alerts()


   
