import numpy as np

if __name__ == "__main__":
    # Read and round primal
    exp = 25.2
    iter = 15
    filePath = f"experiments\\exp{exp}\\results\\primal_history.txt"
    with open(filePath, 'r') as file:
        record = False
        string = ''
        for line in file:
            if record: 
                print(line)
                line = line.strip()
                if line == f'Iteration{iter+1}': break
                line = line.strip('[')
                line = line.strip(']')
                string = string + line + ' '
            line=line.strip()
            if line == f'Iteration{iter}': record = True

    string = np.array(string.split(), float)
    print(string)
    string = np.rint(string) # ceil, floor, fix
    print(string)