import sys
sys.path.append(r"C:\Program Files (x86)\CST STUDIO SUITE 2023\AMD64\python_cst_libraries")
import cst
import cst.results as cstr
import cst.interface as csti


class MyInterface:
    def __init__(self,folder_path, fname):
        self.full_path = f'{folder_path}\\{fname}'
        self.results = cstr.ProjectFile(self.full_path, True) #bool: allow interactive
        self.de = None
        self.prj = None

    def read(self, result_item):
        try:
            res = self.results.get_3d().get_result_item(result_item)
            res = res.get_data()
        except:
            print("No result item. Available result items listed below")
            print(self.results.get_3d().get_tree_items())
            res = None
        return res

    def opencst(self):
        allpids = csti.running_design_environments()
        open = False
        for pid in allpids:
            self.de = csti.DesignEnvironment.connect(pid)
            for project_path in self.de.list_open_projects():
                # print(project_path)
                if self.full_path == project_path:
                    self.prj = self.de.get_open_project(project_path)
                    open = True
                    break
        if not open:
            self.de = csti.DesignEnvironment.new()
            self.prj = self.de.open_project(self.full_path)
            open = True

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
        # res = self.excute_vba (command)
        return command
    
    def create_shape(self, index, xmin, xmax, ymin, ymax, hc): #create or change are the same
        command = ['With Brick', '.Reset ', f'.Name "solid{index}" ', 
                   '.Component "component2" ', f'.Material "material{index}" ', 
                   f'.Xrange "{xmin}", "{xmax}" ', f'.Yrange "{ymin}", "{ymax}" ', 
                   f'.Zrange "0", "{hc}" ', '.Create', 'End With']
        return command
        # command = "\n".join(command)
        # self.prj.modeler.add_to_history(f"solid{index}",command)
    
    def create_material(self, index, sigma, type="Lossy metal"): #create or change are the same
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

    def start_simulate(self):
        try: # problems occur with extreme conditions
            # one actually should not do try-except otherwise severe bug may NOT be detected
            model = self.prj.modeler
            model.run_solver()
        except Exception as e: pass
    
    def set_plane_wave(self):  # doesn't update history, disappear after save but remain after simulation
        command = ['Sub Main', 'With PlaneWave', '.Reset ', 
                   '.Normal "0", "0", "-1" ', '.EVector "1", "0", "0" ', 
                   '.Polarization "Linear" ', '.ReferenceFrequency "2" ', 
                   '.PhaseDifference "-90.0" ', '.CircularDirection "Left" ', 
                   '.AxialRatio "0.0" ', '.SetUserDecouplingPlane "False" ', 
                   '.Store', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_plane_wave(self):
        command = ['Sub Main', 'PlaneWave.Delete', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def set_excitation(self, filePath): # doesn't update history, disappear after save but remain after simulation. 
        # set .UseCopyOnly to false otherwise CST read cache
        command = ['Sub Main', 'With TimeSignal ', '.Reset ', 
                   '.Name "signal1" ', '.SignalType "Import" ', 
                   '.ProblemType "High Frequency" ', 
                   f'.FileName "{filePath}" ', 
                   '.Id "1"', '.UseCopyOnly "false" ', '.Periodic "False" ', 
                   '.Create ', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_excitation(self):
        command = ['Sub Main', 'With TimeSignal', 
     '.Delete "signal1", "High Frequency" ', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_results(self):
        command = ['Sub Main',
        'DeleteResults', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def set_my_environment(self, Lg, Wg, hc, hs):
        paraDict = {"Lg":Lg, "Wg":Wg, "hc":hc, "hs":hs}
        for parameter in paraDict:
            self.create_para(parameter, paraDict[parameter])
        command = ['Component.New "component1"', 'Component.New "component2"',
                   'With Brick', '.Reset ', 
                   '.Name "ground" ', '.Component "component1" ', 
                   '.Material "Copper (annealed)" ', '.Xrange "-Lg/2", "Lg/2" ', 
                   '.Yrange "-Wg/2", "Wg/2" ', '.Zrange "-hc-hs", "-hs" ', '.Create', 
                   'End With', 'With Material', '.Reset', '.Name "FR-4 (lossy)"', 
                   '.Folder ""', '.FrqType "all"', '.Type "Normal"', 
                   '.SetMaterialUnit "GHz", "mm"', '.Epsilon "4.3"', '.Mu "1.0"', 
                   '.Kappa "0.0"', '.TanD "0.025"', '.TanDFreq "10.0"', 
                   '.TanDGiven "True"', '.TanDModel "ConstTanD"', '.KappaM "0.0"', 
                   '.TanDM "0.0"', '.TanDMFreq "0.0"', '.TanDMGiven "False"', 
                   '.TanDMModel "ConstKappa"', '.DispModelEps "None"', 
                   '.DispModelMu "None"', '.DispersiveFittingSchemeEps "General 1st"', 
                   '.DispersiveFittingSchemeMu "General 1st"', 
                   '.UseGeneralDispersionEps "False"', '.UseGeneralDispersionMu "False"', 
                   '.Rho "0.0"', '.ThermalType "Normal"', '.ThermalConductivity "0.3"', 
                   '.SetActiveMaterial "all"', '.Colour "0.94", "0.82", "0.76"', 
                   '.Wireframe "False"', '.Transparency "0"', '.Create', 'End With',
                   'With Brick', '.Reset ', '.Name "substrate" ', 
                   '.Component "component1" ', '.Material "FR-4 (lossy)" ', 
                   '.Xrange "-Lg/2", "Lg/2" ', '.Yrange "-Wg/2", "Wg/2" ', 
                   '.Zrange "-hs", "0" ', '.Create', 'End With ', 'With Cylinder ', 
                   '.Reset ', '.Name "sub" ', '.Component "component1" ', 
                   '.Material "Copper (annealed)" ', '.OuterRadius "1.6" ', 
                   '.InnerRadius "0.0" ', '.Axis "z" ', '.Zrange "-hc-hs", "-hs" ', 
                   '.Xcenter "5" ', '.Ycenter "-0.5" ', '.Segments "0" ', '.Create ', 
                   'End With', 'With Cylinder ', '.Reset ', '.Name "feedsub" ', 
                   '.Component "component1" ', '.Material "FR-4 (lossy)" ', 
                   '.OuterRadius "0.7" ', '.InnerRadius "0.0" ', '.Axis "z" ', 
                   '.Zrange "-hs", "0" ', '.Xcenter "5" ', '.Ycenter "-0.5" ', 
                   '.Segments "0" ', '.Create ', 'End With', 
                   'Solid.Subtract "component1:substrate", "component1:feedsub"', 
                   'Solid.Subtract "component1:ground", "component1:sub"', 'With Cylinder ', 
                   '.Reset ', '.Name "feed" ', '.Component "component1" ', 
                   '.Material "PEC" ', '.OuterRadius "0.7" ', '.InnerRadius "0.0" ', 
                   '.Axis "z" ', '.Zrange "-5-hc-hs", "hc" ', '.Xcenter "5" ', 
                   '.Ycenter "-0.5" ', '.Segments "0" ', '.Create ', 'End With', 
                   'With Cylinder ', '.Reset ', '.Name "coax" ', '.Component "component1" ', 
                   '.Material "Vacuum" ', '.OuterRadius "1.59" ', '.InnerRadius "0.7" ', 
                   '.Axis "z" ', '.Zrange "-5-hc-hs", "-hc-hs" ', '.Xcenter "5" ', 
                   '.Ycenter "-0.5" ', '.Segments "0" ', '.Create ', 'End With', 
                   'With Cylinder ', '.Reset ', '.Name "coaxouter" ', 
                   '.Component "component1" ', '.Material "PEC" ', '.OuterRadius "1.6" ', 
                   '.InnerRadius "1.59" ', '.Axis "z" ', '.Zrange "-5-hc-hs", "-hc-hs" ', 
                   '.Xcenter "5" ', '.Ycenter "-0.5" ', '.Segments "0" ', '.Create ', 
                   'End With']
        command = "\n".join(command)
        res = self.prj.modeler.add_to_history("initialize",command)
        return res
    
    def set_monitor(self, Ld, Wd, d, hc):
        margin = (Ld - d)/2
        EonPatch = ['With Monitor ', '.Reset ', '.Name "E_field_on_patch" ', 
                   '.Dimension "Volume" ', '.Domain "Time" ', '.FieldType "Efield" ', 
                   '.Tstart "0" ', '.Tstep "0.1" ', '.Tend "3.5" ', '.UseTend "True" ', 
                   '.UseSubvolume "True" ', '.Coordinates "Free" ', 
                   f'.SetSubvolume "0", "0", "0", "0", "-6.635", "{hc}" ', 
                   f'.SetSubvolumeOffset "{margin}", "{margin}", "{margin}", "{margin}", "{margin}", "{margin}" ', 
                   '.SetSubvolumeInflateWithOffset "True" ', '.PlaneNormal "z" ', 
                   f'.PlanePosition "{hc}" ', '.Create ', 'End With']
        PonFeed = ['With Monitor ', 
                   '.Reset ', '.Name "power_on_feed" ', '.Dimension "Volume" ', 
                   '.Domain "Time" ', '.FieldType "Powerflow" ', 
                   '.Tstart "0" ', '.Tstep "0.1" ', '.Tend "3.5" ', 
                   '.UseTend "True" ', '.UseSubvolume "True" ', '.Coordinates "Free" ', 
                   '.SetSubvolume "3.4", "6.6", "-1.5", "0.5", "-6.635", "0.035" ', 
                   '.SetSubvolumeOffset "0.0", "0.0", "0.0", "0.0", "0.0", "0.0" ', 
                   '.SetSubvolumeInflateWithOffset "True" ', '.PlaneNormal "z" ', 
                   '.PlanePosition "0.035" ', '.Create ', 'End With']
        command = EonPatch + PonFeed
        command = "\n".join(command)
        self.prj.modeler.add_to_history("set monitor",command)
    
    def set_port(self):
        command = ['Sub Main', 'Pick.PickEdgeFromId "component1:feed", "1", "1"', 
                   'Pick.PickEdgeFromId "component1:coaxouter", "1", "1"', 
                   'With DiscreteFacePort ', '.Reset ', '.PortNumber "1" ', 
                   '.Type "SParameter"', '.Label ""', '.Folder ""', '.Impedance "50.0"', 
                   '.VoltageAmplitude "1.0"', '.CurrentAmplitude "1.0"', '.Monitor "True"', 
                   '.CenterEdge "True"', '.SetP1 "True", "5.7", "-0.5", "-6.635"', 
                   '.SetP2 "True", "6.6", "-0.5", "-6.635"', '.LocalCoordinates "False"', 
                   '.InvertDirection "False"', '.UseProjection "False"', 
                   '.ReverseProjection "False"', '.FaceType "Linear"', '.Create ', 
                   'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def delete_port(self):
        command = ['Sub Main', 'Port.Delete "1"', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def export_E_field(self, outputPath, resultPath):
        step = 3 # grid width=3mm: one sample each grid
        command = ['Sub Main',
        'SelectTreeItem  ("%s")' % resultPath, 
        'With ASCIIExport', '.Reset',
        f'.FileName ("{outputPath}")',
        '.SetSampleRange(0, 35)',
        '.Mode ("FixedWidth")', '.Step (%s)' % step,
        '.Execute', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    def export_power(self, outputPath, resultPath):
        command = ['Sub Main',
        'SelectTreeItem  ("%s")' % resultPath, 
        'With ASCIIExport', '.Reset',
        f'.FileName ("{outputPath}")',
        '.SetSampleRange(0, 35)',
        '.StepX (4)', '.StepY (4)',
        '.Execute', 'End With', 'End Sub']
        res = self.excute_vba(command)
        return res
    
    
    # def export_3D_datas(self,  flag, start_frequency, end_frequency, step, file_path, mode): 
    #     if (mode == 'E'):
    #         if (flag):
    #             command = ['Sub Main',
    #                     'Reset',
    #                     'Dim monitorff As Double',
    #                     'For monitorff = %.2f To %.2f STEP %.2f' % (start_frequency, end_frequency, step),
    #                     r'SelectTreeItem("2D/3D Results E-Field\e-field (f="&CStr(monitorff)&") [pw]")',
    #                     'With ASCIIExport',
    #                     '.FileName ("%s" & "E-field-" & CStr(monitorff) & "GHz" & ".txt")' % file_path,
    #                     '.Execute',
    #                     'End With',
    #                     'Next monitorff',
    #                     'End Sub']
    #         else:
    #             command = ['Sub Main',
    #                     r'SelectTreeltem("2D/3D Results\E-Field\e-field (f=%3s) [pw]")' % start_frequency,
    #                     'With ASCIIExport',
    #                     '.Reset',
    #                     '.FileName ("%s" & "E-field-" & "%s" & "GHz" & ".txt")' % (file_path, start_frequency),
    #                     '.Execute',
    #                     'End With',
    #                     'End Sub']
    #         res = self.excute_vba ( command)
    #     elif (mode == 'I'):
    #         if (flag):
    #             command = ['Sub Main',
    #                     'Dim monitorff As Double',
    #                     'For monitorff = %.2f To %.2f STEP %.2f' % (start_frequency, end_frequency, step),
    #                     r'SelectTreeItem("2D/3D Results\Surface Current\surface current (f="&CStr(monitorff)&") [pw]")'
    #                     'With ASCIIExport',
    #                     '.Reset',
    #                     '.FileName ("%s" & "Surface-Current-" & CStr(monitorff) & "GHz" & ".txt")' % file_path,
    #                     '.Execute',
    #                     'End With',
    #                     'Next monitorff',
    #                     'End Sub']
    #         else:
    #             command = ['Sub Main',
    #                     'With ASCIIExport',
    #                     '.Reset',
    #                     '.FileName ("%s" & "Surface-Current-" & "%s" & "GHz" & ".txt")' % (file_path, start_frequency),
    #                     r'SelectTreeItem("2D/3D Results\Surface Current\surface current (f=%3s) [pw]")' % start_frequency,
    #                     '.Execute',
    #                     'With ASCIIExport',
    #                     '.Reset',
    #                     '.FileName ("%s" & "Surface-Current-" & "%s" & "GHz" & ".txt")' % (file_path, start_frequency),
    #                     '.Execute',
    #                     'End With',
    #                     'End Sub']
    #         res = self.excute_vba( command)
    #     else:
    #         print('Error mode (E or I only)!')
    #         res = False
    #     return res

    # def change_frequency(self,  min_frequency, max_frequency):
    #     command = ['Sub Main', 'Solver. Frequency Range "%s", "%s"' % (min_frequency, max_frequency), 'End Sub']
    #     res = self.excute_vba ( command)
    #     return res

    # def set_monitors(self,  start_frequency, end_frequency, nums, mode):
    #     command= ['Sub Main',
    #             'With Monitor',
    #             '.Reset',
    #             '.Domain "Frequency"',
    #             '.FieldType "%sfield"' % mode.upper(),
    #             '.Dimension "Volume"',
    #             '.UseSubvolume "False"',
    #             '.Coordinates "Structure"',
    #             '.SetSubvolume "-301.705", "301.705", "-301.705", "301.705", "-10", "610"',
    #             '.UseSubvolume "False"',
    #             '.Coordinates "Structure"',
    #             '.SetSubvolume "-301.705", "301.705", "-301.705", "301.705", "-10", "610"',
    #             '.SetSubvolumeOffset "0.0", "0.0", "0.0", "0.0", "0.0", "0.0"',
    #             '.Set SubvolumeInflateWithOffset "False"',
    #             '.CreateUsing Linear Samples "%s", "%s", "%s"' % (start_frequency, end_frequency, nums),
    #             'End With',
    #             'End Sub'] 
    #     res = self.excute_vba ( command)
    #     return res

    # def set_probe(self,  mode, x, y, z):
    #     #mode H/E
    #     if (mode != 'H' and mode != 'E'):
    #         print("Error mode (H/E Only)!")
    #         res = False
    #     else:
    #         command = ['Sub Main',
    #                 'With Probe',
    #                 '.Reset',
    #                 '. ID %s' % id,
    #                 '.AutoLabel 1',
    #                 '.Field "%sfield"' % mode,
    #                 '.Orientation "All"',
    #                 '.Xpos "%s"' % x,
    #                 '.Ypos "%s"' % y,
    #                 '.Zpos "%s"' % z,
    #                 '.Create',
    #                 'End With',
    #                 'End Sub']
    #         id += 1
    #         res = self.excute_vba( command)
    #     return res

    # def delete_probe(self,  id):
    #     command= ['Sub Main',
    #             'With Probe',
    #             '.DeleteById "%s"' % id,
    #             'End With',
    #             'End Sub']
    #     res = self.excute_vba ( command)
    #     return res

    # def export_probe_data(self,  file_path, mode, face, id):
    #     command = ['Sub Main',
    #             r'SelectTreeItem("1D Results\Probes\%s-Field\%s-Field (%s-%s) (Abs) [pw]")'\
    #                 % (mode.upper(), mode.upper(), face, id),
    #                 'With ASCIIExport',
    #                 '.Reset',
    #                 '.FileName ("%s" & "%s-field-" & "(%s-%s) (Abs)" & ".txt")' % (file_path, mode.upper(), face, id),
    #                 '.Execute',
    #                 'End With',
    #                 'End Sub']
    #     res = self.excute_vba ( command)
    #     return res

    # def export_voltage_data(self,  start_num, nums, file_path):
    #     for i in range(start_num, start_num, nums):
    #         name = i
    #         command = ['Sub Main',
    #                 r'SelectTreeItem("1D Results\Voltage Monitors\voltage%s [pw]")' % i,
    #                 'With ASCIIExport',
    #                 '.Reset',
    #                 '.FileName ("%s" & "voltage-" & "%s" & ".txt")' % (file_path, name),
    #                 '.Execute',
    #                 'End With',
    #                 'End Sub']
    #         res = self.excute_vba ( command)
    #     return res

# # Form Macro
# f = open("macro.txt")
# a = f.read()
# print(a.split("\n"))