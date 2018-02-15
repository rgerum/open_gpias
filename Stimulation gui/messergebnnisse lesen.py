# -*- coding: utf-8 -*-
"""
Created on Wed Nov 29 10:47:38 2017

@author: rahlfshh
"""
import matplotlib.pyplot as plt
import numpy as np
file = open("extractedmessergebniss.npy","rb")
data_extracted = np.load(file)
file.close()
file = open("emessergebniss.npy","rb")
all_data = np.load(file)
file.close()
print(np.argmax(data_extracted[0][0]))



plt.figure(50)
#plt.subplot(211)
i = all_data[0]
plt.plot(i[int(i[0]*3/4)+1+77500:int(i[0]*3/4)+1+78000])
plt.xlabel('time')
plt.ylabel('amplitude')
plt.title('trigger')



for i in range(len(data_extracted)):
    for j in range(3):
        fig  = plt.figure(i*3+j)
        #plt.subplot(211)
        plt.plot(data_extracted[i][j])
        plt.xlabel('time')
        plt.ylabel('amplitude')
        plt.title('sensor signal')
        if j == 0:
            fig.savefig("x-kanal" + str(i) + ".png")
            
        if j == 1:
            fig.savefig("y-kanal" + str(i) + ".png")
            
        if j == 2:
            fig.savefig("trigger-kanal" + str(i) + ".png")
            