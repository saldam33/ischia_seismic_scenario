#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  scenario.py
#  
#  Copyright 2021 Salvatore D'Amico <salvatore.damico@ingv.it>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
import math
import numpy as np
import scipy.stats

class Scenario:
    def __init__(self):
        # coefficients of the binomial attenuation law.
        self.g1Coeffs = {8: 2.9081, 9: 8.9291, 10: 21.50223, 11:8.2065}
        self.g2Coeffs = {8: 0.7633, 9: 1.4153, 10:  2.8911,  11:1.5557}            

        # array of intensità
        self.intensities = list(np.arange(1, 13))


    def gdist(self, epiInt, epiDist, useAnisotropic=False):
        epiInt = int(epiInt)

        g1 = self.g1Coeffs[epiInt]
        g2 = self.g2Coeffs[epiInt]

        gd = (g1 / (g1 + epiDist))**g2
        return gd
        
        
    # ~ def probRotondiVarini(self, epiInt, dist, useAnisotropic):
        # ~ # calcola la distribuzione binomiale delle probabilità per i 
        # ~ # gradi di intensità intensities
        # ~ gd = self.gdist(epiInt, dist, useAnisotropic)
        # ~ intensities = list(np.arange(2, 13))
        # ~ p2 = scipy.stats.binom.pmf(self.intensities, epiInt, gd)
        # ~ p1 = math.exp(math.log(epiInt) + math.log(gd) + (epiInt-1)*math.log(1-gd))
        # ~ p1 = p1 + math.exp(epiInt * math.log(1-gd))
        # ~ """
        # ~ dn = dfloat(n)
        # ~ binom = dexp(dlog(dn)+dlog(p)+(dn-1.d0)*dlog(1.d0-p))
        # ~ binom = binom+dexp(dn*dlog(1.d0-p))
        # ~ """
        # ~ p = [p1]
        # ~ p.extend(p2)
        # ~ return p
        
        
    def prob(self, epiInt, distKm, useAnisotropic=False):
        """ The function calculates the binomial distribution of probability
        for each expected intensity. 
        The epicentral intensity epiInt is splitted into 2 values,
        in order to taking into account the uncertainty the 
        probabilities are calculated as weighted average """
        
        epiI1 = int(epiInt)
        if epiInt > epiI1:
            epiI2 = epiI1 + 1
            w2 = 0.5
        else:
            epiI2 = epiI1
            w2 = 1
            
        # calculation for epiI1
        gd = self.gdist(epiI1, distKm, useAnisotropic=False)
        p1 = scipy.stats.binom.pmf(self.intensities, epiI1, gd)
        # calculation for epiI2
        gd = self.gdist(epiI2, distKm, useAnisotropic=False)
        p2 = scipy.stats.binom.pmf(self.intensities, epiI2, gd)
        
        # calculated the weighted average
        p = (p1 + p2*w2) / (1 + w2)
        
        return p
        
        
    def iMax(self, probs):
        """ iMax calculates the expected intensity as the most probable value. """

        # convert from numpy.float64 to float by item() method
        i = np.argmax(probs).item()
        # Add +1 because index starts from 0
        i = i+1
        
        return i

        
    def cumProb(self, probs):
        """ cumProb calculates the cumulative probability. """

        pflip = np.flip(probs, 0)
        pflip = pflip.cumsum()
        p = np.flip(pflip, 0)

        # convert from numpy.float64 to float by item() method
        pp = []
        for r in p:
            pp.append(r.item())
        return pp

