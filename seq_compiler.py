#!/usr/bin/env python3
import click
import numpy as np
import matplotlib.pyplot as plt
import json
import struct

PACKET_LEN = 1024

x = np.linspace(-4.0, 4.0)
rf = np.where(x, np.sin(np.pi * x) / (np.pi * x), 1)

K_INTEGRAL = np.trapz(rf, x) / 8.0
print("Integral of the normalized sinc waveform:", K_INTEGRAL)


# RF Event waveform generation
def generate_rf_waveform(duration, integral, time, sample_period, rf_waveform):
    step_scale = 8.0 / duration
    t = np.arange(-4.0, 4.0, step_scale * sample_period)
    sinc = np.where(t, np.sin(np.pi * t) / (np.pi * t), 1)
    rf = sinc * (integral / duration / K_INTEGRAL)
    time_idx = int((time - 0.5 * duration) / sample_period)
    rf_waveform[time_idx:time_idx + len(rf)] = rf
    return rf_waveform


# Gradient Event waveform generation
def generate_gradient_waveform(duration, integral, time, sample_period, gradient_waveform):
    t = np.arange(0, duration, sample_period)
    gradient = np.ones_like(t) * (integral / duration)
    time_idx = int((time - 0.5 * duration) / sample_period)
    gradient_waveform[time_idx:time_idx + len(gradient)] = gradient
    return gradient_waveform


# Receive Event waveform generation
def generate_receive_waveform(duration, size, time, sample_period, receive_waveform):
    t = np.arange(0, duration, sample_period)
    receive = np.ones_like(t, dtype=bool)
    time_idx = int((time - 0.5 * duration) / sample_period)
    receive_waveform[time_idx:time_idx + len(receive)] = receive
    return receive_waveform


# Parse sequence configuration
def parse_sequence_config(config_file):
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config


# Generate sequence waveforms
def generate_sequence_waveforms(config):
    sample_period = config['hardware']['sample_period']
    max_seq_duration = max(
        max(event['time'] + 0.5 * event['duration'] for event in config['events_gradient']),
        max(event['time'] + 0.5 * event['duration'] for event in config['events_rf']),
        max(event['time'] + 0.5 * event['duration'] for event in config['events_receive']),
    )
    num_samples = int(max_seq_duration / sample_period)

    rf_waveform = np.zeros(num_samples)
    gradient_waveforms = np.zeros((num_samples, 3))
    receive_waveform = np.zeros(num_samples, dtype=bool)

    for event in config['events_rf']:
        generate_rf_waveform(event['duration'], event['integral'], event['time'], sample_period, rf_waveform)

    for event in config['events_gradient']:
        generate_gradient_waveform(event['duration'], event['integral'][0], event['time'],
                                   sample_period, gradient_waveforms[:, 0])
        generate_gradient_waveform(event['duration'], event['integral'][1], event['time'],
                                   sample_period, gradient_waveforms[:, 1])
        generate_gradient_waveform(event['duration'], event['integral'][2], event['time'],
                                   sample_period, gradient_waveforms[:, 2])

    for event in config['events_receive']:
        generate_receive_waveform(event['duration'], event['size'], event['time'], sample_period, receive_waveform)

    return rf_waveform, gradient_waveforms, receive_waveform


# Plot sequence waveforms
def plot_sequence_waveforms(rf_waveform, gradient_waveforms, receive_waveform, output_file, show=False):
    fig, axes = plt.subplots(5, 1, sharex=True, figsize=(8, 8))
    axes[0].plot(rf_waveform)
    axes[0].set_ylabel('RF')

    axes[1].plot(gradient_waveforms[:, 0])
    axes[1].set_ylabel('Gradient X')
    axes[2].plot(gradient_waveforms[:, 1])
    axes[2].set_ylabel('Gradient Y')
    axes[3].plot(gradient_waveforms[:, 2])
    axes[3].set_ylabel('Gradient Z')

    axes[4].plot(receive_waveform)
    axes[4].set_ylabel('Receive')

    plt.xlabel('Sample')
    plt.savefig(output_file)
    if show:
        plt.show()
    plt.close()


# Dump sequence packets to binary file
def dump_sequence_packets(rf_waveform, gradient_waveforms, receive_waveform, output_file):
    packet_size = PACKET_LEN
    num_packets = int(np.ceil(len(rf_waveform) / packet_size))

    with open(output_file, 'wb') as f:
        for packet_idx in range(num_packets):
            start_idx = packet_idx * packet_size
            end_idx = start_idx + packet_size
            pad_zeros = False
            if end_idx > len(rf_waveform):
                end_idx = len(rf_waveform)
                pad_zeros = True
            packet_len = end_idx - start_idx
            num_zeros = PACKET_LEN - packet_len
            zeros = np.zeros(num_zeros)

            packet = struct.pack(f'{packet_len}f', *rf_waveform[start_idx:end_idx])
            f.write(packet)
            if pad_zeros:
                packet = struct.pack(f'{num_zeros}f', *zeros)
                f.write(packet)

            for j in range(3):
                packet = struct.pack(f'{packet_len}f', *gradient_waveforms[start_idx:end_idx, j])
                f.write(packet)
                if pad_zeros:
                    packet = struct.pack(f'{num_zeros}f', *zeros)
                    f.write(packet)

            if pad_zeros:
                receive_wf_packet = np.zeros(PACKET_LEN, dtype=bool)
                receive_wf_packet[:packet_len] = receive_waveform[start_idx:end_idx]
                receive_bytes = np.packbits(receive_wf_packet)
            else:
                receive_bytes = np.packbits(receive_waveform[start_idx:end_idx])
            packet = struct.pack('128B', *receive_bytes)
            f.write(packet)
            # finished writing to the binary file.


def seq_compiler(config_file, output_waveform_plot, output_binary_file):
    # Parse sequence configuration
    config = parse_sequence_config(config_file)

    # Generate sequence waveforms
    rf_waveform, gradient_waveforms, receive_waveform = generate_sequence_waveforms(config)

    # Plot sequence waveforms
    plot_sequence_waveforms(rf_waveform, gradient_waveforms, receive_waveform, output_waveform_plot)

    # Dump sequence packets to binary file
    dump_sequence_packets(rf_waveform, gradient_waveforms, receive_waveform, output_binary_file)


@click.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    default="example/config.json",
    help="Input sequence configuration file",
)
@click.option(
    "--plot",
    type=click.Path(exists=False),
    default="sequence.png",
    help="Plot the waveforms",
)
@click.option(
    "--bin",
    type=click.Path(exists=False),
    default="sequence.bin",
    help="Plot the waveforms",
)
def main(config, plot, bin):
    """Compile a MRI pulse sequence config:
    1. Plot sequence waveforms
    2. Dump sequence packets

    \b
    $ ./seq_compiler.py --config example/config.json --plot sequence.png --bin sequence.bin
    """
    seq_compiler(config, plot, bin)


# Main program
if __name__ == '__main__':
    main()
