import os
import time
import numpy as np
import scipy.ndimage as scimage
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from PIL import Image, ImageDraw, ImageFont
from math import ceil, sqrt
import Controller as cc


# Design parameter
L = 42
W = 42
D = 6
# Some interesting initial shape generator
def generate_shape(n=int(L//D), shape='circle', **kwargs):
    array = np.zeros((n, n), dtype=np.int32)
    if shape == 'circle':
        radius = kwargs.get('radius', n//3)
        center = kwargs.get('center', (n // 2, n // 2))
        y, x = np.ogrid[:n, :n]
        dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        array[dist_from_center <= radius] = 1
    elif shape == 'alphabet':
        letter = kwargs.get('letter', 'F')
        font_size = kwargs.get('font_size', 8)
        array = generate_alphabet(letter, n, font_size)
    return array

def generate_alphabet(letter, n, font_size):
    # Create a blank image with a white background
    img = Image.new('L', (n, n), 0)  # 'L' mode for grayscale, initialized with black (0)
    draw = ImageDraw.Draw(img)
    # Load a default font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)  # You can replace this with any valid font path
    except:
        font = ImageFont.load_default()
    # Get the bounding box of the letter
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Calculate the position to center the letter
    position = (n // 2 - text_width//1.8  , n // 2 - text_height//1.2)
    # Draw the letter on the image
    draw.text(position, letter, fill=1, font=font)
    # Convert the image to a NumPy array (1 for white, 0 for black)
    array = np.array(img)
    return array

def add_noise(binary_array, dB=0):
    length = len(binary_array)
    noise1 = np.random.rand(length)*0.00001*10**dB # 0.00001 because 5.8e7 scale is too large
    noise2 = np.random.rand(length)*0.00001*10**dB # 0.00001 because 5.8e7 scale is too large
    binary_array = binary_array + noise1 - noise2
    binary_array = np.clip(binary_array, 0, 1)
    return binary_array


# Optimizer Class
class Optimizer:
    def __init__(self, call_controller=True):
        self.Ld = L
        self.Wd = W
        self.d = D
        self.nx = int(self.Ld//self.d)
        self.ny = int(self.Wd//self.d)
        self.excitePath = "txtf\\spec.txt"
        if call_controller:
            self.receiver = cc.Controller("CST_Antennas/receiver.cst")
            self.transmitter = cc.Controller("CST_Antennas/transmitter.cst")
        self.results_history_path = {
            'cond':"results\\cond_history.txt", 
            'unit_cond':"results\\unit_cond_history.txt",
            'grad_cond':"results\\grad_history.txt",
            }
    
    def set_environment(self):
        # Set base, domain, and monitor for receiver
        print("Setting environment for receiver...")
        self.receiver.set_base()
        self.receiver.set_domain(self.Ld, self.Wd, self.d)
        self.receiver.set_monitor(self.Ld, self.d)
        print("Receiver environment set")
        # Set base, domain, and monitor for transmitter
        print("Setting environment for transmitter...")
        self.transmitter.set_base()
        self.transmitter.set_domain(self.Ld, self.Wd, self.d)
        self.transmitter.set_monitor(self.Ld, self.d)
        print("transmitter environment set")

    def specification(self, freq):
        self.excitePath = None
        pass

    def gradient_descent(self, unit_cond, alpha=0.5, gamma=0.9, linear_map=True):
        self.clean_results() # clean legacy, otherwise troublesome when plot
        print("Executing gradient ascent:\n")
        '''
        Topology optimization gradient descent parameters:
        1. alpha is learning rate
        2. gamma is gaussian filter radius shrinking rate per iteration
        3. linear_map means linear or nonlinear conductivity mapping from [0,1] to actual conductivity
        '''
        discriminant = 0 # convergence detector
        iterations = 200 # maximum iterations if not converging
        radius = self.nx/2/4 # radius for gaussian filter
        last_step = np.zeros(self.nx*self.ny) # Initial step of descent
        # Gradient ascent loop
        start_time = time.time()
        for index in range(iterations):
            print(f"Iteration{index}:")
            # # Map and calculate gradient
            unit_cond = np.clip(unit_cond, 0, 1) # restrict unit_cond to [0,1] in case of out of bound
            unit_cond_smoothed = scimage.gaussian_filter(unit_cond, radius) # Apply Gaussian filter
            # map unit to full
            if linear_map: cond = unit_cond_smoothed*5.8e7
            else: cond = 10**(9*unit_cond_smoothed - 4)
            # calculate gradient by adjoint method
            grad_cond = self.calculate_gradient(cond)
            rms_grad_cond = np.sqrt(np.mean(grad_cond**2)) # Calculate rms to see overall trend
            print(f"rms_grad = {rms_grad_cond}\n")

            # # Record ---------------------------------
            # Record conductivity (smoothed)
            file = open(self.results_history_path['cond'], "a")
            file.write(f"Iteration{index}, filter_radius={radius}\n")
            file.write(f"{cond}\n")
            file.close()
            # Record unit_cond
            file = open(self.results_history_path['unit_cond'], "a")
            file.write(f"Iteration{index}\n")
            file.write(f"{unit_cond}\n")
            file.close()
            # Record grad_cond
            file = open(self.results_history_path['grad_cond'], "a")
            file.write(f"Iteration{index}, rms={rms_grad_cond}\n")
            file.write(f"{grad_cond}\n")
            file.close() 
            # -------------------------------------------

            # # Do gradient descent
            # calculate unit_cond gradient by chain rule
            if linear_map: cond_by_ucs = unit_cond_smoothed/5.8e7 # linear case
            else: cond_by_ucs = 9 * np.log(10) * 10**(9 * unit_cond_smoothed - 4) # nonlinear case
            grad_uc = grad_cond * cond_by_ucs # first chain
            grad_uc = scimage.gaussian_filter(grad_uc, radius) # second chain (derivatives of kernel)
            step = grad_uc
            # Apply Adam algorithm
            step = self.Adam(step, index)
            # update conductivity distribution
            unit_cond = unit_cond + alpha * step

            # # Discriminant
            if np.dot(last_step, step) < 0: 
                discriminant += 1
                print(f"Discriminant detected, discriminant = {discriminant}")
                if discriminant >= 2: # oscillating around extremum
                    print("Local extremum detected, optimization process done")
                    break
            elif np.square(np.mean((step + last_step)**2)) < 0.001: # two consecutive tiny step, plateau case
                print("Local extremum detected, optimization process done")
                break
            # update radius to make next descent finer
            radius *= gamma
            # update last_step for next discriminant
            last_step = step
        if discriminant == 0: print(f"Problem unsolvable in {index+1} iterations")
        # Set converge (last update) for transmitter to read S11
        grad_cond = self.calculate_gradient(cond)
        end_time = time.time()
        print(f"{index+2} iterations in total, take time {start_time-end_time}")

    def calculate_gradient(self, cond):
        print("Calculating gradient...")
        # Receiver do plane wave excitation, export E and power
        print("Updating receiver conductivity distribution...")
        self.receiver.update_distribution(cond)
        print("Calculating receiver field...")
        Er_Path, powerPath = self.receiver.plane_wave_excitation(self.d, self.excitePath)
        # Transmitter do time reverse excitation
        feedPath = self.power_time_reverse(powerPath)
        print("Updating transmitter conductivity distribution...")
        self.transmitter.update_distribution(cond)
        print("Calculating transmitter field...")
        Et_Path = self.transmitter.feed_excitation(feedPath, self.d)
        # Calculate gradient by adjoint field method
        print("Calculating gradient by adjoint method...")
        E_received = self.Efile2gridE(Er_Path)
        E_excited = self.Efile2gridE(Et_Path)
        grad = np.flip(E_received,0)*E_excited
        grad = -np.sum(grad, axis=0)
        return grad
    
    def power_time_reverse(self, powerPath, plot=False):
        print("Executing time reversal...")
        # Read power file and make power list
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
        feedPath = "txtf\\reversed_power.txt"
        file = open(feedPath, "w")
        file.write("#\n#'Time / ns'	'default [Real Part]'\n#---------------------------------\n") # IDK why but don't change a word
        for pair in feed:
            file.write(f"{pair[0]} {pair[1]}\n")
        file.close()
        print(f"reversed power exported as '{feedPath}'")
        if plot: # for debug
            plt.figure(1)
            plt.plot(power.T[0], power.T[1])
            plt.figure(2)
            plt.plot(feed.T[0], feed.T[1])
            plt.show()
        print(f"Return {feedPath}")
        return feedPath
    
    def Efile2gridE(self, path):
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
        grid_E = np.array(grid_E) # [t0, t1, ...tk=[|E_1|,...|E_k|...,|E_169|],...t35]
        return grid_E

    def Adam(self, gradient, iteration):
        m = np.zeros(self.nx*self.ny)  # First moment
        v = np.zeros(self.nx*self.ny)  # Second moment
        beta1 = 0.9  # Decay rate for first moment
        beta2 = 0.999  # Decay rate for second moment
        epsilon = 1e-8  # Small value to prevent division by zero
        # Update biased first moment estimate
        m = beta1 * m + (1 - beta1) * gradient
        # Update biased second moment estimate
        v = beta2 * v + (1 - beta2) * (gradient ** 2)
        # Compute bias-corrected first and second moment estimates
        m_hat = m / (1 - beta1 ** iteration + epsilon)
        v_hat = v / (1 - beta2 ** iteration + epsilon)
        step = m_hat / (v_hat ** 0.5 + epsilon)
        # Record Adam parameters
        file = open("results\\Adam.txt", "a")
        file.write(f"Iteration{iteration}\n")
        file.write(f"m={m}\nv={v}\nm_hat={m_hat}\nv_hat={v_hat}\nstep={step}\n")
        file.close()
        # return step
        return step

    def clean_results(self):
        print("Cleaning results...")
        for result_path in self.results_history_path.values():
            if os.path.exists(result_path): os.remove(result_path)
        # Clean Adam.txt
        print("All files deleted successfully.")

    # Plotting function--------------------
    def plot_distribution(self, file_path, true_position=True, start=0, end=1):
        print("Plotting distribution history...")
        # txt to array (iterations of distribution)
        array_1D = self.parse_iteration_blocks(file_path)
        num_plots = len(array_1D)
        if start > end:
            print("Error: start > end")
            return None
        else: array_1D = array_1D[int(num_plots*start):int(num_plots*end)]
        array_1D = np.array(array_1D)
        # Plot figure
        # Determine grid size for subplots
        num_plots = len(array_1D)
        if num_plots == 0: 
            print("Array length = 0")
            return None
        cols = ceil(sqrt(num_plots))
        rows = ceil(num_plots / cols)
        # Create figure and subplots
        fig, axes = plt.subplots(rows, cols)
        fig.suptitle(file_path)
        axes = axes.flatten()  # Flatten the axes array for easy iteration
        # 1d to 2d (core)
        print("Creating figures...")
        if true_position:
            mid = (self.Ld/2, self.Wd/2)
            for index, distribution_1D in enumerate(array_1D):
                im = axes[index].imshow(distribution_1D.reshape(self.nx, self.ny), \
                                        extent=[-mid[0], self.Ld-mid[0], -mid[1], self.Wd-mid[1]], \
                                        norm=colors.CenteredNorm(), cmap='coolwarm')
                # axes[index].set_title(f'Iteration {index}')
        else:
            for index, distribution_1D in enumerate(array_1D):
                im = axes[index].imshow(distribution_1D.reshape(self.nx, self.ny), \
                    origin='upper', norm=colors.CenteredNorm(), cmap= 'coolwarm') #'gray_r', 'copper'
                axes[index].axis('off') # 'off' Hide axis for better visualization
        fig.colorbar(im, ax = axes[-1], fraction=0.1)
        # Remove any empty subplots
        for j in range(index + 1, len(axes)):
            fig.delaxes(axes[j])
        # plt.tight_layout()
        print("Figures created")

    def parse_iteration_blocks(self, file_path):
        print(f"Parsing iteration history of {file_path}...")
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
        print("Done, return array.")
        return result
    

if __name__ == "__main__":

    # Optimize any given antenna
    optimizer = Optimizer()
    optimizer.specification(2.4) # Fake, working on it
    unit_initial_antenna = add_noise(generate_shape(shape='alphabet', letter='G').ravel(), dB=0)
    optimizer.gradient_descent(unit_initial_antenna)

    # # Plot distribution of results
    # optimizer = Optimizer(call_controller=False)
    # for path in optimizer.results_history_path.values():
    #     for index in range(3):
    #         optimizer.plot_distribution(path, true_position=False, start=index/3, end=(index+1)/3)
    #         plt.show()