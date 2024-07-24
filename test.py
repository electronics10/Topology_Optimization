import os
import numpy as np
import matplotlib.pyplot as plt

# f = open("Amacro.txt")
# a = f.read()
# print(a.split("\n"))

powerPath = "My_Legacy\power.txt"
file = open(powerPath,'r')
power = []
t = 0
for line in file.readlines()[2:]: # First two lines are titles
    if line.startswith('Sample'): pass
    else:
        line = line.split() # x,y,z,Px,Py,Pz
        P_abs_square = 0
        time = []
        # for word in line[3:]:
        #     word = float(word)
        #     P_abs_square += word**2
        time.append(t)
        # time.append(P_abs_square**(1/2))
        time.append(float(line[3]))
        power.append(time)
        t += 0.1
file.close()
print(power)
