import bluetooth
import time
import struct
import micropython
micropython.alloc_emergency_exception_buf(128)

NAME_FLAG = 0x09
SCAN_RESULT = 5
SCAN_DONE = 6
NAME_FLAG = 0x09
ADV_TYPE_UUID128_COMPLETE = 0x07
ADV_IND = 0x00
ADV_DIRECT_IND = 0x01

IRQ_CENTRAL_CONNECT = 1
IRQ_CENTRAL_DISCONNECT = 2
IRQ_GATTS_WRITE = 3
IRQ_GATTS_READ_REQUEST = 4
IRQ_SCAN_RESULT = 5
IRQ_SCAN_DONE = 6
IRQ_PERIPHERAL_CONNECT = 7
IRQ_PERIPHERAL_DISCONNECT = 8
IRQ_GATTC_SERVICE_RESULT = 9
IRQ_GATTC_SERVICE_DONE = 10
IRQ_GATTC_CHARACTERISTIC_RESULT = 11
IRQ_GATTC_CHARACTERISTIC_DONE = 12
IRQ_GATTC_DESCRIPTOR_RESULT = 13
IRQ_GATTC_DESCRIPTOR_DONE = 14
IRQ_GATTC_READ_RESULT = 15
IRQ_GATTC_READ_DONE = 16
IRQ_GATTC_WRITE_DONE = 17
IRQ_GATTC_NOTIFY = 18
IRQ_GATTC_INDICATE = 19

SERVICE_UUID = bluetooth.UUID('0000fd02-0000-1000-8000-00805f9b34fb')
WRITE_UUID   = bluetooth.UUID('0000fd02-0001-1000-8000-00805f9b34fb')
NOTIFY_UUID  = bluetooth.UUID('0000fd02-0002-1000-8000-00805f9b34fb')

FLAG_READ = 0x0002
FLAG_WRITE_NO_RESPONSE = 0x0004
FLAG_WRITE = 0x0008
FLAG_NOTIFY = 0x0010

TE_TX = (NOTIFY_UUID, FLAG_READ | FLAG_NOTIFY,)
TE_RX = (WRITE_UUID, FLAG_WRITE | FLAG_WRITE_NO_RESPONSE,)
TE_SERVICE = (SERVICE_UUID,(TE_TX, TE_RX),)

class Yell():
    def __init__(self, name = 'Pico', interval_us=10000, verbose = True):

        self._ble = bluetooth.BLE()
        self._ble.active(True)
        self._ble.irq(self._irq)
        self.name = name
        self.string = b''
        self.is_any = 0
        self.verbose = verbose
        self.is_connected = False

        self.service = SERVICE_UUID
        services = [self.service]
        ((self._handle_tx, self._handle_rx),) = self._ble.gatts_register_services((TE_SERVICE,))
        self._connections = set()
        self.callback = self.rx
        self.interval_us = interval_us

    def printIt(self, data):
        if self.verbose:
            print(data)

    def _irq(self, event, data):  # Track connections so we can send notifications.
        if event == IRQ_CENTRAL_CONNECT:
            conn_handle, _, _ = data
            self._connections.add(conn_handle)
            self.is_connected = True
            self.printIt("Connected: "+str(conn_handle))

        elif event == IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _ = data
            self._connections.remove(conn_handle)
            self.is_connected = False  #assuming only one connection
            self.printIt("Disconnected: " + str(conn_handle))

        elif event == IRQ_GATTS_WRITE:
            conn_handle, value_handle = data
            value = self._ble.gatts_read(value_handle)
            if value_handle == self._handle_rx and self.callback:
                self.callback(value)

    def rx(self, data):
        self.printIt("Received: " + str(bytes(data)))

    def advertise(self):
        short = self.name[:8]
        payload = struct.pack("BB", len(short) + 1, NAME_FLAG) + short  # byte length, byte type, value
        value = bytes(self.service)
        payload += struct.pack("BB", len(value) + 1, ADV_TYPE_UUID128_COMPLETE) + value

        self._ble.gap_advertise(self.interval_us, adv_data=payload)
        self.printIt('Advertising...')

    def stop_advertising(self):
        self._ble.gap_advertise(None)
        self.printIt("Advertising stopped")

    def disconnect(self):
        for conn_handle in self._connections:
            self._ble.gap_disconnect(conn_handle)
        self.printIt("Disconnected from central")

    def connect_up(self, timeout = -1):
        self.advertise()
        success = self.wait_for_connection(timeout)
        if success:
            self.printIt("\nConnected to central")
        self.stop_advertising()
        return success

    def wait_for_connection(self, timeout = -1):
        start = time.ticks_ms()
        done = False
        while not done:
            done = self.is_connected
            if not done and timeout >= 0:
                done = (time.ticks_ms()-start) >= timeout
            time.sleep(0.1)
            if self.verbose:
                print('.',end='')
        return self.is_connected

    def send(self, data):
        if not self.is_connected:
            return
        for conn_handle in self._connections:
            self._ble.gatts_notify(conn_handle, self._handle_tx, data)
        self.printIt("sent to %d central(s): %s" % (len(self._connections), data))
