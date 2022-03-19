from enum import Enum
from typing import List
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
            self.TorqueEnable          = ControlData(64, 1, DataAccess.READ_AND_WRITE)
            self.GoalVelocity          = ControlData(116, 4, DataAccess.READ_AND_WRITE)
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
    dxl_data_list, dxl_comm_result = PACKET_HANDLER.broadcastPing(PORT_HANDLER)

    if dxl_comm_result != COMM_SUCCESS:
        tx_rx_res = PACKET_HANDLER.getTxRxResult(dxl_comm_result)
        print(f"{tx_rx_res}")
        raise CommError(tx_rx_res)

    motors_id = []
    for dxl_id in dxl_data_list:
        motors_id.append(dxl_id)

    return motors_id

def dummy_broadcast_ping() -> List[int]:
    motors_id = [1, 2, 15]

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
WRITE_GOAL_VELOCITY = 'Writegoalvelocity'

MOTORS: List[Motor] = []

RAM_TABLE = op('DynamixelMotorsRAM')
EEPROM_TABLE = op('DynamixelMotorsEEPROM')
DEBUG_TABLE = op('Debug')

COUNTER = 0

def build_motors_selector_page(script_op):
    page_motor_selector = script_op.appendCustomPage('Motor Selector')

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
    page_position.appendPulse(READ_CURRENT_POSITION, label='Read Position')

def build_velocity_page(script_op):
    page_velocity = script_op.appendCustomPage('Velocity')
    page_velocity.appendPulse(WRITE_GOAL_VELOCITY, label='Write Goal Velocity')

def fill_initial_eeprom_table():
    EEPROM_TABLE.clear()
    EEPROM_TABLE.appendCol()
    EEPROM_TABLE.appendRow(['ID','Model Number','Model Information','Firmware Version','Baud Rate','Return Delay Time','Drive Mode','Operating Mode','Secondary(Shadow) ID','Protocol Type','Homing Offset','Moving Threshold','Temperature Limit','Max Voltage Limit','Min Voltage Limit','PWM Limit','Velocity Limit','Max Position Limit','Min Position Limit','Startup Configuration','Shutdown'])

def fill_initial_ram_table():
    RAM_TABLE.clear()
    RAM_TABLE.appendCol()
    RAM_TABLE.appendRow(['ID','Torque Enable','LED','Status Return Level','Registered Instruction','Hardware Error Status','Velocity I Gain','Velocity P Gain','Position D Gain','Position I Gain','Position P Gain','Feedforward 2nd Gain','Feedforward 1st Gain','Bus Watchdog','Goal PWM','Goal Velocity','Profile Acceleration','Profile Velocity','Goal Position','Realtime Tick','Moving','Moving Status','Present PWM','Present Load','Present Velocity','Present Position','Velocity Trajectory','Position Trajectory','Present Input Voltage','Present Temperature','Backup Ready'])

def fill_debug_info(messages: List[str]):
    DEBUG_TABLE.clear()
    DEBUG_TABLE.appendCol()

    for message in messages:
        DEBUG_TABLE.appendRow([message])

def get_connected_motors(motors_id):
    MOTORS.clear()
    for motor_id in motors_id:
        MOTORS.append(Motor(motor_id, get_motor_type(motor_id)))

def test_list_motors():
    messages = []
    for motor in MOTORS:
        messages.append(motor.ID)
    fill_debug_info(messages)

def onSetupParameters(scriptOp):
    '''
    Setting up user interface and filling initial EEPROM and RAM from connected motors
    '''
    fill_initial_eeprom_table()
    fill_initial_ram_table()
    # search for available motors
    motors_id = dummy_broadcast_ping()

    # create motors based on GlobalMotorsConfig and check wether user the ID is present in the network
    get_connected_motors(motors_id)

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
    global COUNTER
    COUNTER += 1

    button_name = par.name
    if button_name == READ_TORQUE:
        pass
    elif button_name == WRITE_TORQUE:
        pass
    elif button_name == READ_CURRENT_POSITION:
        pass
    elif button_name == READ_EEPROM:
        raise NotImplementedError
    elif button_name == WRITE_EEPROP:
        raise NotImplementedError
    elif button_name == READ_RAM:
        raise NotImplementedError
    elif button_name == WRITE_RAM:
        raise NotImplementedError

    return

def onCook(scriptOp):
    scriptOp.clear()
    return
