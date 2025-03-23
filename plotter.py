from Antenna_Design import Plotter


if __name__ == "__main__":
    plotter = Plotter()
    plotter.plot_all_results(1, true_position=False)
    
    # f = open("macro.txt")
    # a = f.read()
    # print(a.split("\n"))