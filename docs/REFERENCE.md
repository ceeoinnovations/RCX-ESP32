# RCX-ESP32 Reference Notes

## IR Protocol (How the ESP32 talks to the RCX)

The RCX communicates over IR using **raw UART serial** modulated onto a 38 kHz
carrier. Missing the parity bitcauses the RCX to silently ignore all
transmissions.

The line idles with IR light OFF (logic HIGH).

### 12-Bit Byte Frame

Each byte is transmitted as 12 bits:

```
Bit 1    : START BIT      — always light ON  (logic LOW)
Bits 2-9 : DATA BITS      — LSB first
Bit 10   : PARITY BIT     — odd parity
Bit 11   : STOP BIT       — always light OFF (logic HIGH)
Bit 12   : INTER-BYTE GAP — always light OFF (idle)
```

Total: 12 bits × 417 µs = ~5 ms per byte.

### Parity Rule (Odd Parity)

Count the 1-bits in the data byte:

- Even count → parity bit = 1 (light OFF)
- Odd count → parity bit = 0 (light ON)

Example: `0x55 = 0b01010101` → four 1-bits (even) → parity = 1 (light OFF)

---

## RCX Packet Format (Direct Command Mode)

```
[55 FF 00] [op] [op^FF] [p1] [p1^FF] ... [ck] [ck^FF]
```

- `55 FF 00` — fixed preamble, always the same
- Each opcode and parameter byte is followed by its bitwise complement
  (`^ 0xFF`)
- Checksum `ck = (opcode + sum(params)) & 0xFF`, also followed by complement
- Toggle bit (`0x08`) is XOR'd into the opcode on alternating packets so the RCX
  can distinguish retransmissions from new commands

### Example — beep (sound 5)

```
55  FF  00  51  AE  05  FA  56  A9
preamble    op  ~op  p1  ~p1  ck  ~ck
```

`0x51 ^ 0xFF = 0xAE`, `0x05 ^ 0xFF = 0xFA`, `(0x51 + 0x05) & 0xFF = 0x56`

### Key Opcodes

| Command          | Opcode | Params                          |
| ---------------- | ------ | ------------------------------- |
| Alive / ping     | 0x10   | none                            |
| Set motor on/off | 0x21   | byte flags\|port_mask           |
| Set motor power  | 0x13   | byte motor_id, byte power (0-7) |
| Set time         | 0x22   | byte hours, byte minutes        |
| Play tone        | 0x23   | short freq (LE), byte duration  |
| Set sensor type  | 0x32   | byte sensor, byte type          |
| Set sensor mode  | 0x42   | byte sensor, byte mode          |
| Stop all tasks   | 0x50   | none                            |
| Play sound       | 0x51   | byte sound (1-5)                |
| Set display      | 0x33   | byte source, short argument     |
| Set TX range     | 0x31   | byte range (0=short, 1=long)    |
| Power off        | 0x60   | none                            |
| Set power-down   | 0x46   | byte minutes                    |
| Set message      | 0xF7   | byte value                      |
| Clear sensor     | 0x26   | byte sensor                     |
| Clear timer      | 0x56   | byte timer                      |

Full opcode list: https://www.mralligator.com/rcx/opcodes.html

---

## Motor Control (Opcode 0x21)

The `0x21` opcode uses a bit-flag byte to control direction and on/off state:

| Flags byte   | Effect            |
| ------------ | ----------------- |
| `0x80\|port` | Motor ON, forward |
| `0x40\|port` | Motor OFF (coast) |
| `0xC0\|port` | Motor brake       |

Port mask: Motor A = `0x01`, Motor B = `0x02`, Motor C = `0x04`

Example: motor A forward → `flags = 0x80 | 0x01 = 0x81`

---

## Hardware Notes

- Use an NPN transistor (PN2222A) in common-emitter to drive the IR LED
- GPIO HIGH → transistor ON → LED ON (normal polarity)
- RCX IR receiver is less sensitive than the LEGO IR Tower

### ESP32 Pin Defaults

| Pin | Role                |
| --- | ------------------- |
| 2   | IR LED (RMT output) |

---
