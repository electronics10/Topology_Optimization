import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import Antenna_Design as ad
import csv
import pandas as pd

def plot_s11(path, fig_name):
    plt.figure(fig_name)
    df = pd.read_csv(path)  # Assuming headers are present in CSV
    frequency = df.iloc[:, 0]
    s11 = df.iloc[:, 1]
    plt.plot(frequency, s11)
    plt.xlabel("Frequency (GHz)")
    plt.ylabel("s11 (dB)")
    plt.title("S11")
    plt.grid()
    plt.show()

if __name__ == "__main__":
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
    flag = input("Continue (y/n)? ")
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
        path = f'results\\verified_s11_{iter}_{threshold}.csv'
        s11 = transmitter.read('1D Results\\S-Parameters\\S1,1')
        with open(path, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            for line in s11: # [[freq, s11, 50+j],...]
                line = np.abs(line) # change s11 from complex to absolute
                line[1] = 20*np.log10(line[1]) # convert to dB
                writer.writerow(line[:-1])
        # Plot S11
        plot_s11(path, f"S11_{iter}_{threshold}")
    else: pass

    
