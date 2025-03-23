import numpy as np
import matplotlib.pyplot as plt
import csv


def data_dict(experiment):
    data_dict = []
    max_value = 0
    with open(f'experiments/exp{experiment}/results/total_power.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            current_value = float(row[0])
            data_dict.append(current_value)
            if current_value > max_value: max_value=current_value
    return np.array(data_dict)/max_value

if __name__ == '__main__':
    exp = input("experiment: ")
    data = data_dict(exp)
    x = np.arange(len(data)+1)
    plt.plot(x[1:], data, marker='o')
    plt.grid()
    plt.title("Total Power")
    plt.xlabel("Iterations")
    plt.ylabel("Relative Power")
    plt.show()