class modAddr():
    """Source class for accessing modbus addresses in one location.
    Format is as follows:
    `control_purpose_<optional specifier>_registerType`
    Names match that of config.h, without the mod_prefix
    """

    def __init__(self):
        pass

    # Coils start at 00001-09999
    pid_enable_a_coil    = 1
    pid_enable_b_coil    = 2
    gradient_enable_coil = 3
    autosp_enable_coil   = 4
    autosp_heating_coil  = 5
    motor_enable_coil    = 6
    motor_direction_coil = 7
    gradient_high_coil   = 8
    acquisition_coil     = 9

    # Input registers (read-only, from device) start at 30001-39999
    counter_inp      = 30001
    pid_output_a_inp = 30003
    pid_output_b_inp = 30005

    thermocouple_a_inp = 30007
    thermocouple_b_inp = 30009
    thermocouple_c_inp = 30011
    thermocouple_d_inp = 30013

    gradient_actual_inp     = 30015
    gradient_theory_inp     = 30017
    gradient_setpoint_a_inp = 30019
    gradient_setpoint_b_inp = 30021
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

    gradient_wanted_hold   = 40017
    gradient_distance_hold = 40019

    autosp_rate_hold       = 40021
    autosp_imgdegree_hold  = 40023

    motor_speed_hold = 40025

    # Addresses for controls

    addresses_pid_a = {
        'enable': pid_enable_a_coil,
        'setpoint': pid_setpoint_a_hold,
        'kp': pid_kp_a_hold,
        'ki': pid_ki_a_hold,
        'kd': pid_kd_a_hold,
        'output': pid_output_a_inp,
        'gradient_setpoint': gradient_setpoint_a_inp,
        'thermocouple': thermocouple_a_inp
    }

    addresses_pid_b = {
        'enable': pid_enable_b_coil,
        'setpoint': pid_setpoint_b_hold,
        'kp': pid_kp_b_hold,
        'ki': pid_ki_b_hold,
        'kd': pid_kd_b_hold,
        'output': pid_output_b_inp,
        'gradient_setpoint': gradient_setpoint_b_inp,
        'thermocouple': thermocouple_b_inp
    }

    gradient_addresses = {
        'enable': gradient_enable_coil,
        'wanted': gradient_wanted_hold,
        'distance': gradient_distance_hold,
        'actual': gradient_actual_inp,
        'theoretical': gradient_theory_inp,
        'high': gradient_high_coil,  # Which heater is the 'high' end of the gradient
        'high_options': ["A", "B"]
    }

    aspc_addresses = {
        'enable': autosp_enable_coil,
        'heating': autosp_heating_coil,
        'heating_options': ["Cooling", "Heating"],
        'rate': autosp_rate_hold,
        'midpt': autosp_midpt_inp,
        'imgdegree': autosp_imgdegree_hold
    }

    motor_addresses = {
        'enable': motor_enable_coil,
        'direction': motor_direction_coil,
        'speed': motor_speed_hold,
        'lvdt': motor_lvdt_inp
    }

    # Trigger adapter addresses

    trig_furnace_intvl_hold   = 40001
    trig_widefov_intvl_hold   = 40003
    trig_narrowfov_intvl_hold = 40005

    trig_furnace_target_hold   = 40007
    trig_widefov_target_hold   = 40009
    trig_narrowfov_target_hold = 40011

    trig_enable_coil = 0
    trig_disable_coil = 1
    trig_furnace_enable_coil = 2
    trig_widefov_enable_coil = 3
    trig_narrowfov_enable_coil = 4

    trigger_furnace = {
        'enable_coil':   trig_furnace_enable_coil,
        'freq_hold': trig_furnace_intvl_hold,
        'target_hold':   trig_furnace_target_hold
    }

    trigger_widefov = {
        'enable_coil':   trig_widefov_enable_coil,
        'freq_hold': trig_widefov_intvl_hold,
        'target_hold':   trig_widefov_target_hold
    }

    trigger_narrowfov = {
        'enable_coil':   trig_narrowfov_enable_coil,
        'freq_hold': trig_narrowfov_intvl_hold,
        'target_hold':   trig_narrowfov_target_hold
    }