from enum import Enum
from typing import List


################################################################################################################################
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
    eeprom_table = op('DynamixelMotorsEEPROM')
    eeprom_table.clear()
    eeprom_table.appendCol()
    eeprom_table.appendRow(['ID','Model Number','Model Information','Firmware Version','Baud Rate','Return Delay Time','Drive Mode','Operating Mode','Secondary(Shadow) ID','Protocol Type','Homing Offset','Moving Threshold','Temperature Limit','Max Voltage Limit','Min Voltage Limit','PWM Limit','Velocity Limit','Max Position Limit','Min Position Limit','Startup Configuration','Shutdown'])
    eeprom_table.appendRow()

def fill_initial_ram_table():
    ram_table = op('DynamixelMotorsRAM')
    ram_table.clear()
    ram_table.appendCol()
    ram_table.appendRow(['ID','Torque Enable','LED','Status Return Level','Registered Instruction','Hardware Error Status','Velocity I Gain','Velocity P Gain','Position D Gain','Position I Gain','Position P Gain','Feedforward 2nd Gain','Feedforward 1st Gain','Bus Watchdog','Goal PWM','Goal Velocity','Profile Acceleration','Profile Velocity','Goal Position','Realtime Tick','Moving','Moving Status','Present PWM','Present Load','Present Velocity','Present Position','Velocity Trajectory','Position Trajectory','Present Input Voltage','Present Temperature','Backup Ready'])
    ram_table.appendRow()

def fill_debug_info(message: str):
    debug_table = op('Debug')
    debug_table.clear()
    debug_table.appendCol()
    debug_table.appendRow()
    debug_table[0, 0] = message

def get_connected_motors():
    global MOTORS

    # Using ping and global config

def onSetupParameters(scriptOp):
    '''
    Setting up user interface and filling initial EEPROM and RAM from connected motors
    '''
    # search for available motors and build list of motors
    global MOTORS
    MOTORS.append(Motor(1, 'X_SERIES'))
    MOTORS.append(Motor(2, 'X_SERIES'))
    MOTORS.append(Motor(3, 'X_SERIES'))
    MOTORS.append(Motor(4, 'X_SERIES'))

    build_motors_selector_page(scriptOp)

    build_eeprom_page(scriptOp)
    build_ram_page(scriptOp)
    build_torque_page(scriptOp)
    build_position_page(scriptOp)
    build_velocity_page(scriptOp)

    fill_initial_eeprom_table()
    fill_initial_ram_table()

    # create motors based on GlobalMotorsConfig and check wether user the ID is present in the network

    return

def onPulse(par):
    '''
    called whenever custom pulse parameter is pushed
    '''
    global COUNTER
    COUNTER += 1

    fill_debug_info(COUNTER)

    button_name = par.name
    if button_name == READ_EEPROM:
        pass
    elif button_name == WRITE_EEPROP:
        pass
    elif button_name == READ_RAM:
        pass
    elif button_name == WRITE_RAM:
        pass

    return

def onCook(scriptOp):
    scriptOp.clear()
    return
