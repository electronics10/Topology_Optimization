import Antenna_Design as ad

AMP = [1] # weight for different frequency signal
FREQ = [2.45] # GHz
BW = [0.07] # ratio bandwidth

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
    optimizer = ad.Optimizer(topop, topop, set_environment=True)
    optimizer.specification(excitation_generator.spec_dic, set_monitor=True)

    ## Topology optimization
    # parameters
    exp = "test"
    iter = 0
    alpha = 1
    clean_legacy = True # set "False" for continuation, copy experiment results to global reults folder
    linear_map = False
    filter = False
    Adam = True
    print(f"alpha={alpha}, linear_map={linear_map}, filter={filter}, Adam={Adam}")

    # set initial antenna topology
    initial = ad.generate_shape("square")
    # initial = ad.generate_shape("rectangle") 
    initial = initial.ravel()
    # initial, adam_var = ad.continue_iteration(exp, iter, alpha, Adam)
    # print("Initial topology=\n", initial)

    # set optimizer and run
    optimizer.iter_init = iter
    optimizer.alpha = alpha
    optimizer.primal_init = initial
    # optimizer.Adam_var_init = adam_var
    if clean_legacy: optimizer.clean_results()
    optimizer.gradient_ascent(linear_map=linear_map, filter=filter, Adam=Adam, max_iter=36, symmetric=True)
