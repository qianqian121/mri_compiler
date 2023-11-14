# MRI Pulse Sequence Compiler

MRI Pulse Sequence Compiler takes a sequence configuration as input. The sequence is comprised of RF/Gradient/Receive
events (there can be 0 or more of each). It contains following discrete waveforms:

- RF: 1 real-valued waveform (unit: tesla).
- Gradient: 3 real-valued waveforms for X/Y/Z axes (unit: tesla).
- Receive: Boolean waveform indicating whether to acquire a measurement at each time point.

The compiler:

- Plot the waveforms (example: `example/sequence.png`).
- Dump packets containing the waveforms to a binary file.

**Install** specific dependencies

```
pip3 install -r requirements.txt
```

**Run**

```
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
./seq_compiler.py --config example/config.json --plot sequence.png --bin sequence.bin
```
