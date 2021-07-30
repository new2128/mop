from django import template
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt,mpld3

from mop.time_allocation import ReviewObservation
from tom_observations.models import ObservationRecord
from tom_targets.models import Target

register = template.Library()
Review = ReviewObservation()
review = Review.review()
class Plot():
    
    def plot(self, index):
        fig, axis = plt.subplots(1,1,figsize=(10,5))
        x_values = [0,1,2]
        y_values = [review[index][1]/review[index][0]]
        if(review[index][4]==0):
            y_values.append(0)
        else:
            y_values.append(review[index][5]/review[index][4])
        if(review[index][6]==0):
            y_values.append(0)
        else:
            y_values.append(review[index][7]/review[index][6])
        axis.barh(x_values, y_values,color="red",height=0.4)
        axis.set_xticks(np.arange(0, 1.2, 0.2))
        axis.set_yticks([0,1,2])
        axis.set_yticklabels(['Standard','Rapid Response','Time Critical'])  # isn't currently working
        axis.title.set_text(review[index][9] + " " + review[index][8])
        axis.text(0.01, 0, str(review[index][1])+"/"+str(review[index][0]), color='black',fontweight='bold')
        axis.text(0.01, 1, str(review[index][5])+"/"+str(review[index][4]), color='black',fontweight='bold')
        axis.text(0.01, 2, str(review[index][7])+"/"+str(review[index][6]), color='black',fontweight='bold')
        plt.figtext(0.1, 0.01, "IPP", fontsize=18, bbox={"facecolor":"orange", "alpha":0.5, "pad":5})
        plt.figtext(0.3, 0.01, "Available: " + str(review[index][3]) + " Limit: " + str(review[index][2]), fontsize=14, bbox={"facecolor":"white", "alpha":0.5, "pad":5})
        plt.show()
        mpld3.show()
        return {'figure': fig}
