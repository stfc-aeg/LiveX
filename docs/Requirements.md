Format:  
ID, Necessity, shorthand description  
Then a full description and optionally a *comment*.   
Necessity uses the 'MoSCoW' system: 'Must, Should, Could, and Would'.

Key:  
F = Functional, T = Thermal, C = Control, D = Display, L = Logging  
N = Non-functional

---
## Thermal Control Requirements

| FT1 | Must | Upper and lower heater must be individually controllable |
| --- | --- | --- |

The two heaters must have independent and separate control areas, including the on switch.

| FT2 | Must | Individually display heater PID loop terms |
| --- | --- | --- |

The proportional, integral, and derivative terms for each heater's PID control loop must be displayed and settable.

| FT3 | Must | Heater set points and displays |
| --- | --- | --- |

Each heater must have a settable desired temperature (set point) and current temperature displayed.

| FT4 | Must | Thermal gradient setting and displays |
| --- | --- | --- |

Thermal gradient must be settable, have its distance be settable, and the actual/theoretical values must be displayed.

| FT5 | Must | Auto set point control |
| --- | --- | --- |

Rate of heating or cooling must be controllable, and the image acquisition per degree can be set as well.

| FT6 | Should | Thermocouple 3 and 4 readings displayed |
| --- | --- | --- |

Readings from thermocouples 3 and 4 should be displayed in a separate section to the heater controls.

| FT7 | Must | 50Hz required data reading date |
| --- | --- | --- |

Thermocouples (and therefore PID loops and other dependencies) must be able to be read at a rate of 50Hz. 

---

## Other Control (Motor, Atmosphere, Pulse) Requirements

| FC1 | Should | Start/stop process button |
| --- | --- | --- |

There should be a control to stop and start the overall process on the web application.  
*Comment*: Is the current button ('Stop VI') needed or a LabVIEW thing? Is it required here?

| FC2 | Must | Motor controls |
| --- | --- | --- |

Motor power (on/off), direction (up/down), and speed (Volt) must be controllable in the application.  

| FC3 | Must | Motor LVDT displayed | 
| --- | --- | --- |

Motor LVDT must be displayed.

| FC4 | Must/Should | Atmosphere controls | 
| --- | --- | --- |

Pending more details, may be split into more requirements.  
Controls may be required for the following:  
\> Vacuum pumps  
\> Oxygen sensor  
\> Pressure sensor  
\> Valves switches

| FC5 | Must/Should | Pulse generator controls | 
| --- | --- | --- |

Pending more details, may be split into more requirements.  
*Comment*: pulse generator (TTi TG5011) was interfaced to LabVIEW through LAN/ethernet, and sine/square waves sent as state to the pulse generator as required for the experiment. Such a control, or similar, could possibly be implemented into this application.

---

## Display Requirements

| FD1 | Must | Digital pressure gauge display | 
| --- | --- | --- |

Digital Pressure Gauge (Pressure (Volts)) must be displayed.

| FD2 | Must | Temperature monitor graph display | 
| --- | --- | --- |

Temperature monitor graph must be displayed and update continuously.

| FD3 | Must | Performance monitor | 
| --- | --- | --- |

The application must have a performance monitor, which is a series of displayed values, PID gains and plant parameters 1 and 2.  
*Comment:* at present the 'displayed values' includes:  
Upper loop, Upper ON loop, T/C Loop Iteration, PID loop 1 and 2, Data log Loop, Event Loop, Difference 1 and 2, Temp gradient / launch loop, DO consumer loop, Camera trigger outer loop, AO and DO producer loop, and Auto Set Pt Consumer loop.

| FD4 | Should | Imaging camera feed | 
| --- | --- | --- |

Should display a live feed of the imaging camera / hexitec data near the thermocouple readout plot.  
*Comment*: It may be desirable to have a separate tab for control and monitoring.

---

## Logging Requirements

| FL1 | Must | Data logging tools | 
| --- | --- | --- |

Application must have data logging tools to store camera, hexitec, and temperature data.  
*Comment*: Consideration needed for what the data file / metedata structure should be.

| FL2 | Must | Trigger and log frequency controls | 
| --- | --- | --- |

Camera, hexitec, and log trigger controls must be operable from the web interface.  
Log frequency must also be settable from the interface.

| FL3 | Should | Generate file name for log files | 
| --- | --- | --- |

Application should be able to dictate or generate a file name for the log/data files.

| FL4 | Should | Metadata saved with experiment logs | 
| --- | --- | --- |

Experimental parameters (or 'metadata') should be saved with experiment logs/data.  
*Comment:* Which parameters precisely can be further defined at a later point, as with FL1.

| FL5 | Should | Include notes file with logs | 
| --- | --- | --- |

A notes file should be included with the logs. This could be a markdown (.md) or text (.txt) file for observations about an experiment.

---

## Non-functional Requirements

| N1 | Should | Persistent data displays | 
| --- | --- | --- |

Graph displays should persist between page refreshes.

| N2 | Must | Data integrity | 
| --- | --- | --- |

Data integrity: data must be preserved as it is transmitted between application layers.

| N3 | Must | Interface readability | 
| --- | --- | --- |

Interface must be easily readable and understandable.  
*Comment*: Tabs for separate functions (see FD4) may be beneficial for this.

| N4 | Must | Odin-control | 
| --- | --- | --- |

System must be run through odin-control.
