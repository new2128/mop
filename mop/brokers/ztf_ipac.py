from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from tom_alerts.alerts import GenericBroker, GenericQueryForm
from django import forms
from tom_targets.models import Target
from tom_observations import facility
from tom_dataproducts.models import ReducedDatum
import urllib.request


from tom_alerts.brokers.mars import MARSQueryForm, MARSBroker
from tom_alerts.models import BrokerQuery



BROKER_URL = 'https://www.astro.caltech.edu/~pmroz/microlensing/table.html'


class ZTFIPACQueryForm(GenericQueryForm):
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


class ZTFIPACBroker(GenericBroker):
    name = 'ZTF_IPAC'
    form = ZTFIPACQueryForm
    mars = MARSBroker()
    def fetch_alerts(self,):
        
        #download from ZTF web server (i.e. Przemek webpage)
        ztf_ipac = urllib.request.urlopen(BROKER_URL).readlines()
        
	list_of_events = [str(i)[6:-8] for i in aa if '<td>ZTF' in str(i)]

        for event in list_of_events:

            mars_form = MARSQueryForm({'objectId':event})
            mars_form.is_valid()
            query = BrokerQuery.objects.create(
                               name='Query ZTF IPAC : '+event,
                               broker=mars.name,
                               parameters=mars_form.serialize_parameters()
                                               )
            alerts = mars.fetch_alerts(query.parameters_as_dict)
            for alert in alerts:
                mars.to_target(alert)



 
