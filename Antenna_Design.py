import os
import time
import csv
import Controller as cc
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage as scimage
from scipy.fft import fft, fftfreq
from PIL import Image, ImageDraw, ImageFont


# Design parameter
L = 42
W = 42
D = 6


# Optimizer Class
class Optimizer:
    def __init__(self, set_environment=False):
        # Operating domain
        self.Ld = L
        self.Wd = W
        self.d = D
        self.nx = int(self.Ld//self.d)
        self.ny = int(self.Wd//self.d)
        self.time_step = 0.1 # default 0.1 ns for 1~3 GHz
        self.time_end = 3.5 # default duration=3.5 ns for 1~3 GHz
        self.excitePath = None # use CST default excitation for 1~3 GHz
        # initiate controller (receiver and transmitter pair)
        self.receiver = cc.Controller("CST_Antennas/receiver.cst")
        self.transmitter = cc.Controller("CST_Antennas/transmitter.cst")
        if set_environment: self.set_environment()
        # self.update_controller()
        # not important
        self.results_history_path = {
            'cond':"results\\cond_smoothed_history.txt", 
            'primal':"results\\primal_history.txt",
            'grad_CST':"results\\grad_CST_history.txt",
            'step':"results\\step_history.txt"
            }
        
    def update_controller(self):
        self.receiver.Ld = self.Ld
        self.receiver.Wd = self.Wd
        self.receiver.d = self.d
        self.receiver.time_step = self.time_step
        self.receiver.time_end = self.time_end
        self.receiver.set_monitor()
        self.transmitter.Ld = self.Ld
        self.transmitter.Wd = self.Wd
        self.transmitter.d = self.d
        self.transmitter.time_step = self.time_step
        self.transmitter.time_end = self.time_end
        self.transmitter.set_monitor()

    def set_environment(self):
        # Set base and domain for receiver
        print("Setting environment for receiver...")
        self.receiver.set_base()
        self.receiver.set_domain()
        print("Receiver environment set")
        # Set base and domain for transmitter
        print("Setting environment for transmitter...")
        self.transmitter.set_base()
        self.transmitter.set_domain()
        print("transmitter environment set")

    # Optimization core---------------------------------------------------------------------------------
    def gradient_descent(self, primal, alpha=0.1, gamma=0.9, linear_map=False, filter=True, Adam=True):
        self.clean_results() # clean legacy, otherwise troublesome when plot
        print("Executing gradient ascent:\n")
        '''
        Topology optimization gradient descent parameters:
        1. alpha is learning rate
        2. gamma is gaussian filter radius shrinking rate per iteration
        3. linear_map means linear or nonlinear conductivity mapping from [0,1] to actual conductivity
        '''
        discriminant = 0 # convergence detector
        iterations = 80 # maximum iterations if doesn't converge
        radius = self.nx/4 # radius for gaussian filter
        last_grad_CST = np.zeros(self.nx*self.ny) # Initial grad_CST of descent
        adam_var = np.array([np.zeros(self.nx*self.ny), np.zeros(self.nx*self.ny),\
            np.zeros(self.nx*self.ny), np.zeros(self.nx*self.ny)]) # Initialize variables in Adam algorithm: [m, v, m_hat, v_hat]
        ones = np.ones(self.nx*self.ny)
        # Gradient ascent loop
        start_time = time.time()
        for index in range(iterations):
            print(f"Iteration{index}:")
            # # Map and calculate gradient
            # map unit to full
            if linear_map: 
                primal = np.clip(primal, 0, 1)
                cond = primal*5.8e7
            else: 
                if index == 0: primal = 10 * primal
                cond = 10**(0.776 * np.clip(primal, 0, 10)) - 1
            # else: 
            #     if index == 0: primal = 50 * (primal - 0.5*ones) # since default generation is binary but we don't want [0,1] interval
            #     primal = np.clip(primal, -25, 25) # otherwise inf, or nan raised (e^21 ~= 1.3e9)
            #     cond = 1/(ones + np.exp(-primal))*5.8e7 # 5.8e7*sigmoid(primal)
            # apply Gaussian filter
            if filter: cond_smoothed = scimage.gaussian_filter(cond, radius)
            else: cond_smoothed = cond
            # calculate gradient by adjoint method
            it_start_time = time.time()
            grad_CST = self.calculate_gradient(cond_smoothed)
            it_end_time = time.time()
            print("iteration time =", it_end_time-it_start_time)

            # # Record ---------------------------------
            # Record conductivity (smoothed)
            file = open(self.results_history_path['cond'], "a")
            file.write(f"Iteration{index}, filter_radius={radius}\n")
            file.write(f"{cond_smoothed}\n")
            file.close()
            # Record primal
            file = open(self.results_history_path['primal'], "a")
            file.write(f"Iteration{index}\n")
            file.write(f"{primal}\n")
            file.close()
            # Record grad_CST
            file = open(self.results_history_path['grad_CST'], "a")
            file.write(f"Iteration{index}, rms_grad_CST={np.sqrt(np.mean(grad_CST**2))}\n")
            file.write(f"{grad_CST}\n")
            file.close() 
            # -------------------------------------------

            # # Do gradient descent
            # calculate primal gradient by chain rule
            # first chain (derivatives of kernel)
            if filter: grad_cond = scimage.gaussian_filter(grad_CST, radius)
            else: grad_cond = grad_CST
            # second chain
            if linear_map: 
                # cond_by_primal = 5.8e7 * ones # linear case
                cond_by_primal = 10 * ones # won't converge adjustment
            else: 
                # cond_by_primal = 9 * np.log(10) * 10**(9 * primal - 4) # original chain from paper
                # cond_by_primal = 5.8e7 * np.exp(-primal)/(ones + np.exp(-primal))**2
                cond_by_primal = 100 * ones
            # overall
            grad_primal = grad_cond * cond_by_primal
            step = grad_primal
            # Apply Adam algorithm
            if Adam: step, adam_var = self.Adam(step, index+1, adam_var)
                # if radius < self.nx/4: # filter coverage small enough
                #     if np.sqrt(np.mean((step-last_step)**2))<0.1: pass # not changing
                #     else: step, adam_var = self.Adam(step, index+1, adam_var)
                # else: step, adam_var = self.Adam(step, index+1, adam_var)
            # update conductivity distribution
            if index % 2 == 1: alpha = 1
            else: alpha = 0.1
            primal = primal + alpha * step

            # Print rms to see overall trend
            print(f"rms_grad_CST = {np.sqrt(np.mean(grad_CST**2))}")
            print(f"rms_step = {np.sqrt(np.mean(step**2))}\n")
            # Record step
            file = open(self.results_history_path['step'], "a")
            file.write(f"Iteration{index}, rms_step={np.sqrt(np.mean(step**2))}\n")
            file.write(f"{step}\n")
            file.close()

            # # Discriminant
            criterion = 0.00003
            if np.sqrt(np.mean(grad_CST**2)) < criterion: # heuristic (should come up with a more robust criterion)
                discriminant += 1
                print(f"rms_grad_CST < {criterion}, optimization process done")
                if discriminant > 0: # Set converge (last update) for transmitter to read S11
                    end_time = time.time()
                    print(f"{index+2} iterations in total, take time {end_time-start_time}")
                    break
            # elif np.sqrt(np.mean(grad_CST**2)) < 10*criterion: # heuristic
            #     if np.dot(last_grad_CST, grad_CST) < 0: 
            #         discriminant += 1
            #         print(f"Discriminant detected, discriminant = {discriminant}")
            #         if discriminant >= 4: # oscillating around extremum
            #             print("Local extremum detected, optimization process done")
            #             end_time = time.time()
            #             print(f"{index+2} iterations in total, take time {end_time-start_time}")
            #             break
            # update radius to make next descent finer
            if filter: radius *= gamma
            else: pass
            # update last_grad_CST for next discriminant
            last_grad_CST = grad_CST
        if discriminant == 0: print(f"Problem unsolvable in {index+1} iterations")
        

    def calculate_gradient(self, cond):
        print("Calculating gradient...")
        # Receiver do plane wave excitation, export E and power
        print("Updating receiver conductivity distribution...")
        self.receiver.update_distribution(cond)
        print("Calculating receiver field...")
        Er_Path, powerPath = self.receiver.plane_wave_excitation(self.excitePath)
        # Transmitter do time reverse excitation
        feedPath = self.power_time_reverse(powerPath)
        print("Updating transmitter conductivity distribution...")
        self.transmitter.update_distribution(cond)
        print("Calculating transmitter field...")
        Et_Path = self.transmitter.feed_excitation(feedPath)
        # Calculate gradient by adjoint field method
        print("Calculating gradient by adjoint method...")
        E_received = self.Efile2gridE(Er_Path)
        E_excited = self.Efile2gridE(Et_Path)
        print("E_r, E_r[0]:", len(E_received), len(E_received[0]))
        print("E_e, E_e[0]", len(E_excited), len(E_excited[0]))
        grad = np.flip(E_received,0)*E_excited # adjoint method
        grad = -np.sum(grad, axis=0) # adjoint method continued (see paper: "Topology Optimization of Metallic Antenna")
        return grad

    # Adjoint method -------------------------------------------------------------------------------
    def power_time_reverse(self, powerPath):
        print("Executing time reversal...")
        # Read power file and make power list
        file = open(powerPath,'r')
        power_array = []
        total_power = 0 # record total power for overall validation
        t = 0.0
        for line in file.readlines()[2:]: # First two lines are titles
            if line.startswith('Sample'): pass
            else:
                line = line.split() # x,y,z,Px,Py,Pz
                time = []
                time.append(t)
                poynting_z = float(line[5])
                time.append(poynting_z)
                power_array.append(time)
                t += self.time_step
                total_power += np.abs(poynting_z) # sum up Sz during an impulse of time
        file.close()
        '''-------------------------------------------------
        Record received power while doing power_time_reverse for calculating gradient,
        otherwise lose the information since we don't have exact objective function.
        '''
        with open('results\\total_power.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([total_power])
        '''
        Didn't normalize since it's hard to tell the unit. 
        -----------------------------------------------------
        '''
        # Time reverse
        power_array = np.array(power_array)
        feed = np.array([power_array.T[0], np.flip(power_array.T[1], 0)])
        feed = feed.T
        # Write reversed power
        feedPath = "txtf\\reversed_power.txt"
        file = open(feedPath, "w")
        file.write("#\n#'Time / ns'	'default [Real Part]'\n#---------------------------------\n") # IDK why but don't change a word
        for pair in feed:
            file.write(f"{pair[0]} {pair[1]}\n")
        file.close()
        print(f"reversed power exported as '{feedPath}'")
        return feedPath
    
    def Efile2gridE(self, path):
        file1 = open(path,'r')
        grid_E = []
        time = []
        for line in file1.readlines()[2:]: # First two lines are titles
            if not (line.startswith('Sample')):
                line = line.split() # x,y,z,Ex,Ey,Ez
                # E_abs_square = 0
                # for word in line[:2:-1]: # Ez, Ey, Ex (because I want final word = Ex)
                #     word = float(word)
                #     E_abs_square += word**2
                # time.append(E_abs_square**(1/2)*np.sign(word))
                E_x = float(line[3])
                time.append(E_x)
            else:
                grid_E.append(time)
                time = []
        grid_E = grid_E[1:] # delete initial []
        file1.close()
        grid_E = np.array(grid_E) # [t0, t1, ...tk=[|E_1|,...|E_k|...,|E_169|],...tn]
        return grid_E

    # Descent algorithm---------------------------------------------------------------------------------------
    def Adam(self, gradient, iteration, adam_var):
        beta1 = 0.9  # Decay rate for first moment
        beta2 = 0.999  # Decay rate for second moment
        epsilon = 1e-8  # Small value to prevent division by zero
        # Update biased first moment estimate
        adam_var[0] = beta1 * adam_var[0] + (1 - beta1) * gradient
        # Update biased second moment estimate
        adam_var[1] = beta2 * adam_var[1] + (1 - beta2) * (gradient ** 2)
        # Compute bias-corrected first and second moment estimates
        adam_var[2] = adam_var[0] / (1 - beta1 ** iteration + epsilon)
        adam_var[3] = adam_var[1] / (1 - beta2 ** iteration + epsilon)
        step = adam_var[2] / (adam_var[3] ** 0.5 + epsilon)
        # Record Adam parameters
        file = open("results\\Adam.txt", "a")
        file.write(f"Iteration{iteration}, m_hat={np.mean(adam_var[2])}, v_hat={np.mean(adam_var[3])}\n")
        file.write(f"gradient=\n{gradient}\nm_hat=\n{adam_var[2]}\nv_hat=\n{adam_var[3]}\n")
        file.close()
        # return step
        return step, adam_var
    
    # Excitation control for antenna design--------------------------------------------------------------------
    def specification(self, amplitudes=[1, 1], frequencies=[1.5, 2.4], ratio_bw=[0.18, 0.1], plot=True, CST_default=False):
        if CST_default: pass
        else:
            print("customizing specification")
            '''
            - amplitudes: [Amplitudes] for each frequency component
            - frequecies: Multiple [frequencies] in GHz [2.4, 3.6, 5.1]
            - ratio_bw: Bandwidth-to-frequency [ratios] [0.1, 0.02, 0.5]
            Time unit in nanoseconds (ns).
            '''
            max_freq = max(frequencies)
            ## Make sure time step has no more than n digits, e.g. resolution=0.01 ns
            if max_freq < 2.5: self.time_step = np.around(1/(4 * max_freq), 1)
            elif max_freq < 25: self.time_step = np.around(1/(4 * max_freq), 2)
            elif max_freq < 500: self.time_step = np.around(1/(2 * max_freq), 3)
            else: 
                print("Input frequency too high")
                return None
            
            ## Calculate signal waveform
            # Automatically determine the duration based on the widest Gaussian pulse width
            max_sigma = max([1 / (2 * np.pi * freq * ratio) for freq, ratio in zip(frequencies, ratio_bw)])
            self.time_end = 8 * max_sigma  # Duration of the pulse (6 sigma captures ~99.7% of energy)
            self.time_end = int(self.time_end) 
            # Time array shifted to start from 0 to self.time_end in nanoseconds (ns)
            t = np.linspace(0, self.time_end, int(self.time_end/self.time_step)+1)
            # Generate the superposition of Gaussian sine pulses with adjustable bandwidth ratios and amplitudes
            signal = self.gaussian_sine_pulse_multi(amplitudes, frequencies, ratio_bw, t, self.time_end)
            if plot: self.plot_wave_and_spectrum(signal, t, self.time_step)

            ## Write excitation file
            self.excitePath = "txtf\excitation.txt"
            file = open(self.excitePath, "w")
            file.write("#\n#'Time / ns'	'default [Real Part]'\n#---------------------------------\n") # IDK why but don't change a word
            for index, value in enumerate(signal):
                file.write(f"{t[index]} {value}\n")
            file.close()

        ## Reset monitor and impulse time informtion for controller
        self.update_controller()

    def gaussian_sine_pulse_multi(self, amplitudes, frequencies, ratios, t, duration):
        """
        Parameters:
        - amplitudes: List or array of amplitudes for each frequency component.
        - frequencies: List or array of frequencies (in GHz) for the sine waves.
        - ratios: List or array of bandwidth-to-frequency ratios.
        - t: Time array in nanoseconds (ns).
        """
        signal = np.zeros_like(t)
        # Superpose the Gaussian sine waves for each frequency
        for i, freq in enumerate(frequencies):
            sigma = 1 / (2 * np.pi * freq * ratios[i])
            sine_wave = np.sin(2 * np.pi * freq * (t-duration/2))
            gaussian_envelope = amplitudes[i] * freq * ratios[i] * np.exp((-(t-duration/2)**2) / (2 * (sigma**2)))
            signal += gaussian_envelope * sine_wave
        return signal

    def plot_wave_and_spectrum(self, signal, t, time_step):
        # Time-domain waveform plot
        plt.figure()
        plt.plot(t, signal)
        plt.title('Excitation Signal')
        plt.xlabel('Time (ns)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.show()
        # Frequency spectrum plot
        length = len(signal)
        fft_signal = fft(signal)
        fft_freq = fftfreq(length, time_step)
        # Only take the positive half of the frequencies (real frequencies)
        positive_freqs = fft_freq[:length // 2]
        magnitude_spectrum = np.abs(fft_signal[:length // 2])
        # Plot the energy spectrum
        plt.figure()
        plt.plot(positive_freqs, magnitude_spectrum**2)
        plt.title('Energy Spectrum')
        plt.xlabel('Frequency (GHz)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.show()

    # just for convenience-------------------------------------------------------------------------
    def clean_results(self):
        print("Cleaning result legacy...")
        for result_path in self.results_history_path.values():
            if os.path.exists(result_path): os.remove(result_path)
        # Clean Adam.txt
        if os.path.exists("results\\Adam.txt"): os.remove("results\\Adam.txt")
        # Clean total_power.csv
        if os.path.exists("results\\total_power.csv"): os.remove("results\\total_power.csv")
        # Clean s11.csv (Not good, optimizer shouldn't know the path of s11. but anyway)
        if os.path.exists("results\\s11.csv"): os.remove("results\\s11.csv")
        print("All files deleted successfully.")
    
    # Some interesting initial antenna generator (not important) -------------------------------------------------------
    def generate_binary_pixelated_antenna(self, n, shape, **kwargs):
        print("Generating initial antenna...")
        shape = self.generate_shape(n, shape, **kwargs)
        # initial = self.add_noise(shape.ravel())
        initial = shape.ravel()
        print("Initial antenna generated")
        return initial

    def generate_shape(self, n, shape, **kwargs):
        array = np.zeros((n, n), dtype=np.int32)
        if shape == 'circle':
            print("generating circle")
            radius = kwargs.get('radius', n//3)
            center = kwargs.get('center', (n // 2, n // 2))
            y, x = np.ogrid[:n, :n]
            dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
            array[dist_from_center <= radius] = 1
        elif shape == 'square': array = np.ones(n*n).reshape(n,-1)
        elif shape == 'rectangle':
            horizontal = np.ones(n)
            array = []
            for i in range(n):
                if i < n//3: horizontal[i]=0
                elif i > 2*n//3: horizontal[i]=0
            for i in range (n): array.append(horizontal)
            array = np.array(array)
        elif shape == 'alphabet':
            print("generatine alphabet")
            letter = kwargs.get('letter', 'F')
            font_size = kwargs.get('font_size', 8)
            array = self.generate_alphabet(letter, n, font_size)
        return array

    def generate_alphabet(self, letter, n, font_size):
        print(f"generating letter {letter}")
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

    def add_noise(self, binary_array, dB=0):
        print(f"adding noise with {dB}dB")
        length = len(binary_array)
        noise1 = np.random.rand(length)*0.00001*10**dB # 0.00001 because 5.8e7 scale is too large
        noise2 = np.random.rand(length)*0.00001*10**dB # 0.00001 because 5.8e7 scale is too large
        binary_array = binary_array + noise1 - noise2
        binary_array = np.clip(binary_array, 0, 1)
        return binary_array



if __name__ == "__main__":

    # # Optimize any given antenna
    optimizer = Optimizer(set_environment=False)
    optimizer.specification(amplitudes=[1], frequencies=[2], ratio_bw=[0.1], plot=False)
    initial = optimizer.generate_binary_pixelated_antenna(n=int(L//D), shape='square')
    initial = 0.5 * initial
    optimizer.gradient_descent(initial, linear_map=False, filter=False, Adam=False)
    
    
