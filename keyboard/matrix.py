


import digitalio
import time
# from microcontroller.pin import *


class Matrix:
    # ROWS = (P0_05, P0_06, P0_07, P0_08, P1_09, P1_08, P0_12, P0_11)
    # COLS = (P0_19, P0_20, P0_21, P0_22, P0_23, P0_24, P0_25, P0_26)
    ROWS = ()
    COLS = ()
    ROW2COL = False

    def __init__(self):
        self.keys = len(self.ROWS) * len(self.COLS)
        self.queue = bytearray(self.keys)
        self.head = 0
        self.tail = 0
        self.length = 0

        self.rows = []                                # row as output
        for pin in self.ROWS:
            io = digitalio.DigitalInOut(pin)
            io.direction = digitalio.Direction.OUTPUT
            io.drive_mode = digitalio.DriveMode.PUSH_PULL
            io.value = 0
            self.rows.append(io)

        self.cols = []                                # col as input
        for pin in self.COLS:
            io = digitalio.DigitalInOut(pin)
            io.direction = digitalio.Direction.INPUT
            io.pull = digitalio.Pull.DOWN if self.ROW2COL else digitalio.Pull.UP
            self.cols.append(io)

        # row selected value depends on diodes' direction
        self.pressed = bool(self.ROW2COL)
        self.t0 = [0] * self.keys                   # key pressed time
        self.t1 = [0] * self.keys                   # key released time
        self.mask = 0
        self.count = 0

    def scan(self):
        t = time.monotonic_ns()

        # use local variables to speed up
        pressed = self.pressed
        last_mask = self.mask
        cols = self.cols

        mask = 0
        count = 0
        key_index = -1
        for row in self.rows:
            row.value = pressed           # select row
            for col in cols:
                key_index += 1
                if col.value == pressed:
                    key_mask = 1 << key_index
                    if not (last_mask & key_mask):
                        if t - self.t1[key_index] < 20000000:
                            print('debonce')
                            continue
                            
                        self.t0[key_index] = t
                        self.put(key_index)
                        
                    mask |= key_mask
                    count += 1
                elif last_mask and (last_mask & (1 << key_index)):
                    if t - self.t0[key_index] < 20000000:
                        print('debonce')
                        mask |= 1 << key_index
                        continue
                        
                    self.t1[key_index] = t
                    self.put(0x80 | key_index)

            row.value = not pressed
        self.mask = mask
        self.count = count
        
        return self.length

    def wait(self, timeout=0):
        last = self.length 
        if timeout:
            end_time = time.monotonic_ns() + timeout * 1000000
            while True:
                n = self.scan()
                if n > last or time.monotonic_ns() > end_time:
                    return n
        else:
            while True:
                n = self.scan()
                if n > last:
                    return n

    def put(self, data):
        self.queue[self.head] = data
        self.head += 1
        if self.head >= self.keys:
            self.head = 0
        self.length += 1

    def get(self):
        data = self.queue[self.tail]
        self.tail += 1
        if self.tail >= self.keys:
            self.tail = 0
        self.length -= 1
        return data

    def view(self, n):
        return self.queue[(self.tail + n) % self.keys]

    def __getitem__(self, n):
        return self.queue[(self.tail + n) % self.keys]

    def __len__(self):
        return self.length

    def get_keydown_time(self, key):
        return self.t0[key]

    def get_keyup_time(self, key):
        return self.t1[key]

    def time(self):
        return time.monotonic_ns()

    def ms(self, t):
        return t // 1000000