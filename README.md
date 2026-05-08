# RCX-ESP32

A browser-based tool for programming LEGO RCX using an ESP32 as an IR
transmitter. Write MicroPython in the browser, flash it to the ESP32 over
WebSerial, and control the RCX over IR — no software to install.

Live site: https://ceeoinnovations.github.io/RCX-ESP32/

---

## What You Need

- An ESP32 (tested on ESP32-C6)
- A LEGO RCX 2.0 brick with fresh batteries
- An IR LED wired to GPIO 2 of the ESP32 (see wiring below)
- Chrome or Edge browser (WebSerial and Web Bluetooth require Chromium)
- A USB cable to connect the ESP32 to your computer

---

## Wiring the IR LED

The ESP32 drives an IR LED through an NPN transistor so it has enough current to
reach the RCX. A PCB can be used based on the files in `docs/KiCad`, or you can
wire it up on a breadboard.

```
ESP32 GPIO 2 ──── 330Ω ──── Base (PN2222A)
                             Collector ──── IR LED (anode) ──── 3.3V
                             Emitter  ──── GND
                             IR LED cathode ──── GND
```

---

## First Time Setup

**1. Open the app** Go to https://ceeoinnovations.github.io/RCX-ESP32/ in
Chrome.

**2. Connect your ESP32** Click **connect up** in the Serial Terminal panel.
Select your ESP32's COM port from the browser dialog.

**3. Install the RCX library** Click **Install RCX Lib**. This uploads the RCX
driver files to the ESP32 filesystem. You only need to do this once per board.

**4. Load a template** Pick a template from the dropdown in the right panel
(e.g. Beep Test) and click **Load Template**. The code will appear in the
editor.

**5. Run it** Click **run** to execute the code on the ESP32. Point the IR LED
at the RCX — if wired correctly the RCX should respond.

---

## USB Tower Mode

If you have the original LEGO USB IR Tower you can plug it directly into your
computer and control the RCX without an ESP32 at all.

**Setup:**

1. Plug the USB tower into your computer
2. In the right panel switch to **USB Tower** mode
3. Click **Connect Tower** and select the tower from the browser's USB device
   picker
4. Use the quick action buttons (Ping, Beep, Stop) or load a tower template and
   click **Run on Tower**

The tower templates use `await rcx.*` syntax and run entirely in the browser —
no serial connection needed.

---

## BLE Control (Tech Element Mode)

The ESP32 can also act as a Bluetooth tech element, receiving commands from the
browser over BLE and sending them to the RCX over IR.

**Setup:**

1. Click **Load TE Files** to upload the BLE tech element files to the ESP32
2. The editor will load `main_code.py` — click **run** to start advertising
3. In the right panel, click **Connect** under BLE Control
4. Select the device named **Maria** from the browser's Bluetooth picker
5. Use the command dropdown to send commands to the RCX over BLE
