import Antenna_Design as ad


if __name__ == "__main__":
    # Set excitation signal according to required specification
    excitation_generator = ad.Excitation_Generator()
    excitation_generator.amplitudes=[1]
    excitation_generator.frequencies=[1.7]
    excitation_generator.ratio_bw=[0.1]
    excitation_generator.generate()
    print("Spec_dictionary:", excitation_generator.spec_dic)
    # excitation_generator.plot_wave_and_spectrum()

    # Set initial antenna topology for the first iteration and start gradient ascent
    initial = ad.generate_shape("rectangle")
    # initial = ad.generate_alphabet('E')
    # initial = 0.5 * initial
    print("Initial topology=\n", initial)
    initial = initial.ravel()
    
    # Set optimizer
    receiver = ad.Controller("CST_Antennas/receiver2.cst")
    transmitter = ad.Controller("CST_Antennas/transmitter.cst")
    optimizer = ad.Optimizer(receiver, transmitter, set_environment=False)
    optimizer.specification(excitation_generator.spec_dic, set_monitor=True)

    # Topology optimization
    alpha = 1
    linear_map = False
    filter = True
    Adam = True
    print(f"alpha={alpha}, linear_map={linear_map}, filter={filter}, Adam={Adam}")
    optimizer.gradient_ascent(initial, alpha=alpha, iterations=60, linear_map=linear_map, filter=filter, Adam=Adam)
