from tom_targets.models import Target
from tom_alerts.brokers import 
from tom_dataproducts.models import ReducedDatum
from astropy.time import Time, TimezoneInfo


def ingest_photometry_to_an_event(target,times_in_jd, mags, emags, filters, origin = '', force_ingest = False):

    for index,time in enumerate(times_in_jd):
        
        jd = Time(time, format='jd', scale='utc')
        jd.to_datetime(timezone=TimezoneInfo())
        data = {   'magnitude': mags[ind],
                   'filter': filters[ind],
                   'error': emags[ind]
               }
        rd, created = ReducedDatum.objects.get_or_create(
                timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                value=data,
                source_name=target.name,
                source_location=alert['lco_id'],
                data_type='photometry',
                target=target)
        
        rd.save()



def create_a_new_event():




