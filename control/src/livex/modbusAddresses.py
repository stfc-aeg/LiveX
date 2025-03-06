class modAddr():
    """Source class for accessing modbus addresses in one location.
    Format is as follows:
    `control_purpose_<optional specifier>_registerType`
    Names match that of config.h, without the mod_prefix
    """

    def __init__(self):
        pass

    # Coils start at 00001-09999
    pid_enable_a_coil     = 1
    pid_enable_b_coil     = 2
    gradient_enable_coil  = 3
    autosp_enable_coil    = 4
    autosp_heating_coil   = 5
    motor_enable_coil     = 6
    motor_direction_coil  = 7
    gradient_high_coil    = 8
    acquisition_coil      = 9
    gradient_update_coil  = 10
    freq_aspc_update_coil = 11
    setpoint_update_coil  = 12

    # Input registers (read-only, from device) start at 30001-39999
    counter_inp      = 30001
    pid_output_a_inp = 30003
    pid_output_b_inp = 30005
    pid_outputsum_a_inp = 30007
    pid_outputsum_b_inp = 30009

    thermocouple_a_inp = 30011
    thermocouple_b_inp = 30013
    thermocouple_c_inp = 30015
    thermocouple_d_inp = 30017

    gradient_actual_inp     = 30019
    gradient_theory_inp     = 30021
    autosp_midpt_inp        = 30023

    motor_lvdt_inp = 30027

    # Holding registers (read/write) start at 40001-49999
    pid_setpoint_a_hold = 40001
    pid_kp_a_hold       = 40003
    pid_ki_a_hold       = 40005
    pid_kd_a_hold       = 40007

    pid_setpoint_b_hold = 40009
    pid_kp_b_hold       = 40011
    pid_ki_b_hold       = 40013
    pid_kd_b_hold       = 40015

    furnace_freq_hold   = 40017

    gradient_wanted_hold   = 40019
    gradient_distance_hold = 40021

    autosp_rate_hold       = 40023
    autosp_imgdegree_hold  = 40025

    motor_speed_hold = 40027

    # Addresses for controls

    addresses_pid_a = {
        'enable': pid_enable_a_coil,
        'setpoint': pid_setpoint_a_hold,
        'kp': pid_kp_a_hold,
        'ki': pid_ki_a_hold,
        'kd': pid_kd_a_hold,
        'output': pid_output_a_inp,
        'outputsum': pid_outputsum_a_inp,
        'thermocouple': thermocouple_a_inp,
        'setpoint_update': setpoint_update_coil
    }

    addresses_pid_b = {
        'enable': pid_enable_b_coil,
        'setpoint': pid_setpoint_b_hold,
        'kp': pid_kp_b_hold,
        'ki': pid_ki_b_hold,
        'kd': pid_kd_b_hold,
        'output': pid_output_b_inp,
        'outputsum': pid_outputsum_b_inp,
        'thermocouple': thermocouple_b_inp,
        'setpoint_update': setpoint_update_coil
    }

    gradient_addresses = {
        'enable': gradient_enable_coil,
        'wanted': gradient_wanted_hold,
        'distance': gradient_distance_hold,
        'actual': gradient_actual_inp,
        'theoretical': gradient_theory_inp,
        'high': gradient_high_coil,  # Which heater is the 'high' end of the gradient
        'high_options': ["A", "B"],
        'update': gradient_update_coil
    }

    aspc_addresses = {
        'enable': autosp_enable_coil,
        'heating': autosp_heating_coil,
        'heating_options': ["Cooling", "Heating"],
        'rate': autosp_rate_hold,
        'midpt': autosp_midpt_inp,
        'imgdegree': autosp_imgdegree_hold,
        'update': freq_aspc_update_coil
    }

    motor_addresses = {
        'enable': motor_enable_coil,
        'direction': motor_direction_coil,
        'speed': motor_speed_hold,
        'lvdt': motor_lvdt_inp
    }

    # Trigger adapter addresses

    trig_0_intvl_hold = 40001
    trig_1_intvl_hold = 40003
    trig_2_intvl_hold = 40005
    trig_3_intvl_hold = 40007

    trig_0_target_hold = 40009
    trig_1_target_hold = 40011
    trig_2_target_hold = 40013
    trig_3_target_hold = 40015

    # Write True to enable/disable all triggers
    trig_enable_coil = 0
    trig_disable_coil = 1
    # Write True to enable trigger
    trig_0_enable_coil = 2
    trig_1_enable_coil = 3
    trig_2_enable_coil = 4
    trig_3_enable_coil = 5
    # Write True to disable trigger
    trig_0_disable_coil = 6
    trig_1_disable_coil = 7
    trig_2_disable_coil = 8
    trig_3_disable_coil = 9
    # Read to see if related timer is running
    trig_0_running_coil = 10
    trig_1_running_coil = 11
    trig_2_running_coil = 12
    trig_3_running_coil = 13

    trigger_0 = {
        'enable_coil': trig_0_enable_coil,
        'disable_coil': trig_0_disable_coil,
        'running_coil': trig_0_running_coil,
        'freq_hold': trig_0_intvl_hold,
        'target_hold': trig_0_target_hold,
    }

    trigger_1 = {
        'enable_coil': trig_1_enable_coil,
        'disable_coil': trig_1_disable_coil,
        'running_coil': trig_1_running_coil,
        'freq_hold': trig_1_intvl_hold,
        'target_hold': trig_1_target_hold
    }

    trigger_2 = {
        'enable_coil': trig_2_enable_coil,
        'disable_coil': trig_2_disable_coil,
        'running_coil': trig_2_running_coil,
        'freq_hold': trig_2_intvl_hold,
        'target_hold': trig_2_target_hold
    }

    trigger_3 = {
        'enable_coil': trig_3_enable_coil,
        'disable_coil': trig_3_disable_coil,
        'running_coil': trig_3_running_coil,
        'freq_hold': trig_3_intvl_hold,
        'target_hold': trig_3_target_hold
    }