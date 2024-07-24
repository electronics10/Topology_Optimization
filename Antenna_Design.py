import Controller as cc
import numpy as np
import matplotlib.pyplot as plt
from math import ceil, sqrt


# Antenna parameters
Ld, Wd, Lg, Wg, hc, hs, d = (42,42,104,104,0.035,1.6,1.5)
nx, ny = (int(Ld//d), int(Wd//d))

def call_controller(file, set_domain=False):
    # Initialize antenna
    mycontroller = cc.MyController(file)
    if set_domain:
        print("Setting domain, environment, and monitor")
        mycontroller.set_domain(Ld, Wd, d, hc)
        mycontroller.set_environment(Lg, Wg, hc, hs)
        mycontroller.set_monitor(Ld, Wd, d, hc)
        print("set")
    return mycontroller

def power_time_reverse(plot=False):
    print("Executing time reversal")
    # Read power file and make power list
    powerPath = "power.txt"
    file = open(powerPath,'r')
    power = []
    t = 0
    for line in file.readlines()[2:]: # First two lines are titles
        if line.startswith('Sample'): pass
        else:
            line = line.split() # x,y,z,Px,Py,Pz
            P_abs_square = 0
            time = []
            # for word in line[3:]:
            #     word = float(word)
            #     P_abs_square += word**2
            time.append(t)
            # time.append(P_abs_square**(1/2))
            time.append(float(line[3]))
            power.append(time)
            t += 0.1
    file.close()
    # Time reverse
    power = np.array(power)
    feed = np.array([power.T[0], np.flip(power.T[1], 0)])
    feed = feed.T
    # Write reversed power
    feedPath = "reversed_power.txt"
    file = open(feedPath, "w")
    file.write("#\n#'Time / ns'	'default [Real Part]'\n#---------------------------------\n") # IDK why but don't change a word
    for pair in feed:
        file.write(f"{pair[0]} {pair[1]}\n")
    file.close()
    print(f"reversed power exported as '{feedPath}'")
    if plot:
        plt.figure(1)
        plt.plot(power.T[0], power.T[1])
        plt.figure(2)
        plt.plot(feed.T[0], feed.T[1])
        plt.show()

def Efile2gridE(path):
    file1 = open(path,'r')
    grid_E = []
    time = []
    for line in file1.readlines()[2:]: # First two lines are titles
        if not (line.startswith('Sample')):
            line = line.split() # x,y,z,Ex,Ey,Ez
            E_abs_square = 0
            for word in line[:2:-1]: # Ez, Ey, Ex (because I want final word = Ex)
                word = float(word)
                E_abs_square += word**2
            # time.append(E_abs_square**(1/2))
            time.append(E_abs_square**(1/2)*np.sign(word))
        else:
            grid_E.append(time)
            time = []
    grid_E = grid_E[1:] # delete initial []
    file1.close()
    grid_E = np.array(grid_E) # [t0, t1, ...tk=[|E1|,...|Ek|...,|E169|],...t35]
    return grid_E

def adjoint(receiver, transmitter):
    print("Calculating gradient by adjoint method.")
    # Receiver do plane wave excitation, export E and power
    receiver.plane_wave_excitation()
    # Transmitter do time reverse excitation
    power_time_reverse()
    transmitter.feed_excitation()
    # Calculate gradient by adjoint field method
    E_received = Efile2gridE("E_received.txt")
    E_excited = Efile2gridE("E_excited.txt")
    grad = np.flip(E_received,0)*E_excited
    grad = -np.sum(grad, axis=0)
    dt = 0.1
    dl = 0.75
    grad = grad*dt*dl**3
    print("Adjoint method finished")
    return grad

def topology_filter(px):
    radius = int(nx/2)
    pp = px
    return pp

def px_generator():
    px = np.random.rand(nx*ny)
    window = []
    for i in range(nx*ny):
        if i < 28: window.append(0)
        elif i > 167: window.append(0)
        else:
            if i%14 == 0: window.append(0)
            elif i%14 == 1: window.append(0)
            elif i%14 == 12: window.append(0)
            elif i%14 == 13: window.append(0)
            else: window.append(1)
    window = np.array(window)
    px = 0.5*px + window
    return px

def gradient_ascent(receiver, transmitter):
    print("Executing gradient ascent")
    # Gradient asdfgent parameters
    alpha = 0.1  # learning rate
    # pp = np.ones(nx*ny)  # initial value of pp
    px = px_generator() # initial value of p
    pp = topology_filter(px)
    cond = 10**(pp*9.763-2) # initial value of cond
    pp_history = [] # store the history of pp values to visualize the optimization process
    grad_history = [] # store absolute value of gradient to check convergence
    iterations = 10
    # record pp: create empty file
    file = open("pp_history.txt", "w")
    file.close()
    file = open("grad_history.txt", "w")
    file.close()
    # Gradient ascent loop
    for index in range(iterations):
        print(f"\nIteration{index}:")
        # Calculate gradient by adjoint method
        receiver.update_distribution(cond)
        # transmitter.update_distribution(cond)
        grad_cond = adjoint(receiver, transmitter)
        rms_grad = np.sqrt(np.mean(grad_cond**2))
        grad_history.append(rms_grad)
        print(f"gradient_cond_rms = {rms_grad}")
        grad_pp =  grad_cond*(9.763*np.log(10)*cond)
        rms_grad = np.sqrt(np.mean(grad_pp**2))
        print(f"gradient_pp_rms = {rms_grad}")
        # record pp
        file = open("pp_history.txt", "a")
        file.write(f"Iteration{index}\n")
        file.write(str(pp)+"\n")
        file.close()
        pp_history.append(pp.copy())
        # Do gradient ascent
        alpha = np.exp(-grad_pp**2/90000)/np.sqrt(90000/2)/2
        pp = pp + alpha * grad_pp
        cond = pp #10**(pp*9.763-2)
        # record grad
        file = open("grad_history.txt", "a")
        file.write(f"Iteration{index}\n")
        file.write(str(grad_pp)+"\n")
        file.close()
        # Discriminant
        if rms_grad < 10: break # grad_pp
    return pp_history, grad_history

def plot_grad(grad_history):
    plt.plot(grad_history)
    plt.yscale('log')
    plt.grid(True, which="both")
    plt.xlabel('Iteration (k)')
    plt.ylabel('gradient_rms')
    plt.title('Convergence Plot')

def plot_distribution(file_path = "pp_history.txt"):
    # txt to list
    pp_history = parse_iteration_blocks(file_path)
    pp_history = np.array(pp_history)
    # Plot figure
    # Determine grid size for subplots
    num_plots = len(pp_history)
    cols = ceil(sqrt(num_plots))
    rows = ceil(num_plots / cols)
    # Create figure and subplots
    fig, axes = plt.subplots(rows, cols) # , figsize=(15, 15)
    axes = axes.flatten()  # Flatten the axes array for easy iteration
    # 1d to 2d (core)
    mid = (Ld/2, Wd/2)
    for i, pp in enumerate(pp_history):
        distribution = pp.reshape(nx, ny)
        im = axes[i].imshow(distribution, extent=[-mid[0], Ld-mid[0], -mid[1], Wd-mid[1]])
        axes[i].set_title(f'Iteration {i}')
    fig.colorbar(im, ax = axes[-1], fraction=0.1)
    # Remove any empty subplots
    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])
    plt.tight_layout()

def parse_iteration_blocks(file_path):
    with open(file_path, 'r') as file:
        content = file.read().strip()  # Read the content and strip any extra whitespace
    iteration_blocks = content.split('Iteration')[1:]  # Split by 'Iteration' and ignore the first empty element
    result = []
    for block in iteration_blocks:
        block = block.strip()  # Strip any leading/trailing whitespace
        block_content = block.split('\n', 1)[1]  # Skip the '0', '1', etc., and get the rest of the content
        block_content = block_content.replace('\n', ' ')  # Replace newline characters with spaces
        block_content = block_content.replace('[', '').replace(']', '')  # Remove square brackets
        number_strings = block_content.split()  # Split the content by spaces
        numbers = [float(num) for num in number_strings]  # Convert the strings to integers
        result.append(numbers)
    return result


if __name__ == "__main__":
    receiver = call_controller("CST_Antennas/test.cst")
    # transmitter = receiver #call_controller("transmitter.cst")
    # pp_history, grad_history = gradient_ascent(receiver, transmitter)
    # plot_distribution("pp_history.txt")
    # plot_distribution("grad_history.txt")
    # plt.show()