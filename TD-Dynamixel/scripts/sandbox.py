'''
Sandbox to test dynamixel sdk
'''
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


class CommError(Exception):
    pass


class MotorUnavailable(Exception):
    pass

'''
Global Comm and Motors Config Access
'''
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


'''
Port and Packet Handler
'''
PORT_HANDLER = PortHandler(get_port_name())
PACKET_HANDLER = PacketHandler(get_protocol())

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


test_reading_configs()

run_broadcast_ping = True

if run_broadcast_ping:
    open_port()
    test_broadcast_ping()
    close_port()
