Format:  
ID, Necessity, shorthand description  
Then a full description and optionally a *comment*.   
Necessity uses the 'MoSCoW' system: 'Must, Should, Could, and Would'.

Key:  
F = Functional, T = Thermal, C = Control, D = Display, L = Logging  
N = Non-functional

---
## Thermal Control Requirements

| FT1 | Must | Upper and lower heater can be controlled individually |
| --- | --- | --- |

The two heaters have separate controls and can have relevant values shown and changed independently.

| FT2 | Must | Individually displayed heater PID loops and terms |
| --- | --- | --- |

The values of the PID loop for each heater must be displayed, and the magnitude of their terms controllable individually.

| FT3 | Must | Heater set points and displays |
| --- | --- | --- |

Each heater has a settable desired temperature (set point) and current temperature displayed.

| FT4 | Must | Thermal gradient setting and displays |
| --- | --- | --- |

Thermal gradient can be set, its distance can be set, and the actual/theoretical values displayed.

| FT5 | Must | Auto set point control |
| --- | --- | --- |

Rate of heating or cooling is controllable, and the image acquisition per degree can be set as well.

| FT6 | Must | Thermocouple 3 and 4 readings displayed |
| --- | --- | --- |

These should be displayed in a separate section to the two heaters' sections.

| FT7 | Must | 50Hz required data reading date |
| --- | --- | --- |

Thermocouples (and therefore PID loops and other dependencies) can be read at a rate of 50Hz. 

---

## Other Control (Motor, Atmosphere, Pulse) Requirements

| FC1 | Should | Start/stop process button |
| --- | --- | --- |

A control to stop and start the overall process is on the web application.
*Comment*: Is the current button ('Stop VI') needed or a LabVIEW thing? Is it required here?

| FC2 | Must | Motor controls |
| --- | --- | --- |

Motor power, direction and speed can be controlled via the application.

| FC3 | Must | Motor LVDT displayed. | 
| --- | --- | --- |

Motor LVDT is displayed.

| FC4 | Must/Should | Atmosphere controls | 
| --- | --- | --- |

Pending more details, may be split into more requirements.

| FC5 | Must/Should | Pulse generator controls | 
| --- | --- | --- |

Pending more details, may be split into more requirements.

---

## Display Requirements

| FD1 | Must | Digital pressure gauge display | 
| --- | --- | --- |

Digital Pressure Gauge is displayed.

| FD2 | Must | Temperature monitor graph display | 
| --- | --- | --- |

Temperature monitor graph should be displayed and update continuously.

| FD3 | Must | Performance monitor | 
| --- | --- | --- |

A series of displayed values. PID gains and plant parameters 1 and 2.  
*Comment:* at present this also includes:  
Upper loop, Upper ON loop, T/C Loop Iteration, PID loop 1 and 2, Data log Loop, Event Loop, Difference 1 and 2, Temp gradient / launch loop, DO consumer loop, Camera trigger outer loop, AO and DO producer loop, and Auto Set Pt Consumer loop.

| FD4 | Should | Imaging camera feed | 
| --- | --- | --- |

Life feed of imaging camera / hexitec data near thermocouple readout plot.  
*Comment*: It may be desirable to have a separate tab for control and monitoring.

---

## Logging Requirements

| FL1 | Must | Data logging tools | 
| --- | --- | --- |

Application has data logging tools to store camera, hexitec, and temperature data.  
*Comment*: Consideration needed for what the data file / metedata structure should be.

| FL2 | Must | Trigger and log frequency controls | 
| --- | --- | --- |

Log frequency and camera/hexitec trigger controls can be operated from the web interface.

| FL3 | Should | Generate file name for log files | 
| --- | --- | --- |

Application can dictate or generate a file name for the log/data files.

| FL4 | Should | Metadata saved with experiment logs | 
| --- | --- | --- |

Experimental parameters (or 'metadata') can be saved with experiment logs/data.  
*Comment:* Which parameters precisely can be further defined at a later point, as with FL1.

| FL5 | Should | Include notes file with logs | 
| --- | --- | --- |

A notes file is included with the logs. This could be a markdown (.md) or text (.txt) file for observations about an experiment.

---

## Non-functional Requirements

| N1 | Should | Persistent data displays | 
| --- | --- | --- |

Graph displays should persist between page refreshes.

| N2 | Must | Data integrity | 
| --- | --- | --- |

Data integrity: data is preserved as it is transmitted between application layers.

| N3 | Must | Interface readability | 
| --- | --- | --- |

Interface should be easily readable and understandable. Tabs for separate functions (see FD4) may be beneficial for this.

| N4 | Must | Odin-control | 
| --- | --- | --- |

System is run through odin-control.
