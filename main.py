import Antenna_Design as ad


if __name__ == "__main__":
    # Set excitation signal according to required specification
    excitation_generator = ad.Excitation_Generator()
    excitation_generator.amplitudes=[1]
    excitation_generator.frequencies=[2.4]
    excitation_generator.ratio_bw=[0.1]
    excitation_generator.generate()
    print("Spec_dictionary:", excitation_generator.spec_dic)
    # excitation_generator.plot_wave_and_spectrum()

    # Set initial antenna topology for the first iteration and start gradient ascent
    # initial = ad.generate_shape("rectangle")
    # initial = initial.ravel()
    initial = ad.continue_iteration(exp=28, iter=4, alpha=1)
    print("Initial topology=\n", initial)
    
    # Set optimizer
    receiver = ad.Controller("CST_Antennas/receiver2.cst")
    transmitter = ad.Controller("CST_Antennas/transmitter.cst")
    receiver.delete_results()
    transmitter.delete_results()
    receiver.set_time_solver()
    transmitter.set_time_solver()
    optimizer = ad.Optimizer(receiver, transmitter, set_environment=False)
    optimizer.specification(excitation_generator.spec_dic, set_monitor=True)

    # Topology optimization
    alpha = 1
    linear_map = False
    filter = False
    Adam = False
    print(f"alpha={alpha}, linear_map={linear_map}, filter={filter}, Adam={Adam}")
    optimizer.gradient_ascent(initial, alpha=alpha, iterations=60, linear_map=linear_map, filter=filter, Adam=Adam)
