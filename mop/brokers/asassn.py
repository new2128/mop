import os
from django import forms
import requests
import urllib
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from astropy.time import Time, TimezoneInfo
import datetime
import pandas as pd
import lxml.html as lh
import mechanicalsoup
from bs4 import BeautifulSoup
from astropy.coordinates import SkyCoord
import astropy.units as unit
import json
from html_table_parser.parser import HTMLTableParser


from tom_targets.models import Target
from tom_alerts.alerts import GenericBroker, GenericQueryForm
from tom_dataproducts.models import ReducedDatum

BROKER_URL = 'http://www.astronomy.ohio-state.edu/asassn/transients.html' #should be a known variable?
photometry = 'https://asas-sn.osu.edu/photometry'


class ASASSNBroker():
    def __init__(self, name):  
        self.name = name 
    #name='ASAS-SN'

    def open_webpage(self):
        page_status_code=requests.get(BROKER_URL).status_code
        return page_status_code

    def retrieve_transient_table(self):
        page=requests.get(BROKER_URL)
        doc = lh.fromstring(page.content)
        tr_elements = doc.xpath('//tr')
        col=[]
        i=0
        for t in tr_elements[0]:
            i+=1
            content=t.text_content()
            col.append((content,[]))
        for j in range(1,len(tr_elements)):
            #T is our j'th row
            T=tr_elements[j]
            #If row is not of size 12, the //tr data is not from our table 
            if len(T)!=12:
                break
            i=0
            #Iterate through each element of the row
            for t in T.iterchildren():
                data=t.text_content() 
                #Check if row is empty
                if i>0:
                #Convert any numerical value to integers
                    try:
                        data=int(data)
                    except:
                        pass
                #Append the data to the empty list of the i'th column
                col[i][1].append(data)
                #Increment i for the next column
                i+=1
        return col

    def retrieve_microlensing_coordinates(self):
        transienttable = self.retrieve_transient_table()
        listofindices=[]
        i=0
        newlist = [str(s) for s in transienttable[11][1]]   
        for m in newlist:
            if 'microlensing' in m or 'Microlensing' in m:
                listofindices.append(i)
            i+=1
        fullralist = []
        fulldeclist = []
        fullids = []
        fullasassnids = []
        fullralist = [str(s) for s in transienttable[3][1]] 
        fulldeclist = [str(s) for s in transienttable[4][1]]
        fullids = [str(s) for s in transienttable[0][1]]
        fullasassnids = [str(s) for s in transienttable[1][1]]
        selectedralist=[]
        selecteddeclist=[]
        selectedids=[]
        selectedasassnids=[]
        listofevents=[]
        for n in listofindices:
            #is this set up efficiently? 
            listofevents.append([fullids[n],fullasassnids[n],fullralist[n],fulldeclist[n]])
        return listofevents
    
    def fetch_alerts(self):
        list_of_targets=[]
        time_now=Time(datetime.datetime.now()).jd
        listofevents = self.retrieve_microlensing_coordinates()
        #first index for listofevents is for first event
        #subindices are for id, second id, ra, dec
        #event is an array
        for event in listofevents[0:]:
            target_name=event[0]
            ra_split=event[2].split(':')
            dec_split=event[3].split(':')
            ra = float(ra_split[0]) + (float(ra_split[1])/60) + (float(ra_split[2])/3600)
            dec = float(dec_split[0]) + (float(dec_split[1])/60) + (float(dec_split[2])/3600)
            coords=[ra,dec]
            cible=SkyCoord(coords[0],coords[1],unit="deg")
            try:
                target = Target.objects.get(name=target_name)
                #target = Target.objects.get(ra=)
                #2arcsec
            except: 
                target, created = Target.objects.get_or_create(name=target_name,ra=cible.ra.degree,dec=cible.dec.degree,
                type='SIDEREAL',epoch=2000)
                if created:
                    target.save()
            list_of_targets.append(target)
        return list_of_targets

    def url_get_contents(self,url):
        req = urllib.request.Request(url=url)
        f = urllib.request.urlopen(req)
        return f.read() 

    def find_and_ingest_photometry(self):
            targets = self.fetch_alerts()
            #eventually add target parameter, and only do this search if the target isn't fully created
            #(e.g. no photometry data exists for it yet )
            time_now = Time(datetime.datetime.now()).jd
            #for target in targets:
            #datasets = ReducedDatum.objects.filter(target=target)
            #existing_time = [Time(i.timestamp).jd for i in datasets if i.data_type == 'photometry']
            i=0
            lightcurvelinks=[]
            lightcurvepartlinks=[]
            while(i<len(self.retrieve_microlensing_coordinates())):
                samplera=self.retrieve_microlensing_coordinates()[i][2]
                sampledec=self.retrieve_microlensing_coordinates()[i][3]
                sampleralist=samplera.split(':')
                sampledeclist=sampledec.split(':')
                photometryurl=os.path.join("https://asas-sn.osu.edu/photometry?utf8=%E2%9C%93&ra="
                +sampleralist[0]+"%3A"+sampleralist[1]+"%3A"+sampleralist[2]+"&dec="+sampledeclist[0]
                +"%3A"+sampledeclist[1]+"%3A"+sampledeclist[2]
                +"&radius=1&vmag_min=&vmag_max=&epochs_min=&epochs_max=&rms_min=&rms_max=&sort_by=raj2000")
                #req=Request(photometryurl)
                #html_page=urlopen(req)
                html_page=urllib.request.urlopen(photometryurl)
                soup=BeautifulSoup(html_page,"lxml")
                
                for link in soup.findAll('a'):
                    s=str(link.get('href'))
                    if('/photometry/' in s):
                        lightcurvepartlinks.append(link.get('href'))
                
                for partlink in lightcurvepartlinks:
                    lightcurvelinks.append(os.path.join('https://asas-sn.osu.edu'+partlink))
                i=i+1
            
            #read links:
            running = True
            for link in lightcurvelinks:
                    hjd=[]
                    ut_date=[]
                    camera=[]
                    myfilter=[]
                    mag=[]
                    mag_error=[]
                    flux=[]
                    flux_error=[]
                    i=1
                    while(running==True):
                        functional_link=os.path.join(link+"?page="+str(i))
                        #parse through each page of data 
                        try:
                            xhtml=self.url_get_contents(functional_link).decode('utf-8')
                            p = HTMLTableParser()
                            p.feed(xhtml)
                            dataframe=pd.DataFrame(p.tables)
                            matrix=dataframe.to_numpy()
                            length=len(matrix[0])
                            j=1
                            
                            while(j<length):
                                hjd.append(matrix[0][j][0])
                                ut_date.append(matrix[0][j][1])
                                camera.append(matrix[0][j][2])
                                myfilter.append(matrix[0][j][3])
                                mag.append(matrix[0][j][4])
                                mag_error.append(matrix[0][j][5])
                                flux.append(matrix[0][j][6])
                                flux_error.append(matrix[0][j][7])
                                j=j+1
                            data = {'magnitude':mag,'myfilter':myfilter,
                            'error':mag_error}
                            jd=Time(2451544.5, format='jd', scale='utc')
                            try:
                                rd = ReducedDatum.objects.get(value=data)
                                #2arcsec
                                #django cone searches 
                            except:
                                rd, created = ReducedDatum.objects.get_or_create(
                                timestamp=jd.to_datetime(timezone=TimezoneInfo()),
                                value=['data','nodata'],
                                source_name='ASAS-SN',
                                data_type='photometry',
                                target=targets[0]
                                )
                            if created:
                                rd.save()
                                print(rd.data_type)
                            i=i+1
                                
                            break
                        except HTTPError as err:
                            running==False
                            break
                       
                        
            
            return lightcurvelinks
                            
