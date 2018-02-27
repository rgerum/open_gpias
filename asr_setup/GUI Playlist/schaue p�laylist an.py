# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 14:23:37 2018

@author: rahlfshh
"""

import numpy as np
import pandas as pd

def tryint(value):
    try:
        return int(value)
    except:
        return value

playlist = np.load("playlist_neu_20_TURNER.npy")


# Need To match indices of BackendPlaylist
header=["noiseIDX", "noiseGapIDX", "noiseFreqMinIDX", "noiseFreqMaxIDX", "preStimAttenIDX", "preStimFreqIDX", "ISIIDX", "noiseTimeIDX"]
pd.set_option('expand_frame_repr', False)
df = pd.DataFrame(playlist.astype("int"), columns=header)
print(df)
