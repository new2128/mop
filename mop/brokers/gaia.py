from tom_dataproducts.models import ReducedDatum
import json

#for a given mag computes new error-bar
#from Gaia DR2 papers, degraded by x10 (N=100 ccds), in log
def estimateGaiaError(mag) :

    a1=0.2
    b1= -5.3#-5.2
    log_err1 = a1*mag + b1
    a2=0.2625
    b2= -6.3625#-6.2625
    log_err2 = a2*mag + b2

    if (mag<13.5): expectedStdAtBaselineMag = 10**(a1*13.5+b1)
    if (mag>=13.5 and mag<17) : expectedStdAtBaselineMag = 10**log_err1
    if (mag>=17) : expectedStdAtBaselineMag = 10**log_err2
    #this works until 21 mag.

    return expectedStdAtBaselineMag

def update_gaia_errors(target):

    datasets = ReducedDatum.objects.filter(target=target)




    for i in datasets:

        if i.data_type == 'photometry':
            magnitude = json.loads(i.value)['magnitude']
            error = estimateGaiaError(magnitude)
            new_value = i.value[:-1]+', "error":'+str(error)[:7]+'}'
            i.value = new_value 
            i.save()
