# -*- coding: utf-8 -*-
"""
Created on Fri Nov 10 11:23:50 2017

@author: rahlfshh
"""
##indices as used in StimulusBackend.py
#only to be changed in both python codes otherwise uncontrolled behavior may occure
#TODO we could use imported values from that class but that means we need to add it to same directory/ste-packages
noiseIDX = 0
noiseGapIDX = 1
noiseFreqMinIDX = 2
noiseFreqMaxIDX = 3
preStimAttenIDX = 4
preStimFreqIDX = 5
ISIIDX = 6
noiseTimeIDX = 7

import numpy as np
import numpy.random as rnd
rnd.seed(1234)



###Input Values

#paramSchwelle are the parameters recived by the user via the GUI

#paramTurner are the differen Band middles used for turner

#nturner is the number of trials

#nennerTurner is the nominator of the exponent

#####Return values
#generate an array, which is used to generate stmulation,
#each measurement is represented in on row
#each row looks like:
#[noise, noiseGap,noiseFreqMin, noiseFreqMax, preStimAtten, preStimFreq, ISI, noiseTime]
#noise           => whether a noise is played ot not
#noiseGap        => whether a noise Gap occures(only relevant if noise is true)
#noiseFreqMin/Max=> cutoff frequences of the noise in Hz
#preStimAtten    => Attenuation of the prestimulus in dBspl negative values 
#                   mean no prestimulus at all
#preStimFreq     => Frequency of the preStimulus in Hz
#                   At this moment no band prestimulus is possible,
#                   StimuluationBackend would need a update to do so
#ISI             => Inter Stimulus Intervall in ms, Time between two stimuli
#                   Randomised inbetween 6 and 14, only relevant if no noise 
#                   is present as the noise time fullfills the job of ISI  
#noiseTime       => Time a noise is present in ms, Randomised between 6 and 14

#ending is the ending the konfig file is supposed to have 
#only hearingthreshold measurement => _HEARINGTHRESHOLD
#only tinnitus perception =>_TURNER
#both =>_TURNER_AND_HEARINGTHRESHOLD



def fiveStartles():
    print(5)
    arr = np.zeros(8)
    arr[preStimAttenIDX] = -1
    arr[ISIIDX] = 10000
    print(np.vstack((arr,arr,arr,arr,arr)))
    return np.vstack((arr,arr,arr,arr,arr))

def generateKonfigArray(paramSchwelle,paramTurner,nturner, nennerTurner):
    a = []
    b = []
    ending = ""
    if len(paramSchwelle) == 6:
        a = generateSchwellKonifg(paramSchwelle)
    if len(paramTurner) > 0:
        b = generateTurnerKonifg(paramTurner,nturner, nennerTurner)
    if a ==[] and b == []:
        print("fehler")
        return[]
    if a == []:
        output = b
        ending = "_TURNER"
    elif b == []:
        output = a
        ending = "_HEARINGTHRESHOLD"
    else:
        print(1)
        output = np.concatenate((a,b))
        ending = "_TURNER_AND_HEARINGTHRESHOLD"
        
    #This shuffels the measurement to prevent adaption.
    #Thats why all tests subjects are supposed to recive the same stimulus file
    print(2)
    rnd.shuffle(output)
    print(4)
    #add five startle measurments to adjust the mouse to the environment

    output = np.concatenate((fiveStartles(),output))
    print(output)
    print(3)
    return output, ending
    
#generate all konfig rows for the hearing threshold measurement
def generateSchwellKonifg(paramSchwelle):
    #extract konfiguration entered by the user(GUI)
    output = []
    
    #number of trials
    n = paramSchwelle[0]
    #smallest Frequency for which a hearing threshold is measured
    kleinsteFrequenz = paramSchwelle[1]
    #highest Frequency for which a hearing threshold is measured
    groeßteFrequenz = paramSchwelle[2]
    #factor which decides the steps inbetween measured frequencies
    frequenzFactor = paramSchwelle[3]
    #maximum attenuation in dBspl for which a hearingthreshold is measured
    maximaleLautstaerke = paramSchwelle[4]
    #steps in which the attenuation is raised
    SchrittgroeßeLautstaerke = paramSchwelle[5]
  
    #translate the button state into Exponent denominator 
    #each turn the exponent needs to be raised linearly
    #but the steps differe to reach different steps
    if frequenzFactor == 0:
        potenzNennerFrequenzfaktor = 1
    if frequenzFactor == 1:
        potenzNennerFrequenzfaktor = 2    
    if frequenzFactor == 2:
        potenzNennerFrequenzfaktor = 4
    #exponent nominator
    potenzZaehlerFrequenzfaktor = 0
    
    for i in range(n):
        arr = [None,None,None,None,None,None,None,None]
        arr[noiseIDX] = 0
        arr[noiseGapIDX] = 0
        arr[noiseFreqMinIDX] = 0
        arr[noiseFreqMaxIDX] = 0
        arr[preStimAttenIDX] = -1
        #needs to be done like this to prevent floating point mistakes
        arr[preStimFreqIDX] = kleinsteFrequenz*2**(potenzZaehlerFrequenzfaktor/potenzNennerFrequenzfaktor)
        #generate random ISI in ms
        arr[ISIIDX] = (6 + 2*4*rnd.rand())*1000
        arr[noiseTimeIDX] = 0
        output.append(arr)
        #output.append([0,0,0,0,lautstaerke, kleinsteFrequenz*2**(potenzZaehlerFrequenzfaktor/potenzNennerFrequenzfaktor), (6 + 2*4*rnd.rand())*1000,0])
        
	
    #loop over different frequencies
    while kleinsteFrequenz*2**(potenzZaehlerFrequenzfaktor/potenzNennerFrequenzfaktor) <= groeßteFrequenz:
        #one startel measurement without any prestimulous is needed
        lautstaerke = SchrittgroeßeLautstaerke
        #loop over different attenuations
        while lautstaerke <= maximaleLautstaerke:
            #loop for number of turns 
            for i in range(n):
                arr = [None,None,None,None,None,None,None,None]
                arr[noiseIDX] = 0
                arr[noiseGapIDX] = 0
                arr[noiseFreqMinIDX] = 0
                arr[noiseFreqMaxIDX] = 0
                arr[preStimAttenIDX] = lautstaerke
                #needs to be done like this to prevent floating point mistakes
                arr[preStimFreqIDX] = kleinsteFrequenz*2**(potenzZaehlerFrequenzfaktor/potenzNennerFrequenzfaktor)
                #generate random ISI in ms
                arr[ISIIDX] = (6 + 2*4*rnd.rand())*1000
                arr[noiseTimeIDX] = 0
                output.append(arr)
                #output.append([0,0,0,0,lautstaerke, kleinsteFrequenz*2**(potenzZaehlerFrequenzfaktor/potenzNennerFrequenzfaktor), (6 + 2*4*rnd.rand())*1000,0])
            lautstaerke += SchrittgroeßeLautstaerke
        potenzZaehlerFrequenzfaktor+=1
    #Print output to check, this can be removed later
    for o in output:
        print(o)
    return output

#TODO wie wollen wir das hier machen, wenn die maximale rauschfrequenz über 48000 geht`???
#generate all konfig rows for the turner measurement
def generateTurnerKonifg(paramTurner,nturner, nennerTurner):
    output = []
    #loop over differen band middles
    for mid in paramTurner:
        print("mid" + str(mid))
        if mid > 0:
            noiseType = 1
        elif mid == 0:
            noiseType = 2
        else:
            noiseType = 3
        #loop over number of turns
        for i in range(nturner):
            #####no gap startel
            arr = [None,None,None,None,None,None,None,None,]
            arr[noiseIDX] = noiseType
            arr[noiseGapIDX] = 0
            #bandwidth depends on selected bandwidth
            arr[noiseFreqMinIDX] = int(abs(mid)/(2**(1/nennerTurner)))
            arr[noiseFreqMaxIDX] = int(abs(mid)*(2**(1/nennerTurner)))
            arr[preStimAttenIDX] = 0
            arr[preStimFreqIDX] = 0
            arr[ISIIDX] = 0
            arr[noiseTimeIDX] = (6 + 2*4*rnd.rand())*1000
            output.append(arr)
            #output.append([1,0,0,0,0,0,0, (6 + 2*4*rnd.rand())*1000])
            #########Gap startel
            arr2 = [None,None,None,None,None,None,None,None,]
            arr2[noiseIDX] = noiseType
            arr2[noiseGapIDX] = 1
            #bandwidth depends on selected bandwidth
            arr2[noiseFreqMinIDX] = int(abs(mid)/(2**(1/nennerTurner)))
            arr2[noiseFreqMaxIDX] = int(abs(mid)*(2**(1/nennerTurner)))
            arr2[preStimAttenIDX] = 0
            arr2[preStimFreqIDX] = 0
            arr2[ISIIDX] = 0
            arr2[noiseTimeIDX] = (6 + 2*4*rnd.rand())*1000
            output.append(arr2)
            #output.append([1,1,int(mid-rauschBandbreite/2),int(mid+rauschBandbreite/2),0,0,0, (6 + 2*4*rnd.rand())*1000])
    #Print output to check, this can be removed later
    for o in output:
        print(o)
    return output
