import os
import MyInterface as MI
import numpy as np
import matplotlib.pyplot as plt


class MyController:
    def __init__(self, fname): # Information of which project to open
        self.myinterface = MI.MyInterface(os.getcwd(), fname)
        self.myinterface.opencst()

    def set_environment(self,Lg, Wg, hc, hs): # initialize ground, substrate, feed, and port
        self.myinterface.set_environment(Lg, Wg, hc, hs)
        # self.myinterface.save()

    def set_domain(self, Ld, Wd, d, hc): # initialize domain with uniform conductivity
        nx, ny = (int(Ld//d), int(Wd//d))
        cond = np.ones(nx*ny)*5.8e7
        self.update_distribution(cond)
        command = []
        for index, sigma in enumerate(cond): 
            # self.myinterface.create_para(f"c{index}", sigma)
            # self.myinterface.create_material(index)
            # Down left to upright, better since it's the order CST export
            midpoint = (Ld/2, Wd/2)
            xi = index%nx
            yi = index//nx
            xmin = xi*d-midpoint[0]
            xmax = xmin+d
            ymin = yi*d-midpoint[1]
            ymax = ymin+d
            command += self.myinterface.create_shape(index, xmin, xmax, ymin, ymax, hc)
        command = "\n".join(command)
        self.myinterface.prj.modeler.add_to_history("domain",command)
        # self.myinterface.save()

    def set_monitor(self, Ld, Wd, d, hc):
        self.myinterface.set_monitor(Ld, Wd, d, hc)
        self.myinterface.save()

    def update_distribution(self, cond):
        print("Conductivity distribution updating")
        command_material = []
        # command = ['Sub Main']
        for index, sigma in enumerate(cond):
            # command.append(f'StoreDoubleParameter("c{index}", "{sigma}")')
            # Change material type for dielectric otherwise solver error
            if sigma < 9000: command_material += self.myinterface.create_material(index, sigma, "Normal")
            else: command_material += self.myinterface.create_material(index, sigma)
        # command.append('RebuildOnParametricChange(False, True)')
        # command.append('End Sub')
        # self.myinterface.excute_vba(command)
        # self.myinterface.save()
        command_material = "\n".join(command_material)
        self.myinterface.prj.modeler.add_to_history("material update",command_material)

    def feed_excitation(self, feedFile = "reversed_power.txt", outputName="E_excited.txt"):
        print("Start feed exciation")
        # Import feed file
        print("fe: importing feed file")
        feedFile = os.getcwd() + "\\" + feedFile
        self.myinterface.set_excitation(feedFile)
        # Start simulation with feed
        print("fe: simulating")
        self.myinterface.delete_results() # otherwise CST will raise popup window
        self.myinterface.set_port()
        self.myinterface.start_simulate()
        # Export E field on patch to txt
        outputPath = os.getcwd() + f"\{outputName}"
        self.myinterface.export_E_field(outputPath, "2D/3D Results\\E-Field\\E_field_on_patch [1]")
        print(f"fe: electric field exported as '{outputName}'")
        self.myinterface.delete_results()
        self.myinterface.delete_excitation()
        self.myinterface.delete_port()

    def plane_wave_excitation(self, outputName="E_received.txt"):
        print("Start plane wave excitation")
        # Start simulation with plane wave
        print("pw: simulating")
        self.myinterface.set_plane_wave()
        self.myinterface.start_simulate()
        # Export E field on patch to txt
        outputPath = os.getcwd() + f"\{outputName}"
        self.myinterface.export_E_field(outputPath, "2D/3D Results\\E-Field\\E_field_on_patch [pw]")
        print(f"pw: electric field exported as '{outputName}'")
        # # Return power on feed, must set Result Template on CST by hand in advance (IDK how to do it by code)
        # print("pw: return power on feed")
        # power = self.myinterface.read("Tables\\1D Results\\power_on_feed (pw)_Abs_0D")
        # self.myinterface.save()
        # Export Power Flow to txt
        outputPath = os.getcwd() + "\power.txt"
        self.myinterface.export_power(outputPath, "2D/3D Results\\Power Flow\\power_on_feed [pw]")
        print("pw: power flow exported as 'power.txt'")
        self.myinterface.delete_results()
        self.myinterface.delete_plane_wave()
    



