import Antenna_Design as ad
import numpy as np

AMP = [0.4, 0.6] # weight for different frequency signal
FREQ = [1.8, 2.7] # GHz
BW = [0.13, 0.07] # ratio bandwidth
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
    topop = ad.Controller("CST_Antennas/topop.cst")
    topop.delete_results()
    topop.set_time_solver()
    optimizer = ad.Optimizer(topop, topop, set_environment=False)
    # optimizer.specification(excitation_generator.spec_dic, set_monitor=True)

    ## Topology optimization
    # parameters
    exp = "test3_3" # Legacy, not important
    iter = 0
    alpha = 1
    clean_legacy = True # set "False" for continuation, copy experiment results to global results folder
    linear_map = False
    filter = False
    Adam = False
    print(f"alpha={alpha}, linear_map={linear_map}, filter={filter}, Adam={Adam}")

    # set initial antenna topology
    if clean_legacy:
        initial = ad.generate_shape("square")
        # initial = ad.generate_shape("rectangle") 
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
