import numpy as np
import matplotlib.pyplot as plt
import csv


def data_dict():
    data_dict = []
    with open('csv/total_power.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            data_dict.append(float(row[0]))
        return np.array(data_dict)*10000

if __name__ == '__main__':
    data = data_dict()
    x = np.arange(len(data)+1)
    plt.plot(x[1:], data, marker='o')
    plt.grid()
    plt.title("Total Power")
    plt.xlabel("Iterations")
    plt.ylabel("Relative Power")
    plt.show()