class modAddr():
    """Source class for accessing modbus addresses in one location.
    Format is as follows:
    `control_purpose_<optional specifier>_registerType`
    Names match that of config.h, without the mod_prefix
    """

    def __init__(self):
        pass

    # What order are the thermocouples in. See mcp_type[] in main.cpp in firmware/livex
    # Addresses are fixed order of (0x60, 0x67, 0x66, 0x65, 0x64, 0x63, 0x62)
    # So these values should correlate with what is connected to those addresses

    # mcp types
    mcp_types = ["K", "J", "T", "N", "S", "E", "B", "R"]
    # Numbered 0-7 as with Adafruit library enumeration
    mcp_type_from_val = dict(enumerate(mcp_types))
    # Get the enum value from the type
    mcp_val_from_type = {v:k for k,v in mcp_type_from_val.items()}


    # Coils start at 00001-09999
    pid_upper_enable_coil     = 1
    pid_lower_enable_coil     = 2
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
    tc_type_update_coil   = 13
    output_override_upper_coil  = 14
    output_override_lower_coil  = 15

    # Input registers (read-only, from device) start at 30001-39999
    counter_inp      = 30001
    pid_upper_output_inp = 30003
    pid_lower_output_inp = 30005
    pid_upper_outputsum_inp = 30007
    pid_lower_outputsum_inp = 30009

    thermocouple_a_inp = 30011
    thermocouple_b_inp = 30013
    thermocouple_c_inp = 30015
    thermocouple_d_inp = 30017
    thermocouple_e_inp = 30019
    thermocouple_f_inp = 30021
    number_mcp_inp     = 30023

    gradient_actual_inp     = 30025
    gradient_theory_inp     = 30027
    autosp_midpt_inp        = 30029

    # Holding registers (read/write) start at 40001-49999
    pid_setpoint_upper_hold = 40001
    pid_kp_upper_hold       = 40003
    pid_ki_upper_hold       = 40005
    pid_kd_upper_hold       = 40007

    pid_lower_setpoint_hold = 40009
    pid_lower_kp_hold       = 40011
    pid_lower_ki_hold       = 40013
    pid_lower_kd_hold       = 40015

    furnace_freq_hold   = 40017

    gradient_wanted_hold   = 40019
    gradient_distance_hold = 40021

    autosp_rate_hold       = 40023
    autosp_imgdegree_hold  = 40025

    # Named differently to config.h, which is heatertc_a/b and extratc_a/b/c/d
    thermocouple_a_idx_hold    = 40027
    thermocouple_b_idx_hold    = 40029
    thermocouple_c_idx_hold     = 40031
    thermocouple_d_idx_hold     = 40033
    thermocouple_e_idx_hold     = 40035
    thermocouple_f_idx_hold     = 40037

    tcidx_0_type_hold           = 40039
    tcidx_1_type_hold           = 40041
    tcidx_2_type_hold           = 40043
    tcidx_3_type_hold           = 40045
    tcidx_4_type_hold           = 40049
    tcidx_5_type_hold           = 40049

    setpoint_limit_hold         = 40051
    setpoint_step_hold          = 40053

    output_override_upper_hold  = 40055
    output_override_lower_hold  = 40057

    power_output_scale          = 40059

    # Addresses for controls
    addresses_pid_upper = {
        'enable': pid_upper_enable_coil,
        'setpoint': pid_setpoint_upper_hold,
        'kp': pid_kp_upper_hold,
        'ki': pid_ki_upper_hold,
        'kd': pid_kd_upper_hold,
        'output': pid_upper_output_inp,
        'outputsum': pid_upper_outputsum_inp,
        'thermocouple': thermocouple_a_inp,
        'setpoint_update': setpoint_update_coil,
        'output_override': output_override_upper_hold,
        'output_override_enable': output_override_upper_coil,
        'max_setpoint': setpoint_limit_hold,
        'max_setpoint_step': setpoint_step_hold
    }

    addresses_pid_lower = {
        'enable': pid_lower_enable_coil,
        'setpoint': pid_lower_setpoint_hold,
        'kp': pid_lower_kp_hold,
        'ki': pid_lower_ki_hold,
        'kd': pid_lower_kd_hold,
        'output': pid_lower_output_inp,
        'outputsum': pid_lower_outputsum_inp,
        'thermocouple': thermocouple_b_inp,
        'setpoint_update': setpoint_update_coil,
        'output_override': output_override_lower_hold,
        'output_override_enable': output_override_lower_coil,
        'max_setpoint': setpoint_limit_hold,
        'max_setpoint_step': setpoint_step_hold
    }

    gradient_addresses = {
        'enable': gradient_enable_coil,
        'wanted': gradient_wanted_hold,
        'distance': gradient_distance_hold,
        'actual': gradient_actual_inp,
        'theoretical': gradient_theory_inp,
        'high': gradient_high_coil,  # Which heater is the 'high' end of the gradient
        'update': gradient_update_coil
    }

    aspc_addresses = {
        'enable': autosp_enable_coil,
        'heating': autosp_heating_coil,
        'rate': autosp_rate_hold,
        'midpt': autosp_midpt_inp,
        'imgdegree': autosp_imgdegree_hold,
        'update': freq_aspc_update_coil
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