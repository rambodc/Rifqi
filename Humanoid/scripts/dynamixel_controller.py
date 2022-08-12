from enum import Enum
from typing import List
from datetime import datetime
import os

# Import suitable modules based on current OS (Windows/Mac)
if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import *  # Uses Dynamixel SDK library

################################################################################################################################
'''
Global Config Parser
'''
GLOBAL_COMM_CONFIG = op('GlobalCommConfig')
GLOBAL_MOTORS_CONFIG = op('GlobalMotorsConfig')

class MotorConfigNotFound(Exception):
    pass

def get_port_name() -> str:
    return str(GLOBAL_COMM_CONFIG[1,1].val)

def get_baudrate() -> int:
    return int(GLOBAL_COMM_CONFIG[2,1].val)

def get_protocol() -> float:
    return float(GLOBAL_COMM_CONFIG[3,1].val)

def get_motor_num_from_config():
    return int(GLOBAL_MOTORS_CONFIG.numRows - 1)

def get_motor_type(motor_id: int) -> str:
    for i in range(1, GLOBAL_MOTORS_CONFIG.numRows):
        if int(GLOBAL_MOTORS_CONFIG[i, 0]) == motor_id:
            return str(GLOBAL_MOTORS_CONFIG[i, 1].val)

    raise MotorConfigNotFound(f"Motor type not found for ID: {motor_id}")


################################################################################################################################
'''
Motor and Control Table Class
'''
class MotorTypeNotSupported(Exception):
    pass

class OperatingMode(Enum):
    VELOCITY_CONTROL            = 1
    POSITION_CONTROL            = 3
    EXTENDED_POSITION_CONTROL   = 4
    PWM_CONTROL                 = 16

class DataAccess(Enum):
    READ_AND_WRITE = 1
    READ = 2

class ControlData:
    def __init__(self, address: int, data_size_byte: int, data_access: DataAccess = DataAccess.READ) -> None:
        self.Address = address
        self.DataSize = data_size_byte
        self.DataAccess = data_access

class ControlTable:
    def __init__(self, motor_type: str) -> None:
        if motor_type == 'X_SERIES' or motor_type == 'MX_SERIES':
            self.OperatingMode         = ControlData(11, 1, DataAccess.READ_AND_WRITE)
            self.Torque                = ControlData(64, 1, DataAccess.READ_AND_WRITE)
            self.GoalVelocity          = ControlData(104, 4, DataAccess.READ_AND_WRITE)
            self.GoalPosition          = ControlData(116, 4, DataAccess.READ_AND_WRITE)
            self.PresentPosition       = ControlData(132, 4, DataAccess.READ_AND_WRITE)
        elif motor_type == 'PRO_SERIES':
            raise NotImplementedError
        elif motor_type == 'P_SERIES' or motor_type == 'PRO_A_SERIES':
            raise NotImplementedError
        elif motor_type == 'XL320':
            raise NotImplementedError
        else:
            raise MotorTypeNotSupported(
                f"motor_type: {motor_type} is not supported. Supported motor type: X_SERIES, MX_SERIES, PRO_SERIES, P_SERIES, PRO_A_SERIES and XL320")

class Motor:
    def __init__(self, id: int, motor_type: str) -> None:
        self.ID = id
        self.ControlTable = ControlTable(motor_type)

################################################################################################################################
# Dynamixel
PORT_HANDLER = PortHandler(get_port_name())
PACKET_HANDLER = PacketHandler(get_protocol())

class CommError(Exception):
    pass

def open_port():
    if PORT_HANDLER.openPort():
        print(f"Port {get_port_name()} successfully opened")
    else:
        raise CommError(f"Failed to open {get_port_name()} port, make sure port is available.")

    if PORT_HANDLER.setBaudRate(get_baudrate()):
        print(f"Baudrate set to {get_baudrate()}")
    else:
        raise CommError(f"Failed to set baudrate to {get_baudrate()} on {get_port_name()}")

def close_port():
    PORT_HANDLER.closePort()

def test_reading_configs():
    print(f"port: {get_port_name()}")
    print(f"baudrate: {get_baudrate()}")
    print(f"protocol: {get_protocol()}")
    print(f"\nnumber of motors from GlobalMotorsConfig: {get_motor_num_from_config()}")

def test_broadcast_ping():
    dxl_data_list, dxl_comm_result = PACKET_HANDLER.broadcastPing(PORT_HANDLER)

    if dxl_comm_result != COMM_SUCCESS:
        tx_rx_res = PACKET_HANDLER.getTxRxResult(dxl_comm_result)
        print(f"{tx_rx_res}")
        raise CommError(tx_rx_res)

    print("Detected Dynamixel: ")
    for dxl_id in dxl_data_list:
        print(f"[ID: {dxl_id}] model version: {dxl_data_list.get(dxl_id)[0]} | firmware version: {dxl_data_list.get(dxl_id)[1]}")

def broadcast_ping() -> List[int]:
    '''
    run broadcast ping to find all connected motors on the port
    '''
    dxl_data_list, dxl_comm_result = PACKET_HANDLER.broadcastPing(PORT_HANDLER)

    if dxl_comm_result != COMM_SUCCESS:
        tx_rx_res = PACKET_HANDLER.getTxRxResult(dxl_comm_result)
        print(f"{tx_rx_res}")
        raise CommError(tx_rx_res)

    motors_id = []
    for dxl_id in dxl_data_list:
        motors_id.append(dxl_id)

    for motor_id in motors_id:
        RAM_TABLE.appendRow([motor_id])
        EEPROM_TABLE.appendRow([motor_id])

    return motors_id

def dummy_broadcast_ping() -> List[int]:
    '''
    Broadcast ping simulation for getting number of connected motors and ther id's
    '''
    motors_id = [1, 2]

    for motor_id in motors_id:
        RAM_TABLE.appendRow([motor_id])
        EEPROM_TABLE.appendRow([motor_id])

    return motors_id

################################################################################################################################
# Global variable for defining button name, it should start with capital letter
# and using only alphabet without space
READ_EEPROM = 'Readeeprom'
WRITE_EEPROP = 'Writeeeprom'
READ_RAM = 'Readram'
WRITE_RAM = 'Writeram'
WRITE_TORQUE = 'Writetorque'
READ_TORQUE = 'Readtorque'
READ_CURRENT_POSITION = 'Readposition'
WRITE_GOAL_POSITION = 'Writegoalposition'
WRITE_GOAL_VELOCITY = 'Writegoalvelocity'

MOTORS: List[Motor] = []

CONTROLLER_OP = op('DynamixelController')
RAM_TABLE = op('DynamixelMotorsRAM')
EEPROM_TABLE = op('DynamixelMotorsEEPROM')
DEBUG_TABLE = op('Debug')

# Dictionary for holding Row index and variable name
class EEPROM(Enum):
    ID                          = 0
    MODEL_NUMBER                = 1
    MODEL_INFORMATION           = 2
    FIRMWARE_VERSION            = 3
    BAUD_RATE                   = 4
    RETURN_DELAY_TIME           = 5
    DRIVE_MODE                  = 6
    OPERATING_MODE              = 7
    SECONDARY_SHADOW_ID         = 8
    PROTOCOL_TYPE               = 9
    HOMING_OFFSET               = 10
    MOVING_THRESHOLD            = 11
    TEMPERATURE_LIMIT           = 12
    MAX_VOLTAGE_LIMIT           = 13
    MIN_VOLTAGE_LIMIT           = 14
    PWM_LIMIT                   = 15
    VELOCITY_LIMIT              = 16
    MAX_POSITION_LIMIT          = 17
    MIN_POSITION_LIMIT          = 18
    STARTUP_CONFIGURATION       = 19
    SHUTDOWN                    = 20

EEPROM_ROW_NAME_DICT = {
    EEPROM.ID                    : "ID",
    EEPROM.MODEL_NUMBER          : "Model Number",
    EEPROM.MODEL_INFORMATION     : "Model Information",
    EEPROM.FIRMWARE_VERSION      : "Firmware Version",
    EEPROM.BAUD_RATE             : "Baud Rate",
    EEPROM.RETURN_DELAY_TIME     : "Return Delay Time",
    EEPROM.DRIVE_MODE            : "Drive Mode",
    EEPROM.OPERATING_MODE        : "Operating Mode",
    EEPROM.SECONDARY_SHADOW_ID   : "Secondary(Shadow) ID",
    EEPROM.PROTOCOL_TYPE         : "Protocol Type",
    EEPROM.HOMING_OFFSET         : "Homing Offset",
    EEPROM.MOVING_THRESHOLD      : "Moving Threshold",
    EEPROM.TEMPERATURE_LIMIT     : "Temperature Limit",
    EEPROM.MAX_VOLTAGE_LIMIT     : "Max Voltage Limit",
    EEPROM.MIN_VOLTAGE_LIMIT     : "Min Voltage Limit",
    EEPROM.PWM_LIMIT             : "PWM Limit",
    EEPROM.VELOCITY_LIMIT        : "Velocity Limit",
    EEPROM.MAX_POSITION_LIMIT    : "Max Position Limit",
    EEPROM.MIN_POSITION_LIMIT    : "Min Position Limit",
    EEPROM.STARTUP_CONFIGURATION : "Startup Configuration",
    EEPROM.SHUTDOWN              : "Shutdown"
}

class RAM(Enum):
    ID                          = 0
    TORQUE                      = 1
    LED                         = 2
    STATUS_RETURN_LEVEL         = 3
    REGISTERED_INSTRUCTION      = 4
    HARDWARE_ERROR_STATUS       = 5
    VELOCITY_I_GAIN             = 6
    VELOCITY_P_GAIN             = 7
    POSITION_D_GAIN             = 8
    POSITION_I_GAIN             = 9
    POSITION_P_GAIN             = 10
    FEEDFORWARD_2ND_GAIN        = 11
    FEEDFORWARD_1ST_GAIN        = 12
    BUS_WATCHDOG                = 13
    GOAL_PWM                    = 14
    GOAL_VELOCITY               = 15
    PROFILE_ACCELERATION        = 16
    PROFILE_VELOCITY            = 17
    GOAL_POSITION               = 18
    REALTIME_TICK               = 19
    MOVING                      = 20
    MOVING_STATUS               = 21
    PRESENT_PWM                 = 22
    PRESENT_LOAD                = 23
    PRESENT_VELOCITY            = 24
    PRESENT_POSITION            = 25
    VELOCITY_TRAJECTORY         = 26
    POSITION_TRAJECTORY         = 27
    PRESENT_INPUT_VOLTAGE       = 28
    PRESENT_TEMPERATURE         = 29
    BACKUP_READY                = 30

RAM_ROW_NAME_DICT = {
    RAM.ID                          : "ID",
    RAM.TORQUE                      : "Torque",
    RAM.LED                         : "LED",
    RAM.STATUS_RETURN_LEVEL         : "Status Return Level",
    RAM.REGISTERED_INSTRUCTION      : "Registered Instruction",
    RAM.HARDWARE_ERROR_STATUS       : "Hardware Error Status",
    RAM.VELOCITY_I_GAIN             : "Velocity I Gain",
    RAM.VELOCITY_P_GAIN             : "Velocity P Gain",
    RAM.POSITION_D_GAIN             : "Position D Gain",
    RAM.POSITION_I_GAIN             : "Position I Gain",
    RAM.POSITION_P_GAIN             : "Position P Gain",
    RAM.FEEDFORWARD_2ND_GAIN        : "Feedforward 2nd Gain",
    RAM.FEEDFORWARD_1ST_GAIN        : "Feedforward 1st Gain",
    RAM.BUS_WATCHDOG                : "Bus Watchdog",
    RAM.GOAL_PWM                    : "Goal PWM",
    RAM.GOAL_VELOCITY               : "Goal Velocity",
    RAM.PROFILE_ACCELERATION        : "Profile Acceleration",
    RAM.PROFILE_VELOCITY            : "Profile Velocity",
    RAM.GOAL_POSITION               : "Goal Position",
    RAM.REALTIME_TICK               : "Realtime Tick",
    RAM.MOVING                      : "Moving",
    RAM.MOVING_STATUS               : "Moving Status",
    RAM.PRESENT_PWM                 : "Present PWM",
    RAM.PRESENT_LOAD                : "Present Load",
    RAM.PRESENT_VELOCITY            : "Present Velocity",
    RAM.PRESENT_POSITION            : "Present Position",
    RAM.VELOCITY_TRAJECTORY         : "Velocity Trajectory",
    RAM.POSITION_TRAJECTORY         : "Position Trajectory",
    RAM.PRESENT_INPUT_VOLTAGE       : "Present Input Voltage",
    RAM.PRESENT_TEMPERATURE         : "Present Temperature",
    RAM.BACKUP_READY                : "Backup Ready"
}

def build_motors_selector_page(script_op):
    page_motor_selector = script_op.appendCustomPage('Selector')
    global MOTORS
    for motor in MOTORS:
        page_motor_selector.appendToggle(f'Motor{motor.ID}', label=f'Motor {motor.ID}')

def build_eeprom_page(script_op):
    page_EEPROM = script_op.appendCustomPage('EEPROM')
    page_EEPROM.appendPulse(READ_EEPROM, label='Read EEPROM')
    page_EEPROM.appendPulse(WRITE_EEPROP, label='Write EEPROM')

def build_ram_page(script_op):
    page_RAM = script_op.appendCustomPage('RAM')
    page_RAM.appendPulse(READ_RAM, label='Read RAM')
    page_RAM.appendPulse(WRITE_RAM, label='Write RAM')

def build_torque_page(script_op):
    page_torque = script_op.appendCustomPage('Torque')
    page_torque.appendPulse(READ_TORQUE, label='Read Torque')
    page_torque.appendPulse(WRITE_TORQUE, label='Write Torque')

def build_position_page(script_op):
    page_position = script_op.appendCustomPage('Position')
    page_position.appendPulse(READ_CURRENT_POSITION, label='Read Current Position')
    page_position.appendPulse(WRITE_GOAL_POSITION, label='Write Goal Position')

def build_velocity_page(script_op):
    page_velocity = script_op.appendCustomPage('Velocity')
    page_velocity.appendPulse(WRITE_GOAL_VELOCITY, label='Write Goal Velocity')

def fill_initial_eeprom_table():
    EEPROM_TABLE.clear()
    EEPROM_TABLE.appendCol()
    EEPROM_TABLE.appendRow([row_name for key, row_name in EEPROM_ROW_NAME_DICT.items()])

def fill_initial_ram_table():
    RAM_TABLE.clear()
    RAM_TABLE.appendCol()
    RAM_TABLE.appendRow([row_name for key, row_name in RAM_ROW_NAME_DICT.items()])

def fill_debug_info(messages: List[str]):
    DEBUG_TABLE.clear()
    DEBUG_TABLE.appendCol()

    for message in messages:
        DEBUG_TABLE.appendRow([message])

def update_connected_motors(motors_id):
    global MOTORS
    MOTORS.clear()
    for motor_id in motors_id:
        MOTORS.append(Motor(motor_id, get_motor_type(motor_id)))

def test_list_motors():
    messages = []
    global MOTORS
    for motor in MOTORS:
        messages.append(motor.ID)
    fill_debug_info(messages)

def get_selected_motors() -> List[Motor]:
    selected_motors = []

    global MOTORS
    for motor in MOTORS:
        is_selected = CONTROLLER_OP.par[f'Motor{motor.ID}'].val
        if is_selected:
            selected_motors.append(motor)

    return selected_motors

def get_row_index_by_motor_id(motor_id: int):
    for index in range(1, RAM_TABLE.numRows):
        if motor_id == int(RAM_TABLE[index, 0]):
            return index

def write_to_table(val, table, row: int, col: int):
    table[row, col] = str(val)

def read_from_table(table, row: int, col: int) -> str:
    return table[row, col]

def check_comm_result(comm_result, error):
    if comm_result != COMM_SUCCESS:
        raise CommError(f"{PACKET_HANDLER.getTxRxResult(comm_result)}")
    elif error != 0:
        raise CommError(f"{PACKET_HANDLER.getRxPacketError(error)}")

def handler_read_torque():
    motors = get_selected_motors()

    for motor in motors:
        torque, comm_result, error = PACKET_HANDLER.read1ByteTxRx(PORT_HANDLER, motor.ID, motor.ControlTable.Torque.Address)
        check_comm_result(comm_result, error)
        write_to_table(torque, RAM_TABLE, get_row_index_by_motor_id(motor.ID), RAM.TORQUE.value)

def handler_write_torque():
    motors = get_selected_motors()

    for motor in motors:
        torque = 0
        try:
            torque = int(read_from_table(RAM_TABLE, get_row_index_by_motor_id(motor.ID), RAM.TORQUE.value))
        except ValueError:
            print(f"MotorID {motor.ID} torque value is empty disabling motor torque instead")

        comm_result, error = PACKET_HANDLER.write1ByteTxRx(PORT_HANDLER, motor.ID, motor.ControlTable.Torque.Address, bool(torque))

        check_comm_result(comm_result, error)
        print(f"Writing Torque: {torque} to motor_ID: {motor.ID}")

def handler_read_current_position():
    motors = get_selected_motors()
    groupBulkRead = GroupBulkRead(PORT_HANDLER, PACKET_HANDLER)

    # Add parameter storage for present position of all motors
    for motor in motors:
        addparam_result = groupBulkRead.addParam(motor.ID, motor.ControlTable.PresentPosition.Address, motor.ControlTable.PresentPosition.DataSize)

        if addparam_result != True:
            raise CommError(f"[ID:{motor.ID}] groupBulkRead addParam PresentPosition failed")

    # send bulk read request to port
    comm_result = groupBulkRead.txRxPacket()
    if comm_result != COMM_SUCCESS:
        raise CommError(f"{PACKET_HANDLER.getTxRxResult(comm_result)}")

    # retrieve data and write it to table for each selected motor
    for motor in motors:
        getdata_result = groupBulkRead.isAvailable(motor.ID, motor.ControlTable.PresentPosition.Address, motor.ControlTable.PresentPosition.DataSize)
        if getdata_result != True:
            raise CommError(f"[ID:{motor.ID}] groupBulkRead getdata failed")

        # Get present position value
        present_position = groupBulkRead.getData(motor.ID, motor.ControlTable.PresentPosition.Address, motor.ControlTable.PresentPosition.DataSize)
        write_to_table(present_position, RAM_TABLE, get_row_index_by_motor_id(motor.ID), RAM.PRESENT_POSITION.value)

    # Clear bulkread parameter storage
    groupBulkRead.clearParam()

def set_operating_mode(motor: Motor, operating_mode: OperatingMode):
    comm_result, error = PACKET_HANDLER.write1ByteTxRx(PORT_HANDLER, motor.ID, motor.ControlTable.OperatingMode.Address, operating_mode.value)
    check_comm_result(comm_result, error)
    print(f"Setting motor: {motor.ID} operating mode to {operating_mode}")

def handler_write_goal_position():
    motors = get_selected_motors()
    groupBulkWrite = GroupBulkWrite(PORT_HANDLER, PACKET_HANDLER)

    for motor in motors:
        goal_position = 0
        try:
            goal_position = int(read_from_table(RAM_TABLE, get_row_index_by_motor_id(motor.ID), RAM.GOAL_POSITION.value))
        except ValueError:
            print(f"MotorID {motor.ID} goal position value is empty sending 0 position instead")

        param_goal_position = [ DXL_LOBYTE( DXL_LOWORD( goal_position ) ),
                                DXL_HIBYTE( DXL_LOWORD( goal_position ) ),
                                DXL_LOBYTE( DXL_HIWORD( goal_position ) ),
                                DXL_HIBYTE( DXL_HIWORD( goal_position ) )]

        addparam_result = groupBulkWrite.addParam(
                            motor.ID,
                            motor.ControlTable.GoalPosition.Address,
                            motor.ControlTable.GoalPosition.DataSize,
                            param_goal_position)

        if addparam_result != True:
            raise CommError(f"[ID:{motor.ID}] groupBulkRead addParam GoalPosition failed")

    # Send goal velocity in bulk (all command will be executed at the same time)
    comm_result = groupBulkWrite.txPacket()
    if comm_result != COMM_SUCCESS:
        raise CommError(f"{PACKET_HANDLER.getTxRxResult(comm_result)}")

    # Clear bulkwrite parameter storage
    groupBulkWrite.clearParam()

def handler_write_goal_velocity():
    motors = get_selected_motors()
    groupBulkWrite = GroupBulkWrite(PORT_HANDLER, PACKET_HANDLER)

    # Add parameter storage for present position of all motors
    for motor in motors:
        goal_velocity = 0
        try:
            goal_velocity = int(read_from_table(RAM_TABLE, get_row_index_by_motor_id(motor.ID), RAM.GOAL_VELOCITY.value))
        except ValueError:
            print(f"MotorID {motor.ID} goal velocity value is empty sending 0 velocity instead")

        param_goal_velocity = [ DXL_LOBYTE( DXL_LOWORD( goal_velocity ) ),
                                DXL_HIBYTE( DXL_LOWORD( goal_velocity ) ),
                                DXL_LOBYTE( DXL_HIWORD( goal_velocity ) ),
                                DXL_HIBYTE( DXL_HIWORD( goal_velocity ) )]

        addparam_result = groupBulkWrite.addParam(
                            motor.ID,
                            motor.ControlTable.GoalVelocity.Address,
                            motor.ControlTable.GoalVelocity.DataSize,
                            param_goal_velocity)

        if addparam_result != True:
            raise CommError(f"[ID:{motor.ID}] groupBulkRead addParam GoalVelocity failed")

    # Send goal velocity in bulk (all command will be executed at the same time)
    comm_result = groupBulkWrite.txPacket()
    if comm_result != COMM_SUCCESS:
        raise CommError(f"{PACKET_HANDLER.getTxRxResult(comm_result)}")

    # Clear bulkwrite parameter storage
    groupBulkWrite.clearParam()

def handler_read_eeprom():
    # read operating mode only for now
    motors = get_selected_motors()

    for motor in motors:
        operating_mode, comm_result, error = PACKET_HANDLER.read1ByteTxRx(PORT_HANDLER, motor.ID, motor.ControlTable.OperatingMode.Address)
        check_comm_result(comm_result, error)
        write_to_table(operating_mode, EEPROM_TABLE, get_row_index_by_motor_id(motor.ID), EEPROM.OPERATING_MODE.value)

def handler_write_eeprom():
    # write operating mode only for now
    motors = get_selected_motors()

    for motor in motors:
        operating_mode = 0
        try:
            operating_mode = int(read_from_table(EEPROM_TABLE, get_row_index_by_motor_id(motor.ID), EEPROM.OPERATING_MODE.value))
        except ValueError:
            print(f"MotorID {motor.ID} operating mode value is empty not writing any data to the motor")
            continue

        comm_result, error = PACKET_HANDLER.write1ByteTxRx(PORT_HANDLER, motor.ID, motor.ControlTable.OperatingMode.Address, operating_mode)
        check_comm_result(comm_result, error)

################################################################################################################################
# Operator callbacks
def onSetupParameters(scriptOp):
    '''
    Setting up user interface and filling initial EEPROM and RAM from connected motors
    '''
    # Check if the port is open. Close and re-open it
    if PORT_HANDLER.is_open:
        close_port()
    open_port()

    fill_initial_eeprom_table()
    fill_initial_ram_table()

    # search for available motors
    # motors_id = dummy_broadcast_ping()
    motors_id = broadcast_ping()

    # create motors based on GlobalMotorsConfig and check wether user the ID is present in the network
    update_connected_motors(motors_id)

    build_motors_selector_page(scriptOp)
    build_eeprom_page(scriptOp)
    build_ram_page(scriptOp)
    build_torque_page(scriptOp)
    build_position_page(scriptOp)
    build_velocity_page(scriptOp)

    return

def onPulse(par):
    '''
    called whenever custom pulse parameter is pushed
    '''
    button_name = par.name
    if button_name == READ_TORQUE:
        handler_read_torque()
    elif button_name == WRITE_TORQUE:
        handler_write_torque()
    elif button_name == READ_CURRENT_POSITION:
        handler_read_current_position()
    elif button_name == WRITE_GOAL_POSITION:
        handler_write_goal_position()
    elif button_name == WRITE_GOAL_VELOCITY:
        handler_write_goal_velocity()
    elif button_name == READ_EEPROM:
        handler_read_eeprom()
    elif button_name == WRITE_EEPROP:
        handler_write_eeprom()
    elif button_name == READ_RAM:
        raise NotImplementedError
    elif button_name == WRITE_RAM:
        raise NotImplementedError

    return

def onCook(scriptOp):
    scriptOp.clear()
    # print(datetime.now())
    handler_read_current_position()
    return
