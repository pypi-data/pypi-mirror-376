from pymammotion.proto import dev_net_pb2 as _dev_net_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor
ERASE: Operation
NET_USED_TYPE_MNET: net_used_type
NET_USED_TYPE_NONE: net_used_type
NET_USED_TYPE_WIFI: net_used_type
OFF_PART_DEV_INFO: OffPartId
OFF_PART_DL_IMG: OffPartId
OFF_PART_FLASHDB: OffPartId
OFF_PART_MAX: OffPartId
OFF_PART_NAKEDB: OffPartId
OFF_PART_NAKEDB_BACK: OffPartId
OFF_PART_UPDINFO: OffPartId
OFF_PART_UPDINFO_BACK: OffPartId
OFF_PART_UPD_APP_IMG: OffPartId
OFF_PART_UPD_BMS_IMG: OffPartId
OFF_PART_UPD_TMP_IMG: OffPartId
QC_APP_ITEM_KEY: QCAppTestId
QC_APP_ITEM_ON_CHARGESATSTION: QCAppTestId
QC_APP_ITEM_SENEOR: QCAppTestId
QC_APP_ITEM_SQ: QCAppTestId
QC_APP_TEST_BLE_RSSI: QCAppTestId
QC_APP_TEST_BUMPER_FRONTLEFT: QCAppTestId
QC_APP_TEST_BUMPER_FRONTRIGHT: QCAppTestId
QC_APP_TEST_BUZZ: QCAppTestId
QC_APP_TEST_CHARGESTATION_TEMP: QCAppTestId
QC_APP_TEST_CHARGE_STATUS: QCAppTestId
QC_APP_TEST_CNO_REF_STATION: QCAppTestId
QC_APP_TEST_CNO_ROVER: QCAppTestId
QC_APP_TEST_COMPLETE_SIGNAL: QCAppTestId
QC_APP_TEST_HEADLAMP_TEST: QCAppTestId
QC_APP_TEST_LIFT: QCAppTestId
QC_APP_TEST_LOCATION_STATE: QCAppTestId
QC_APP_TEST_LORA_RSSI: QCAppTestId
QC_APP_TEST_MAX: QCAppTestId
QC_APP_TEST_PPS_EXTI_COUNT: QCAppTestId
QC_APP_TEST_RAIN: QCAppTestId
QC_APP_TEST_REF_STATION_LINK_STATUS: QCAppTestId
QC_APP_TEST_ROLL_LEFT: QCAppTestId
QC_APP_TEST_ROLL_RIGHT: QCAppTestId
QC_APP_TEST_SAFE_KEY: QCAppTestId
QC_APP_TEST_SATELLITES_COMMON_VIEW: QCAppTestId
QC_APP_TEST_SATELLITES_REF_STATION_L1: QCAppTestId
QC_APP_TEST_SATELLITES_REF_STATION_L2: QCAppTestId
QC_APP_TEST_SATELLITES_ROVER: QCAppTestId
QC_APP_TEST_STATIC_OBSTACLE_DETECTION: QCAppTestId
QC_APP_TEST_STOP: QCAppTestId
QC_APP_TEST_ULTRA0_COVER: QCAppTestId
QC_APP_TEST_ULTRA1_COVER: QCAppTestId
QC_APP_TEST_ULTRA2_COVER: QCAppTestId
QC_APP_TEST_ULTRA_UNCOVER: QCAppTestId
QC_APP_TEST_UNLOCK: QCAppTestId
QC_APP_TEST_WIPER_TEST: QCAppTestId
QC_APP_TEST_X3_SPEAKER: QCAppTestId
READ: Operation
RIT_BASESTATION_INFO: rpt_info_type
RIT_CONNECT: rpt_info_type
RIT_CUTTER_INFO: rpt_info_type
RIT_DEV_LOCAL: rpt_info_type
RIT_DEV_STA: rpt_info_type
RIT_FW_INFO: rpt_info_type
RIT_MAINTAIN: rpt_info_type
RIT_RTK: rpt_info_type
RIT_VIO: rpt_info_type
RIT_VISION_POINT: rpt_info_type
RIT_VISION_STATISTIC: rpt_info_type
RIT_WORK: rpt_info_type
RPT_KEEP: rpt_act
RPT_START: rpt_act
RPT_STOP: rpt_act
RS_FAIL_MAGIC: Command_Result
RS_FAIL_OTA: Command_Result
RS_FAIL_SLOPE: Command_Result
RS_OK: Command_Result
RTK_USED_INTERNET: rtk_used_type
RTK_USED_LORA: rtk_used_type
RTK_USED_NRTK: rtk_used_type
WRITE: Operation

class LoraCfgReq(_message.Message):
    __slots__ = ["cfg", "op"]
    CFG_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    cfg: str
    op: int
    def __init__(self, op: _Optional[int] = ..., cfg: _Optional[str] = ...) -> None: ...

class LoraCfgRsp(_message.Message):
    __slots__ = ["cfg", "fac_cfg", "op", "result"]
    CFG_FIELD_NUMBER: _ClassVar[int]
    FAC_CFG_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    cfg: str
    fac_cfg: str
    op: int
    result: int
    def __init__(self, result: _Optional[int] = ..., op: _Optional[int] = ..., cfg: _Optional[str] = ..., fac_cfg: _Optional[str] = ...) -> None: ...

class MctlSys(_message.Message):
    __slots__ = ["app_to_dev_get_mqtt_config_msg", "app_to_dev_set_mqtt_rtk_msg", "bidire_comm_cmd", "blade_used_warn_time", "border", "current_cutter_mode", "debug_cfg_read", "debug_cfg_write", "debug_common_report", "debug_enable", "debug_errocode_report", "debug_res_cfg_ability", "dev_to_app_get_mqtt_config_msg", "dev_to_app_set_mqtt_rtk_msg", "device_product_type_info", "job_plan", "mow_to_app_info", "mow_to_app_qctools_info", "plan_job_del", "report_info", "response_set_mode", "set_peripherals", "set_special_mode", "set_work_mode", "simulation_cmd", "systemRapidStateTunnel", "systemTardStateTunnel", "systemTmpCycleTx", "systemUpdateBuf", "to_app_msgbus", "to_app_remote_reset", "to_dev_msgbus", "to_dev_remote_reset", "to_dev_set_sun_time", "toapp_batinfo", "toapp_dev_fw_info", "toapp_err_code", "toapp_lora_cfg_rsp", "toapp_mow_info", "toapp_plan_status", "toapp_report_data", "toapp_ul_fprogress", "toapp_work_state", "todev_data_time", "todev_deljobplan", "todev_factor_reset_system", "todev_get_dev_fw_info", "todev_job_plan_time", "todev_knife_ctrl", "todev_lora_cfg_req", "todev_mow_info_up", "todev_off_chip_flash", "todev_report_cfg", "todev_reset_blade_used_time", "todev_reset_blade_used_time_status", "todev_reset_system", "todev_reset_system_status", "todev_time_ctrl_light", "todev_time_zone"]
    APP_TO_DEV_GET_MQTT_CONFIG_MSG_FIELD_NUMBER: _ClassVar[int]
    APP_TO_DEV_SET_MQTT_RTK_MSG_FIELD_NUMBER: _ClassVar[int]
    BIDIRE_COMM_CMD_FIELD_NUMBER: _ClassVar[int]
    BLADE_USED_WARN_TIME_FIELD_NUMBER: _ClassVar[int]
    BORDER_FIELD_NUMBER: _ClassVar[int]
    CURRENT_CUTTER_MODE_FIELD_NUMBER: _ClassVar[int]
    DEBUG_CFG_READ_FIELD_NUMBER: _ClassVar[int]
    DEBUG_CFG_WRITE_FIELD_NUMBER: _ClassVar[int]
    DEBUG_COMMON_REPORT_FIELD_NUMBER: _ClassVar[int]
    DEBUG_ENABLE_FIELD_NUMBER: _ClassVar[int]
    DEBUG_ERROCODE_REPORT_FIELD_NUMBER: _ClassVar[int]
    DEBUG_RES_CFG_ABILITY_FIELD_NUMBER: _ClassVar[int]
    DEVICE_PRODUCT_TYPE_INFO_FIELD_NUMBER: _ClassVar[int]
    DEV_TO_APP_GET_MQTT_CONFIG_MSG_FIELD_NUMBER: _ClassVar[int]
    DEV_TO_APP_SET_MQTT_RTK_MSG_FIELD_NUMBER: _ClassVar[int]
    JOB_PLAN_FIELD_NUMBER: _ClassVar[int]
    MOW_TO_APP_INFO_FIELD_NUMBER: _ClassVar[int]
    MOW_TO_APP_QCTOOLS_INFO_FIELD_NUMBER: _ClassVar[int]
    PLAN_JOB_DEL_FIELD_NUMBER: _ClassVar[int]
    REPORT_INFO_FIELD_NUMBER: _ClassVar[int]
    RESPONSE_SET_MODE_FIELD_NUMBER: _ClassVar[int]
    SET_PERIPHERALS_FIELD_NUMBER: _ClassVar[int]
    SET_SPECIAL_MODE_FIELD_NUMBER: _ClassVar[int]
    SET_WORK_MODE_FIELD_NUMBER: _ClassVar[int]
    SIMULATION_CMD_FIELD_NUMBER: _ClassVar[int]
    SYSTEMRAPIDSTATETUNNEL_FIELD_NUMBER: _ClassVar[int]
    SYSTEMTARDSTATETUNNEL_FIELD_NUMBER: _ClassVar[int]
    SYSTEMTMPCYCLETX_FIELD_NUMBER: _ClassVar[int]
    SYSTEMUPDATEBUF_FIELD_NUMBER: _ClassVar[int]
    TOAPP_BATINFO_FIELD_NUMBER: _ClassVar[int]
    TOAPP_DEV_FW_INFO_FIELD_NUMBER: _ClassVar[int]
    TOAPP_ERR_CODE_FIELD_NUMBER: _ClassVar[int]
    TOAPP_LORA_CFG_RSP_FIELD_NUMBER: _ClassVar[int]
    TOAPP_MOW_INFO_FIELD_NUMBER: _ClassVar[int]
    TOAPP_PLAN_STATUS_FIELD_NUMBER: _ClassVar[int]
    TOAPP_REPORT_DATA_FIELD_NUMBER: _ClassVar[int]
    TOAPP_UL_FPROGRESS_FIELD_NUMBER: _ClassVar[int]
    TOAPP_WORK_STATE_FIELD_NUMBER: _ClassVar[int]
    TODEV_DATA_TIME_FIELD_NUMBER: _ClassVar[int]
    TODEV_DELJOBPLAN_FIELD_NUMBER: _ClassVar[int]
    TODEV_FACTOR_RESET_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    TODEV_GET_DEV_FW_INFO_FIELD_NUMBER: _ClassVar[int]
    TODEV_JOB_PLAN_TIME_FIELD_NUMBER: _ClassVar[int]
    TODEV_KNIFE_CTRL_FIELD_NUMBER: _ClassVar[int]
    TODEV_LORA_CFG_REQ_FIELD_NUMBER: _ClassVar[int]
    TODEV_MOW_INFO_UP_FIELD_NUMBER: _ClassVar[int]
    TODEV_OFF_CHIP_FLASH_FIELD_NUMBER: _ClassVar[int]
    TODEV_REPORT_CFG_FIELD_NUMBER: _ClassVar[int]
    TODEV_RESET_BLADE_USED_TIME_FIELD_NUMBER: _ClassVar[int]
    TODEV_RESET_BLADE_USED_TIME_STATUS_FIELD_NUMBER: _ClassVar[int]
    TODEV_RESET_SYSTEM_FIELD_NUMBER: _ClassVar[int]
    TODEV_RESET_SYSTEM_STATUS_FIELD_NUMBER: _ClassVar[int]
    TODEV_TIME_CTRL_LIGHT_FIELD_NUMBER: _ClassVar[int]
    TODEV_TIME_ZONE_FIELD_NUMBER: _ClassVar[int]
    TO_APP_MSGBUS_FIELD_NUMBER: _ClassVar[int]
    TO_APP_REMOTE_RESET_FIELD_NUMBER: _ClassVar[int]
    TO_DEV_MSGBUS_FIELD_NUMBER: _ClassVar[int]
    TO_DEV_REMOTE_RESET_FIELD_NUMBER: _ClassVar[int]
    TO_DEV_SET_SUN_TIME_FIELD_NUMBER: _ClassVar[int]
    app_to_dev_get_mqtt_config_msg: app_to_dev_get_mqtt_config_t
    app_to_dev_set_mqtt_rtk_msg: app_to_dev_set_mqtt_rtk_t
    bidire_comm_cmd: SysCommCmd
    blade_used_warn_time: user_set_blade_used_warn_time
    border: SysBorder
    current_cutter_mode: rpt_cutter_rpm
    debug_cfg_read: debug_cfg_read_t
    debug_cfg_write: debug_cfg_write_t
    debug_common_report: debug_common_report_t
    debug_enable: debug_enable_t
    debug_errocode_report: debug_errocode_report_t
    debug_res_cfg_ability: debug_res_cfg_ability_t
    dev_to_app_get_mqtt_config_msg: dev_to_app_get_mqtt_config_t
    dev_to_app_set_mqtt_rtk_msg: dev_to_app_set_mqtt_rtk_t
    device_product_type_info: device_product_type_info_t
    job_plan: SysJobPlan
    mow_to_app_info: mow_to_app_info_t
    mow_to_app_qctools_info: mow_to_app_qctools_info_t
    plan_job_del: int
    report_info: report_info_t
    response_set_mode: response_set_mode_t
    set_peripherals: set_peripherals_t
    set_special_mode: special_mode_t
    set_work_mode: work_mode_t
    simulation_cmd: mCtrlSimulationCmdData
    systemRapidStateTunnel: systemRapidStateTunnel_msg
    systemTardStateTunnel: systemTardStateTunnel_msg
    systemTmpCycleTx: systemTmpCycleTx_msg
    systemUpdateBuf: systemUpdateBuf_msg
    to_app_msgbus: msgbus_pkt
    to_app_remote_reset: remote_reset_rsp_t
    to_dev_msgbus: msgbus_pkt
    to_dev_remote_reset: remote_reset_req_t
    to_dev_set_sun_time: debug_sun_time_t
    toapp_batinfo: SysBatUp
    toapp_dev_fw_info: device_fw_info
    toapp_err_code: SysDevErrCode
    toapp_lora_cfg_rsp: LoraCfgRsp
    toapp_mow_info: SysMowInfo
    toapp_plan_status: SysPlanJobStatus
    toapp_report_data: report_info_data
    toapp_ul_fprogress: SysUploadFileProgress
    toapp_work_state: SysWorkState
    todev_data_time: SysSetDateTime
    todev_deljobplan: SysDelJobPlan
    todev_factor_reset_system: int
    todev_get_dev_fw_info: int
    todev_job_plan_time: SysJobPlanTime
    todev_knife_ctrl: SysKnifeControl
    todev_lora_cfg_req: LoraCfgReq
    todev_mow_info_up: int
    todev_off_chip_flash: SysOffChipFlash
    todev_report_cfg: report_info_cfg
    todev_reset_blade_used_time: int
    todev_reset_blade_used_time_status: SysResetBladeUsedTimeStatus
    todev_reset_system: int
    todev_reset_system_status: SysResetSystemStatus
    todev_time_ctrl_light: TimeCtrlLight
    todev_time_zone: SysSetTimeZone
    def __init__(self, toapp_batinfo: _Optional[_Union[SysBatUp, _Mapping]] = ..., toapp_work_state: _Optional[_Union[SysWorkState, _Mapping]] = ..., todev_time_zone: _Optional[_Union[SysSetTimeZone, _Mapping]] = ..., todev_data_time: _Optional[_Union[SysSetDateTime, _Mapping]] = ..., job_plan: _Optional[_Union[SysJobPlan, _Mapping]] = ..., toapp_err_code: _Optional[_Union[SysDevErrCode, _Mapping]] = ..., todev_job_plan_time: _Optional[_Union[SysJobPlanTime, _Mapping]] = ..., toapp_mow_info: _Optional[_Union[SysMowInfo, _Mapping]] = ..., bidire_comm_cmd: _Optional[_Union[SysCommCmd, _Mapping]] = ..., plan_job_del: _Optional[int] = ..., border: _Optional[_Union[SysBorder, _Mapping]] = ..., toapp_plan_status: _Optional[_Union[SysPlanJobStatus, _Mapping]] = ..., toapp_ul_fprogress: _Optional[_Union[SysUploadFileProgress, _Mapping]] = ..., todev_deljobplan: _Optional[_Union[SysDelJobPlan, _Mapping]] = ..., todev_mow_info_up: _Optional[int] = ..., todev_knife_ctrl: _Optional[_Union[SysKnifeControl, _Mapping]] = ..., todev_reset_system: _Optional[int] = ..., todev_reset_system_status: _Optional[_Union[SysResetSystemStatus, _Mapping]] = ..., systemRapidStateTunnel: _Optional[_Union[systemRapidStateTunnel_msg, _Mapping]] = ..., systemTardStateTunnel: _Optional[_Union[systemTardStateTunnel_msg, _Mapping]] = ..., systemUpdateBuf: _Optional[_Union[systemUpdateBuf_msg, _Mapping]] = ..., todev_time_ctrl_light: _Optional[_Union[TimeCtrlLight, _Mapping]] = ..., systemTmpCycleTx: _Optional[_Union[systemTmpCycleTx_msg, _Mapping]] = ..., todev_off_chip_flash: _Optional[_Union[SysOffChipFlash, _Mapping]] = ..., todev_get_dev_fw_info: _Optional[int] = ..., toapp_dev_fw_info: _Optional[_Union[device_fw_info, _Mapping]] = ..., todev_lora_cfg_req: _Optional[_Union[LoraCfgReq, _Mapping]] = ..., toapp_lora_cfg_rsp: _Optional[_Union[LoraCfgRsp, _Mapping]] = ..., mow_to_app_info: _Optional[_Union[mow_to_app_info_t, _Mapping]] = ..., device_product_type_info: _Optional[_Union[device_product_type_info_t, _Mapping]] = ..., mow_to_app_qctools_info: _Optional[_Union[mow_to_app_qctools_info_t, _Mapping]] = ..., todev_report_cfg: _Optional[_Union[report_info_cfg, _Mapping]] = ..., toapp_report_data: _Optional[_Union[report_info_data, _Mapping]] = ..., simulation_cmd: _Optional[_Union[mCtrlSimulationCmdData, _Mapping]] = ..., app_to_dev_get_mqtt_config_msg: _Optional[_Union[app_to_dev_get_mqtt_config_t, _Mapping]] = ..., dev_to_app_get_mqtt_config_msg: _Optional[_Union[dev_to_app_get_mqtt_config_t, _Mapping]] = ..., app_to_dev_set_mqtt_rtk_msg: _Optional[_Union[app_to_dev_set_mqtt_rtk_t, _Mapping]] = ..., dev_to_app_set_mqtt_rtk_msg: _Optional[_Union[dev_to_app_set_mqtt_rtk_t, _Mapping]] = ..., todev_reset_blade_used_time: _Optional[int] = ..., todev_reset_blade_used_time_status: _Optional[_Union[SysResetBladeUsedTimeStatus, _Mapping]] = ..., todev_factor_reset_system: _Optional[int] = ..., blade_used_warn_time: _Optional[_Union[user_set_blade_used_warn_time, _Mapping]] = ..., debug_common_report: _Optional[_Union[debug_common_report_t, _Mapping]] = ..., debug_errocode_report: _Optional[_Union[debug_errocode_report_t, _Mapping]] = ..., debug_enable: _Optional[_Union[debug_enable_t, _Mapping]] = ..., debug_cfg_read: _Optional[_Union[debug_cfg_read_t, _Mapping]] = ..., debug_cfg_write: _Optional[_Union[debug_cfg_write_t, _Mapping]] = ..., debug_res_cfg_ability: _Optional[_Union[debug_res_cfg_ability_t, _Mapping]] = ..., to_dev_msgbus: _Optional[_Union[msgbus_pkt, _Mapping]] = ..., to_app_msgbus: _Optional[_Union[msgbus_pkt, _Mapping]] = ..., response_set_mode: _Optional[_Union[response_set_mode_t, _Mapping]] = ..., report_info: _Optional[_Union[report_info_t, _Mapping]] = ..., set_work_mode: _Optional[_Union[work_mode_t, _Mapping]] = ..., set_special_mode: _Optional[_Union[special_mode_t, _Mapping]] = ..., set_peripherals: _Optional[_Union[set_peripherals_t, _Mapping]] = ..., to_dev_set_sun_time: _Optional[_Union[debug_sun_time_t, _Mapping]] = ..., to_dev_remote_reset: _Optional[_Union[remote_reset_req_t, _Mapping]] = ..., to_app_remote_reset: _Optional[_Union[remote_reset_rsp_t, _Mapping]] = ..., current_cutter_mode: _Optional[_Union[rpt_cutter_rpm, _Mapping]] = ...) -> None: ...

class QCAppTestConditions(_message.Message):
    __slots__ = ["cond_type", "double_val", "float_val", "int_val", "string_val"]
    COND_TYPE_FIELD_NUMBER: _ClassVar[int]
    DOUBLE_VAL_FIELD_NUMBER: _ClassVar[int]
    FLOAT_VAL_FIELD_NUMBER: _ClassVar[int]
    INT_VAL_FIELD_NUMBER: _ClassVar[int]
    STRING_VAL_FIELD_NUMBER: _ClassVar[int]
    cond_type: str
    double_val: float
    float_val: float
    int_val: int
    string_val: str
    def __init__(self, cond_type: _Optional[str] = ..., int_val: _Optional[int] = ..., float_val: _Optional[float] = ..., double_val: _Optional[float] = ..., string_val: _Optional[str] = ...) -> None: ...

class QCAppTestExcept(_message.Message):
    __slots__ = ["conditions", "except_type"]
    CONDITIONS_FIELD_NUMBER: _ClassVar[int]
    EXCEPT_TYPE_FIELD_NUMBER: _ClassVar[int]
    conditions: _containers.RepeatedCompositeFieldContainer[QCAppTestConditions]
    except_type: str
    def __init__(self, except_type: _Optional[str] = ..., conditions: _Optional[_Iterable[_Union[QCAppTestConditions, _Mapping]]] = ...) -> None: ...

class SysBatUp(_message.Message):
    __slots__ = ["batVal"]
    BATVAL_FIELD_NUMBER: _ClassVar[int]
    batVal: int
    def __init__(self, batVal: _Optional[int] = ...) -> None: ...

class SysBoardType(_message.Message):
    __slots__ = ["boardType"]
    BOARDTYPE_FIELD_NUMBER: _ClassVar[int]
    boardType: int
    def __init__(self, boardType: _Optional[int] = ...) -> None: ...

class SysBorder(_message.Message):
    __slots__ = ["borderval"]
    BORDERVAL_FIELD_NUMBER: _ClassVar[int]
    borderval: int
    def __init__(self, borderval: _Optional[int] = ...) -> None: ...

class SysCommCmd(_message.Message):
    __slots__ = ["context", "id", "rw"]
    CONTEXT_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    RW_FIELD_NUMBER: _ClassVar[int]
    context: int
    id: int
    rw: int
    def __init__(self, rw: _Optional[int] = ..., id: _Optional[int] = ..., context: _Optional[int] = ...) -> None: ...

class SysDelJobPlan(_message.Message):
    __slots__ = ["deviceId", "planId"]
    DEVICEID_FIELD_NUMBER: _ClassVar[int]
    PLANID_FIELD_NUMBER: _ClassVar[int]
    deviceId: str
    planId: str
    def __init__(self, deviceId: _Optional[str] = ..., planId: _Optional[str] = ...) -> None: ...

class SysDevErrCode(_message.Message):
    __slots__ = ["errorCode"]
    ERRORCODE_FIELD_NUMBER: _ClassVar[int]
    errorCode: int
    def __init__(self, errorCode: _Optional[int] = ...) -> None: ...

class SysErrorCode(_message.Message):
    __slots__ = ["code_no"]
    CODE_NO_FIELD_NUMBER: _ClassVar[int]
    code_no: int
    def __init__(self, code_no: _Optional[int] = ...) -> None: ...

class SysJobPlan(_message.Message):
    __slots__ = ["jobId", "jobMode", "knifeHeight", "rainTactics"]
    JOBID_FIELD_NUMBER: _ClassVar[int]
    JOBMODE_FIELD_NUMBER: _ClassVar[int]
    KNIFEHEIGHT_FIELD_NUMBER: _ClassVar[int]
    RAINTACTICS_FIELD_NUMBER: _ClassVar[int]
    jobId: int
    jobMode: int
    knifeHeight: int
    rainTactics: int
    def __init__(self, jobId: _Optional[int] = ..., jobMode: _Optional[int] = ..., rainTactics: _Optional[int] = ..., knifeHeight: _Optional[int] = ...) -> None: ...

class SysJobPlanTime(_message.Message):
    __slots__ = ["end_job_time", "everyDay", "job_plan", "job_plan_enable", "job_plan_mode", "planId", "start_job_time", "timeInWeekDay", "time_in_day", "weekDay"]
    END_JOB_TIME_FIELD_NUMBER: _ClassVar[int]
    EVERYDAY_FIELD_NUMBER: _ClassVar[int]
    JOB_PLAN_ENABLE_FIELD_NUMBER: _ClassVar[int]
    JOB_PLAN_FIELD_NUMBER: _ClassVar[int]
    JOB_PLAN_MODE_FIELD_NUMBER: _ClassVar[int]
    PLANID_FIELD_NUMBER: _ClassVar[int]
    START_JOB_TIME_FIELD_NUMBER: _ClassVar[int]
    TIMEINWEEKDAY_FIELD_NUMBER: _ClassVar[int]
    TIME_IN_DAY_FIELD_NUMBER: _ClassVar[int]
    WEEKDAY_FIELD_NUMBER: _ClassVar[int]
    end_job_time: int
    everyDay: int
    job_plan: SysJobPlan
    job_plan_enable: int
    job_plan_mode: int
    planId: int
    start_job_time: int
    timeInWeekDay: _containers.RepeatedScalarFieldContainer[int]
    time_in_day: int
    weekDay: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, planId: _Optional[int] = ..., start_job_time: _Optional[int] = ..., end_job_time: _Optional[int] = ..., time_in_day: _Optional[int] = ..., job_plan_mode: _Optional[int] = ..., job_plan_enable: _Optional[int] = ..., weekDay: _Optional[_Iterable[int]] = ..., timeInWeekDay: _Optional[_Iterable[int]] = ..., everyDay: _Optional[int] = ..., job_plan: _Optional[_Union[SysJobPlan, _Mapping]] = ...) -> None: ...

class SysKnifeControl(_message.Message):
    __slots__ = ["knife_height", "knife_status"]
    KNIFE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    KNIFE_STATUS_FIELD_NUMBER: _ClassVar[int]
    knife_height: int
    knife_status: int
    def __init__(self, knife_status: _Optional[int] = ..., knife_height: _Optional[int] = ...) -> None: ...

class SysMowInfo(_message.Message):
    __slots__ = ["RTKstars", "RTKstatus", "batVal", "deviceState", "knifeHeight"]
    BATVAL_FIELD_NUMBER: _ClassVar[int]
    DEVICESTATE_FIELD_NUMBER: _ClassVar[int]
    KNIFEHEIGHT_FIELD_NUMBER: _ClassVar[int]
    RTKSTARS_FIELD_NUMBER: _ClassVar[int]
    RTKSTATUS_FIELD_NUMBER: _ClassVar[int]
    RTKstars: int
    RTKstatus: int
    batVal: int
    deviceState: int
    knifeHeight: int
    def __init__(self, deviceState: _Optional[int] = ..., batVal: _Optional[int] = ..., knifeHeight: _Optional[int] = ..., RTKstatus: _Optional[int] = ..., RTKstars: _Optional[int] = ...) -> None: ...

class SysOffChipFlash(_message.Message):
    __slots__ = ["code", "data", "id", "length", "msg", "offset", "op", "start_addr"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    ID_FIELD_NUMBER: _ClassVar[int]
    LENGTH_FIELD_NUMBER: _ClassVar[int]
    MSG_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    OP_FIELD_NUMBER: _ClassVar[int]
    START_ADDR_FIELD_NUMBER: _ClassVar[int]
    code: int
    data: bytes
    id: OffPartId
    length: int
    msg: str
    offset: int
    op: Operation
    start_addr: int
    def __init__(self, op: _Optional[_Union[Operation, str]] = ..., id: _Optional[_Union[OffPartId, str]] = ..., start_addr: _Optional[int] = ..., offset: _Optional[int] = ..., length: _Optional[int] = ..., data: _Optional[bytes] = ..., code: _Optional[int] = ..., msg: _Optional[str] = ...) -> None: ...

class SysOptiLineAck(_message.Message):
    __slots__ = ["currentFrame", "responesCmd"]
    CURRENTFRAME_FIELD_NUMBER: _ClassVar[int]
    RESPONESCMD_FIELD_NUMBER: _ClassVar[int]
    currentFrame: int
    responesCmd: int
    def __init__(self, responesCmd: _Optional[int] = ..., currentFrame: _Optional[int] = ...) -> None: ...

class SysPlanJobStatus(_message.Message):
    __slots__ = ["planjob_status"]
    PLANJOB_STATUS_FIELD_NUMBER: _ClassVar[int]
    planjob_status: int
    def __init__(self, planjob_status: _Optional[int] = ...) -> None: ...

class SysResetBladeUsedTimeStatus(_message.Message):
    __slots__ = ["reset_blade_used_time_status"]
    RESET_BLADE_USED_TIME_STATUS_FIELD_NUMBER: _ClassVar[int]
    reset_blade_used_time_status: int
    def __init__(self, reset_blade_used_time_status: _Optional[int] = ...) -> None: ...

class SysResetSystemStatus(_message.Message):
    __slots__ = ["reset_staus"]
    RESET_STAUS_FIELD_NUMBER: _ClassVar[int]
    reset_staus: int
    def __init__(self, reset_staus: _Optional[int] = ...) -> None: ...

class SysSetDateTime(_message.Message):
    __slots__ = ["Date", "Hours", "Minutes", "Month", "Seconds", "Week", "Year", "daylight", "timeZone"]
    DATE_FIELD_NUMBER: _ClassVar[int]
    DAYLIGHT_FIELD_NUMBER: _ClassVar[int]
    Date: int
    HOURS_FIELD_NUMBER: _ClassVar[int]
    Hours: int
    MINUTES_FIELD_NUMBER: _ClassVar[int]
    MONTH_FIELD_NUMBER: _ClassVar[int]
    Minutes: int
    Month: int
    SECONDS_FIELD_NUMBER: _ClassVar[int]
    Seconds: int
    TIMEZONE_FIELD_NUMBER: _ClassVar[int]
    WEEK_FIELD_NUMBER: _ClassVar[int]
    Week: int
    YEAR_FIELD_NUMBER: _ClassVar[int]
    Year: int
    daylight: int
    timeZone: int
    def __init__(self, Year: _Optional[int] = ..., Month: _Optional[int] = ..., Date: _Optional[int] = ..., Week: _Optional[int] = ..., Hours: _Optional[int] = ..., Minutes: _Optional[int] = ..., Seconds: _Optional[int] = ..., timeZone: _Optional[int] = ..., daylight: _Optional[int] = ...) -> None: ...

class SysSetTimeZone(_message.Message):
    __slots__ = ["timeArea", "timeStamp"]
    TIMEAREA_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    timeArea: int
    timeStamp: int
    def __init__(self, timeStamp: _Optional[int] = ..., timeArea: _Optional[int] = ...) -> None: ...

class SysSwVersion(_message.Message):
    __slots__ = ["boardType", "versionLen"]
    BOARDTYPE_FIELD_NUMBER: _ClassVar[int]
    VERSIONLEN_FIELD_NUMBER: _ClassVar[int]
    boardType: int
    versionLen: int
    def __init__(self, boardType: _Optional[int] = ..., versionLen: _Optional[int] = ...) -> None: ...

class SysUploadFileProgress(_message.Message):
    __slots__ = ["bizId", "progress", "result"]
    BIZID_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    bizId: str
    progress: int
    result: int
    def __init__(self, bizId: _Optional[str] = ..., result: _Optional[int] = ..., progress: _Optional[int] = ...) -> None: ...

class SysWorkState(_message.Message):
    __slots__ = ["chargeState", "cmHash", "deviceState", "pathHash"]
    CHARGESTATE_FIELD_NUMBER: _ClassVar[int]
    CMHASH_FIELD_NUMBER: _ClassVar[int]
    DEVICESTATE_FIELD_NUMBER: _ClassVar[int]
    PATHHASH_FIELD_NUMBER: _ClassVar[int]
    chargeState: int
    cmHash: int
    deviceState: int
    pathHash: int
    def __init__(self, deviceState: _Optional[int] = ..., chargeState: _Optional[int] = ..., cmHash: _Optional[int] = ..., pathHash: _Optional[int] = ...) -> None: ...

class TimeCtrlLight(_message.Message):
    __slots__ = ["action", "enable", "end_hour", "end_min", "operate", "start_hour", "start_min"]
    ACTION_FIELD_NUMBER: _ClassVar[int]
    ENABLE_FIELD_NUMBER: _ClassVar[int]
    END_HOUR_FIELD_NUMBER: _ClassVar[int]
    END_MIN_FIELD_NUMBER: _ClassVar[int]
    OPERATE_FIELD_NUMBER: _ClassVar[int]
    START_HOUR_FIELD_NUMBER: _ClassVar[int]
    START_MIN_FIELD_NUMBER: _ClassVar[int]
    action: int
    enable: int
    end_hour: int
    end_min: int
    operate: int
    start_hour: int
    start_min: int
    def __init__(self, operate: _Optional[int] = ..., enable: _Optional[int] = ..., start_hour: _Optional[int] = ..., start_min: _Optional[int] = ..., end_hour: _Optional[int] = ..., end_min: _Optional[int] = ..., action: _Optional[int] = ...) -> None: ...

class app_to_dev_get_mqtt_config_t(_message.Message):
    __slots__ = ["get_mqtt_config"]
    GET_MQTT_CONFIG_FIELD_NUMBER: _ClassVar[int]
    get_mqtt_config: int
    def __init__(self, get_mqtt_config: _Optional[int] = ...) -> None: ...

class app_to_dev_set_mqtt_rtk_t(_message.Message):
    __slots__ = ["set_nrtk_net_mode", "set_rtk_mode", "stop_nrtk_flag"]
    SET_NRTK_NET_MODE_FIELD_NUMBER: _ClassVar[int]
    SET_RTK_MODE_FIELD_NUMBER: _ClassVar[int]
    STOP_NRTK_FLAG_FIELD_NUMBER: _ClassVar[int]
    set_nrtk_net_mode: int
    set_rtk_mode: rtk_used_type
    stop_nrtk_flag: int
    def __init__(self, set_rtk_mode: _Optional[_Union[rtk_used_type, str]] = ..., stop_nrtk_flag: _Optional[int] = ..., set_nrtk_net_mode: _Optional[int] = ...) -> None: ...

class blade_used(_message.Message):
    __slots__ = ["blade_used_time", "blade_used_warn_time"]
    BLADE_USED_TIME_FIELD_NUMBER: _ClassVar[int]
    BLADE_USED_WARN_TIME_FIELD_NUMBER: _ClassVar[int]
    blade_used_time: int
    blade_used_warn_time: int
    def __init__(self, blade_used_time: _Optional[int] = ..., blade_used_warn_time: _Optional[int] = ...) -> None: ...

class collector_status_t(_message.Message):
    __slots__ = ["collector_installation_status"]
    COLLECTOR_INSTALLATION_STATUS_FIELD_NUMBER: _ClassVar[int]
    collector_installation_status: int
    def __init__(self, collector_installation_status: _Optional[int] = ...) -> None: ...

class debug_cfg_read_t(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class debug_cfg_write_t(_message.Message):
    __slots__ = ["key", "value"]
    KEY_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    key: str
    value: str
    def __init__(self, key: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class debug_common_report_t(_message.Message):
    __slots__ = ["gen_time", "key", "m_name", "value"]
    GEN_TIME_FIELD_NUMBER: _ClassVar[int]
    KEY_FIELD_NUMBER: _ClassVar[int]
    M_NAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    gen_time: int
    key: str
    m_name: str
    value: str
    def __init__(self, m_name: _Optional[str] = ..., key: _Optional[str] = ..., value: _Optional[str] = ..., gen_time: _Optional[int] = ...) -> None: ...

class debug_enable_t(_message.Message):
    __slots__ = ["enbale"]
    ENBALE_FIELD_NUMBER: _ClassVar[int]
    enbale: int
    def __init__(self, enbale: _Optional[int] = ...) -> None: ...

class debug_errocode_report_t(_message.Message):
    __slots__ = ["code", "gen_time", "mname", "value"]
    CODE_FIELD_NUMBER: _ClassVar[int]
    GEN_TIME_FIELD_NUMBER: _ClassVar[int]
    MNAME_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    code: int
    gen_time: int
    mname: str
    value: str
    def __init__(self, code: _Optional[int] = ..., mname: _Optional[str] = ..., value: _Optional[str] = ..., gen_time: _Optional[int] = ...) -> None: ...

class debug_res_cfg_ability_t(_message.Message):
    __slots__ = ["cur_key_id", "keys", "total_keys", "value"]
    CUR_KEY_ID_FIELD_NUMBER: _ClassVar[int]
    KEYS_FIELD_NUMBER: _ClassVar[int]
    TOTAL_KEYS_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    cur_key_id: int
    keys: str
    total_keys: int
    value: str
    def __init__(self, total_keys: _Optional[int] = ..., cur_key_id: _Optional[int] = ..., keys: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class debug_sun_time_t(_message.Message):
    __slots__ = ["subCmd", "sunRiseTime", "sunSetTime"]
    SUBCMD_FIELD_NUMBER: _ClassVar[int]
    SUNRISETIME_FIELD_NUMBER: _ClassVar[int]
    SUNSETTIME_FIELD_NUMBER: _ClassVar[int]
    subCmd: int
    sunRiseTime: int
    sunSetTime: int
    def __init__(self, subCmd: _Optional[int] = ..., sunRiseTime: _Optional[int] = ..., sunSetTime: _Optional[int] = ...) -> None: ...

class dev_statue_t(_message.Message):
    __slots__ = ["bat_val", "ble_rssi", "charge_status", "iot_connect_status", "model", "pump_status", "sys_status", "wheel_status", "wifi_available", "wifi_connect_status", "wifi_rssi", "work_mode"]
    BAT_VAL_FIELD_NUMBER: _ClassVar[int]
    BLE_RSSI_FIELD_NUMBER: _ClassVar[int]
    CHARGE_STATUS_FIELD_NUMBER: _ClassVar[int]
    IOT_CONNECT_STATUS_FIELD_NUMBER: _ClassVar[int]
    MODEL_FIELD_NUMBER: _ClassVar[int]
    PUMP_STATUS_FIELD_NUMBER: _ClassVar[int]
    SYS_STATUS_FIELD_NUMBER: _ClassVar[int]
    WHEEL_STATUS_FIELD_NUMBER: _ClassVar[int]
    WIFI_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    WIFI_CONNECT_STATUS_FIELD_NUMBER: _ClassVar[int]
    WIFI_RSSI_FIELD_NUMBER: _ClassVar[int]
    WORK_MODE_FIELD_NUMBER: _ClassVar[int]
    bat_val: int
    ble_rssi: int
    charge_status: int
    iot_connect_status: int
    model: int
    pump_status: int
    sys_status: int
    wheel_status: int
    wifi_available: int
    wifi_connect_status: int
    wifi_rssi: int
    work_mode: int
    def __init__(self, sys_status: _Optional[int] = ..., charge_status: _Optional[int] = ..., bat_val: _Optional[int] = ..., wheel_status: _Optional[int] = ..., pump_status: _Optional[int] = ..., work_mode: _Optional[int] = ..., model: _Optional[int] = ..., ble_rssi: _Optional[int] = ..., wifi_rssi: _Optional[int] = ..., wifi_connect_status: _Optional[int] = ..., iot_connect_status: _Optional[int] = ..., wifi_available: _Optional[int] = ...) -> None: ...

class dev_to_app_get_mqtt_config_t(_message.Message):
    __slots__ = ["rtk_base_num", "rtk_status"]
    RTK_BASE_NUM_FIELD_NUMBER: _ClassVar[int]
    RTK_STATUS_FIELD_NUMBER: _ClassVar[int]
    rtk_base_num: str
    rtk_status: int
    def __init__(self, rtk_status: _Optional[int] = ..., rtk_base_num: _Optional[str] = ...) -> None: ...

class dev_to_app_set_mqtt_rtk_t(_message.Message):
    __slots__ = ["set_rtk_mode_error"]
    SET_RTK_MODE_ERROR_FIELD_NUMBER: _ClassVar[int]
    set_rtk_mode_error: int
    def __init__(self, set_rtk_mode_error: _Optional[int] = ...) -> None: ...

class device_fw_info(_message.Message):
    __slots__ = ["mod", "result", "version"]
    MOD_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    mod: _containers.RepeatedCompositeFieldContainer[mod_fw_info]
    result: int
    version: str
    def __init__(self, result: _Optional[int] = ..., version: _Optional[str] = ..., mod: _Optional[_Iterable[_Union[mod_fw_info, _Mapping]]] = ...) -> None: ...

class device_product_type_info_t(_message.Message):
    __slots__ = ["main_product_type", "result", "sub_product_type"]
    MAIN_PRODUCT_TYPE_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    SUB_PRODUCT_TYPE_FIELD_NUMBER: _ClassVar[int]
    main_product_type: str
    result: int
    sub_product_type: str
    def __init__(self, result: _Optional[int] = ..., main_product_type: _Optional[str] = ..., sub_product_type: _Optional[str] = ...) -> None: ...

class fpv_to_app_info_t(_message.Message):
    __slots__ = ["fpv_flag", "mobile_net_available", "wifi_available"]
    FPV_FLAG_FIELD_NUMBER: _ClassVar[int]
    MOBILE_NET_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    WIFI_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    fpv_flag: int
    mobile_net_available: int
    wifi_available: int
    def __init__(self, fpv_flag: _Optional[int] = ..., wifi_available: _Optional[int] = ..., mobile_net_available: _Optional[int] = ...) -> None: ...

class lock_state_t(_message.Message):
    __slots__ = ["lock_state"]
    LOCK_STATE_FIELD_NUMBER: _ClassVar[int]
    lock_state: int
    def __init__(self, lock_state: _Optional[int] = ...) -> None: ...

class mCtrlSimulationCmdData(_message.Message):
    __slots__ = ["param_id", "param_value", "subCmd"]
    PARAM_ID_FIELD_NUMBER: _ClassVar[int]
    PARAM_VALUE_FIELD_NUMBER: _ClassVar[int]
    SUBCMD_FIELD_NUMBER: _ClassVar[int]
    param_id: int
    param_value: _containers.RepeatedScalarFieldContainer[int]
    subCmd: int
    def __init__(self, subCmd: _Optional[int] = ..., param_id: _Optional[int] = ..., param_value: _Optional[_Iterable[int]] = ...) -> None: ...

class mod_fw_info(_message.Message):
    __slots__ = ["identify", "type", "version"]
    IDENTIFY_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    identify: str
    type: int
    version: str
    def __init__(self, type: _Optional[int] = ..., identify: _Optional[str] = ..., version: _Optional[str] = ...) -> None: ...

class mow_to_app_info_t(_message.Message):
    __slots__ = ["cmd", "mow_data", "type"]
    CMD_FIELD_NUMBER: _ClassVar[int]
    MOW_DATA_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    cmd: int
    mow_data: _containers.RepeatedScalarFieldContainer[int]
    type: int
    def __init__(self, type: _Optional[int] = ..., cmd: _Optional[int] = ..., mow_data: _Optional[_Iterable[int]] = ...) -> None: ...

class mow_to_app_qctools_info_t(_message.Message):
    __slots__ = ["result", "result_details", "timeOfDuration", "type"]
    EXCEPT_FIELD_NUMBER: _ClassVar[int]
    RESULT_DETAILS_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    TIMEOFDURATION_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    result: int
    result_details: str
    timeOfDuration: int
    type: QCAppTestId
    def __init__(self, type: _Optional[_Union[QCAppTestId, str]] = ..., timeOfDuration: _Optional[int] = ..., result: _Optional[int] = ..., result_details: _Optional[str] = ..., **kwargs) -> None: ...

class mqtt_rtk_connect(_message.Message):
    __slots__ = ["latitude", "longitude", "new_rtk_mode", "nrtk_map_convert_status", "nrtk_net_mode", "rtk_base_num", "rtk_channel", "rtk_switch"]
    LATITUDE_FIELD_NUMBER: _ClassVar[int]
    LONGITUDE_FIELD_NUMBER: _ClassVar[int]
    NEW_RTK_MODE_FIELD_NUMBER: _ClassVar[int]
    NRTK_MAP_CONVERT_STATUS_FIELD_NUMBER: _ClassVar[int]
    NRTK_NET_MODE_FIELD_NUMBER: _ClassVar[int]
    RTK_BASE_NUM_FIELD_NUMBER: _ClassVar[int]
    RTK_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    RTK_SWITCH_FIELD_NUMBER: _ClassVar[int]
    latitude: float
    longitude: float
    new_rtk_mode: int
    nrtk_map_convert_status: int
    nrtk_net_mode: int
    rtk_base_num: str
    rtk_channel: int
    rtk_switch: rtk_used_type
    def __init__(self, rtk_switch: _Optional[_Union[rtk_used_type, str]] = ..., rtk_channel: _Optional[int] = ..., rtk_base_num: _Optional[str] = ..., latitude: _Optional[float] = ..., longitude: _Optional[float] = ..., nrtk_map_convert_status: _Optional[int] = ..., nrtk_net_mode: _Optional[int] = ..., new_rtk_mode: _Optional[int] = ...) -> None: ...

class msgbus_pkt(_message.Message):
    __slots__ = ["ctrl", "data", "dataLength", "flag", "recvDeviceId", "sendDeviceId", "seqs", "type", "typeCommand"]
    CTRL_FIELD_NUMBER: _ClassVar[int]
    DATALENGTH_FIELD_NUMBER: _ClassVar[int]
    DATA_FIELD_NUMBER: _ClassVar[int]
    FLAG_FIELD_NUMBER: _ClassVar[int]
    RECVDEVICEID_FIELD_NUMBER: _ClassVar[int]
    SENDDEVICEID_FIELD_NUMBER: _ClassVar[int]
    SEQS_FIELD_NUMBER: _ClassVar[int]
    TYPECOMMAND_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    ctrl: int
    data: str
    dataLength: int
    flag: int
    recvDeviceId: int
    sendDeviceId: int
    seqs: int
    type: int
    typeCommand: int
    def __init__(self, type: _Optional[int] = ..., typeCommand: _Optional[int] = ..., recvDeviceId: _Optional[int] = ..., sendDeviceId: _Optional[int] = ..., dataLength: _Optional[int] = ..., data: _Optional[str] = ..., ctrl: _Optional[int] = ..., flag: _Optional[int] = ..., seqs: _Optional[int] = ...) -> None: ...

class nav_heading_state_t(_message.Message):
    __slots__ = ["heading_state"]
    HEADING_STATE_FIELD_NUMBER: _ClassVar[int]
    heading_state: int
    def __init__(self, heading_state: _Optional[int] = ...) -> None: ...

class net_speed(_message.Message):
    __slots__ = ["download", "upload"]
    DOWNLOAD_FIELD_NUMBER: _ClassVar[int]
    UPLOAD_FIELD_NUMBER: _ClassVar[int]
    download: int
    upload: int
    def __init__(self, download: _Optional[int] = ..., upload: _Optional[int] = ...) -> None: ...

class pos_score(_message.Message):
    __slots__ = ["base_level", "base_moved", "base_moving", "base_score", "rover_level", "rover_score"]
    BASE_LEVEL_FIELD_NUMBER: _ClassVar[int]
    BASE_MOVED_FIELD_NUMBER: _ClassVar[int]
    BASE_MOVING_FIELD_NUMBER: _ClassVar[int]
    BASE_SCORE_FIELD_NUMBER: _ClassVar[int]
    ROVER_LEVEL_FIELD_NUMBER: _ClassVar[int]
    ROVER_SCORE_FIELD_NUMBER: _ClassVar[int]
    base_level: int
    base_moved: int
    base_moving: int
    base_score: int
    rover_level: int
    rover_score: int
    def __init__(self, rover_score: _Optional[int] = ..., rover_level: _Optional[int] = ..., base_score: _Optional[int] = ..., base_level: _Optional[int] = ..., base_moved: _Optional[int] = ..., base_moving: _Optional[int] = ...) -> None: ...

class remote_reset_req_t(_message.Message):
    __slots__ = ["account", "bizid", "force_reset", "magic", "reset_mode"]
    ACCOUNT_FIELD_NUMBER: _ClassVar[int]
    BIZID_FIELD_NUMBER: _ClassVar[int]
    FORCE_RESET_FIELD_NUMBER: _ClassVar[int]
    MAGIC_FIELD_NUMBER: _ClassVar[int]
    RESET_MODE_FIELD_NUMBER: _ClassVar[int]
    account: int
    bizid: int
    force_reset: int
    magic: int
    reset_mode: int
    def __init__(self, magic: _Optional[int] = ..., bizid: _Optional[int] = ..., reset_mode: _Optional[int] = ..., force_reset: _Optional[int] = ..., account: _Optional[int] = ...) -> None: ...

class remote_reset_rsp_t(_message.Message):
    __slots__ = ["bizid", "magic", "result"]
    BIZID_FIELD_NUMBER: _ClassVar[int]
    MAGIC_FIELD_NUMBER: _ClassVar[int]
    RESULT_FIELD_NUMBER: _ClassVar[int]
    bizid: int
    magic: int
    result: Command_Result
    def __init__(self, magic: _Optional[int] = ..., bizid: _Optional[int] = ..., result: _Optional[_Union[Command_Result, str]] = ...) -> None: ...

class report_info_cfg(_message.Message):
    __slots__ = ["act", "count", "no_change_period", "period", "sub", "timeout"]
    ACT_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    NO_CHANGE_PERIOD_FIELD_NUMBER: _ClassVar[int]
    PERIOD_FIELD_NUMBER: _ClassVar[int]
    SUB_FIELD_NUMBER: _ClassVar[int]
    TIMEOUT_FIELD_NUMBER: _ClassVar[int]
    act: rpt_act
    count: int
    no_change_period: int
    period: int
    sub: _containers.RepeatedScalarFieldContainer[rpt_info_type]
    timeout: int
    def __init__(self, act: _Optional[_Union[rpt_act, str]] = ..., timeout: _Optional[int] = ..., period: _Optional[int] = ..., no_change_period: _Optional[int] = ..., count: _Optional[int] = ..., sub: _Optional[_Iterable[_Union[rpt_info_type, str]]] = ...) -> None: ...

class report_info_data(_message.Message):
    __slots__ = ["basestation_info", "connect", "cutter_work_mode_info", "dev", "fw_info", "locations", "maintain", "rtk", "vio_to_app_info", "vision_point_info", "vision_statistic_info", "work"]
    BASESTATION_INFO_FIELD_NUMBER: _ClassVar[int]
    CONNECT_FIELD_NUMBER: _ClassVar[int]
    CUTTER_WORK_MODE_INFO_FIELD_NUMBER: _ClassVar[int]
    DEV_FIELD_NUMBER: _ClassVar[int]
    FW_INFO_FIELD_NUMBER: _ClassVar[int]
    LOCATIONS_FIELD_NUMBER: _ClassVar[int]
    MAINTAIN_FIELD_NUMBER: _ClassVar[int]
    RTK_FIELD_NUMBER: _ClassVar[int]
    VIO_TO_APP_INFO_FIELD_NUMBER: _ClassVar[int]
    VISION_POINT_INFO_FIELD_NUMBER: _ClassVar[int]
    VISION_STATISTIC_INFO_FIELD_NUMBER: _ClassVar[int]
    WORK_FIELD_NUMBER: _ClassVar[int]
    basestation_info: rpt_basestation_info
    connect: rpt_connect_status
    cutter_work_mode_info: rpt_cutter_rpm
    dev: rpt_dev_status
    fw_info: device_fw_info
    locations: _containers.RepeatedCompositeFieldContainer[rpt_dev_location]
    maintain: rpt_maintain
    rtk: rpt_rtk
    vio_to_app_info: vio_to_app_info_msg
    vision_point_info: _containers.RepeatedCompositeFieldContainer[vision_point_info_msg]
    vision_statistic_info: vision_statistic_info_msg
    work: rpt_work
    def __init__(self, connect: _Optional[_Union[rpt_connect_status, _Mapping]] = ..., dev: _Optional[_Union[rpt_dev_status, _Mapping]] = ..., rtk: _Optional[_Union[rpt_rtk, _Mapping]] = ..., locations: _Optional[_Iterable[_Union[rpt_dev_location, _Mapping]]] = ..., work: _Optional[_Union[rpt_work, _Mapping]] = ..., fw_info: _Optional[_Union[device_fw_info, _Mapping]] = ..., maintain: _Optional[_Union[rpt_maintain, _Mapping]] = ..., vision_point_info: _Optional[_Iterable[_Union[vision_point_info_msg, _Mapping]]] = ..., vio_to_app_info: _Optional[_Union[vio_to_app_info_msg, _Mapping]] = ..., vision_statistic_info: _Optional[_Union[vision_statistic_info_msg, _Mapping]] = ..., basestation_info: _Optional[_Union[rpt_basestation_info, _Mapping]] = ..., cutter_work_mode_info: _Optional[_Union[rpt_cutter_rpm, _Mapping]] = ...) -> None: ...

class report_info_t(_message.Message):
    __slots__ = ["dev_status"]
    DEV_STATUS_FIELD_NUMBER: _ClassVar[int]
    dev_status: dev_statue_t
    def __init__(self, dev_status: _Optional[_Union[dev_statue_t, _Mapping]] = ...) -> None: ...

class response_set_mode_t(_message.Message):
    __slots__ = ["cur_work_mode", "cur_work_time", "end_work_time", "interruptflag", "set_work_mode", "start_work_time", "statue"]
    CUR_WORK_MODE_FIELD_NUMBER: _ClassVar[int]
    CUR_WORK_TIME_FIELD_NUMBER: _ClassVar[int]
    END_WORK_TIME_FIELD_NUMBER: _ClassVar[int]
    INTERRUPTFLAG_FIELD_NUMBER: _ClassVar[int]
    SET_WORK_MODE_FIELD_NUMBER: _ClassVar[int]
    START_WORK_TIME_FIELD_NUMBER: _ClassVar[int]
    STATUE_FIELD_NUMBER: _ClassVar[int]
    cur_work_mode: int
    cur_work_time: int
    end_work_time: int
    interruptflag: int
    set_work_mode: int
    start_work_time: int
    statue: int
    def __init__(self, statue: _Optional[int] = ..., set_work_mode: _Optional[int] = ..., cur_work_mode: _Optional[int] = ..., start_work_time: _Optional[int] = ..., end_work_time: _Optional[int] = ..., interruptflag: _Optional[int] = ..., cur_work_time: _Optional[int] = ...) -> None: ...

class rpt_basestation_info(_message.Message):
    __slots__ = ["basestation_status", "connect_status_since_poweron", "ver_build", "ver_major", "ver_minor", "ver_patch"]
    BASESTATION_STATUS_FIELD_NUMBER: _ClassVar[int]
    CONNECT_STATUS_SINCE_POWERON_FIELD_NUMBER: _ClassVar[int]
    VER_BUILD_FIELD_NUMBER: _ClassVar[int]
    VER_MAJOR_FIELD_NUMBER: _ClassVar[int]
    VER_MINOR_FIELD_NUMBER: _ClassVar[int]
    VER_PATCH_FIELD_NUMBER: _ClassVar[int]
    basestation_status: int
    connect_status_since_poweron: int
    ver_build: int
    ver_major: int
    ver_minor: int
    ver_patch: int
    def __init__(self, ver_major: _Optional[int] = ..., ver_minor: _Optional[int] = ..., ver_patch: _Optional[int] = ..., ver_build: _Optional[int] = ..., basestation_status: _Optional[int] = ..., connect_status_since_poweron: _Optional[int] = ...) -> None: ...

class rpt_connect_status(_message.Message):
    __slots__ = ["ble_rssi", "connect_type", "dev_net_speed", "iot_con_status", "iot_wifi_report", "link_type", "mnet_cfg", "mnet_inet", "mnet_rssi", "used_net", "wifi_con_status", "wifi_is_available", "wifi_rssi"]
    BLE_RSSI_FIELD_NUMBER: _ClassVar[int]
    CONNECT_TYPE_FIELD_NUMBER: _ClassVar[int]
    DEV_NET_SPEED_FIELD_NUMBER: _ClassVar[int]
    IOT_CON_STATUS_FIELD_NUMBER: _ClassVar[int]
    IOT_WIFI_REPORT_FIELD_NUMBER: _ClassVar[int]
    LINK_TYPE_FIELD_NUMBER: _ClassVar[int]
    MNET_CFG_FIELD_NUMBER: _ClassVar[int]
    MNET_INET_FIELD_NUMBER: _ClassVar[int]
    MNET_RSSI_FIELD_NUMBER: _ClassVar[int]
    USED_NET_FIELD_NUMBER: _ClassVar[int]
    WIFI_CON_STATUS_FIELD_NUMBER: _ClassVar[int]
    WIFI_IS_AVAILABLE_FIELD_NUMBER: _ClassVar[int]
    WIFI_RSSI_FIELD_NUMBER: _ClassVar[int]
    ble_rssi: int
    connect_type: int
    dev_net_speed: net_speed
    iot_con_status: int
    iot_wifi_report: bool
    link_type: int
    mnet_cfg: _dev_net_pb2.MnetCfg
    mnet_inet: int
    mnet_rssi: int
    used_net: net_used_type
    wifi_con_status: int
    wifi_is_available: int
    wifi_rssi: int
    def __init__(self, connect_type: _Optional[int] = ..., ble_rssi: _Optional[int] = ..., wifi_rssi: _Optional[int] = ..., link_type: _Optional[int] = ..., mnet_rssi: _Optional[int] = ..., mnet_inet: _Optional[int] = ..., used_net: _Optional[_Union[net_used_type, str]] = ..., mnet_cfg: _Optional[_Union[_dev_net_pb2.MnetCfg, _Mapping]] = ..., dev_net_speed: _Optional[_Union[net_speed, _Mapping]] = ..., iot_wifi_report: bool = ..., iot_con_status: _Optional[int] = ..., wifi_con_status: _Optional[int] = ..., wifi_is_available: _Optional[int] = ...) -> None: ...

class rpt_cutter_rpm(_message.Message):
    __slots__ = ["current_cutter_mode", "current_cutter_rpm"]
    CURRENT_CUTTER_MODE_FIELD_NUMBER: _ClassVar[int]
    CURRENT_CUTTER_RPM_FIELD_NUMBER: _ClassVar[int]
    current_cutter_mode: int
    current_cutter_rpm: int
    def __init__(self, current_cutter_mode: _Optional[int] = ..., current_cutter_rpm: _Optional[int] = ...) -> None: ...

class rpt_dev_location(_message.Message):
    __slots__ = ["bol_hash", "pos_type", "real_pos_x", "real_pos_y", "real_toward", "zone_hash"]
    BOL_HASH_FIELD_NUMBER: _ClassVar[int]
    POS_TYPE_FIELD_NUMBER: _ClassVar[int]
    REAL_POS_X_FIELD_NUMBER: _ClassVar[int]
    REAL_POS_Y_FIELD_NUMBER: _ClassVar[int]
    REAL_TOWARD_FIELD_NUMBER: _ClassVar[int]
    ZONE_HASH_FIELD_NUMBER: _ClassVar[int]
    bol_hash: int
    pos_type: int
    real_pos_x: int
    real_pos_y: int
    real_toward: int
    zone_hash: int
    def __init__(self, real_pos_x: _Optional[int] = ..., real_pos_y: _Optional[int] = ..., real_toward: _Optional[int] = ..., pos_type: _Optional[int] = ..., zone_hash: _Optional[int] = ..., bol_hash: _Optional[int] = ...) -> None: ...

class rpt_dev_status(_message.Message):
    __slots__ = ["battery_val", "charge_state", "collector_status", "fpv_info", "last_status", "lock_state", "mnet_info", "self_check_status", "sensor_status", "sys_status", "sys_time_stamp", "vio_survival_info", "vslam_status"]
    BATTERY_VAL_FIELD_NUMBER: _ClassVar[int]
    CHARGE_STATE_FIELD_NUMBER: _ClassVar[int]
    COLLECTOR_STATUS_FIELD_NUMBER: _ClassVar[int]
    FPV_INFO_FIELD_NUMBER: _ClassVar[int]
    LAST_STATUS_FIELD_NUMBER: _ClassVar[int]
    LOCK_STATE_FIELD_NUMBER: _ClassVar[int]
    MNET_INFO_FIELD_NUMBER: _ClassVar[int]
    SELF_CHECK_STATUS_FIELD_NUMBER: _ClassVar[int]
    SENSOR_STATUS_FIELD_NUMBER: _ClassVar[int]
    SYS_STATUS_FIELD_NUMBER: _ClassVar[int]
    SYS_TIME_STAMP_FIELD_NUMBER: _ClassVar[int]
    VIO_SURVIVAL_INFO_FIELD_NUMBER: _ClassVar[int]
    VSLAM_STATUS_FIELD_NUMBER: _ClassVar[int]
    battery_val: int
    charge_state: int
    collector_status: collector_status_t
    fpv_info: fpv_to_app_info_t
    last_status: int
    lock_state: lock_state_t
    mnet_info: _dev_net_pb2.MnetInfo
    self_check_status: int
    sensor_status: int
    sys_status: int
    sys_time_stamp: int
    vio_survival_info: vio_survival_info_t
    vslam_status: int
    def __init__(self, sys_status: _Optional[int] = ..., charge_state: _Optional[int] = ..., battery_val: _Optional[int] = ..., sensor_status: _Optional[int] = ..., last_status: _Optional[int] = ..., sys_time_stamp: _Optional[int] = ..., vslam_status: _Optional[int] = ..., mnet_info: _Optional[_Union[_dev_net_pb2.MnetInfo, _Mapping]] = ..., vio_survival_info: _Optional[_Union[vio_survival_info_t, _Mapping]] = ..., collector_status: _Optional[_Union[collector_status_t, _Mapping]] = ..., lock_state: _Optional[_Union[lock_state_t, _Mapping]] = ..., self_check_status: _Optional[int] = ..., fpv_info: _Optional[_Union[fpv_to_app_info_t, _Mapping]] = ...) -> None: ...

class rpt_lora(_message.Message):
    __slots__ = ["lora_connection_status", "pair_code_channel", "pair_code_locid", "pair_code_netid", "pair_code_scan"]
    LORA_CONNECTION_STATUS_FIELD_NUMBER: _ClassVar[int]
    PAIR_CODE_CHANNEL_FIELD_NUMBER: _ClassVar[int]
    PAIR_CODE_LOCID_FIELD_NUMBER: _ClassVar[int]
    PAIR_CODE_NETID_FIELD_NUMBER: _ClassVar[int]
    PAIR_CODE_SCAN_FIELD_NUMBER: _ClassVar[int]
    lora_connection_status: int
    pair_code_channel: int
    pair_code_locid: int
    pair_code_netid: int
    pair_code_scan: int
    def __init__(self, pair_code_scan: _Optional[int] = ..., pair_code_channel: _Optional[int] = ..., pair_code_locid: _Optional[int] = ..., pair_code_netid: _Optional[int] = ..., lora_connection_status: _Optional[int] = ...) -> None: ...

class rpt_maintain(_message.Message):
    __slots__ = ["bat_cycles", "blade_used_time", "mileage", "work_time"]
    BAT_CYCLES_FIELD_NUMBER: _ClassVar[int]
    BLADE_USED_TIME_FIELD_NUMBER: _ClassVar[int]
    MILEAGE_FIELD_NUMBER: _ClassVar[int]
    WORK_TIME_FIELD_NUMBER: _ClassVar[int]
    bat_cycles: int
    blade_used_time: blade_used
    mileage: int
    work_time: int
    def __init__(self, mileage: _Optional[int] = ..., work_time: _Optional[int] = ..., bat_cycles: _Optional[int] = ..., blade_used_time: _Optional[_Union[blade_used, _Mapping]] = ...) -> None: ...

class rpt_rtk(_message.Message):
    __slots__ = ["age", "co_view_stars", "dis_status", "gps_stars", "l2_stars", "lat_std", "lon_std", "lora_info", "mqtt_rtk_info", "pos_level", "reset", "score_info", "status", "top4_total_mean"]
    AGE_FIELD_NUMBER: _ClassVar[int]
    CO_VIEW_STARS_FIELD_NUMBER: _ClassVar[int]
    DIS_STATUS_FIELD_NUMBER: _ClassVar[int]
    GPS_STARS_FIELD_NUMBER: _ClassVar[int]
    L2_STARS_FIELD_NUMBER: _ClassVar[int]
    LAT_STD_FIELD_NUMBER: _ClassVar[int]
    LON_STD_FIELD_NUMBER: _ClassVar[int]
    LORA_INFO_FIELD_NUMBER: _ClassVar[int]
    MQTT_RTK_INFO_FIELD_NUMBER: _ClassVar[int]
    POS_LEVEL_FIELD_NUMBER: _ClassVar[int]
    RESET_FIELD_NUMBER: _ClassVar[int]
    SCORE_INFO_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TOP4_TOTAL_MEAN_FIELD_NUMBER: _ClassVar[int]
    age: int
    co_view_stars: int
    dis_status: int
    gps_stars: int
    l2_stars: int
    lat_std: int
    lon_std: int
    lora_info: rpt_lora
    mqtt_rtk_info: mqtt_rtk_connect
    pos_level: int
    reset: int
    score_info: pos_score
    status: int
    top4_total_mean: int
    def __init__(self, status: _Optional[int] = ..., pos_level: _Optional[int] = ..., gps_stars: _Optional[int] = ..., age: _Optional[int] = ..., lat_std: _Optional[int] = ..., lon_std: _Optional[int] = ..., l2_stars: _Optional[int] = ..., dis_status: _Optional[int] = ..., top4_total_mean: _Optional[int] = ..., co_view_stars: _Optional[int] = ..., reset: _Optional[int] = ..., lora_info: _Optional[_Union[rpt_lora, _Mapping]] = ..., mqtt_rtk_info: _Optional[_Union[mqtt_rtk_connect, _Mapping]] = ..., score_info: _Optional[_Union[pos_score, _Mapping]] = ...) -> None: ...

class rpt_work(_message.Message):
    __slots__ = ["area", "bp_hash", "bp_info", "bp_pos_x", "bp_pos_y", "cutter_offset", "cutter_width", "init_cfg_hash", "knife_height", "man_run_speed", "nav_edit_status", "nav_heading_state", "nav_run_mode", "path_hash", "path_pos_x", "path_pos_y", "plan", "progress", "real_path_num", "test_mode_status", "ub_ecode_hash", "ub_path_hash", "ub_zone_hash"]
    AREA_FIELD_NUMBER: _ClassVar[int]
    BP_HASH_FIELD_NUMBER: _ClassVar[int]
    BP_INFO_FIELD_NUMBER: _ClassVar[int]
    BP_POS_X_FIELD_NUMBER: _ClassVar[int]
    BP_POS_Y_FIELD_NUMBER: _ClassVar[int]
    CUTTER_OFFSET_FIELD_NUMBER: _ClassVar[int]
    CUTTER_WIDTH_FIELD_NUMBER: _ClassVar[int]
    INIT_CFG_HASH_FIELD_NUMBER: _ClassVar[int]
    KNIFE_HEIGHT_FIELD_NUMBER: _ClassVar[int]
    MAN_RUN_SPEED_FIELD_NUMBER: _ClassVar[int]
    NAV_EDIT_STATUS_FIELD_NUMBER: _ClassVar[int]
    NAV_HEADING_STATE_FIELD_NUMBER: _ClassVar[int]
    NAV_RUN_MODE_FIELD_NUMBER: _ClassVar[int]
    PATH_HASH_FIELD_NUMBER: _ClassVar[int]
    PATH_POS_X_FIELD_NUMBER: _ClassVar[int]
    PATH_POS_Y_FIELD_NUMBER: _ClassVar[int]
    PLAN_FIELD_NUMBER: _ClassVar[int]
    PROGRESS_FIELD_NUMBER: _ClassVar[int]
    REAL_PATH_NUM_FIELD_NUMBER: _ClassVar[int]
    TEST_MODE_STATUS_FIELD_NUMBER: _ClassVar[int]
    UB_ECODE_HASH_FIELD_NUMBER: _ClassVar[int]
    UB_PATH_HASH_FIELD_NUMBER: _ClassVar[int]
    UB_ZONE_HASH_FIELD_NUMBER: _ClassVar[int]
    area: int
    bp_hash: int
    bp_info: int
    bp_pos_x: int
    bp_pos_y: int
    cutter_offset: float
    cutter_width: float
    init_cfg_hash: int
    knife_height: int
    man_run_speed: int
    nav_edit_status: int
    nav_heading_state: nav_heading_state_t
    nav_run_mode: int
    path_hash: int
    path_pos_x: int
    path_pos_y: int
    plan: int
    progress: int
    real_path_num: int
    test_mode_status: int
    ub_ecode_hash: int
    ub_path_hash: int
    ub_zone_hash: int
    def __init__(self, plan: _Optional[int] = ..., path_hash: _Optional[int] = ..., progress: _Optional[int] = ..., area: _Optional[int] = ..., bp_info: _Optional[int] = ..., bp_hash: _Optional[int] = ..., bp_pos_x: _Optional[int] = ..., bp_pos_y: _Optional[int] = ..., real_path_num: _Optional[int] = ..., path_pos_x: _Optional[int] = ..., path_pos_y: _Optional[int] = ..., ub_zone_hash: _Optional[int] = ..., ub_path_hash: _Optional[int] = ..., init_cfg_hash: _Optional[int] = ..., ub_ecode_hash: _Optional[int] = ..., nav_run_mode: _Optional[int] = ..., test_mode_status: _Optional[int] = ..., man_run_speed: _Optional[int] = ..., nav_edit_status: _Optional[int] = ..., knife_height: _Optional[int] = ..., nav_heading_state: _Optional[_Union[nav_heading_state_t, _Mapping]] = ..., cutter_offset: _Optional[float] = ..., cutter_width: _Optional[float] = ...) -> None: ...

class set_peripherals_t(_message.Message):
    __slots__ = ["buzz_enable"]
    BUZZ_ENABLE_FIELD_NUMBER: _ClassVar[int]
    buzz_enable: int
    def __init__(self, buzz_enable: _Optional[int] = ...) -> None: ...

class special_mode_t(_message.Message):
    __slots__ = ["berthing_mode", "stair_mode", "violent_mode"]
    BERTHING_MODE_FIELD_NUMBER: _ClassVar[int]
    STAIR_MODE_FIELD_NUMBER: _ClassVar[int]
    VIOLENT_MODE_FIELD_NUMBER: _ClassVar[int]
    berthing_mode: int
    stair_mode: int
    violent_mode: int
    def __init__(self, stair_mode: _Optional[int] = ..., violent_mode: _Optional[int] = ..., berthing_mode: _Optional[int] = ...) -> None: ...

class systemRapidStateTunnel_msg(_message.Message):
    __slots__ = ["rapid_state_data", "vio_to_app_info", "vision_point_info", "vision_statistic_info"]
    RAPID_STATE_DATA_FIELD_NUMBER: _ClassVar[int]
    VIO_TO_APP_INFO_FIELD_NUMBER: _ClassVar[int]
    VISION_POINT_INFO_FIELD_NUMBER: _ClassVar[int]
    VISION_STATISTIC_INFO_FIELD_NUMBER: _ClassVar[int]
    rapid_state_data: _containers.RepeatedScalarFieldContainer[int]
    vio_to_app_info: vio_to_app_info_msg
    vision_point_info: _containers.RepeatedCompositeFieldContainer[vision_point_info_msg]
    vision_statistic_info: vision_statistic_info_msg
    def __init__(self, rapid_state_data: _Optional[_Iterable[int]] = ..., vision_point_info: _Optional[_Iterable[_Union[vision_point_info_msg, _Mapping]]] = ..., vio_to_app_info: _Optional[_Union[vio_to_app_info_msg, _Mapping]] = ..., vision_statistic_info: _Optional[_Union[vision_statistic_info_msg, _Mapping]] = ...) -> None: ...

class systemTardStateTunnel_msg(_message.Message):
    __slots__ = ["tard_state_data"]
    TARD_STATE_DATA_FIELD_NUMBER: _ClassVar[int]
    tard_state_data: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, tard_state_data: _Optional[_Iterable[int]] = ...) -> None: ...

class systemTmpCycleTx_msg(_message.Message):
    __slots__ = ["cycle_tx_data"]
    CYCLE_TX_DATA_FIELD_NUMBER: _ClassVar[int]
    cycle_tx_data: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, cycle_tx_data: _Optional[_Iterable[int]] = ...) -> None: ...

class systemUpdateBuf_msg(_message.Message):
    __slots__ = ["update_buf_data"]
    UPDATE_BUF_DATA_FIELD_NUMBER: _ClassVar[int]
    update_buf_data: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, update_buf_data: _Optional[_Iterable[int]] = ...) -> None: ...

class user_set_blade_used_warn_time(_message.Message):
    __slots__ = ["blade_used_warn_time"]
    BLADE_USED_WARN_TIME_FIELD_NUMBER: _ClassVar[int]
    blade_used_warn_time: int
    def __init__(self, blade_used_warn_time: _Optional[int] = ...) -> None: ...

class vio_survival_info_t(_message.Message):
    __slots__ = ["vio_survival_distance"]
    VIO_SURVIVAL_DISTANCE_FIELD_NUMBER: _ClassVar[int]
    vio_survival_distance: float
    def __init__(self, vio_survival_distance: _Optional[float] = ...) -> None: ...

class vio_to_app_info_msg(_message.Message):
    __slots__ = ["brightness", "detect_feature_num", "heading", "track_feature_num", "vio_state", "x", "y"]
    BRIGHTNESS_FIELD_NUMBER: _ClassVar[int]
    DETECT_FEATURE_NUM_FIELD_NUMBER: _ClassVar[int]
    HEADING_FIELD_NUMBER: _ClassVar[int]
    TRACK_FEATURE_NUM_FIELD_NUMBER: _ClassVar[int]
    VIO_STATE_FIELD_NUMBER: _ClassVar[int]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    brightness: int
    detect_feature_num: int
    heading: float
    track_feature_num: int
    vio_state: int
    x: float
    y: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., heading: _Optional[float] = ..., vio_state: _Optional[int] = ..., brightness: _Optional[int] = ..., detect_feature_num: _Optional[int] = ..., track_feature_num: _Optional[int] = ...) -> None: ...

class vision_point_info_msg(_message.Message):
    __slots__ = ["label", "num", "vision_point"]
    LABEL_FIELD_NUMBER: _ClassVar[int]
    NUM_FIELD_NUMBER: _ClassVar[int]
    VISION_POINT_FIELD_NUMBER: _ClassVar[int]
    label: int
    num: int
    vision_point: _containers.RepeatedCompositeFieldContainer[vision_point_msg]
    def __init__(self, label: _Optional[int] = ..., num: _Optional[int] = ..., vision_point: _Optional[_Iterable[_Union[vision_point_msg, _Mapping]]] = ...) -> None: ...

class vision_point_msg(_message.Message):
    __slots__ = ["x", "y", "z"]
    X_FIELD_NUMBER: _ClassVar[int]
    Y_FIELD_NUMBER: _ClassVar[int]
    Z_FIELD_NUMBER: _ClassVar[int]
    x: float
    y: float
    z: float
    def __init__(self, x: _Optional[float] = ..., y: _Optional[float] = ..., z: _Optional[float] = ...) -> None: ...

class vision_statistic_info_msg(_message.Message):
    __slots__ = ["num", "timestamp", "vision_statistics"]
    NUM_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMP_FIELD_NUMBER: _ClassVar[int]
    VISION_STATISTICS_FIELD_NUMBER: _ClassVar[int]
    num: int
    timestamp: float
    vision_statistics: _containers.RepeatedCompositeFieldContainer[vision_statistic_msg]
    def __init__(self, timestamp: _Optional[float] = ..., num: _Optional[int] = ..., vision_statistics: _Optional[_Iterable[_Union[vision_statistic_msg, _Mapping]]] = ...) -> None: ...

class vision_statistic_msg(_message.Message):
    __slots__ = ["mean", "var"]
    MEAN_FIELD_NUMBER: _ClassVar[int]
    VAR_FIELD_NUMBER: _ClassVar[int]
    mean: float
    var: float
    def __init__(self, mean: _Optional[float] = ..., var: _Optional[float] = ...) -> None: ...

class work_mode_t(_message.Message):
    __slots__ = ["work_mode"]
    WORK_MODE_FIELD_NUMBER: _ClassVar[int]
    work_mode: int
    def __init__(self, work_mode: _Optional[int] = ...) -> None: ...

class Operation(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class OffPartId(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class QCAppTestId(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class rtk_used_type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class net_used_type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class rpt_info_type(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class rpt_act(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []

class Command_Result(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = []
