import numpy as np
import matplotlib.pyplot as plt
import csv


def data_dict():
    data_dict = []
    with open('csv/s11.csv', newline='') as csvfile:
        freq = []
        s11 = []
        reader = csv.reader(csvfile, delimiter = ' ')
        for row in reader:
            if len(row) == 0:
                data_dict.append([freq, s11])
                freq = []
                s11 = []
            else:   
                row = row[0].split(',')
                freq.append(float(row[0]))
                s11.append(float(row[1]))
    return np.array(data_dict)
        
def color_plot(all_data, indices):
    for index in indices:
        data = all_data[index-1]
        cc = np.random.rand(3)
        plt.plot(data[0], data[1], label=f"L{index}", \
                 color=[cc[0], cc[1], cc[2]])
    plt.legend()
    plt.grid()
    plt.title("S11")
    plt.xlabel("frequency (GHz)")
    plt.ylabel("S11 (dB)")
    plt.show()

def indices_input():
    indices = []
    string = input()
    string = string.split(' ')
    for ss in string:
        indices.append(int(ss))
    return indices

if __name__ == '__main__':
    indices = indices_input()
    all_data = data_dict()
    color_plot(all_data, indices)