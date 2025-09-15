#!/usr/bin/env python

import argparse

MIDINOTES = 150
ROOTNOTE = 16.35159781250000000000  # C0


def pitch(F0, n):
    return F0 * pow(2, (n / 12.0))


parser = argparse.ArgumentParser(
    description="Generate frequency tables for use with LameStation audio modules."
)
parser.add_argument(
    "-c", "--clkfreq", type=int, default=80000000, help="Propeller clock speed"
)
parser.add_argument("-p", "--period", type=int, default=2000, help="PWM period")
parser.add_argument(
    "-s", "--samples", type=int, default=512, help="Number of frames in a sample"
)

args = parser.parse_args()

CLKFREQ = args.clkfreq
PERIOD = args.period
SAMPLES = args.samples
FS = CLKFREQ / PERIOD
FCmin = FS / SAMPLES

output = ""

output += "' --------------------------------------------------\n"
output += "' * frequency table\n"
output += "' --------------------------------------------------\n"
output += "'     Clkfreq: " + str(CLKFREQ) + "\n"
output += "'      Period: " + str(PERIOD) + "\n"
output += "'     Samples: " + str(SAMPLES) + "\n"
output += "' Sample Rate: " + str(FS) + " Hz\n"
output += "'       FCmin: " + str(FCmin) + " Hz\n"

output += "\nfreqTable\n"

realFrequency = []
incrementFrequency = []

for i in range(0, MIDINOTES):
    realFrequency.append(pitch(ROOTNOTE, i))
    incrementFrequency.append(int(pow(2.0, 12.0) * realFrequency[i] / FCmin))

for i in range(0, MIDINOTES):
    if i % 8 == 0:
        output += "\nlong    "
    output += "%8s" % (str(incrementFrequency[i]))
    if not i % 8 == 7:
        output += ", "

output += "\n"

print(output)
