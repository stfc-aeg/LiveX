Format:  
ID, Necessity: description and optional *comment*.   
Necessity uses the 'MoSCoW' system: 'Must, Should, Could, and Would'.

Key:  
F = Functional, T = Thermal, C = Control, D = Display, L = Logging  
N = Non-functional

---

**FT1, Must**:  
Upper and lower heater can be controlled individually.

**FT2, Must**:  
Each heater has a PID loop which is displayed individually, including control of the PID term magnitudes.

**FT3, Must**:  
Each heater has a desired temperature set (set point) and current temperature displayed.

**FT4, Must**:  
Thermal gradient can be set, its distance can be set, and the actual/theoretical values displayed.

**FT5, Must**:  
Auto set point control: The rate of heating or cooling is controllable, and the image acquisition per degree can be set as well.

**FT6, Must**:  
Thermocouples 3 and 4 have their readings displayed.  
*Comment*: unclear what 'Suggest Frame Rate' is suggesting the frame rate of or how

**FT7, Must**:  
Thermocouples (and therefore PID loops and other dependencies) can be read at a rate of 50Hz.  

**FC1, Should**:  
Control to stop and start overall process must be on the web application.  
*Comment*: Is the current button ('Stop VI') needed or a LabVIEW thing? Is it needed here?

**FC2, Must**:  
Motor power, direction, and speed can be controlled via the application.

**FC3, Must**:  
Motor LVDT is displayed.

**FC4, Must/Should**:  
Atmosphere controls (to be investigated)

**FC5, Must/Should**:  
Pulse generator controls (to be investigated)

**FD1, Must**:  
Digital Pressure Gauge is displayed.

**FD2, Must**:  
Temperature monitor graph should be displayed and update continuously.

**FD3, Must**:  
Performance monitor. PID gains and plant parameters 1 and 2, and loop details.  
*Comment*: Reference the previous LabVIEW layout as per email on 27/01/23 from Andrew. Are all of those displays desirable?

**FD4, Should**:  
Live feed of imaging camera / hexitec data near thermocouple readout plot.  
*Comment:* A separate tab for control and monitoring may be desirable.

**FL1, Must**:  
Application has data logging tools to store camera, hexitec, and temperature data.  
*Comment:* Consideration needed for what the data file / metadata structure should be.

**FL2, Must**:  
Log frequency and camera/hexitec trigger controls can be operated from the web interface.

**FL3, Should**:  
Application can dictate or generate a file name for the log/data files.

**FL4, Should**:  
Experimental parameters (or 'metadata') can be saved with experiment logs/data.  
*Comment:* Which parameters precisely can be further defined at a later point, as with FL1.

**FL5, Should**:  
A notes file is included with the logs. This could be a markdown (.md) or text (.txt) file for observations about an experiment.

---

**N1, Should**:  
Graph displays should persist between page refreshes.

**N2, Must**:  
Data integrity: data is preserved as it is transmitted between application layers.

**N3, Must**:  
Interface should be easily readable and understandable. Tabs for separate functions (see FD4) may be beneficial for this.

**N4, Must**:  
System is run through odin-control.
