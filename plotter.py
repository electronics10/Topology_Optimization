import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as colors
from math import ceil, sqrt
from matplotlib import cm
from matplotlib.colors import LinearSegmentedColormap
from settings import*

# Get the original 'coolwarm' colormap
coolwarm_cmap = cm.get_cmap('coolwarm')

# Create a list of colors from the first half (0 to 0.5) of 'coolwarm'
# We'll sample 256 colors for a smooth transition
colors = [coolwarm_cmap(i) for i in np.linspace(0.5, 1, 256)]

# Create a new colormap from this list of colors
half_coolwarm_cmap = LinearSegmentedColormap.from_list("half_coolwarm", colors)

# results plotting functions
class Plotter():
    def __init__(self):
        self.Ld = L
        self.Wd = W
        self.d = D
        self.nx = NX
        self.ny = NY
        self.results_history_path = {
            'cond':"results\\cond_smoothed_history.txt", 
            'primal':"results\\primal_history.txt",
            'grad_CST':"results\\grad_CST_history.txt",
            'step':"results\\step_history.txt"
            }
        
    def plot_distribution(self, file_path, true_position=True, start=0, end=1):
        print("Plotting distribution history...")
        # txt to array (iterations of distribution)
        array_1D = self.parse_iteration_blocks(file_path)
        if file_path == self.results_history_path['cond']: title = "Conductivity Distribution"
        elif file_path == self.results_history_path['primal']: title = "Distribution"
        elif file_path == self.results_history_path['grad_CST']: title = "Gradient"
        elif file_path == self.results_history_path['step']: title = "Step"
        num_plots = len(array_1D)
        if start > end:
            print("Error: start > end")
            return None
        else: array_1D = array_1D[int(num_plots*start):int(num_plots*end)]
        array_1D = np.array(array_1D)
        # Plot figure
        # Determine grid size for subplots
        num_plots = len(array_1D)
        if num_plots == 1:
            if true_position:
                mid = (self.Ld/2, self.Wd/2)
                im = plt.imshow(array_1D[0].reshape(self.nx, self.ny), \
                                        extent=[-mid[0], self.Ld-mid[0], -mid[1], self.Wd-mid[1]], \
                                        norm=colors.CenteredNorm(), cmap='coolwarm')
            else:
                im = plt.imshow(array_1D[0].reshape(self.nx, self.ny), \
                    origin='upper', norm=colors.CenteredNorm(), cmap= 'coolwarm') #'gray_r', 'copper'
            plt.colorbar(im)
            plt.title(title)
        else: # more than one plot (most of the cases)
            cols = ceil(sqrt(num_plots))
            rows = ceil(num_plots / cols)
            # Create figure and subplots
            fig, axes = plt.subplots(rows, cols)
            fig.suptitle(title)
            axes = axes.flatten()  # Flatten the axes array for easy iteration
            # 1d to 2d (core)
            print("Creating figures...")
            if true_position:
                mid = (self.Ld/2, self.Wd/2)
                for index, distribution_1D in enumerate(array_1D):
                    im = axes[index].imshow(distribution_1D.reshape(self.nx, self.ny), \
                                            extent=[-mid[0], self.Ld-mid[0], -mid[1], self.Wd-mid[1]], \
                                            norm=colors.CenteredNorm(), cmap='coolwarm')
                    # axes[index].set_title(f'Iteration {index}')
            else:
                for index, distribution_1D in enumerate(array_1D):
                    im = axes[index].imshow(distribution_1D.reshape(self.nx, self.ny), \
                        origin='upper', norm=colors.CenteredNorm(), cmap= 'coolwarm') #'gray_r', 'copper'
                    axes[index].axis('off') # 'off' Hide axis for better visualization
            fig.colorbar(im, ax = axes[-1], fraction=0.1)
            # Remove any empty subplots
            for j in range(index + 1, len(axes)):
                fig.delaxes(axes[j])
            # plt.tight_layout()
        print("Figures created")

    def parse_iteration_blocks(self, file_path):
        print(f"Parsing iteration history of {file_path}...")
        with open(file_path, 'r') as file:
            content = file.read().strip()  # Read the content and strip any extra whitespace
        iteration_blocks = content.split('Iteration')[1:]  # Split by 'Iteration' and ignore the first empty element
        result = []
        for block in iteration_blocks:
            block = block.strip()  # Strip any leading/trailing whitespace
            block_content = block.split('\n', 1)[1]  # Skip the '0', '1', etc., and get the rest of the content
            block_content = block_content.replace('\n', ' ')  # Replace newline characters with spaces
            block_content = block_content.replace('[', '').replace(']', '')  # Remove square brackets
            number_strings = block_content.split()  # Split the content by spaces
            numbers = [float(num) for num in number_strings]  # Convert the strings to integers
            result.append(numbers)
        print("Done, return array.")
        return result

    def plot_all_results(self, batch=1, true_position=False): # may plot only 1/batch of total history for long history
        for path in self.results_history_path.values():
            for index in range(batch):
                self.plot_distribution(path, true_position, start=index/batch, end=(index+1)/batch)
        plt.show()

if __name__ == "__main__":
    plotter = Plotter()
    plotter.plot_all_results(1, true_position=False)
    
    # f = open("macro.txt")
    # a = f.read()
    # print(a.split("\n"))
