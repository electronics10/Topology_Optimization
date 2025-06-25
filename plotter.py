import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from math import ceil, sqrt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap

# Get the original 'coolwarm' colormap
coolwarm_cmap = cm.get_cmap('coolwarm')

# Create a list of colors from the first half (0 to 0.5) of 'coolwarm'
# We'll sample 256 colors for a smooth transition
colors = [coolwarm_cmap(i) for i in np.linspace(0.5, 1, 256)]

# Create a new colormap from this list of colors
half_coolwarm_cmap = LinearSegmentedColormap.from_list("half_coolwarm", colors)


if __name__ == "__main__":
    plotter = Plotter()
    plotter.plot_all_results(1, true_position=False)
    
    # f = open("macro.txt")
    # a = f.read()
    # print(a.split("\n"))
