import numpy as np
import matplotlib.pyplot as plt
import csv

def FourierTransform(data):
    time = data[0]
    signal = data[1]
    # Define new evenly spaced time grid
    start_time = 0.0
    end_time = time[-1] # last entry
    time = np.array(time)
    signal = np.array(signal)
    time_interval = 0.0005
    new_time = np.arange(start_time, end_time + time_interval, time_interval)
    # Interpolate values for new time grid
    new_signal = np.interp(new_time, time, signal)
    length = len(new_signal)
    fft_signal = np.fft.fft(new_signal)
    fft_freq = np.fft.fftfreq(length, time_interval)
    positive_freqs = fft_freq[:length // (2)]
    magnitude_spectrum = np.abs(fft_signal[:length // (2)])
    return (positive_freqs, magnitude_spectrum)


def data_dict(filePath):
    data_dict = []
    with open(filePath, newline='') as csvfile:
        time = []
        signal = []
        reader = csv.reader(csvfile, delimiter = ' ')
        for row in reader:
            if len(row) != 0:
                row = row[0].split(',')
                time.append(float(row[0]))
                signal.append(float(row[1]))
            else:
                data_dict.append([time, signal])
                time = []
                signal = []
    return data_dict
        
def color_plot(all_data1, all_data2, indices):
    if indices[0] == -1: indices = np.arange(0,len(all_data1))
    plt.figure()
    cc_index = 0
    cc_interval = int(256//len(indices))
    # time signal
    for index in indices:
        data = all_data1[index]
        plt.plot(data[0], data[1], label=f"L{index}", \
                 color=plt.cm.copper(cc_index*cc_interval))
        cc_index += 1
    plt.legend()
    plt.grid()
    plt.title("Input Signal")
    plt.xlabel("time (ns)")
    plt.ylabel("magnitude")

    # frequency spectrum
    plt.figure()
    cc_index = 0
    for index in indices:
        data = all_data1[index]
        FT_data = FourierTransform(data)
        start = 0
        end = 0
        for j, value in enumerate(FT_data[0]):
            if value >= 1 and start == 0:
                start = j - 1
            if value >= 3 and end == 0:
                end = j + 1
                break
        plt.plot(FT_data[0][start:end], 10*np.log(FT_data[1][start:end]), \
                 label=f"L{index}", color=plt.cm.copper(cc_index*cc_interval))
        cc_index += 1
    plt.legend()
    plt.grid()
    plt.title("Spectrum")
    plt.xlabel("frequency (GHz)")
    plt.ylabel("magnitude (dB)")

    # all_data2
    plt.figure()
    cc_index = 0
    # time signal
    for index in indices:
        data = all_data2[index]
        plt.plot(data[0], data[1], label=f"L{index}", \
                 color=plt.cm.copper(cc_index*cc_interval))
        cc_index += 1
    plt.legend()
    plt.grid()
    plt.title("Reflected Signal")
    plt.xlabel("time (ns)")
    plt.ylabel("magnitude")

    # frequency spectrum
    plt.figure()
    cc_index = 0
    for index in indices:
        data1 = all_data1[index-1]
        data2 = all_data2[index-1]
        FT_data1 = FourierTransform(data1)
        FT_data2 = FourierTransform(data2)
        start = 0
        end = 0
        for j, value in enumerate(FT_data2[0]):
            if value >= 1 and start == 0:
                start = j - 1
            if value >= 3 and end == 0:
                end = j + 1
                break
        plt.plot(FT_data2[0][start:end], 10*np.log(FT_data2[1][start:end]/FT_data1[1][start:end]), \
                 label=f"L{index}", color=plt.cm.copper(cc_index*cc_interval))
        cc_index += 1
    plt.legend()
    plt.grid()
    plt.title("S11 (likely wrong theoretically)")
    plt.xlabel("frequency (GHz)")
    plt.ylabel("magnitude (dB)")
    plt.show()

def indices_input():
    indices = []
    string = input("choose iterations: ")
    string = string.split(' ')
    for ss in string:
        indices.append(int(ss))
    return indices

if __name__ == '__main__':
    exp = input("experiment: ")
    indices = indices_input()
    filePath = f'experiments/exp{exp}/results/Tx_input_signal.csv'
    filePath2 = f'experiments/exp{exp}/results/Tx_reflected_signal.csv'
    all_data1 = data_dict(filePath)
    all_data2 = data_dict(filePath2)
    color_plot(all_data1, all_data2, indices)