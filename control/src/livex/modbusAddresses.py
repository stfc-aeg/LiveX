class modAddr():
    """Source class for accessing modbus addresses in one location.
    Format is as follows:
    `control_purpose_<optional specifier>_registerType`
    Names match that of modbusAddresses.h, without the mod_prefix
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
