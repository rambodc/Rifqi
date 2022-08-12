'''
me is this DAT.
scriptOp is the OP which is cooking.
'''

####################################################################################################
# Dynamixel Classes and Functions
from enum import Enum
import os
from time import sleep
from typing import List

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


class CommError(Exception):
    pass


class MotorUnavailable(Exception):
    pass


class MotorTypeNotSupported(Exception):
    pass


class MotorControlAddress:
    TorqueEnable: int
    GoalPosition: int
    PresentPosition: int
    MinPosValue: int
    MaxPosValue: int


GLOBAL_COMM_CONFIG = op('GlobalCommConfig')
GLOBAL_MOTORS_CONFIG = op('GlobalMotorsConfig')


def get_port_name():
    return str(GLOBAL_COMM_CONFIG[1,1].val)


def get_baudrate():
    return int(GLOBAL_COMM_CONFIG[2,1].val)


def get_protocol():
    return float(GLOBAL_COMM_CONFIG[3,1].val)


def get_motor_num_from_config():
    return int(GLOBAL_MOTORS_CONFIG.numRows - 1)


PORT_HANDLER = PortHandler(get_port_name())
PACKET_HANDLER = PacketHandler(get_protocol())

TORQUE_ENABLE               = 1     # Value for enabling the torque
TORQUE_DISABLE              = 0     # Value for disabling the torque


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


def get_motor_control_address(motor_type: str) -> MotorControlAddress:
    motor_control_addresses = MotorControlAddress()

    if motor_type == 'X_SERIES' or motor_type == 'MX_SERIES':
        motor_control_addresses.TorqueEnable          = 64
        motor_control_addresses.GoalPosition          = 116
        motor_control_addresses.PresentPosition       = 132
        motor_control_addresses.MinPosValue           = 0
        motor_control_addresses.MaxPosValue           = 4095
    elif motor_type == 'PRO_SERIES':
        motor_control_addresses.TorqueEnable          = 562
        motor_control_addresses.GoalPosition          = 596
        motor_control_addresses.PresentPosition       = 611
        motor_control_addresses.MinPosValue           = -150000
        motor_control_addresses.MaxPosValue           = 150000
    elif motor_type == 'P_SERIES' or motor_type == 'PRO_A_SERIES':
        motor_control_addresses.TorqueEnable          = 512
        motor_control_addresses.GoalPosition          = 564
        motor_control_addresses.PresentPosition       = 580
        motor_control_addresses.MinPosValue           = -150000
        motor_control_addresses.MaxPosValue           = 150000
    elif motor_type == 'XL320':
        motor_control_addresses.TorqueEnable          = 24
        motor_control_addresses.GoalPosition          = 30
        motor_control_addresses.PresentPosition       = 37
        motor_control_addresses.MinPosValue           = 0
        motor_control_addresses.MaxPosValue           = 1023
    else:
        raise MotorTypeNotSupported(
            f"motor_type: {motor_type} is not supported. Supported motor type: X_SERIES, MX_SERIES, PRO_SERIES, P_SERIES, PRO_A_SERIES and XL320")

    return motor_control_addresses


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
    def __init__(self, id: int, control_address: MotorControlAddress) -> None:
        self.ID = id
        self.ControlAddress = control_address


def get_motors() -> List[Motor]:
    motors: List(Motor) = []

    for i in range(get_motor_num_from_config()):
        motor = Motor(  id = int(GLOBAL_MOTORS_CONFIG[i+1, 0].val),
                        control_address = get_motor_control_address(str(GLOBAL_MOTORS_CONFIG[i+1, 1].val)))
        motors.append(motor)

    return motors


def set_motor_torque(motor: Motor, val: int):
    dxl_comm_result, dxl_error = PACKET_HANDLER.write1ByteTxRx(PORT_HANDLER, motor.ID, motor.ControlAddress.TorqueEnable, val)

    if dxl_comm_result != COMM_SUCCESS:
        raise CommError(PACKET_HANDLER.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        raise CommError(PACKET_HANDLER.getRxPacketError(dxl_error))


def test_enable_disable_torque():
    pass


####################################################################################################
# Touchdesigner Classes and Functions


class InputParser:
    def __init__(self, script_op) -> None:
        self._script_op = script_op
        self.channel_num = len(self._script_op.inputs)

    def get_input_torque_enable(self, channel: int) -> int:
        cmd = self._script_op.inputs[channel]
        cmd_torque_enable = cmd[0].eval()

        return int(cmd_torque_enable)

    def get_input_goal_velocity(self, channel: int) -> int:
        cmd = self._script_op.inputs[channel]
        cmd_goal_velocity = cmd[1].eval()

        return int(cmd_goal_velocity)

    def get_motor_command(self) -> MotorCommand:
        cmd = MotorCommand( self.get_input_torque_enable(),
                            self.get_input_goal_velocity())

        return cmd

    def get_motor_commands(self):
        motor_commands = [self.get_motor_command(i) for i in range(self.channel_num)]

        return motor_commands


def setupParameters(scriptOp):
    '''
    press 'Setup Parameters' in the OP to call this function to re-create the parameters.
    '''
    return


def onPulse(par):
    '''
    called whenever custom pulse parameter is pushed
    '''
    return


def cook(scriptOp):
    scriptOp.clear()

    input_parser = InputParser(scriptOp)

    motors = get_motors()

    for motor in motors:
        set_motor_torque(motor, input_parser.get_input_torque_enable(motor.ID))

    debug_info = scriptOp.appendChan('info')
    debug_info[0] = len(motors)

    return

'''
    # create new out channels use this as feedback
    b = scriptOp.appendChan('motor_0-cmd_vel')
    c = scriptOp.appendChan('motor_1-torque_enable')
    d = scriptOp.appendChan('motor_1-cmd_vel')

    # assign out channels with below values
    a[0] = input_parser.get_input_torque_enable(0)
    b[0] = input_parser.get_input_goal_velocity(0)
    c[0] = input_parser.get_input_torque_enable(1)
    d[0] = input_parser.get_input_goal_velocity(1)
'''
test_reading_configs()
