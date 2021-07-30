import requests

from django.core.management.base import BaseCommand


from tom_dataproducts.models import ReducedDatum
from tom_observations.models import ObservationRecord
import tom_observations.templatetags.observation_extras as obslist
from tom_targets.models import Target, TargetExtra, TargetList

#change to BaseCommand when uploading the code, this is just for testing purposes
class ReviewObservation():

    help = 'Retrieve time allocation variables for different proposals to add new functionality to MOP'

    def review(self):
        list_of_observations = []
        headers={'Authorization': 'Token {0}'.format(LCO_SETTINGS['api_key'])}
        response = requests.get('https://observe.lco.global/api/proposals/', headers=headers,timeout=20)
        results_dictionary = response.json().get('results')
        instruments_dictionaries = results_dictionary[0].get('timeallocation_set')
        for instrument_dictionary in instruments_dictionaries:
            std_allocation = instrument_dictionary.get('std_allocation')
            std_time_used = instrument_dictionary.get('std_time_used')
            ipp_limit = instrument_dictionary.get('ipp_limit')
            ipp_time_available = instrument_dictionary.get('ipp_time_available')
            rr_allocation = instrument_dictionary.get('rr_allocation')
            rr_time_used = instrument_dictionary.get('rr_time_used')
            tc_allocation = instrument_dictionary.get('tc_allocation')
            tc_time_used = instrument_dictionary.get('tc_time_used')
            instrument_type = instrument_dictionary.get('instrument_type')
            semester = instrument_dictionary.get('semester')
            variable_list = [std_allocation, std_time_used, ipp_limit, ipp_time_available,
                            rr_allocation, rr_time_used, tc_allocation, tc_time_used,
                            instrument_type, semester]
            list_of_observations.append(variable_list)
        return list_of_observations
