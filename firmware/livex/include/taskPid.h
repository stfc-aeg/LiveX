#ifndef TASKPID_H
#define TASKPID_H

#include <resources.h>

void Core0PIDTask(void * pvParameters);
void thermalGradient();
void autoSetPointControl();
void runPID(PIDEnum pid);

#endif
