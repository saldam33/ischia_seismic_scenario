# ischia_seismic_scenario
QGIS Plugin to create an intensity seismic scenario at a local scale of the island of Ischia

This plugin allows calculating seismic scenarios expressed in terms of macroseismic intensity 
according to deterministic or probabilistic models of attenuation.
The input parameters required to simulate an earthquake, are:
- epicentral location, expressed in degrees (xx.yyy);
- epicentral intensity (I<sub>0</sub>) or magnitude.
In the latter case, the magnitude (Md or MW) is converted into intensity by the relationships
obtained by Selva et al. (2021)*.

Selection of the attenuation models:
- deterministic: scenarios for epicentral intensity between 6 and 11 (MCS);
- probabilistic: scenarios for epicentral intensity between 8 and 11 (MCS).

Results are plotted on map with a grid with node distances of 0.5 km. For the probabilistic scenario, 
the mode of the distribution is taken as the expected intensity at that site.

This plugin is a product (supplementary material) related to the paper:
Azzaro R, D'Amico S, Rotondi R, Varini E (2023) The attenuation of macroseismic intensity in the volcanic 
island of Ischia (Gulf of Naples, Italy): comparison between deterministic and probabilistic models and 
application to seismic scenarios. Bull Earth Eng, submitted.

*see Table 2 in: Selva J, Azzaro R, Taroni M, Tramelli A, Alessio G, Castellano M, Ciuccarelli C, Cubellis E, 
Lo Bascio D, Porfido S, Ricciolino P, Rovida A (2021) The seismicity of Ischia Island, Italy: an integrated 
earthquake catalogue from 8th century BC to 2019 and its statistical properties. 
Frontiers, Earth Sci 9, 629736.
