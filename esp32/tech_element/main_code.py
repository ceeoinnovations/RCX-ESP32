import time
import struct
from definitions import *
from pyConst import *
from TE_BLE import Yell
import motion_rcx as motion
import motors_rcx as motors
import sound_rcx as sound

myTimer = None
p = None

# ── RCX command bytes ─────────────────────────────────────────────────────────
# Motion
RCX_MOVE_FWD    = 0x10
RCX_MOVE_BWD    = 0x11
RCX_TURN_LEFT   = 0x12
RCX_TURN_RIGHT  = 0x13
RCX_SPIN_LEFT   = 0x14
RCX_SPIN_RIGHT  = 0x15
RCX_STOP        = 0x16
RCX_BRAKE       = 0x17
# Sound
RCX_BEEP        = 0x20
# Motors (byte1 = motor_id)
RCX_MOTOR_ON    = 0x30
RCX_MOTOR_OFF   = 0x31
RCX_MOTOR_BRAKE = 0x32
RCX_MOTOR_POWER = 0x33  # byte1=motor_id, byte2=level
RCX_ALL_OFF     = 0x34
RCX_ALL_BRAKE   = 0x35

# ── Tech element protocol handlers ───────────────────────────────────────────
def build_payload(reply, message, answers):
    payload = bytes([reply])
    for name, fmt, atr in message:
        if atr:
            number = [a if isinstance(a, int) else answers.get(name, {}).get(a, -1) for a in atr]
            payload += struct.pack(fmt, *number)
        else:
            payload += struct.pack(fmt, answers.get(name, 0))
    return payload

def return_info(reply, message, data):
    answers = {'RPC': {'build': 47, 'major': 1, 'minor': 0},
               'Firmware': {'build': 1, 'major': 0, 'minor': 5},
               'MaxSize': {'packet': 512, 'message': 0, 'chunk': 247},
               'GroupID': 21}
    return build_payload(reply, message, answers)

def send_payload(info):
    answers = {'hub info': {'key': 0x00, 'Battery': 90, 'USB': 1},
               'vision sensor': {'key': 0x01, 'x': 12, 'y': 300, 'red': 250, 'green': 12, 'blue': 1}}
    message = [(name, fmt, [key] + atr) for key, (name, fmt, atr) in DEVICE_MESSAGE_MAP.items()]
    if p and p.is_connected:
        p.send(build_payload(DEVICE_NOTIFICATION, message, answers))

def start_feed(reply, message, data):
    from machine import Timer
    global myTimer
    fmt, cmd, _ = commands.get('feed')
    period = struct.unpack(fmt, bytes(data[:3]))[1]
    print(f'starting feed: period={period}')
    myTimer = Timer(-1)
    myTimer.init(period=period, mode=Timer.PERIODIC, callback=send_payload)
    return bytes([reply])

def handle_rcx(reply, message, data):
    cmd = data[0]
    print(f'RCX cmd: {hex(cmd)} data={data}')
    if   cmd == RCX_MOVE_FWD:    motion.move(speed=data[1] if len(data) > 1 else 7)
    elif cmd == RCX_MOVE_BWD:    motion.backward(speed=data[1] if len(data) > 1 else 7)
    elif cmd == RCX_TURN_LEFT:   motion.turn_left(speed=data[1] if len(data) > 1 else 7)
    elif cmd == RCX_TURN_RIGHT:  motion.turn_right(speed=data[1] if len(data) > 1 else 7)
    elif cmd == RCX_SPIN_LEFT:   motion.spin_left(speed=data[1] if len(data) > 1 else 7)
    elif cmd == RCX_SPIN_RIGHT:  motion.spin_right(speed=data[1] if len(data) > 1 else 7)
    elif cmd == RCX_STOP:        motion.stop()
    elif cmd == RCX_BRAKE:       motion.brake()
    elif cmd == RCX_BEEP:        sound.beep()
    elif cmd == RCX_MOTOR_ON:    motors.on(data[1] if len(data) > 1 else 0)
    elif cmd == RCX_MOTOR_OFF:   motors.off(data[1] if len(data) > 1 else 0)
    elif cmd == RCX_MOTOR_BRAKE: motors.brake(data[1] if len(data) > 1 else 0)
    elif cmd == RCX_MOTOR_POWER: motors.power(data[1] if len(data) > 1 else 0, data[2] if len(data) > 2 else 5)
    elif cmd == RCX_ALL_OFF:     motors.all_off()
    elif cmd == RCX_ALL_BRAKE:   motors.all_brake()
    return bytes([reply])

_RCX_CMDS = [RCX_MOVE_FWD, RCX_MOVE_BWD, RCX_TURN_LEFT, RCX_TURN_RIGHT,
             RCX_SPIN_LEFT, RCX_SPIN_RIGHT, RCX_STOP, RCX_BRAKE,
             RCX_BEEP, RCX_MOTOR_ON, RCX_MOTOR_OFF, RCX_MOTOR_BRAKE,
             RCX_MOTOR_POWER, RCX_ALL_OFF, RCX_ALL_BRAKE]

options = {
    INFO_REQUEST:                (INFO_RESPONSE,                INFO_MESSAGE,       return_info),
    DEVICE_NOTIFICATION_REQUEST: (DEVICE_NOTIFICATION_RESPONSE, DEVICE_MESSAGE_MAP, start_feed),
}
for cmd in _RCX_CMDS:
    options[cmd] = (cmd + 1, [], handle_rcx)

# ── Main ──────────────────────────────────────────────────────────────────────
def peripheral(name):
    global p
    def callback(value):
        data = list(value)
        print(f'Received: {data}')
        reply, message, subroutine = options.get(data[0], (None, None, None))
        if reply is None:
            print(f'Unknown command: {data}')
            return
        payload = subroutine(reply, message, data)
        if p.is_connected:
            p.send(payload)
    try:
        p = Yell(name, interval_us=30000, verbose=True)
        p.callback = callback
        if p.connect_up():
            print('Connected')
            while p.is_connected:
                time.sleep(1)
        print('Lost connection')
    except Exception as e:
        print(f'Error: {e}')
    finally:
        if p:
            p.disconnect()
        if myTimer:
            myTimer.deinit()
        print('Closed')

peripheral('Maria')
