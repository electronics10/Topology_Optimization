import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import Antenna_Design as ad


if __name__ == "__main__":
    # Read and round primal
    iter = input("iteration: ")
    threshold = float(input("threshold: "))
    iter = int(iter)
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
    im = plt.imshow(cond.reshape(ad.NX, ad.NY),origin='upper',norm=colors.CenteredNorm(),cmap='coolwarm')
    plt.colorbar(im)
    plt.show()

    # Set verification
    flag = input("Continue (y/n)? ")
    if flag == 'y':
        transmitter = ad.Controller("CST_Antennas/topop.cst")
        transmitter.delete_results()
        try: transmitter.delete_signal1()
        except: pass
        transmitter.update_distribution(cond)
        transmitter.set_port(transmitter.port[0], transmitter.port[1])
        transmitter.set_frequency_solver()
        transmitter.start_simulate()
    else: pass