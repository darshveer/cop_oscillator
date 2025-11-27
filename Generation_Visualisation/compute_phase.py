import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def extract_phase(time, voltage, threshold=0.5):
    """
    Compute phase of a periodic square-like waveform using zero-crossings.
    """
    # Find rising edges: v crosses threshold with positive slope
    rising = []
    for i in range(len(voltage)-1):
        if voltage[i] < threshold and voltage[i+1] >= threshold:
            t = time[i] + (threshold - voltage[i]) * (time[i+1]-time[i]) / (voltage[i+1]-voltage[i])
            rising.append(t)

    if len(rising) < 2:
        return None, None

    # Estimate period T
    rising = np.array(rising)
    periods = np.diff(rising)
    T = np.median(periods)

    # Use last rising edge to compute phase
    t_last = rising[-1]
    phase = (t_last % T) / T * 2*np.pi

    return phase, T


def compute_all_phases(csv_file):
    df = pd.read_csv(csv_file, sep=' ')

    time = df.iloc[:,0].values
    phases = {}

    for col in df.columns[1:]:
        v = df[col].values
        phase, T = extract_phase(time, v)
        phases[col] = phase

    return phases


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python compute_phase.py output_nodes.csv")
        exit()

    csvfile = sys.argv[1]
    phases = compute_all_phases(csvfile)

    print("\nPHASES (radians):")
    for node, ph in phases.items():
        print(node, ":", ph)
