from django.core.management.base import BaseCommand
from mop.brokers import ztf_ipac


class Command(BaseCommand):

    help = 'Downloads ZTF IPAC data for all events '

    def add_arguments(self, parser):
        #parser.add_argument('years', help='years you want to harvest, spearted by ,')
        pass
    def handle(self, *args, **options):
        
        ZTF_IPAC = ztf_ipac.ZTFIPACBroker()
        ZTF_IPAC.fetch_alerts()


   
