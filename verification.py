import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import Antenna_Design as ad
import csv
import pandas as pd
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap

# Get the original 'coolwarm' colormap
coolwarm_cmap = cm.get_cmap('coolwarm')

# Create a list of colors from the first half (0 to 0.5) of 'coolwarm'
# We'll sample 256 colors for a smooth transition
colors = [coolwarm_cmap(i) for i in np.linspace(0.5, 1, 256)]

# Create a new colormap from this list of colors
half_coolwarm_cmap = LinearSegmentedColormap.from_list("half_coolwarm", colors)

def plot_s11(path, fig_name):
    plt.figure(fig_name)
    df = pd.read_csv(path)  # Assuming headers are present in CSV
    frequency = df.iloc[:, 0]
    s11 = df.iloc[:, 1]
    plt.plot(frequency, s11)
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("|S11| (dB)")
    plt.title("S11")
    # plt.grid()
    plt.show()

def run_CST():
    # Read and round primal
    iter = int(input("iteration: "))
    threshold = float(input("threshold: "))
    filePath = f"results/primal_history.txt"
    with open(filePath, 'r') as file:
        record = False
        string = ''
        for line in file:
            if record: 
                # print(line)
                line = line.strip()
                if line == f'Iteration{iter+1}': break
                line = line.strip('[')
                line = line.strip(']')
                string = string + line + ' '
            line=line.strip()
            if line == f'Iteration{iter}': record = True
    string = np.array(string.split(), float)
    # print("Read:\n", string)
    # string = np.rint(string) # ceil, floor, fix
    for index, val in enumerate(string):
        if val < threshold: string[index] = 0
        else: string[index] = 1
    # print("Rounded:\n",string)
    # string = np.ones(49)# test
    cond = string*5.8e7

    # Plot test case
    plt.figure("verified_topology")
    im = plt.imshow(cond.reshape(ad.NX, ad.NY),origin='upper',norm=colors.CenteredNorm(),cmap='coolwarm')
    plt.colorbar(im)
    plt.title("Antenna Topology")
    plt.show()

    # Set verification
    path = f'results\\verified_s11_{iter}_{threshold}.csv'
    fig_name = f"S11_{iter}_{threshold}"
    flag = input("Run CST and store S11 (y/n)? ")
    if flag == 'y':
        transmitter = ad.Controller("CST_Antennas/topop_18.cst")
        transmitter.delete_results()
        try: transmitter.delete_signal1()
        except: pass
        transmitter.update_distribution(cond)
        transmitter.set_port(transmitter.port[0], transmitter.port[1])
        transmitter.set_frequency_solver()
        transmitter.start_simulate()
        # Store s11
        s11 = transmitter.read('1D Results\\S-Parameters\\S1,1')
        with open(path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for line in s11: # [[freq, s11, 50+j],...]
                line = np.abs(line) # change s11 from complex to absolute
                line[1] = 20*np.log10(line[1]) # convert to dB
                writer.writerow(line[:-1])
    return path, fig_name

if __name__ == "__main__":
    path, fig_name = run_CST()
    plot = input("Plot S11 (y/n)? ")
    if plot: plot_s11(path, fig_name)

    
