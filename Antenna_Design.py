import sys
sys.path.append(r"C:\Program Files (x86)\CST STUDIO SUITE 2023\AMD64\python_cst_libraries")
sys.path.append(r"C:\Program Files (x86)\CST STUDIO SUITE 2024\AMD64\python_cst_libraries")
sys.path.append(r"C:\Program Files (x86)\CST STUDIO SUITE 2025\AMD64\python_cst_libraries")
import cst
import cst.results as cstr
import cst.interface as csti
import os
import time
import csv
import numpy as np
import matplotlib.pyplot as plt
import scipy.ndimage as scimage
from scipy.fft import fft, fftfreq
from PIL import Image, ImageDraw, ImageFont
import matplotlib.colors as colors
from math import ceil, sqrt
import difflib


# Design parameter
L = 48 # mm
W = 48 # mm
D = 3 # mm
NX= int(L//D)
NY = int(W//D)
TSTEP = 0.1 # default 0.1 ns for 1~3 GHz
TEND = 3.5 # default duration=3.5 ns for 1~3 GHz

LG = 104
WG = 104
HC = 0.035
HS = 1.6
FEEDX = 5
FEEDY = 0


class CSTInterface:
    def __init__(self, fname):
        self.full_path = os.getcwd() + f"\{fname}"
        self.opencst()

    def opencst(self):
        print("CST opening...")
        allpids = csti.running_design_environments()
        open = False
        for pid in allpids:
            self.de = csti.DesignEnvironment.connect(pid)
            # self.de.set_quiet_mode(True) # suppress message box
            print(f"Opening {self.full_path}...")
            try: self.prj = self.de.open_project(self.full_path)
            except: 
                print(f"Creating new project {self.full_path}")
                self.prj = self.de.new_mws()
                self.prj.save(self.full_path)
            open = True
            print(f"{self.full_path} open")
            break
        if not open:
            print("File path not found in current design environment...")
            print("Opening new design environment...")
            self.de = csti.DesignEnvironment.new()
            # self.de.set_quiet_mode(True) # suppress message box
            try: self.prj = self.de.open_project(self.full_path)
            except: 
                print(f"Creating new project {self.full_path}")
                self.prj = self.de.new_mws()
                self.prj.save(self.full_path)
            open = True
            print(f"{self.full_path} open")

    def read(self, result_item):
        results = cstr.ProjectFile(self.full_path, True) #bool: allow interactive
        try:
            res = results.get_3d().get_result_item(result_item)
            res = res.get_data()
        except:
            print("No result item.")
            available_files = results.get_3d().get_tree_items()
            closest_match = difflib.get_close_matches(result_item, available_files, n=1, cutoff=0.5)
            if closest_match: 
                result_item = closest_match[0] 
                print(f"Fetch '{result_item}' instead.")
            else: result_item = None
            res = results.get_3d().get_result_item(result_item)
            res = res.get_data()
        return res

    def save(self):
        self.prj.modeler.full_history_rebuild() 
        #update history, might discard changes if not added to history list
        self.prj.save()

    def close(self):
        self.de.close()

    def excute_vba(self,  command):
        command = "\n".join(command)
        vba = self.prj.schematic
        res = vba.execute_vba_code(command)
        return res

    def create_para(self,  para_name, para_value): #create or change are the same
        command = ['Sub Main', 'StoreDoubleParameter("%s", "%.4f")' % (para_name, para_value),
                'RebuildOnParametricChange(False, True)', 'End Sub']
        res = self.excute_vba (command)
        return command
    
    def create_shape(self, index, xmin, xmax, ymin, ymax, hc): #create or change are the same
        command = ['With Brick', '.Reset ', f'.Name "solid{index}" ', 
                   '.Component "component2" ', f'.Material "material{index}" ', 
                   f'.Xrange "{xmin}", "{xmax}" ', f'.Yrange "{ymin}", "{ymax}" ', 
                   f'.Zrange "0", "{hc}" ', '.Create', 'End With']
        return command
        # command = "\n".join(command)
        # self.prj.modeler.add_to_history(f"solid{index}",command)
    
    def create_cond_material(self, index, sigma, type="Lossy metal"): #create or change are the same
        command = ['With Material', '.Reset ', f'.Name "material{index}"', 
                #    '.Folder ""', '.Rho "8930"', '.ThermalType "Normal"', 
                #    '.ThermalConductivity "401"', '.SpecificHeat "390", "J/K/kg"', 
                #    '.DynamicViscosity "0"', '.UseEmissivity "True"', '.Emissivity "0"', 
                #    '.MetabolicRate "0.0"', '.VoxelConvection "0.0"', 
                #    '.BloodFlow "0"', '.MechanicsType "Isotropic"', 
                #    '.YoungsModulus "120"', '.PoissonsRatio "0.33"', 
                #    '.ThermalExpansionRate "17"', '.IntrinsicCarrierDensity "0"', 
                   '.FrqType "all"', f'.Type "{type}"', 
                   '.MaterialUnit "Frequency", "GHz"', '.MaterialUnit "Geometry", "mm"', 
                   '.MaterialUnit "Time", "ns"', '.MaterialUnit "Temperature", "Celsius"', 
                   '.Mu "1"', f'.Sigma "{sigma}"', 
                   '.LossyMetalSIRoughness "0.0"', '.ReferenceCoordSystem "Global"', 
                   '.CoordSystemType "Cartesian"', '.NLAnisotropy "False"', 
                   '.NLAStackingFactor "1"', '.NLADirectionX "1"', '.NLADirectionY "0"', 
                   '.NLADirectionZ "0"', '.Colour "0", "1", "1" ', '.Wireframe "False" ', 
                   '.Reflection "False" ', '.Allowoutline "True" ', 
                   '.Transparentoutline "False" ', '.Transparency "0" ', 
                   '.Create', 'End With']
        return command
        # command = "\n".join(command)
        # self.prj.modeler.add_to_history(f"material{index}",command)

    def set_frequency_solver(self):
        command = ['Sub Main', 'ChangeSolverType "HF Frequency Domain"', 
                   'Solver.FrequencyRange "1", "3"', 'End Sub']
        self.excute_vba(command)
        print("Frequency solver set")

    def set_time_solver(self):
        command = ['ChangeSolverType "HF Time Domain"', 
                   'Solver.FrequencyRange "1", "3"']
        command = "\n".join(command)
        self.prj.modeler.add_to_history("time_solver_and_freq_range",command)
        self.save()
        print("Time solver set")

    def start_simulate(self, plane_wave_excitation=False):
        print("Solving...")
        try: # problems occur with extreme conditions
            if plane_wave_excitation:
                command = ['Sub Main', 'With Solver', 
                '.StimulationPort "Plane wave"', 'End With', 'End Sub']
                self.excute_vba(command)
                print("Plane wave excitation = True")
            # one actually should not do try-except otherwise severe bug may NOT be detected
            model = self.prj.modeler
            model.run_solver()
        except Exception as e: pass
        print("Solved")
    
    def set_plane_wave(self):  # doesn't update history, disappear after save but remain after simulation
        command = ['Sub Main', 'With PlaneWave', '.Reset ', 
                   '.Normal "0", "0", "-1" ', '.EVector "1", "0", "0" ', 
                   '.Polarization "Linear" ', '.ReferenceFrequency "2" ', 
                   '.PhaseDifference "-90.0" ', '.CircularDirection "Left" ', 
                   '.AxialRatio "0.0" ', '.SetUserDecouplingPlane "False" ', 
                   '.Store', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def set_excitation(self, filePath): # doesn't update history, disappear after save but remain after simulation. 
        # set .UseCopyOnly to false otherwise CST read cache
        command = ['Sub Main', 'With TimeSignal ', '.Reset ', 
                   '.Name "signal1" ', '.SignalType "Import" ', 
                   '.ProblemType "High Frequency" ', 
                   f'.FileName "{filePath}" ', 
                   '.Id "1"', '.UseCopyOnly "false" ', '.Periodic "False" ', 
                   '.Create ', '.ExcitationSignalAsReference "signal1", "High Frequency"',
                   'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_plane_wave(self):
        command = ['Sub Main', 'PlaneWave.Delete', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_signal1(self):
        command = ['Sub Main', 'With TimeSignal', 
     '.Delete "signal1", "High Frequency" ', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def set_port(self, point1, point2): # Not a robust piece of code, but anyway
        command = ['Sub Main', 'Pick.PickEdgeFromId "component1:feed", "1", "1"', 
                   'Pick.PickEdgeFromId "component1:coaxouter", "1", "1"', 
                   'With DiscreteFacePort ', '.Reset ', '.PortNumber "1" ', 
                   '.Type "SParameter"', '.Label ""', '.Folder ""', '.Impedance "50.0"', 
                   '.VoltageAmplitude "1.0"', '.CurrentAmplitude "1.0"', '.Monitor "True"', 
                   '.CenterEdge "True"', f'.SetP1 "True", "{point1[0]}", "{point1[1]}", "{point1[2]}"', 
                   f'.SetP2 "True", "{point2[0]}", "{point2[1]}", "{point2[2]}"', '.LocalCoordinates "False"', 
                   '.InvertDirection "False"', '.UseProjection "False"', 
                   '.ReverseProjection "False"', '.FaceType "Linear"', '.Create ', 
                   'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_port(self):
        command = ['Sub Main', 'Port.Delete "1"', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def export_E_field(self, outputPath, resultPath, time_end, time_step, d_step):
        total_samples = int(time_end/time_step)
        command = ['Sub Main',
        'SelectTreeItem  ("%s")' % resultPath, 
        'With ASCIIExport', '.Reset',
        f'.FileName ("{outputPath}")',
        f'.SetSampleRange(0, {total_samples})',
        '.Mode ("FixedWidth")', f'.Step ({d_step})',
        '.Execute', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def export_power(self, outputPath, resultPath, time_end, time_step):
        total_samples = int(time_end/time_step)
        command = ['Sub Main',
        f'SelectTreeItem  ("{resultPath}")', 
        'With ASCIIExport', '.Reset',
        f'.FileName ("{outputPath}")',
        f'.SetSampleRange(0, {total_samples})',
        '.StepX (4)', '.StepY (4)',
        '.Execute', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_results(self):
        command = ['Sub Main',
        'DeleteResults', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def xz_symmetric_boundary(self): # don't know how to nonmanually delete though
        command = ['With Boundary', '.Xmin "expanded open"', 
                   '.Xmax "expanded open"', '.Ymin "expanded open"', '.Ymax "expanded open"', 
                   '.Zmin "expanded open"', '.Zmax "expanded open"', '.Xsymmetry "none"', 
                   '.Ysymmetry "magnetic"', '.Zsymmetry "none"', '.ApplyInAllDirections "False"', 
                   '.OpenAddSpaceFactor "0.5"', 'End With']
        command = "\n".join(command)
        self.prj.modeler.add_to_history("symmetric_boundary",command)
        self.save()
        print("Symmetric boundary set")

class Controller(CSTInterface):
    def __init__(self, fname):
        super().__init__(fname)
        self.Lg = LG
        self.Wg = WG
        self.hc = HC
        self.hs = HS
        self.feedx = FEEDX
        self.feedy = FEEDY
        self.Ld = L
        self.Wd = W
        self.d = D
        self.time_step = TSTEP
        self.time_end = TEND
        point1 = (self.feedx+self.hs/2-0.1, self.feedy, -5-self.hc-self.hs)
        point2 = (self.feedx+self.hs, self.feedy, -5-self.hc-self.hs)
        self.port = (point1, point2)


    # initialize ground, substrate, feed, and port
    def set_base(self):
        print("Setting base...")
        # Create ground, substrate, feed, and port
        ground = ['Component.New "component1"', 'Component.New "component2"',
                   'With Brick', '.Reset ', 
                   '.Name "ground" ', '.Component "component1" ', 
                   '.Material "Copper (annealed)" ', f'.Xrange "{-self.Lg/2}", "{self.Lg/2}" ', 
                   f'.Yrange "{-self.Wg/2}", "{self.Wg/2}" ', f'.Zrange "{-self.hc-self.hs}", "{-self.hs}" ', '.Create', 'End With']
        substrate = ['With Material', '.Reset', '.Name "FR-4 (loss free)"', 
                   '.Folder ""', '.FrqType "all"', '.Type "Normal"', 
                   '.SetMaterialUnit "GHz", "mm"', '.Epsilon "4.3"', '.Mu "1.0"', 
                   '.Kappa "0.0"', '.KappaM "0.0"', 
                   '.TanDM "0.0"', '.TanDMFreq "0.0"', '.TanDMGiven "False"', 
                   '.TanDMModel "ConstKappa"', '.DispModelEps "None"', 
                   '.DispModelMu "None"', '.DispersiveFittingSchemeEps "General 1st"', 
                   '.DispersiveFittingSchemeMu "General 1st"', 
                   '.UseGeneralDispersionEps "False"', '.UseGeneralDispersionMu "False"', 
                   '.Rho "0.0"', '.ThermalType "Normal"', '.ThermalConductivity "0.3"', 
                   '.SetActiveMaterial "all"', '.Colour "0.94", "0.82", "0.76"', 
                   '.Wireframe "False"', '.Transparency "0"', '.Create', 'End With',
                   'With Brick', '.Reset ', '.Name "substrate" ', 
                   '.Component "component1" ', '.Material "FR-4 (loss free)" ', 
                   f'.Xrange "{-self.Lg/2}", "{self.Lg/2}" ', f'.Yrange "{-self.Wg/2}", "{self.Wg/2}" ', 
                   f'.Zrange "{-self.hs}", "0" ', '.Create', 'End With ']
        ground_sub = ['With Cylinder ', '.Reset ', '.Name "sub" ', '.Component "component1" ', 
                   '.Material "Copper (annealed)" ', f'.OuterRadius "{self.hs}" ', 
                   '.InnerRadius "0.0" ', '.Axis "z" ', f'.Zrange "{-self.hc-self.hs}", "{-self.hs}" ', 
                   f'.Xcenter "{self.feedx}" ', f'.Ycenter "{self.feedy}" ', '.Segments "0" ', '.Create ', 
                   'End With', 'Solid.Subtract "component1:ground", "component1:sub"']
        substrate_sub = ['With Cylinder ', '.Reset ', '.Name "feedsub" ', 
                   '.Component "component1" ', '.Material "FR-4 (loss free)" ', 
                   f'.OuterRadius "{self.hs/2-0.1}" ', '.InnerRadius "0.0" ', '.Axis "z" ', 
                   f'.Zrange "{-self.hs}", "0" ', f'.Xcenter "{self.feedx}" ', f'.Ycenter "{self.feedy}" ', 
                   '.Segments "0" ', '.Create ', 'End With', 
                   'Solid.Subtract "component1:substrate", "component1:feedsub"'] 
        feed = ['With Cylinder ', '.Reset ', '.Name "feed" ', '.Component "component1" ', 
                   '.Material "PEC" ', f'.OuterRadius "{self.hs/2-0.1}" ', '.InnerRadius "0.0" ', 
                   '.Axis "z" ', f'.Zrange "{-5-self.hc-self.hs}", "{self.hc}" ', f'.Xcenter "{self.feedx}" ', 
                   f'.Ycenter "{self.feedy}" ', '.Segments "0" ', '.Create ', 'End With']
        coax = ['With Cylinder ', '.Reset ', '.Name "coax" ', '.Component "component1" ', 
                   '.Material "Vacuum" ', f'.OuterRadius "{self.hs-0.01}" ', f'.InnerRadius "{self.hs/2-0.1}" ', 
                   '.Axis "z" ', f'.Zrange "{-5-self.hc-self.hs}", "{-self.hc-self.hs}" ', f'.Xcenter "{self.feedx}" ', 
                   f'.Ycenter "{self.feedy}" ', '.Segments "0" ', '.Create ', 'End With', 
                   'With Cylinder ', '.Reset ', '.Name "coaxouter" ', 
                   '.Component "component1" ', '.Material "PEC" ', f'.OuterRadius "{self.hs}" ', 
                   f'.InnerRadius "{self.hs-0.01}" ', '.Axis "z" ', f'.Zrange "{-5-self.hc-self.hs}", "{-self.hc-self.hs}" ', 
                   f'.Xcenter "{self.feedx}" ', f'.Ycenter "{self.feedy}" ', '.Segments "0" ', '.Create ', 
                   'End With']
        command = ground + substrate + ground_sub + substrate_sub + feed + coax
        command = "\n".join(command)
        self.prj.modeler.add_to_history("initialize",command)
        self.save()
        print("Base set")
    
    def set_monitor(self):
        print("Setting monitor...")
        margin = (self.Ld - self.d)/2
        # Set monitor to read E field on domain
        EonPatch = ['With Monitor ', '.Reset ', '.Name "E_field_on_patch" ', 
                   '.Dimension "Volume" ', '.Domain "Time" ', '.FieldType "Efield" ', 
                   '.Tstart "0" ', f'.Tstep "{self.time_step}" ', f'.Tend "{self.time_end}" ', '.UseTend "True" ', 
                   '.UseSubvolume "True" ', '.Coordinates "Free" ', 
                   f'.SetSubvolume "0", "0", "0", "0", "{-5-self.hc-self.hs}", "{self.hc}" ', 
                   f'.SetSubvolumeOffset "{margin}", "{margin}", "{margin}", "{margin}", "{margin}", "{margin}" ', 
                   '.SetSubvolumeInflateWithOffset "True" ', '.PlaneNormal "z" ', 
                   f'.PlanePosition "{self.hc}" ', '.Create ', 'End With']
        # # Set monitor to read power at feed
        # PonFeed = ['With Monitor ', 
        #            '.Reset ', '.Name "power_on_feed" ', '.Dimension "Volume" ', 
        #            '.Domain "Time" ', '.FieldType "Powerflow" ', 
        #            '.Tstart "0" ', f'.Tstep "{self.time_step}" ', f'.Tend "{self.time_end}" ', 
        #            '.UseTend "True" ', '.UseSubvolume "True" ', '.Coordinates "Free" ', 
        #            f'.SetSubvolume "{self.feedx-1}", "{self.feedx+1}", "{self.feedy-1}", "{self.feedy+1}", "{-5-self.hc-self.hs}", "{self.hc}" ', 
        #            '.SetSubvolumeOffset "0.0", "0.0", "0.0", "0.0", "0.0", "0.0" ', 
        #            '.SetSubvolumeInflateWithOffset "True" ', '.PlaneNormal "z" ', 
        #            f'.PlanePosition "{self.hc}" ', '.Create ', 'End With']
        # command = EonPatch + PonFeed
        command = EonPatch
        command = "\n".join(command)
        self.prj.modeler.add_to_history("set monitor",command)
        self.save()
        print("Monitor set")

    def set_domain(self): 
        print("Setting domain...")
        # Initialize domain with uniform conductivity
        nx, ny = (int(self.Ld//self.d), int(self.Wd//self.d))
        cond = np.zeros(nx*ny)
        print(f"{nx*ny} pixels in total...")
        # Define materials first
        self.update_distribution(cond)
        command = []
        # Define shape and index based on materials
        for index, sigma in enumerate(cond): 
            midpoint = (self.Ld/2, self.Wd/2)
            xi = index%nx
            yi = index//nx
            xmin = xi*self.d-midpoint[0]
            xmax = xmin+self.d
            ymin = yi*self.d-midpoint[1]
            ymax = ymin+self.d
            command += self.create_shape(index, xmin, xmax, ymin, ymax, self.hc)
        command = "\n".join(command)
        self.prj.modeler.add_to_history("domain",command)
        self.save()
        print("Domain set")

    def update_distribution(self, cond):
        print("Conductivity distribution updating...")
        command_material = []
        for index, sigma in enumerate(cond):
            if sigma < 9000: command_material += self.create_cond_material(index, sigma, "Normal")
            else: command_material += self.create_cond_material(index, sigma)
        command_material = "\n".join(command_material)
        self.prj.modeler.add_to_history("material update",command_material)
        print("Conductivity distribution updated")

    def feed_excitation(self, feedPath):
        print("Start feed exciation")
        # Import feed file
        print("fe: importing feed file")
        feedPath = os.getcwd() + "\\" + feedPath # getcwd so CST don't load cache
        self.set_excitation(feedPath)
        # Start simulation with feed
        print("fe: simulating")
        self.set_port(self.port[0], self.port[1])
        self.start_simulate()
        # Export E field on patch to txt
        E_Path = "txtf\E_excited.txt"
        outputPath = os.getcwd() + "\\" + E_Path
        self.export_E_field(outputPath, "2D/3D Results\\E-Field\\E_field_on_patch [1]", self.time_end, self.time_step, self.d)
        print(f"fe: electric field exported as {outputPath}")
        # # Record s11 to s11.csv
        # s11 = self.read('1D Results\\S-Parameters\\S1,1')
        # with open('results\\s11.csv', 'a', newline='') as csvfile:
        #     writer = csv.writer(csvfile)
        #     for line in s11: # [[freq, s11, 50+j],...]
        #         line = np.abs(line) # change s11 from complex to absolute
        #         line[1] = 20*np.log10(line[1]) # convert to dB
        #         writer.writerow(line[:-1])
        #     writer.writerow([]) # space line for seperation from next call
        # # Record Tx_input_signal to Tx_input_signal.csv
        # Tx_input_signal = self.read('1D Results\\Port signals\\i1')
        # with open('results\\Tx_input_signal.csv', 'a', newline='') as csvfile:
        #     writer = csv.writer(csvfile)
        #     for line in Tx_input_signal: # [(time, signal_value),...]
        #         writer.writerow(line)
        #     writer.writerow([]) # space line for seperation from next call
        # # Record Tx_reflected_signal to Tx_reflected_signal.csv
        # Tx_reflected_signal = self.read('1D Results\\Port signals\\o1,1')
        # with open('results\\Tx_reflected_signal.csv', 'a', newline='') as csvfile2:
        #     writer2 = csv.writer(csvfile2)
        #     for line in Tx_reflected_signal: # [(time, signal_value),...]
        #         writer2.writerow(line)
        #     writer2.writerow([]) # space line for seperation from next call
        # Must delete before return, otherwise CST will save and raise popup window in next iteration
        self.delete_results() # otherwise CST may raise popup window
        self.delete_signal1() # otherwise CST may raise popup window
        self.delete_port() # otherwise CST may raise popup window
        print(f"Return E_Path")
        return E_Path

    def plane_wave_excitation(self, excitePath=None):
        print("Start plane wave excitation")
        # Import excitation file
        if excitePath: 
            print("pw: importing specified excitation file")
            excitePath = os.getcwd() + "\\" + excitePath # getcwd so CST don't load cache
            self.set_excitation(excitePath)
        ## Start simulation with plane wave
        print("pw: simulating")
        self.set_port(self.port[0], self.port[1])
        self.set_plane_wave()
        self.start_simulate(plane_wave_excitation=True)
        ## Export E field on patch to txt
        E_Path = "txtf\E_received.txt"
        outputPath = os.getcwd() + "\\" + E_Path
        self.export_E_field(outputPath, "2D/3D Results\\E-Field\\E_field_on_patch [pw]", self.time_end, self.time_step, self.d)
        print(f"pw: electric field exported as {outputPath}")
        ## Legacy-----------------------------------
        # # Return power on feed, must set Result Template on CST by hand in advance (IDK how to do it by code)
        # print("pw: return power on feed")
        # power = self.read("Tables\\1D Results\\power_on_feed (pw)_Abs_0D")
        # self.save() ------------------------------
        ## Legacy 2
        # Export Power Flow to txt
        # powerPath = "txtf\power.txt"
        # outputPath = os.getcwd() + "\\" + powerPath 
        # self.export_power(outputPath, "2D/3D Results\\Power Flow\\power_on_feed [pw]", self.time_end, self.time_step)
        # print(f"pw: power flow exported as {outputPath}")
        power_data = self.read('1D Results\\Port signals\\o1 [pw]')
        powerPath = "txtf\power.txt"
        file = open(powerPath, "w")
        file.write("#\n#'Time / ns'	'default [Real Part]'\n#---------------------------------\n") # IDK why but don't change a word
        for row in power_data:
            file.write(f"{row[0]} {row[1]}\n")
        file.close()
        # # Record Rx_signal to Rx_signal.csv
        # Rx_signal = self.read('1D Results\\Port signals\\o1 [pw]')
        # with open('results\\Rx_signal.csv', 'a', newline='') as csvfile:
        #     writer = csv.writer(csvfile)
        #     for line in Rx_signal: # [(time, signal_value),...]
        #         writer.writerow(line)
        #     writer.writerow([]) # space line for seperation from next call
        ## Must delete before return, otherwise CST will save and raise popup window in next iteration
        self.delete_results() # otherwise CST may raise popup window
        self.delete_port() # otherwise CST may raise popup window
        self.delete_plane_wave() # otherwise CST may raise popup window
        print(f"Return E_Path and powerPath")
        return E_Path, powerPath


# Optimizer Class
class Optimizer:
    def __init__(self, receiver = None, transmitter = None, set_environment=False):
        # Operating domain
        self.Ld = L
        self.Wd = W
        self.d = D
        self.nx = NX
        self.ny = NY
        self.time_step = TSTEP
        self.time_end = TEND
        self.excitePath = None # use CST default excitation for 1~3 GHz
        self.excitation_power = 1 # use CST default excitation for 1~3 GHz
        # Initiate controller (receiver and transmitter pair)
        self.receiver = receiver
        self.transmitter = transmitter
        if set_environment: self.set_environment()
        # Set initial optimization parameters
        self.iter_init = 0
        self.alpha = 1
        self.gamma = 0.9
        self.primal_init = 0.5 * np.ones(self.nx*self.ny)
        self.Adam_var_init = np.array([np.zeros(self.nx*self.ny), np.zeros(self.nx*self.ny), np.zeros(self.nx*self.ny), np.zeros(self.nx*self.ny)]) # [m, v, m_hat, v_hat]
        self.power_init = 100
        self.received_power = 0
        # not important
        os.makedirs("./results", exist_ok=True)
        os.makedirs("./txtf", exist_ok=True)
        self.results_history_path = {
            'cond':"results\\cond_smoothed_history.txt", 
            'primal':"results\\primal_history.txt",
            'grad_CST':"results\\grad_CST_history.txt",
            'step':"results\\step_history.txt"
            }

    def set_environment(self):
        # Set base and domain for receiver
        print("Setting environment for receiver...")
        self.receiver.set_base()
        self.receiver.set_domain()
        print("Receiver environment set")
        # # Set base and domain for transmitter
        # print("Setting environment for transmitter...")
        # self.transmitter.set_base()
        # self.transmitter.set_domain()
        # print("transmitter environment set")

    # Optimization core---------------------------------------------------------------------------------
    def gradient_ascent(self, max_iter=36, linear_map=False, filter=False, Adam=False, symmetric=True):
        print("Executing gradient ascent:\n")
        '''
        Topology optimization gradient descent parameters:
        1. alpha is learning rate
        2. gamma is gaussian filter radius shrinking rate per iteration
        3. linear_map means linear or nonlinear conductivity mapping from [0,1] to actual conductivity
        '''
        # Use symmetry to accelerate
        if symmetric: 
            self.receiver.xz_symmetric_boundary()
            # self.transmitter.xz_symmetric_boundary()
        # Set up initial parameters
        primal = self.primal_init
        adam_var = self.Adam_var_init
        discriminant = 0 # convergence detector
        radius = self.nx/16 # radius for gaussian filter
        ones = np.ones(self.nx*self.ny) # easier to read the code, not important
        # last_grad_CST = np.zeros(self.nx*self.ny) # Initial grad_CST of descent
        
        # Gradient ascent loop
        start_time = time.time()
        for index in range(self.iter_init, max_iter): # maximum iterations if doesn't converge
            print(f"\nIteration{index}:")
            # Apply Gaussian filter
            if filter:
                primal = scimage.gaussian_filter(primal.reshape(self.nx,self.ny), radius)
                primal = primal.ravel()
            
            # # Experimental. Assume mostly saddle points and self penalty trivial, we can clip to 0,1 for faster simulation in next iteration. 20250422
            # threshold = np.random.rand()
            # print(f"threshold = {threshold}")
            # for i, val in enumerate(primal):
            #     if val < threshold: primal[i] = 0
            #     else: primal[i] = 1
            
            # Map primal to cond
            if linear_map: 
                primal = np.clip(primal, 0, 1)
                cond = primal*5.8e7
            else: # log
                primal = np.clip(primal, 0, 1)
                cond = 10**(7.76 * primal) - 1
            # else: # sigmoid
            #     if index == 0: primal = 50 * (primal - 0.5*ones) # since default generation is binary but we don't want [0,1] interval
            #     primal = np.clip(primal, -25, 25) # otherwise inf, or nan raised (e^21 ~= 1.3e9)
            #     cond = 1/(ones + np.exp(-primal))*5.8e7 # 5.8e7*sigmoid(primal)
            
            # # Apply Gaussian filter
            # if filter:
            #     cond_smoothed = scimage.gaussian_filter(cond.reshape(self.nx,self.ny), radius)
            #     cond_smoothed = cond_smoothed.ravel()
            # else: cond_smoothed = cond
            
            cond_smoothed = cond # legacy
            
            # Calculate gradient by adjoint method
            it_start_time = time.time()
            grad_CST = self.calculate_gradient(cond_smoothed)
            it_end_time = time.time()
            print("iteration time =", it_end_time-it_start_time)

            # Record conductivity (smoothed)
            file = open(self.results_history_path['cond'], "a")
            file.write(f"Iteration{index}, filter_radius={radius}\n")
            file.write(f"{cond_smoothed}\n")
            file.close()
            # Record primal
            file = open(self.results_history_path['primal'], "a")
            file.write(f"Iteration{index}\n")
            file.write(f"{primal}\n")
            file.close()
            # Record grad_CST
            rms_grad_CST = np.sqrt(np.mean(grad_CST**2))
            file = open(self.results_history_path['grad_CST'], "a")
            file.write(f"Iteration{index}, rms_grad_CST={rms_grad_CST}\n")
            file.write(f"{grad_CST}\n")
            file.close() 

            # Gradient ascent
            # # Legacy--------
            # # calculate primal gradient by chain rule
            # # first chain (derivatives of kernel)
            # if filter: grad_cond = scimage.gaussian_filter(grad_CST, radius)
            # else: grad_cond = grad_CST
            # # second chain
            # if linear_map: 
            #     # cond_by_primal = 5.8e7 * ones # linear case
            #     cond_by_primal = 100 * ones # won't converge adjustment
            # else: 
            #     # cond_by_primal = 7.76 * np.log(10) * 10**(7.76 * primal) * 0.1**4 # log (0.1^4 because time and volume differential)
            #     # cond_by_primal = 5.8e7 * np.exp(-primal)/(ones + np.exp(-primal))**2 * 0.1**4 # sigmoid (0.1^4 because time and volume differential)
            #     cond_by_primal = ones # won't converge adjustment
            # grad_primal = grad_cond * cond_by_primal
            # # ----------
            grad_primal = grad_CST
            step = grad_primal
            # Apply Adam algorithm
            if Adam: step, adam_var = self.Adam(grad_primal, index, adam_var)
            primal = primal + self.alpha * step
            
            # # Experimental: Dyanmic learning rate (to escape local optima)
            # if index % 4 == 0: self.alpha = 3
            # elif index % 4 == 1: self.alpha = 5
            # elif index % 4 == 2: self.alpha = 7
            # elif index % 4 == 3: self.alpha = 1

            # Print rms to see overall trend
            print(f"rms_grad_CST = {rms_grad_CST}")
            print(f"rms_step = {np.sqrt(np.mean(step**2))}")
            # Record step
            file = open(self.results_history_path['step'], "a")
            file.write(f"Iteration{index}, rms_step={np.sqrt(np.mean(step**2))}\n")
            file.write(f"{step}\n")
            file.close()

            # Discriminant
            if index == 0: self.power_init = self.received_power
            if self.received_power >= 10*self.power_init: 
                print("Large received power detected.")
                discriminant += 1
            else: discriminant = 0 # reset
            if discriminant > 4:
                print("Optimization process done!")
                break
            print("received power = ", self.received_power)
            print("discriminant = ", discriminant)
            # update radius to make next descent finer
            if filter: 
                print("filter radius = ", radius)
                radius *= self.gamma
            else: pass
        if discriminant <= 5: print(f"Problem unsolvable in {index+1} iterations")
        

    def calculate_gradient(self, cond):
        print("Calculating gradient...")
        # Receiver do plane wave excitation, export E and power
        print("Updating receiver conductivity distribution...")
        self.receiver.update_distribution(cond)
        print("Calculating receiver field...")
        Er_Path, powerPath = self.receiver.plane_wave_excitation(self.excitePath)
        # Transmitter do time reverse excitation
        feedPath = self.power_time_reverse(powerPath)
        # print("Updating transmitter conductivity distribution...")
        # self.transmitter.update_distribution(cond)
        print("Calculating transmitter field...")
        Et_Path = self.transmitter.feed_excitation(feedPath)
        # Calculate gradient by adjoint field method
        print("Calculating gradient by adjoint method...")
        E_received = self.Efile2gridE(Er_Path)
        E_excited = self.Efile2gridE(Et_Path)
        # Some strange bug from CST (I think it's because of early convergence of time solver)
        len_r = len(E_received)
        len_e = len(E_excited)
        print("E_r, E_r[0]:", len_r, len(E_received[0]))
        print("E_e, E_e[0]", len_e, len(E_excited[0]))
        if len_e < len_r: E_received = E_received[:len_e]
        elif len_r < len_e: E_excited = E_excited[:len_r]
        else: pass
        # grad = np.flip(E_received,0)*E_excited # adjoint method
        grad = np.sum(np.flip(E_received,0) * E_excited, axis=2)
        grad = np.sum(grad, axis=0) # adjoint method continued (see paper: "Topology Optimization of Metallic Antenna")
        return grad

    # Adjoint method -------------------------------------------------------------------------------
    def power_time_reverse(self, powerPath):
        print("Executing time reversal...")
        # Read power file and make power list
        file = open(powerPath,'r')
        power_array = []
        total_power = 0 # record total power for overall validation
        # Legacy
        # t = 0.0
        # for line in file.readlines()[2:]: # First two lines are titles
        #     if line.startswith('Sample'): pass
        #     else:
        #         line = line.split() # x,y,z,Px,Py,Pz
        #         time = []
        #         time.append(t)
        #         poynting_z = float(line[5])
        #         time.append(poynting_z)
        #         power_array.append(time)
        #         t += self.time_step
        #         total_power += np.abs(poynting_z) # sum up Sz during an impulse of time
        last_time = 0.0
        for line in file.readlines()[3:]: # First three lines are titles
            line = line.split() # time, value
            current_time = float(line[0])
            current_value = float(line[1])
            power_array.append([current_time, current_value])
            # integration
            total_power += np.abs(current_value) * (current_time - last_time)
            last_time = current_time
        file.close()
        total_power = total_power/self.excitation_power # normalize
        self.received_power = total_power
        '''-------------------------------------------------
        Record received power while doing power_time_reverse for calculating gradient,
        otherwise lose the information since we don't have exact objective function.
        '''
        with open('results\\total_power.csv', 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([total_power])
        '''
        Didn't normalize since it's hard to tell the unit. 
        -----------------------------------------------------
        '''
        # Time reverse
        power_array = np.array(power_array)
        feed = np.array([power_array.T[0], np.flip(power_array.T[1], 0)])
        feed = feed.T
        # Write reversed power
        feedPath = "txtf\\reversed_power.txt"
        file = open(feedPath, "w")
        file.write("#\n#'Time / ns'	'default [Real Part]'\n#---------------------------------\n") # IDK why but don't change a word
        for pair in feed:
            file.write(f"{pair[0]} {pair[1]}\n")
        file.close()
        print(f"reversed power exported as '{feedPath}'")
        return feedPath
    
    def Efile2gridE(self, path):
        file1 = open(path,'r')
        grid_E = []
        time = []
        for line in file1.readlines()[2:]: # First two lines are titles
            if not (line.startswith('Sample')):
                line = line.split() # x,y,z,Ex,Ey,Ez
                # E_abs_square = 0
                # for word in line[:2:-1]: # Ez, Ey, Ex (because I want final word = Ex)
                #     word = float(word)
                #     E_abs_square += word**2
                # time.append(E_abs_square**(1/2)*np.sign(word))
                # E_x = float(line[3])
                # time.append(E_x)
                E_vec = [float(line[3]), float(line[4]), float(line[5])]
                time.append(E_vec)
            else:
                grid_E.append(time)
                time = []
        grid_E = grid_E[1:] # delete initial []
        file1.close()
        grid_E = np.array(grid_E) # [t0, t1, ...tk=[|E_1|,...|E_k|...,|E_169|],...tn]
        return grid_E

    # Descent algorithm---------------------------------------------------------------------------------------
    def Adam(self, gradient, iteration, adam_var):
        iteration = iteration + 1
        beta1 = 0.9  # Decay rate for first moment
        beta2 = 0.999  # Decay rate for second moment
        epsilon = 1e-8  # Small value to prevent division by zero
        # Update biased first moment estimate
        adam_var[0] = beta1 * adam_var[0] + (1 - beta1) * gradient
        # Update biased second moment estimate
        adam_var[1] = beta2 * adam_var[1] + (1 - beta2) * (gradient ** 2)
        # Compute bias-corrected first and second moment estimates
        adam_var[2] = adam_var[0] / (1 - beta1 ** iteration + epsilon)
        adam_var[3] = adam_var[1] / (1 - beta2 ** iteration + epsilon)
        step = adam_var[2] / (adam_var[3] ** 0.5 + epsilon)
        # Record Adam parameters
        file = open("results\\Adam.txt", "a")
        file.write(f"Iteration{iteration-1}, m_hat={np.mean(adam_var[2])}, v_hat={np.mean(adam_var[3])}\n")
        file.write(f"gradient=\n{gradient}\nm_hat=\n{adam_var[2]}\nv_hat=\n{adam_var[3]}\n")
        file.close()
        # return step
        return step, adam_var
    
    # Excitation control for antenna design--------------------------------------------------------------------
    def specification(self, spec_dic=None, set_monitor=True):
        if spec_dic == None: pass
        else:
            self.time_end = spec_dic["time_end"]
            self.time_step = spec_dic["time_step"]
            self.excitePath = spec_dic["excitePath"]
            self.excitation_power = spec_dic["power"]
            ## Reset impulse time informtion for controller
            self.receiver.time_step = self.time_step
            self.receiver.time_end = self.time_end
            # self.transmitter.time_step = self.time_step
            # self.transmitter.time_end = self.time_end
        # Set monitor
        if set_monitor:
            print("Setting monitor for receiver")
            self.receiver.set_monitor()
            # print("Setting monitor for transmitter")
            # self.transmitter.set_monitor()
        else: print("Specification: Use monitor from last history entry, make sure same time interval are used.")

    # just for convenience-------------------------------------------------------------------------
    def clean_results(self):
        print("Cleaning result legacy...")
        folder = os.getcwd() + "/results"
        for file in os.listdir(folder): 
            file = folder + "/" + file
            os.remove(file)
        print("All files deleted successfully.")


# Excitation signal generator
class Excitation_Generator:
    def __init__(self, amplitudes=[1, 1], frequencies=[1.5, 2.4], ratio_bw=[0.18, 0.1]):
        self.resolution = 10
        self.amplitudes = amplitudes
        self.frequencies = frequencies
        self.ratio_bw = ratio_bw
        self.time_end = None
        self.time_shift = None
        self.time_step = None
        self.excitePath = None
        self.t = None
        self.signal = None
        self.power = 0
        self.spec_dic = None

    def generate(self):
        print("customizing specification")
        '''
        - amplitudes: [Amplitudes] for each frequency component
        - frequecies: Multiple [frequencies] in GHz [2.4, 3.6, 5.1]
        - ratio_bw: Bandwidth-to-frequency [ratios] [0.1, 0.02, 0.5]
        Time unit in nanoseconds (ns).
        '''
        max_freq = max(self.frequencies)
        ## Make sure time step has no more than n digits, e.g. resolution=0.01 ns
        if max_freq < 2.5: self.time_step = np.around(1/(4 * max_freq), 1)
        elif max_freq < 25: self.time_step = np.around(1/(4 * max_freq), 2)
        elif max_freq < 500: self.time_step = np.around(1/(2 * max_freq), 3)
        else: 
            print("Input frequency too high")
            return None
        
        ## Calculate signal waveform
        # Automatically determine the duration based on the widest Gaussian pulse width
        max_sigma = max([1 / (2 * np.pi * freq * ratio) for freq, ratio in zip(self.frequencies, self.ratio_bw)])
        self.time_end = 8 * max_sigma  # Duration of the pulse (6 sigma captures ~99.7% of energy)
        self.time_shift = self.time_end/2
        self.time_end = 10*self.time_end # Need longer time interval for time reverse in adjoint method
        self.time_end = int(self.time_end) 
        # Time array shifted to start from 0 to self.time_end in nanoseconds (ns)
        self.t = np.linspace(0, self.time_end, int(self.time_end/(self.time_step/self.resolution))+1)
        # Generate the superposition of Gaussian sine pulses with adjustable bandwidth ratios and amplitudes
        self.signal = self.gaussian_sine_pulse_multi()
        # Normalize to 1
        self.signal = self.signal/np.max(self.signal)

        ## Write excitation file
        self.excitePath = "txtf\excitation.txt"
        os.makedirs(os.path.dirname(self.excitePath), exist_ok=True)
        file = open(self.excitePath, "w")
        file.write("#\n#'Time / ns'	'default [Real Part]'\n#---------------------------------\n") # IDK why but don't change a word
        for index, value in enumerate(self.signal):
            file.write(f"{self.t[index]} {value}\n")
        file.close()

        ## Calculate total power the signal carries
        last_time = 0.0
        for index, current_time in enumerate(self.t):
            current_value = self.signal[index]
            # integration
            self.power += np.abs(current_value) * (current_time - last_time) # power^1/2 actually 
            last_time = current_time 
         
        ## Update spec_dictionary
        self.spec_dic = {
            "time_end" : self.time_end,
            "time_step" : self.time_step,
            "excitePath" : self.excitePath,
            "power" : self.power}

    def gaussian_sine_pulse_multi(self):
        """
        Parameters:
        - amplitudes: List or array of amplitudes for each frequency component.
        - frequencies: List or array of frequencies (in GHz) for the sine waves.
        - ratios: List or array of bandwidth-to-frequency ratios.
        - t: Time array in nanoseconds (ns).
        """
        signal = np.zeros_like(self.t)
        # Superpose the Gaussian sine waves for each frequency
        for i, freq in enumerate(self.frequencies):
            sigma = 1 / (2 * np.pi * freq * self.ratio_bw[i])
            sine_wave = np.sin(2 * np.pi * freq * (self.t-self.time_shift))
            gaussian_envelope = self.amplitudes[i] * freq * self.ratio_bw[i] * \
            np.exp((-(self.t-self.time_shift)**2) / (2 * (sigma**2)))
            signal += gaussian_envelope * sine_wave
        return signal

    def plot_wave_and_spectrum(self):
        # Time-domain waveform plot
        plt.figure()
        plt.plot(self.t, self.signal)
        plt.title('Excitation Signal')
        plt.xlabel('Time (ns)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.show()
        # Frequency spectrum plot
        length = len(self.signal)
        fft_signal = fft(self.signal)
        fft_freq = fftfreq(length, (self.time_step/self.resolution))
        # Only take the positive half of the frequencies (real frequencies)
        positive_freqs = fft_freq[:length // (2*self.resolution)]
        magnitude_spectrum = np.abs(fft_signal[:length // (2*self.resolution)])
        # Plot the energy spectrum
        plt.figure()
        plt.plot(positive_freqs, magnitude_spectrum**2)
        plt.title('Energy Spectrum')
        plt.xlabel('Frequency (GHz)')
        plt.ylabel('Amplitude')
        plt.grid(True)
        plt.show()

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
            plt.title(file_path)
        else: # more than one plot (most of the cases)
            cols = ceil(sqrt(num_plots))
            rows = ceil(num_plots / cols)
            # Create figure and subplots
            fig, axes = plt.subplots(rows, cols)
            fig.suptitle(file_path)
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

# Some interesting initial antenna generator
def generate_shape(shape):
    array = np.zeros((NX, NY), dtype=np.int32)
    if shape == 'circle':
        print("generating circle")
        radius = min(NX, NY)//3
        center = (NX // 2, NY // 2)
        y, x = np.ogrid[:NX, :NX]
        dist_from_center = np.sqrt((x - center[0])**2 + (y - center[1])**2)
        array[dist_from_center <= radius] = 1
    elif shape == 'square': array = np.ones(NX*NY).reshape(NX,-1)
    elif shape == 'rectangle':
        horizontal = np.ones(NX)
        array = []
        for i in range(NX):
            if i < NX//3: horizontal[i]=0
            elif i > 2*NX//3: horizontal[i]=0
        for i in range (NY): array.append(horizontal)
        array = np.array(array)
    return array

def generate_alphabet(letter, font_size=8):
    print(f"generating letter {letter}")
    # Create a blank image with a white background
    img = Image.new('L', (NX, NY), 0)  # 'L' mode for grayscale, initialized with black (0)
    draw = ImageDraw.Draw(img)
    # Load a default font
    try:
        font = ImageFont.truetype("arial.ttf", font_size)  # You can replace this with any valid font path
    except:
        font = ImageFont.load_default()
    # Get the bounding box of the letter
    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
    # Calculate the position to center the letter
    position = (NX // 2 - text_width//1.8  , NY // 2 - text_height//1.2)
    # Draw the letter on the image
    draw.text(position, letter, fill=1, font=font)
    # Convert the image to a NumPy array (1 for white, 0 for black)
    array = np.array(img)
    return array

def add_noise_to_1D(binary_array, dB=0):
    print(f"adding noise with {dB}dB")
    length = len(binary_array)
    noise1 = np.random.rand(length)*0.00001*10**dB # 0.00001 because 5.8e7 scale is too large
    noise2 = np.random.rand(length)*0.00001*10**dB # 0.00001 because 5.8e7 scale is too large
    binary_array = binary_array + noise1 - noise2
    binary_array = np.clip(binary_array, 0, 1)
    return binary_array

# CST shutdown sometimes, continuation can be done by the following
def continue_iteration(exp, iter, alpha, Adam):
    iter = iter - 1
    primal_file = "primal_history.txt"
    step_file = "step_history.txt"
    Adam_file = "Adam.txt"
    # primal
    primal = read_experiment_history(exp, iter, primal_file)
    step = read_experiment_history(exp, iter, step_file)
    primal = primal + alpha * step
    primal = np.clip(primal, 0, 1)
    print(f"Primal iteration{iter+1} in experiment{exp} read.")
    # Adam
    if Adam:
        beta1 = 0.9  # Decay rate for first moment
        beta2 = 0.999  # Decay rate for second moment
        epsilon = 1e-8  # Small value to prevent division by zero
        adam_var = []
        m_hat, v_hat = read_Adam_history(exp, iter, Adam_file)
        adam_var.append(m_hat * (1 - beta1 ** (iter+1) + epsilon)) # adam_var[0]=m, iter+1 because my algorithm start from 1
        adam_var.append(v_hat * (1 - beta2 ** (iter+1) + epsilon)) # adam_var[1]=v, iter+1 because my algorithm start from 1
        adam_var.append(m_hat)
        adam_var.append(v_hat)
        adam_var = np.array(adam_var)
    else:
        zeros = np.zeros(len(primal))
        adam_var = np.array([zeros, zeros, zeros, zeros])
    # power_init
    # with open(f"experiments/exp{exp}/results/total_power.csv", newline='') as csvfile:
    with open("results/total_power.csv", newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=' ', quotechar='|')
        for row in spamreader:
            power_init = float(row[0])
            break
    return primal, adam_var, power_init

def read_experiment_history(exp, iter, assign):
    # filePath = f"experiments/exp{exp}/results/{assign}"
    filePath = f"results/{assign}"
    with open(filePath, 'r') as file:
        record = False
        string = ''
        for line in file:
            if record: 
                line = line.strip()
                if line.startswith(f'Iteration{iter+1}'): break
                line = line.strip('[')
                line = line.strip(']')
                string = string + line + ' '
            line=line.strip()
            if line.startswith(f'Iteration{iter}'): record = True
    string = np.array(string.split(), float)
    return string

def read_Adam_history(exp, iter, assign):
    # filePath = f"experiments/exp{exp}/results/{assign}"
    filePath = f"results/{assign}"
    with open(filePath, 'r') as file:
        record = False
        record_m = False
        record_v = False
        m_hat = ''
        v_hat = ''
        for line in file:
            if record_v:
                if line.startswith(f'Iteration{iter+1}'): break
                line = line.strip()
                line = line.strip('[')
                line = line.strip(']')
                v_hat = v_hat + line + ' '
            if record_m:
                if line.startswith(f'v_hat='): 
                    record_m = False
                    record_v = True
                    continue
                line = line.strip()
                line = line.strip('[')
                line = line.strip(']')
                m_hat = m_hat + line + ' '
            if record:
                if line.startswith(f'm_hat='): record_m = True
            line=line.strip()
            if line.startswith(f'Iteration{iter}'): record = True
    m_hat = np.array(m_hat.split(), float)
    v_hat = np.array(v_hat.split(), float)
    return m_hat, v_hat
