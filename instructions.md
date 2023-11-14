# Sequence Compiler

## Overview

We would like you to design an MRI pulse sequence framework that takes a sequence configuration as input. The sequence is comprised of RF/Gradient/Receive events (there can be 0 or more of each). It should output the following discrete waveforms:

- RF: 1 real-valued waveform (unit: tesla).
- Gradient: 3 real-valued waveforms for X/Y/Z axes (unit: tesla).
- Receive: Boolean waveform indicating whether to acquire a measurement at each time point.

### RF Event

Each RF event waveform is a sinc with 4 zero crossings (normalized sinc function on the domain [-4.0, 4.0]). Pseudo-code:

```
x = linspace(-4.0, 4.0)
rf = where(x, sin(pi * x) / (pi * x), 1)
```

You will need to sample/scale the sinc function to match the event parameters.

### Gradient Event

Each gradient event waveform is a rectangle (constant amplitude during the duration of the event). The duration/time of the axis waveforms are identical. Only the integral varies per axis.

### Receive Event

Uniformly spaced acquisition times.

## Implementation

### Parse sequence config

Parse an input sequence configuration file `config.json`. See `config_doc.json` for a description of each field in `config.json`.

### Generate sequence waveforms

Compile events into discrete waveforms with sample period `sample_period` from time `0` to the end of the last component.

### Plot sequence waveforms

Plot the waveforms (example: `example/sequence.png`). You do not need to exactly match the example, it is just provided for reference.

### Dump sequence packets

Dump packets containing the waveforms to a binary file. Each packet should contain 1024 samples (zero pad the last packet).

```c
struct SequencePacket {
    float rf[1024];
    float gradient[1024][3];
    // big-endian bit-packed array of booleans
    uint8_t receive[1024/8];
};
```

## Deliverables

1. Upload your code to GitHub or GitLab.
2. You can use any programming language and 3rd party libraries.
3. Your code must contain a README that describes how to run it.
4. The problem specification is purposely somewhat vague/open ended. If something is not specified in this document, it is up to your discretion to decide. Your code will be evaluated by a human, so document any decisions/clarifications that you make to the problem.
