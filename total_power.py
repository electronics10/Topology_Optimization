import numpy as np
import matplotlib.pyplot as plt
import csv


def data_dict():
    data_dict = []
    max_value = 0
    with open(f'results/total_power.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            current_value = float(row[0])
            data_dict.append(current_value)
            if current_value > max_value: max_value=current_value
    return np.array(data_dict)/max_value

if __name__ == '__main__':
    data = data_dict()
    x = np.arange(len(data))
    plt.plot(x, data, marker='^')
    # plt.grid()
    plt.ylim(0, 1.1)
    x_max = 7
    plt.xlim(0, x_max)
    plt.xticks(np.arange(0, x_max+1, 1))
    plt.title("Relative Received Power at Feed")
    plt.xlabel("Number of Iterations")
    plt.ylabel("Normalized Relative Power")
    plt.show()
