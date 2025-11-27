import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from ngspice_read import RawRead

raw = RawRead("output_nodes.raw")
vars = raw.get_plot_names()

time = raw.get_scalevector()

data = {"time": time.get_data()}

for name in vars:
    vec = raw.get_vector(name)
    data[name] = vec.get_data()

pd.DataFrame(data).to_csv("output_nodes.csv", index=False)

print("Converted to output_nodes.csv")
