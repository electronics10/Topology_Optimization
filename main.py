import Antenna_Design as ad
import numpy as np

AMP = [1] # weight for different frequency signal
FREQ = [2.1] # GHz
BW = [0.1] # ratio bandwidth
# AXRR = [0, 0] # axial ratio reciprocal (minor_axis/major_axis)

if __name__ == "__main__":
    # Set excitation signal according to required specification
    excitation_generator = ad.Excitation_Generator()
    excitation_generator.amplitudes = AMP
    excitation_generator.frequencies = FREQ
    excitation_generator.ratio_bw = BW
    excitation_generator.generate()
    print("Spec_dictionary:", excitation_generator.spec_dic)
    # excitation_generator.plot_wave_and_spectrum()
    
    ## Initiate optimizer
    topop = ad.Controller("CST_Antennas/topop_hex.cst")
    topop.delete_results()
    topop.set_time_solver()
    optimizer = ad.Optimizer(topop, topop, set_environment=False)
    optimizer.specification(excitation_generator.spec_dic, set_monitor=True)

    ## Topology optimization
    # parameters
    exp = "hex7" # Legacy, not important
    iter = 0
    alpha = 0.5
    clean_legacy = True # set "False" for continuation, copy experiment results to global results folder
    linear_map = False
    filter = False
    Adam = True
    print(f"alpha={alpha}, linear_map={linear_map}, filter={filter}, Adam={Adam}")

    # set initial antenna topology
    def u_slot():
            half = []
            
            H0 = 3
            H1 = 2
            # H3 = 8-H0-H1
            L1 = 10
            D1 = 3
            L2 = 2
            D2 = D1
            
            arr1 = [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
            arr2 = []
            arr3 = []
            for j in range(16):
                if j<D1: arr2.append(1)
                elif j<D1+L1: arr2.append(0)
                else: arr2.append(1)
            for j in range(16):
                if j<D2: arr3.append(1)
                elif j<D2+L2: arr3.append(0)
                else: arr3.append(1)
            
            for i in range(8):
                if i < H0: half.append(arr1)
                elif i < H0 + H1: half.append(arr2)
                else: half.append(arr3)
            
            shape = half + half[::-1]
            shape = np.array(shape)
            return shape
        
    if clean_legacy:
        # initial = u_slot()
        # initial = ad.generate_shape("square")
        initial = ad.generate_shape("rectangle") 
        # initial = initial*0.5
        initial = initial.ravel()
    else:
        initial, adam_var, power_init = ad.continue_iteration(exp, iter, alpha, Adam)
        optimizer.Adam_var_init = adam_var
        optimizer.power_init = power_init

    # set optimizer and run
    optimizer.iter_init = iter
    optimizer.alpha = alpha
    optimizer.primal_init = initial
    if clean_legacy: optimizer.clean_results()
    optimizer.gradient_ascent(linear_map=linear_map, filter=filter, Adam=Adam, max_iter=64, symmetric=True)
