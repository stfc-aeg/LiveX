provides = ['configure_pids', 'stabilise_at_temperature_a', 'furnace_acquisition_full']

import time

def configure_pids(setpoint_a=200, kp_a=0.3, ki_a=0.02, kd_a=0 , setpoint_b=200, kp_b=0.3, ki_b=0.02, kd_b=0):
    furnace = get_context('furnace')

    furnace.pid_a.set_setpoint(setpoint_a)
    furnace.pid_a.set_proportional(kp_a)
    furnace.pid_a.set_integral(ki_a)
    furnace.pid_a.set_derivative(kd_a)

    furnace.pid_b.set_setpoint(setpoint_b)
    furnace.pid_b.set_proportional(kp_b)
    furnace.pid_b.set_integral(ki_b)
    furnace.pid_b.set_derivative(kd_b)
    print(f"Setpoint now equal to {furnace.pid_a.setpoint}")

def stabilise_at_temperature_a(setpoint=300, stability_threshold=0.25, do_gradient=False, gradient_temp_per_mm=2, distance=5, grad_high_towards_a=True):
    """Set PID A to reach and maintain a target temperature."""
    furnace = get_context('furnace')
    trigger = get_context('trigger')

    furnace.pid_a.set_setpoint(setpoint)
    interval = furnace.bg_read_task_interval

    freq = trigger.triggers['furnace'].frequency
    duration = 10*freq

    if do_gradient:
        furnace.gradient.set_distance(distance)
        furnace.gradient.set_wanted(gradient_temp_per_mm)
        furnace.gradient.set_high(grad_high_towards_a)
        furnace.gradient.set_enable(do_gradient)

    furnace.pid_a.set_enable(True)

    def mean(errors):
        if len(errors) == 0:
            return -1
        return (sum(abs(err) for err in errors) / len(errors))
    # Need to determine that temperature is stable
    # Seeing that magnitude error of last 50 readings is below a certain amount should suffice
    # When testing, this is 10 seconds. Should be based off of frequency
    errors = []
    # Checking
    while (len(errors)<duration) or (mean(errors) >= stability_threshold):
        errors.append((furnace.pid_a.temperature - furnace.pid_a.setpoint))
        if len(errors) > duration:
            errors.pop(0)
        time.sleep(interval)

    print(f"temperature stabilised at {furnace.pid_a.temperature} for setpoint {furnace.pid_a.setpoint}")

def furnace_acquisition_full(setpoint=300, stability_threshold=0.25, cooling_rate=1.5, final_setpoint=40, do_gradient=False, gradient_temp_per_mm=2, distance=5, grad_high_towards_a=True):

    furnace = get_context('furnace')
    interval = furnace.bg_read_task_interval

    stabilise_at_temperature_a(setpoint, stability_threshold, do_gradient, gradient_temp_per_mm, distance, grad_high_towards_a)

    # Once stabilised, start acquisition
    # furnace.solo_acquisition(True)

    # Then start cooling
    furnace.aspc.set_rate(cooling_rate)
    furnace.aspc.set_enable(True)

    while furnace.pid_a.setpoint > final_setpoint:
        time.sleep(interval)

    furnace.aspc.set_enable(False)
    print("ASPC at target; disabling.")

    while furnace.pid_a.temperature > final_setpoint:
        time.sleep(interval)

    furnace.pid_a.set_enable(False)
    # furnace.solo_acquisition(False)
    print(f"Furnace acquisition finished, disabling PID and acquisition.")
