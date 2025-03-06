provides = ['configure_pids', 'furnace_acquisition_full']
requires = ['example_sequences']

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

def furnace_acquisition_full(setpoint=300, stability_threshold=0.25, cooling_rate=1.5, final_setpoint=40, do_gradient=False, gradient_temp_per_mm=2, distance=5, grad_high_towards_a=True):
    """Sequence to run a full acquisition"""

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
