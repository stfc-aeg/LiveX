import type { ParamNode } from 'odin-react';

export interface ThermocoupleType extends ParamNode {
    connection: string;
    label: string;
    value: number;
}

export interface FurnaceTCPReadingType extends ParamNode {
    counter: number;
    temperature_upper: number;
    output_upper: number;
    kp_upper: number;
    ki_upper: number;
    kd_upper: number;
    lastInput_upper: number;
    outputSum_upper: number;
    setpoint_upper: number;
    temperature_lower: number;
    output_lower: number;
    kp_lower: number;
    ki_lower: number;
    kd_lower: number;
    lastInput_lower: number;
    outputSum_lower: number;
    setpoint_lower: number;
}

export interface FurnaceEndpointTypes extends ParamNode {
    autosp: {
        enable: boolean;
        heating: number;
        midpt_temp: number;
        rate: number;
    };
    background_task: {
        enable: boolean;
        interval: number;
        thread_count: number;
    };
    filewriter: {
        filename: string;
        filepath: string;
    };
    gradient: {
        actual: number;
        distance: number;
        enable: boolean;
        high_heater: number;
        theoretical: number;
        wanted: number;
    };
    max_setpoint: number;
    max_setpoint_increase: number;
    pid_lower: {
        derivative: number;
        enable: boolean;
        integral: number;
        output: number;
        output_scalar: number;
        outputsum: number;
        override: {
            enable: boolean;
            percent_out: number;
        };
        proportional: number;
        setpoint: number;
        temperature: number;
    };
    pid_upper: {
        derivative: number;
        enable: boolean;
        integral: number;
        output: number;
        output_scalar: number;
        outputsum: number;
        override: {
            enable: boolean;
            percent_out: number;
        };
        proportional: number;
        setpoint: number;
        temperature: number;
    };
    status: {
        allow_pid_override: boolean;
        allow_solo_acquisition: boolean;
        connected: boolean;
        full_stop: any;
        reconnect: any;
    };
    tcp: {
        acquire: boolean;
        tcp_reading: FurnaceTCPReadingType;
    };
    thermocouples: Record<string, ThermocoupleType>;
}

export interface TriggerEndpointTypes extends ParamNode {
    all_timers_enable: boolean;
    background: {
        enable: boolean;
        interval: number;
    };
    modbus: {
        connected: boolean;
        ip: string;
        reconnect: any;
    };
    triggers: {
        furnace: {
            enable: boolean;
            frequency: number;
            running: boolean;
            target: number;
        };
        narrowfov: {
            enable: boolean;
            frequency: number;
            running: boolean;
            target: number;
        };
        widefov: {
            enable: boolean;
            frequency: number;
            running: boolean;
            target: number;
        };
    };
}

export interface LiveXEndpointTypes extends ParamNode {
    acquisition: {
        acquiring: boolean;
        frame_target: number;
        freerun: boolean;
        frequencies: {
            furnace: number;
            narrowfov: number;
            widefov: number;
        };
        link_triggers: {
            current: string[];
            link_cameras: string[] | null;
            unlink_cameras: string[] | null;
        };
        reference_trigger: string;
        start: any;
        stop: any;
    };
    cameras: Record<string, CameraType>;
}

export interface MetadataField extends ParamNode {
    choices: any[] | null;
    default: any;
    key: string;
    label: string;
    multi_choice: boolean;
    multi_line: boolean;
    persist: boolean;
    type: string;
    user_input: boolean;
    value: any;
}

export interface MetadataEndpointTypes extends ParamNode {
    config_error: string;
    config_loaded: boolean;
    fields: Record<string, MetadataField>;
    hdf: {
        file: string;
        group: string;
        path: string;
        write: boolean;
    };
    markdown: {
        file: string;
        group: string;
        path: string;
        write: boolean;
    };
    metadata_config: string;
    metadata_store: string;
    yaml: {
        file: string;
        group: string;
        write: boolean;
    };
}

export interface LiveDataDetailsTypes extends ParamNode {
    cam_name: string;
    endpoint: string;
    image: {
        autoclip: boolean;
        autoclip_percent: number;
        clip_range_percent: [number, number];
        clip_range_value: [number, number];
        colour: string;
        dimensions: [number, number];
        resolution: number;
        size_x: number;
        size_y: number;
        zoom: [number, number, number, number];
    };
}

export interface LiveDataEndpointTypes extends ParamNode {
    [camera_id: string]: LiveDataDetailsTypes;
}


export interface SequenceParameter extends ParamNode {
    default: any;
    type: string;
    value: any;
}

export type Sequence = Record<string, SequenceParameter>;
export type SequenceModule = Record<string, Sequence>;

export interface SequencerEndpointTypes extends ParamNode {
    abort: null;
    detect_module_modifications: boolean;
    execute: string;
    execution_progress: {
        current: number;
        total: number;
    };
    is_aborting: boolean;
    is_executing: boolean;
    last_message_timestamp: string;
    log_messages: string[];
    module_modifications_detected: boolean;
    process_tasks: any[];
    reload: {
        execute: boolean;
        status: string;
        success: boolean;
    };
    sequence_modules: SequenceModule;
}

export type KDCController = {
    connected: boolean;
    decrease_label: string;
    increase_label: string;
    type: string;
    motor: {
        jog: {
            accel: number;
            max_vel: number;
            min_vel: number;
            mode: number;
            step: null;
            step_size: number;
            stop_mode: number;
        };
        limits: {
            lower_limit: number;
            upper_limit: number;
        };
        position: {
            current_pos: number;
            home: null;
            set_target_pos: number;
            stop: null
        };
    };
};

export interface KinesisEndpointTypes extends ParamNode {
    bg_task_interval: number;
    controllers: Record<string, KDCController>;
};

export interface CameraType extends ParamNode {
    background_task: {
        enable: boolean;
        interval: number;
    };
    camera_name: string;
    command: any;
    config: {
        camera_number: number;
        exposure_time: number;
        frame_rate: number;
        image_timeout: number;
        num_frames: number;
        timestamp_mode: number;
        trigger_active: number;
        trigger_connector: number;
        trigger_mode: number;
        trigger_polarity: number;
        trigger_source: number;
    };
    connection: {
        connected: boolean;
        reconnect: any;
    };
    endpoint: string;
    status: {
        camera_status: string;
        camera_temperature: number;
        frame_number: number;
    };
}

export interface CameraEndpointTypes extends ParamNode {
    [camera_id: string]: CameraType;
}

export interface InferenceEndpointResultTypes extends ParamNode {
    endpoint_name: string;
    endpoint: string;
    connection: {
        connected: boolean;
        reconnect: boolean;
    };
    probabilities: {
        columnar: number;
        equiaxed: number;
        alpha: number;
        beta: number;
        hot_tear: number;
    };
    results: {
        inference_enabled: boolean;
        inference_running: boolean;
        last_frame_number: number;
        avg_inference_time_ms: number;
        flatfield_file: string;
        experiment_number: number;
        recording: boolean;
        num_predictions: number;
    };
    set_flatfield_num: number;
    background_task: {
        interval: number;
        enable: boolean;
    };
}

export interface InferenceEndpointTypes extends ParamNode {
    [endpoint_id: string]: InferenceEndpointResultTypes;
}