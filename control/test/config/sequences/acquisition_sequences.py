provides=['d25_test_acquisition']

import time

def d25_test_acquisition(
    heat_rate=2.5, target_temp=600, heat_hold_time=60,
    gradient_distance=2.5, gradient_k_mm=20, use_thermal_gradient=True,
    first_cool_rate=2.5, cool_target=500, cool_hold_time=30,
    second_cool_rate=1.5, cool_target_2=300
):
    """Test sequence to run a full acquisition including heating, holding, cooling, holding, and cooling again.
    It does not modify the frequencies of the triggers in any way, so ensure triggers/cameras are in the proper state before starting it.
    """
    furnace = get_context('furnace')
    livex = get_context('livex')

    heaters = [furnace.pid_a, furnace.pid_b]
    gradient = furnace.gradient
    aspc = furnace.aspc
    interval = furnace.bg_read_task_interval

    # Heat up furnace and maintain that temperature for a time
    gradient.set_enable(False)
    for heater in heaters:
        heater.set_setpoint(30) # Start both heaters at room temperature
        heater.set_enable(True)

    if use_thermal_gradient:
        print("Thermal gradient enabled")
        gradient.set_distance(gradient_distance)
        gradient.set_wanted(gradient_k_mm)
        gradient.set_high(False)  # In this script, assume A is always higher
        gradient.set_enable(True)

    aspc.set_rate(heat_rate)
    aspc.set_heating(True)
    aspc.set_enable(True)

    # Wait until temperature at least reaches target temperature
    while furnace.pid_a.setpoint < target_temp:
        time.sleep(interval)  # Sleep for period of furnace background task to minimise 'lag' on updates
    
    aspc.set_enable(False)  # Turn heating off when reached target
    print("Reached target temperature, auto set point control disabled.")

    for heater in heaters:
        heater.set_setpoint(target_temp)  # Now at temperature, make sure setpoints are on the dot

    print(f"Holding for {heat_hold_time} seconds.")
    time.sleep(heat_hold_time)

    # After waiting, start acquisition and wait another couple of seconds before starting to cool
    print("Starting acquisition, then continuing cooling.")
    livex.start_acquisition(['furnace', 'widefov', 'narrowfov'])
    time.sleep(3)

    aspc.set_heating(False)
    aspc.set_rate(first_cool_rate)
    aspc.set_enable(True)

    while furnace.pid_a.setpoint > cool_target:
        time.sleep(interval)

    print(f"First cooling target reached, holding for {cool_hold_time} seconds.")
    aspc.set_enable(False)
    time.sleep(cool_hold_time)
    print("Beginning second cool.")
    aspc.set_rate(second_cool_rate)
    aspc.set_enable(True)

    while furnace.pid_a.setpoint > cool_target_2:
        time.sleep(interval)
    print("Second cooling target reached, ending acquisition.")
    aspc.set_enable(False)
    livex.stop_acquisition()




