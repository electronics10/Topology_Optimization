# Antenna Topology Optimization by Adjoint Method
## Introduction
This is a python implementation for antenna design automation. The program will automatically generate a planar antenna on a given design region according to input specifications such as operating frequency and bandwidth. This is done by solving an optimization problem which is to maximize the power recieved from the coaxial cable feed as an Rx antenna. Unlike traditional evolutionary optimization methods, adjoint method is adopted to calculate gradient and subsequently conduct gradient descent. In adjoint method theory, we consider each antenna topology as a functional, we can obtain the variation of the functional by performing inner product on the electric fields calculated from solving a forward problem and an adjoint problem. CST Studio Suite® 2023 is used to solve the forward and adjoint problem to obtain electric fields and power. Python is used to control the antenna design automation process such as setting up and calling CST, calculate gradient, and iteratively conduct gradient descent, etc.

**Reference:** Topology Optimization of Metallic Antennas.” _IEEE Transactions on Antennas and Propagation_ 62, no. 5 (May 2014): 2488–2500. [https://doi.org/10.1109/TAP.2014.2309112](https://doi.org/10.1109/TAP.2014.2309112).

---
## Setup
Before running the code, ensure you have the following installed:
- **CST Studio Suite®**: To solve EM problems. Official interface only support python 3.6~3.9.
- **Git**: To clone this repository.
- **Miniconda** or **Anaconda**: To manage the Python environment and dependencies.

### 1. Install Git
- **Windows**: Download and install Git from [git-scm.com](https://git-scm.com/downloads). Follow the default installation options.

Verify Git is installed by running:
```
git --version
```

### 2. Install Miniconda
Miniconda is a lightweight version of Anaconda that manages Python environments.
- Download Miniconda from [docs.conda.io](https://docs.conda.io/en/latest/miniconda.html) (choose the version for your OS: Windows, Mac, or Linux).
- Follow the installer instructions:
  - **Windows**: Double-click the `.exe` file and follow the prompts. Check "Add Miniconda to my PATH" if available.
- Restart your terminal after installation.

Verify Miniconda is installed by running:
```
conda --version
```

### 3. Clone the Repository
In a terminal or command prompt, navigate to the folder where you want the project and run:
```
git clone https://github.com/electronics10/Topology_Optimization.git
```
Then, enter the project directory:
```
cd Topology_Optimization
```

### 4. Set Up the Conda Environment
This project uses a predefined environment file (`environment.yml`) to install all dependencies.

- Create the environment:
```
conda env create -f environment.yml
```
- Activate the environment:
```
conda activate autotune
```

### 5. Run the Code
- Run the main script:
```
python main.py
```


### Troubleshooting
- If `conda` commands don’t work, ensure Miniconda is added to your system PATH or restart your terminal.
- For errors during `conda env create`, ensure you have an active internet connection, as it downloads packages.

---
