import os
import requests
import urllib
from urllib.error import HTTPError
from astropy.time import Time, TimezoneInfo
import datetime
import pandas as pd
import lxml.html as lh
from bs4 import BeautifulSoup
from astropy.coordinates import SkyCoord
from html_table_parser.parser import HTMLTableParser
from tom_targets.models import Target
from tom_dataproducts.models import ReducedDatum

BROKER_URL = 'http://www.astronomy.ohio-state.edu/asassn/transients.html'
photometry = 'https://asas-sn.osu.edu/photometry'


class ASASSNBroker():

    def __init__(self, name):
        self.name = name

    '''
    Opens the URL of the ASAS-SN transient table to ensure that the link functions
    '''
    def open_webpage(self):
        page_status_code = requests.get(BROKER_URL).status_code
        return page_status_code

    '''
    Reads data from the ASAS-SN transient table into a list
    '''
    def retrieve_transient_table(self):
        page = requests.get(BROKER_URL)
        doc = lh.fromstring(page.content)
        tr_elements = doc.xpath('//tr')
        col = []
        i = 0
        for t in tr_elements[0]:
            i += 1
            content = t.text_content()
            col.append((content, []))
        for j in range(1, len(tr_elements)):
            T = tr_elements[j]
            '''
            If row is not of size 12, the data is not from the right table
            '''
            if len(T) != 12:
                break
            i = 0
            for t in T.iterchildren():
                data = t.text_content()
                if i>0:
                    try:
                        data = int(data)
                    except:
                        pass
                col[i][1].append(data)
                i += 1
        return col

    '''
    Searches the transient list for microlensing candidates and appends them to a list of events
    '''
    def retrieve_microlensing_coordinates(self):
        transienttable = self.retrieve_transient_table()
        listofindices = []
        i = 0
        newlist = [str(s) for s in transienttable[11][1]]
        for m in newlist:
            if 'microlensing' in m or 'Microlensing' in m:
                listofindices.append(i)
            i += 1
        fullralist = []
        fulldeclist = []
        fullids = []
        fullasassnids = []
        fullralist = [str(s) for s in transienttable[3][1]]
        fulldeclist = [str(s) for s in transienttable[4][1]]
        fullids = [str(s) for s in transienttable[0][1]]
        fullasassnids = [str(s) for s in transienttable[1][1]]
        listofevents = []
        for n in listofindices:
            listofevents.append([fullids[n], fullasassnids[n], fullralist[n], fulldeclist[n]])
        return listofevents

    '''
    Creates and saves Target objects from the list of microlensing events
    '''
    def fetch_alerts(self):
        list_of_targets = []
        listofevents = self.retrieve_microlensing_coordinates()
        for event in listofevents[0:]:
            target_name = event[0]
            ra_split = event[2].split(':')
            dec_split = event[3].split(':')
            ra = float(ra_split[0]) + (float(ra_split[1])/60) + (float(ra_split[2])/3600)
            dec = float(dec_split[0]) + (float(dec_split[1])/60) + (float(dec_split[2])/3600)
            coords = [ra, dec]
            cible = SkyCoord(coords[0], coords[1], unit="deg")
            try:
                target = Target.objects.get(name=target_name)
                '''
                check for target duplication by ra and dec once this code is written
                '''
            except Target.DoesNotExist:
                target, created = Target.objects.get_or_create(name=target_name,
                    ra=cible.ra.degree, dec=cible.dec.degree,
                    type='SIDEREAL', epoch=2000)
                if created:
                    target.save()
            list_of_targets.append(target)
        return list_of_targets

    '''
    Reads a URL to determine whether it is valid/contains relevent data
    '''
    def url_get_contents(self, url):
        req = urllib.request.Request(url=url)
        f = urllib.request.urlopen(req)
        return f.read()

    '''
    Searches the ASAS-SN photometry database using RA and Dec of photometry candidates and a 2 arcminute radius
    Creates and saves a ReducedDatum object of the given Target and its associated photometry data
    '''
    def find_and_ingest_photometry(self):
        targets = self.fetch_alerts()
        i = 0
        lightcurvelinks = []
        lightcurvepartlinks = []
        indices_with_photometry_data = []
        rd_list = []

        events = self.retrieve_microlensing_coordinates()
        while(i < len(events)):
            samplera = self.retrieve_microlensing_coordinates()[i][2]
            sampledec = self.retrieve_microlensing_coordinates()[i][3]
            sampleralist = samplera.split(':')
            sampledeclist = sampledec.split(':')
            photometryurl = os.path.join("https://asas-sn.osu.edu/photometry?utf8=%E2%9C%93&ra="
                    + sampleralist[0] + "%3A"+sampleralist[1] + "%3A" + sampleralist[2] + "&dec=" + sampledeclist[0]
                + "%3A"+sampledeclist[1] + "%3A"+sampledeclist[2]
                + "&radius=.033333&vmag_min=&vmag_max=&epochs_min=&epochs_max=&rms_min=&rms_max=&sort_by=raj2000")
            html_page = urllib.request.urlopen(photometryurl)
            soup = BeautifulSoup(html_page, "lxml")

            for link in soup.findAll('a'):
                s = str(link.get('href'))
                if('/photometry/' in s):
                    lightcurvepartlinks.append(link.get('href'))
                    indices_with_photometry_data.append(i)
            i = i + 1

        for partlink in lightcurvepartlinks:
            lightcurvelinks.append(os.path.join('https://asas-sn.osu.edu' + partlink))

        '''
        Reads links with photometry data
        '''
        k = 0
        for link in lightcurvelinks:
            running = True
            hjd = []
            ut_date = []
            camera = []
            myfilter = []
            mag = []
            mag_error = []
            flux = []
            flux_error = []
            '''
            Parses through each page of data, starting at page 1
            '''
            i = 1
            while(running == True):
                functional_link = os.path.join(link+"?page=" + str(i))
                try:
                    xhtml = self.url_get_contents(functional_link).decode('utf-8')
                    p = HTMLTableParser()
                    p.feed(xhtml)
                    dataframe = pd.DataFrame(p.tables)
                    matrix = dataframe.to_numpy()
                    length = len(matrix[0])
                    j = 1
                    while(j < length):
                        hjd.append(matrix[0][j][0])
                        ut_date.append(matrix[0][j][1])
                        camera.append(matrix[0][j][2])
                        myfilter.append(matrix[0][j][3])
                        mag.append(matrix[0][j][4])
                        mag_error.append(matrix[0][j][5])
                        flux.append(matrix[0][j][6])
                        flux_error.append(matrix[0][j][7])
                        j = j + 1

                except HTTPError:
                    running == False
                    break
                i = i + 1
            data = {'magnitude': mag, 'myfilter': myfilter,
                    'error': mag_error}
            jd = Time(datetime.datetime.now()).jd
            jd = Time(jd, format='jd', scale='utc')
            index = indices_with_photometry_data[k]
            target = targets[index]
            try:
                rd = ReducedDatum.objects.get(value=data)
            except:
                rd, created = ReducedDatum.objects.get_or_create(
                    timestamp = jd.to_datetime(timezone=TimezoneInfo()),
                    value=data,
                    source_name='ASAS-SN',
                    data_type='photometry',
                    target=target)
            if created:
                rd.save()
            rd_list.append(rd)
            k = k + 1
        return rd_list
