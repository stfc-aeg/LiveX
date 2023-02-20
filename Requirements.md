**ID**: Shorthand reference for requirement  
**Description**: Actual requirement  
**Necessity**: MoSCoW (Must, Should, Could, and Would)  
**Comments**: impressions and thoughts on current requirement. Column likely to be removed later

| ID  | Description | Necessity | Comments |
| --- | ----------- | --------- | -------- |
| FT1 | The upper and lower heater can be controlled separately: set desired temperature.| Must |          |
| FT2  | Each heater’s PID loop is displayed and controllable individually.| Must | Assuming the arrows on the PID controller adjust the magnitude of the three terms |
| FT3 | Each heater can have a desired temperature set (set point) and current temperature displayed.|Must|| 
| FT4|Thermal gradient can be set, its distance can be set, and the actual/theoretical values displayed.|Must|      | 
| FT5 |Auto set point control.|Must|Unclear exactly how this automatically sets the set point| 
| FT6 |Thermocouples 3 and 4 have readings displayed.|Must|      | 
| FC1 |Control to stop and start overall process must be on the web application.|Must|i.e.: big red stop button| 
| FC2 |Motor power, direction and speed can be controlled via the application.|Must|      | 
| FC3 |Motor LVDT is displayed.|Must|LVDT referring to displacement| 
| FC4 |Atmosphere Controls.|Must/Should|      | 
| FC5 |Pulse generator controls.|Must/Should|This and FC4 may require more details (specific controls/displays) and could be split into more requirements| 
| FD1 |Digital Pressure Gauge is displayed.|Must|Pressure=volts?| 
| FD2 |Temperature Monitor graph should be displayed and update continuously.|Must|Rolling graphs exist in other odin applications as a reference point.| 
| FD3 |Performance monitor. PID gains and plant parameters 1 and 2, loop details.|Must|See Labview layout| 
| FD4 |Live feed of imaging camera / hexitec data near thermocouple readout plot.|Should|A separate tab for monitoring may be desirable| 
| FL1 |Application has data logging tools to store camera, hexitec, and temperature data.|Must|      | 
| FL2 |Log frequency and camera/hexitec trigger controls can be operated from the web interface.|Must|      | 
| FL3 |Application can dictate or generate a file name for the log/data files.|Should|STEvIE did similar. Some sequencer scripts specify folder/filename prefix too.| 
| FL4 |Experimental parameters (or 'metadata') can be saved with experiment logs/data.|Should|Worth clarifying which parameters this includes but should not be complex.|
| FL5 |A notes file is included with the logs. This could be a markdown (.md) or text (.txt) file for observations about an experiment.|Should|Desirable for tidiness.|
| | | | |
| N1 |Thermocouples (and therefore PID loops and other dependencies) can be read at a rate of at least 50Hz|Must|Proven possible. What else depends on the thermocouple readings? How fast does overall update speed need to be? New requirement?|
| N2 |Graph displays should persist between page refreshes.|Should|Seeing history may be important.|
| N3 |Data integrity: data is preserved as it is transmitted between application layers.|Must|Allow for float rounding errors if present.|
| N4 |Interface should be easily readable and understandable.|Must|Tab use likely to avoid overcrowding.|
| N5 |System is run through odin-control.|Must|A given but perhaps still worth documenting?|