#!/opt/miniconda3/bin/python
import numpy as np
import pandas as pd


###### GENERATE SOME DATA #######
'''
df = pd.read_csv('/Users/stephencurran/teaching/VUW/345_Experiments_In_Space/data/weight-height.csv')
df['Height'] =  df['Height']*2.54 # TO cm
df['Weight'] = df['Weight']/2.20462 # TO kg

M = df[df['Gender'] == "Male"]
M = M[['Height','Weight']]

M_123 =  M.head(123); print(M_123)

M.to_csv('hw_all.dat', sep =' ', header = False, index = False)
M_123.to_csv('hw_all-123.dat', sep =' ', header = False, index = False)
'''
# START WITH hw_all-123.dat
data = pd.read_csv("hw_all-123.dat",delim_whitespace=True, header=None)

#x = data[0]; y = data[1]
#print(y)
import scatterbin

scatterbin.plot(data,fs = 14,xlabel = "Height [cm]",ylabel = "Weight [kg]",
                      pvalue=True, equal_span = 'x', nbins = 5,
                      point_ec = 'r', point_fc = 'r', inc_strays = True,
                      hc=True, plot_name = 'hw_123') 

data = pd.read_csv("hw_all.dat",delim_whitespace=True, header=None)

scatterbin.plot(data,fs = 14,xlabel = "Height [cm]",ylabel = "Weight [kg]",
                      pvalue=True, equal_span = 'nx',point_fc = 'b',point_ec = 'b',
                      point_s = 2,alpha=1,nbins = 10,
                      two_panel = True, width=7,height=7,
                      hc=True, plot_name = 'hw_all') 

