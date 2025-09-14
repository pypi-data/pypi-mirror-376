# trgenpy

A Python library for IIT's TriggerBox device 🐍.

- [Documentation]()

## Getting started

To install this package use is required `Python >= 3.9`

```shell
pip install trgenpy
```

### Client

The `TriggerClient` is the object that stores all the information about the socket connection between you and the TriggerBox.  
You can instantiate the `TriggerClient` object like this:

```python
client = TriggerClient() 
```

Once the client object is created you can connect to Trgen Device...

```python
client.connect()
```

...or check device availability

```python
isAavailable = client.is_available() # true / false
```

### Single Trigger Send

To send a defaul trigger signal (positive square with a logic state of 20µs) you can use the `sendTrigger()` function:

```python
client.sendTrigger()
```

### Custom Trigger Send

If you want to send trigger to a custom list inside the pinout you can use the `sendCustomTrigger()` function:

```python
client.sendCustomTrigger([TriggerPin.NS0,TriggerPin.GPIO0])
```

### Sending Markers

In order to send a marker value to all (Neuroscan,Synamps and GPIO) ports you can use the `sendMarker()` function:

```python
client.sendMarker(13)
```

if you want invert the bit order, just flag the `LSB` argument (`True`by default)

```python
client.sendMarker(13,LSB=False)
```

if you want to send different markers simultaiously on different ports you can use the arguments:

- `markerNS`
- `markerSA`
- `markerGPIO`

like this:

```python
client.sendMarker(markerNS=8,markerSA=2,markerGPIO=15)
```

### Trigger

The `Trigger` object defines a single trigger behaviours through its id.
This is the list of supported `trigger_id` values for the TriggerBox:

#### Trigger ID List

- Neuroscan IDs
    The Neuroscan pinout (only for used pins) goes from 0 to 7  
    - `[NS0,NS1,NS2,NS3,NS4,NS5,NS6,NS7]`
- Synamps IDs
     The Neuroscan pinout (only for used pins) goes from 0 to 7  
    - `[SA0,SA1,SA2,SA3,SA4,SA5,SA6,SA7]`
- TMSI/O IDs
    - `TMSO`
    - `TMSI`
- GPIO IDs
    The GPIO pinout goes from 0 to 7  
    - `[GPIO0,GPIO01,GPIO02,GPIO03,GPIO04,GPIO05,GPIO06,GPIO07]`

You can instantiate the `Trigger` object with:

```python
neuroScan = TriggerClient.create_trigger(TriggerPin.NS3)
```

passing ad only argument the constant from `TriggerPin`

Now you're ready to define the instruction set for `Trigger` with the `set_instruction()` function.
Each trigger has a `memory` property, a list that can contain 32 instructions, so this function is defined:

```
def set_instruction(self, index, instruction):
# index: 0-32 value
# instruction: instruction_code
```

Each instruction code can be encoded using the [Instruction Helpers](#instruction-helpers)

```python
# call the function directly on the same Trigger object
neuroScan.set_instruction(0, active_for_us(5))
neuroScan.set_instruction(1, unactive_for_us(3))
# ...
```

## Instruction Helpers

The supported instruction set for Trgen is:

| Instruction | 1° Param | 2° Param | Description |
| ----------- | ----------- | ------------ | ----------- |
| `unactive_for_us(us)` | µ seconds duration | | Set the unactivation time for µ seconds |
| `active_for_us(us)` | µ seconds duration | | Set the activation time for µ seconds |
| `wait_pe(tr)` | Trigger ID | | Wait the positive edge for a specific [Trigger ID](#trigger-id-list) |
| `wait_ne(tr)` | Trigger ID | | Wait the negative edge for a specific [Trigger ID](#trigger-id-list) |
| `repeat(addr,time)` | Instruction address | Time of repeat | Set the activation time for µ seconds |
| `end()` | | | End the behaviour |
| `not_admissible()` | | | Empty instruction, it has to be placed after the `end()`|

#### NOTE
Each Trigger can support a list of N instructions, where N = 2^MTML (Max Trigger Memory Length)

You can access to the `mtml` value by

```python
# Add this in try block to manage errors
try:
    impl = client.get_implementation()
    mtml = impml.mtml
except InvalidAckError as e:
    print(f"⚠️ ACK sbagliato: {e}")
except AckFormatError as e:
    print(f"⚠️ ACK malformato: {e}")
except TimeoutError as e:
    print(f"⏱️ Timeout: {e}")
```

## Native Commands

IIT's TriggerBox can receive some commands, the full instruction set includes:

- Program Trigger
- Start Trigger
- Set GPIO I/O Direction
- Request Implementation parameters
- Request Trgen Status
- Set the Trigger level
- Get GPIO I/O Direction
- Get the Trigger Level
- Stop the Triggers

### Program Trigger


### Start Trigger

### Set GPIO I/O Direction

### Request Implementation

### Request Trgen Status

### Set the Trigger level

### Get the GPIO I/O Direction

### Get the Trigger Level






## E-Prime integration via Python COM-visible

Install pywin32
```bash
pip install pywin32
```

TODO continue...