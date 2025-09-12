# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.5'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# +
# Definitions for (custom) poling from GitHub library

import numpy as np
import matplotlib.pyplot as plt

class Sellmeier:
    def __init__(self,A1,A2,A3,A4):
        self.A1 = A1
        self.A2 = A2
        self.A3 = A3
        self.A4 = A4
        self.n = lambda x: np.sqrt
        (A1 + A2/(x**2 - A3) - A4 * x**2)

class Wavenumbers:
    def __init__(self,A1,A2,A3,A4):
        self.A1 = A1
        self.A2 = A2
        self.A3 = A3
        self.A4 = A4
        self.c = 3e8
        self.conversion = 1e6
        self.x = lambda omega: 2*np.pi*self.c*self.conversion/omega
        self.k = lambda omega: omega * np.sqrt(self.A1 + self.A2/(self.x(omega)**2 - self.A3) - self.A4 * self.x(omega)**2)/self.c
        self.k1 = lambda omega: (self.A1*(self.x(omega)**2-self.A3)**2 + self.A2*(2*self.x(omega)**2-self.A3))/(self.c*(self.x(omega)**2-self.A3)**2*np.sqrt(self.A1+self.A2/(self.x(omega)**2-self.A3)-self.x(omega)**2*self.A4))
        self.k2 = lambda omega: (self.x(omega)**3*(self.A2*(-self.A2*(2*self.x(omega)**2+self.A3)+self.A1*(-3*self.x(omega)**4+2*self.x(omega)**2*self.A3+self.A3**2))+(self.x(omega)**2-self.A3)*(self.A1*(self.x(omega)**2-self.A3)**3+self.A2*(6*self.x(omega)**4-3*self.x(omega)**2*self.A3+self.A3**2))*self.A4))/(2*self.c**2*self.conversion*np.pi*(self.x(omega)**2-self.A3)**3*np.sqrt(self.A1+self.A2/(self.x(omega)**2-self.A3)-self.x(omega)**2*self.A4)*(-self.A2+(self.x(omega)**2-self.A3)*(-self.A1+self.x(omega)**2*self.A4)))

def func_to_matrix(lambda_func,list1,list2):
    A =[]
    for idx1 in list1:
        A_row = []
        for idx2 in list2:
            A_row += [lambda_func(idx1,idx2)]
        A += [A_row]
    return A

def pmf(domain_walls, domain_configuration, k):
    pmf_one_domain = lambda z1,z2:2*np.pi*1j*(np.exp(1j*k*z1)-np.exp(1j*k*z2))/(k*2*np.pi)
    pmf = 0
    for idx in range(len(domain_configuration)):
        pmf = pmf + domain_configuration[idx]*pmf_one_domain(domain_walls[idx],domain_walls[idx+1])
    return pmf

#from custom_poling.utils.pmf import pmf

class Crystal:
    """ A class for a poled crystal.
    
    Attr:
        domain_width
        number_domains
        z0
        length = domain_width * number_domains
        domain_walls
        domain_middles
    """

    def __init__(self, domain_width, number_domains, z0=0):
        """ Initialize the Crystal class.
        
        Params:
            domain_width
            number_domains
        """
        self.domain_width = domain_width
        self.number_domains = number_domains
        self.z0 = z0
        self.length = self.number_domains * self.domain_width
        self.domain_walls = np.arange(z0, z0 + (self.number_domains + 1) * self.domain_width, self.domain_width)
        self.domain_middles = (self.domain_walls + self.domain_width/2)[0:-1]
    
    def compute_pmf(self, domain_configuration, k_array):
        """Returns the phasematching function (PMF) as a function of k for a given domain_configuration.

        Args:
            domain_configuration (list of int): elements of list must be +1 or -1
            k_array (array of floats)

        Returns:
            PMF as an array of floats
        """
        self.domain_configuration = domain_configuration
        self.k_array = k_array
        crystal_pmf = pmf(self.domain_walls, self.domain_configuration, self.k_array)
        return crystal_pmf

    def plot_domains(self,domain_configuration,n_max=None,show=True,save_as=False,fix_ticks=False):
        x_axis = self.domain_walls
        y_axis = np.concatenate(([domain_configuration[0]],domain_configuration))
        if n_max != None and n_max < len(x_axis):
            x_axis = x_axis[0:n_max]
            y_axis = y_axis[0:n_max]
        plt.step(x_axis,y_axis)
        plt.xlabel('z')
        plt.ylabel('g(z)')
        plt.ylim([-1.2, 1.2])
        if fix_ticks==True:
            plt.xticks(rotation=45)
        if type(save_as)==str:
            plt.savefig(save_as)
            plt.close()
            print("Saved figure as: " + save_as)
        if show==False:
            plt.close()
        if show:
            plt.show()

#from custom_poling.core.crystal import Crystal
#from custom_poling.utils.pmf import pmf

class CustomCrystal(Crystal):

    def __init__(self, domain_width, number_domains, z0=0):
        super().__init__(domain_width, number_domains, z0)

    def compute_domains(self,target_amplitudes,k):
        domain_configuration = []
        amplitudes = []
        for target_amplitude in target_amplitudes:
            ampPRE = pmf(self.domain_walls,domain_configuration, k)
            ampUP  = pmf(self.domain_walls,domain_configuration + [1], k)
            ampDW  = pmf(self.domain_walls,domain_configuration + [-1], k)
            test_amplitudes = np.array([np.mean([ampPRE, ampUP]), np.mean([ampPRE, ampDW])])
            cost = target_amplitude - test_amplitudes
            cost = np.abs(cost)
            if cost[0] == np.min(cost):
                domain_configuration = domain_configuration + [1]
                amplitudes = amplitudes + [test_amplitudes[0]]
            elif cost[1] == np.min(cost):
                domain_configuration = domain_configuration + [-1]
                amplitudes = amplitudes + [test_amplitudes[1]]
        self.domain_configuration = np.array(domain_configuration)
        # self.amplitudes = amplitudes
        return self.domain_configuration

    # def compute_pmf(self, k_array): 
    #     self.pmf = super().compute_pmf(self.domain_configuration,k_array)
    #     return self.pmf

    def compute_pmf(self, k_array): 
        pmf = super().compute_pmf(self.domain_configuration,k_array)
        return pmf

    def plot_domains(self,n_max=None,show=True,save_as=False,fix_ticks=False): 
        super().plot_domains(self.domain_configuration,n_max,show,save_as,fix_ticks)

    def compute_amplitude(self,k,num_internal_points=0):
        amplitude_one_domain = lambda z1,z2:2*np.pi*1j*(np.exp(-1j*k*z2)-np.exp(-1j*k*z1))/(2*np.pi*k)
        amplitude = 0
        self.amplitudes = [0]
        z = self.z0
        z_array = [self.z0]
        for idx in range(len(self.domain_configuration)):
            domain_width = (self.domain_walls[idx+1]-self.domain_walls[idx])
            delta_z = domain_width/(num_internal_points+1)
            amplitudes_in = []
            for point in np.arange(1,num_internal_points+1):
                z = self.domain_walls[idx]+point*delta_z
                amplitudes_in = amplitudes_in + [amplitude + self.domain_configuration[idx]*amplitude_one_domain(self.domain_walls[idx],z)]
                z_array = z_array + [z] 
            amplitude = amplitude + self.domain_configuration[idx]*amplitude_one_domain(self.domain_walls[idx],self.domain_walls[idx+1])
            self.amplitudes = self.amplitudes + amplitudes_in + [amplitude]
            z_array = z_array + [self.domain_walls[idx+1]] 
        return self.amplitudes,z_array

class Target:

    def __init__(self,pmf_func,k_array):
        self.pmf_func = pmf_func
        self.k_array = k_array
        self.pmf = self.pmf_func(k_array)

    def plot_pmf(self,show=True,save_as=False,fix_ticks=False):
        """Plots the taret phasematching function (PMF).
        
        Returns:
            Plot of PMF as a function of k_array
        """
        plt.plot(self.k_array,np.abs(self.pmf),label='abs')
        plt.plot(self.k_array,np.real(self.pmf),'--',label='real')
        plt.plot(self.k_array,np.imag(self.pmf),'--',label='imag')
        plt.xlabel(r'$\Delta k$')
        plt.ylabel('Target PMF')
        plt.legend()
        if fix_ticks==True:
            plt.xticks(rotation=45)
        if type(save_as)==str:
            plt.savefig(save_as)
            plt.close()
            print("Saved figure as: " + save_as)
        if show==False:
            plt.close()
        if show:
            plt.show()

    def compute_amplitude(self,k,z_array,z0=0):
        """Computes the target amplitude.
        
        Returns:
            The target amplitude as a function of z_array.
        """
        self.k = k
        self.z_array = z_array
        self.z0 = z0
        amplitude = []
        for z1 in self.z_array:
            phase = lambda k1,k2,za,z0a: 1j*(np.exp(-1j*(k1-k2)*za)-np.exp(-1j*(k1-k2)*z0a))/(k1-k2)
            phase_factor = phase(self.k_array,self.k,z1,self.z0)
            self.dk = self.k_array[1]-self.k_array[0]
            kernel = self.pmf * phase_factor
            result = np.sum(kernel) * self.dk
            amplitude = amplitude + [result]
        self.amplitude = np.array(amplitude)/(2*np.pi)
        return self.amplitude

    def plot_amplitude(self,show=True,save_as=False,fix_ticks=False):
        """Plots the taret phasematching function (PMF).
        
        Returns:
            Plot of PMF as a function of k_array
        """
        plt.plot(self.z_array,np.abs(self.amplitude),'x',label='abs')
        plt.plot(self.z_array,np.real(self.amplitude),'.',label='real')
        plt.plot(self.z_array,np.imag(self.amplitude),'.',label='imag')
        plt.xlabel('z')
        plt.ylabel('Target Amplitude')
        plt.legend()
        if fix_ticks==True:
            plt.xticks(rotation=45)
        if type(save_as)==str:
            plt.savefig(save_as)
            plt.close()
            print("Saved figure as: " + save_as)
        if show==False:
            plt.close()
        if show:
            plt.show()


# -

# # Simulation classes

# ## Sellmeier equations

import numpy as np
import time
import datetime
from scipy.linalg import expm
from matplotlib import pyplot as plt
from tqdm import tqdm
from numpy import random


class Sellmeier:
    """
    A class to calculate the different material refractive indeces from the respective Sellmeier equations
    """
    def Sellmeier_LN(self, wl_Zelmon, extraordinary_axis):

        # Sellmeier eqations for LN
        # Zelmon et al; Infrared corrected Sellmeier coefficients for congruently grown lithium niobate and 5 mol. % magnesium oxide–doped lithium niobate
        A_ne = 2.9804
        B_ne = 0.02047
        C_ne = 0.5981
        D_ne = 0.0666
        E_ne = 8.9543
        F_ne = 416.08
        
        A_no = 2.6734
        B_no = 0.01764
        C_no = 1.2290
        D_no = 0.05914
        E_no = 12.614
        F_no = 474.6

        if extraordinary_axis:
            A = A_ne
            B = B_ne 
            C = C_ne
            D = D_ne
            E = E_ne
            F = F_ne
        else:
            A = A_no
            B = B_no 
            C = C_no
            D = D_no
            E = E_no
            F = F_no
            
        wl_Zelmon = 1e6*wl_Zelmon # takes wavelengths in um
        n_Zelmon = ((A * (wl_Zelmon**2)) / (wl_Zelmon**2 - B)) + ((C * (wl_Zelmon**2)) / (wl_Zelmon**2 - D)) + ((E * (wl_Zelmon**2)) / (wl_Zelmon**2 - F)) + 1
        
        n_Zelmon = np.sqrt(n_Zelmon)    
        return n_Zelmon

    def Sellmeier_SiO2(self, wl_SiO2):

        # Sellmeier eqations for SiO2
        # I. H. Malitson 'Interspecimen comparison of the refractive index of fused silica' J. Opt. Soc. Am. 55, 1205-1208 (1965)
        wl_SiO2 = 1e6*wl_SiO2 # takes wavelengths in um
        n_SiO2 = ((0.6961663 * (wl_SiO2**2)) / (wl_SiO2**2 - 0.0684043**2)) + ((0.4079426 * (wl_SiO2**2)) / (wl_SiO2**2 - 0.1162414**2)) + ((0.8974794 * (wl_SiO2**2)) / (wl_SiO2**2 - 9.896161**2)) + 1
                
        n_SiO2 = np.sqrt(n_SiO2)    
        return n_SiO2


# ## Dispersion Class

class Dispersion:

    """ A class that calculates the dispersion data from the mode solver data

    Attr:
        wavelength_pump
        wavelength_signal
        wavelength_idler

        mode_pump
        mode_signal
        mode_idler

        wls
        neffs
        mode_order
        group_velocities

        start_indices
        stop_indices

        neff_p
        neff_s
        neff_i

        v_p_c
        v_s_c
        v_i_c
    """
    hbar = 6.62607015e-34 / (2*np.pi) #reduced Planck constant in J/Hz (SI units)
    epsilon0 = 8.8541878188e-12 # vacuum permittivity in A*s/(V*m) (SI units)
    c = 299792458 # vacuum speed-of-light (SI units)

    def __init__(self, input_filepath, input_modes, input_wls, plot_boundaries=[], input_anticrossing_correction_info=[], make_plots=True):
        """         
        Params:
            input_filepath (contains path to file with the COMSOL eefective refractive index data)
            input_modes (modes, in decending oder, at the largest wl, at which the eefective refractive index was calculated)
            wls (corresponds to the wavelengths at which the refractive index was calculated as array of strings | in m) 
            input_anticrossing_correction_info (contains information about where anticrossing corrections are to be made to the eefective refractive index data read from file as [['location of anticrossing 1,'mode 1 (the lower one)','mode 1 (the higher one)'],[info about next anticrossing],...]
            plot_boundaries (contains info about where the eefective refractive index data is to be considered)
        """

        self.wls = input_wls
        self.mode_order = input_modes
        self.group_velocities = np.zeros((len(self.mode_order),len(self.wls)))

        self.start_indices = np.zeros((len(self.mode_order)), dtype=int)
        self.stop_indices = np.zeros((len(self.mode_order)), dtype=int) + len(self.wls) - 1
        
        self.neffs = self.read_dispersion_data(input_filepath, len(input_modes), len(self.wls))

        self.correct_anticrossings(input_anticrossing_correction_info, make_plots=make_plots)
        
        if make_plots:
            self.plot_eff_ref_index(plot_boundaries)
        

    def read_dispersion_data(self, filename, n_modes, n_wls):
        """
        reads effective refractive index data from file
        """
        
        Data = np.zeros((n_modes,n_wls))
        PolData = np.zeros((n_modes,n_wls))
        
        RawData = np.loadtxt(filename)
    
        count = 0
        for j in range(n_wls):
            for k in range(n_modes):
                Data[k][j] = RawData[count][3]
                Ex = RawData[count][1]
                Ey = RawData[count][2]
                # if Ex / Ey >= 2:
                #     PolData[k][j] = 1
                # elif Ey / Ex > 2:
                #     PolData[k][j] = 0
                # else:
                #     PolData[k][j] = 0.5
                count = count + 1
                    
        return Data#, PolData

    def correct_anticrossings(self, input_anticrossing_correction_info, make_plots=True):
        """
        correct for anticrossings in the dispersion data from the mode-solver 
        """
        # the input n*3 array contains information about [wavelength where anticrossing occurs, lower mode, higher mode]
        for i in range(len(input_anticrossing_correction_info)):
            wl_index = np.where(np.round(self.wls,9) == input_anticrossing_correction_info[i][0])[0][0]
            lower_mode = np.where(self.mode_order == input_anticrossing_correction_info[i][1])[0][0]
            higher_mode = np.where(self.mode_order == input_anticrossing_correction_info[i][2])[0][0]
            self.neffs[lower_mode][wl_index:], self.neffs[higher_mode][wl_index:] = self.neffs[higher_mode][wl_index:].copy(), self.neffs[lower_mode][wl_index:].copy()

        if make_plots:
            self.plot_eff_ref_index()
    
    def correct_anticrossings_gv(self, input_anticrossing_correction_info, make_plots=True):
        """
        remove the anticorssing conribution in the group velocity data by replacing with straight line
        the input n*3 array contains information about [index where anticrossing occurs, start of correction, stop of correction]
        """
        correction_start = np.where(np.round(self.wls,9) == input_anticrossing_correction_info[1])[0][0]
        correction_stop = np.where(np.round(self.wls,9) == input_anticrossing_correction_info[2])[0][0]
        correction_mode = np.where(self.mode_order == input_anticrossing_correction_info[0])[0][0]
        self.group_velocities[correction_mode][correction_start:correction_stop] = np.linspace(self.group_velocities[correction_mode][correction_start], self.group_velocities[correction_mode][correction_stop], num=len(self.group_velocities[correction_mode][correction_start:correction_stop]))

        if make_plots:
            self.plot_dispersion_data([self.wavelength_pump,self.wavelength_signal,self.wavelength_idler],[self.mode_pump,self.mode_signal,self.mode_idler])
        
    def plot_eff_ref_index(self, plot_boundaries2=[]):
        """
        plot the effective refractive index data in the specified ranges to cross-check corrections
        """
        if plot_boundaries2 != []:
            self.start_indices = plot_boundaries2[0]
            self.stop_indices = plot_boundaries2[1]

        # Note: areas featuring (corrected) (anti-)crossing between different modes indicate wavelength ranges with strong coupling between the respective modes (best avoided in experiments)
        plt.figure(dpi=100)
        
        plt.plot(1e9*self.wls[self.start_indices[4]:self.stop_indices[4]], self.neffs[4][self.start_indices[4]:self.stop_indices[4]], marker='x', linestyle='solid', linewidth=1, markersize=2, label=self.mode_order[4])
        plt.plot(1e9*self.wls[self.start_indices[3]:self.stop_indices[3]], self.neffs[3][self.start_indices[3]:self.stop_indices[3]], marker='x', linestyle='solid', linewidth=1, markersize=2, label=self.mode_order[3])
        plt.plot(1e9*self.wls[self.start_indices[2]:self.stop_indices[2]], self.neffs[2][self.start_indices[2]:self.stop_indices[2]], marker='x', linestyle='solid', linewidth=1, markersize=2, label=self.mode_order[2])
        plt.plot(1e9*self.wls[self.start_indices[1]:self.stop_indices[1]], self.neffs[1][self.start_indices[1]:self.stop_indices[1]], marker='x', linestyle='solid', linewidth=1, markersize=2, label=self.mode_order[1])
        plt.plot(1e9*self.wls[self.start_indices[0]:self.stop_indices[0]], self.neffs[0][self.start_indices[0]:self.stop_indices[0]], marker='x', linestyle='solid', linewidth=1, markersize=2, label=self.mode_order[0])
        
        plt.xlabel("wavelength (nm)")
        plt.ylabel("effective refractive index")
        plt.legend(loc="upper right",fontsize=8)
        plt.title("waveguide dispersion")
        plt.show()

    def calc_group_velocities(self, input_wls, input_modes, make_plots=True, plot_boundaries=[]):
        """
        calculate the group velocities from the effective refractive index data
        """
        # calculate group velocities
        for i in range((len(self.mode_order))):
            derivative = np.gradient(self.neffs[i],(self.wls[1]-self.wls[0]),edge_order=1)
            self.group_velocities[i] = self.c / (self.neffs[i] - self.wls*derivative)

        self.wavelength_pump = input_wls[0]
        self.wavelength_signal = input_wls[1] 
        self.wavelength_idler = input_wls[2]

        self.mode_pump = input_modes[0]
        self.mode_signal = input_modes[1]
        self.mode_idler = input_modes[2]

        wl_index1 = np.where(np.round(self.wls,9) == self.wavelength_pump)[0][0]
        wl_index2 = np.where(np.round(self.wls,9) == self.wavelength_signal)[0][0]
        wl_index3 = np.where(np.round(self.wls,9) == np.round(self.wavelength_idler,9))[0][0]

        mode_index1 = np.where(self.mode_order == self.mode_pump)[0][0]
        mode_index2 = np.where(self.mode_order == self.mode_signal)[0][0]
        mode_index3 = np.where(self.mode_order == self.mode_idler)[0][0]

        # define the effetive refractive indices at the central frequencies
        self.neff_p = self.neffs[mode_index1][wl_index1] 
        self.neff_s = self.neffs[mode_index2][wl_index2]
        self.neff_i = self.neffs[mode_index3][wl_index3]
        
        # define the group velocities indices at the central frequencies
        self.v_p_c = self.group_velocities[mode_index1][wl_index1] 
        self.v_s_c = self.group_velocities[mode_index2][wl_index2]
        self.v_i_c = self.group_velocities[mode_index3][wl_index3]

        if make_plots:
            self.plot_dispersion_data(input_wls, input_modes, plot_boundaries)

    def plot_dispersion_data(self, input_wls, input_modes, plot_boundaries2=[]):
        """
        plot the full dispersion data of the waveguide
        """
        if plot_boundaries2 != []:
            self.start_indices = plot_boundaries2[0]
            self.stop_indices = plot_boundaries2[1]

        wavelength_pump_plot = input_wls[0]
        wavelength_signal_plot = input_wls[1] 
        wavelength_idler_plot = input_wls[2]

        mode_pump_plot = input_modes[0]
        mode_signal_plot = input_modes[1]
        mode_idler_plot = input_modes[2]

        wl_index1 = np.where(np.round(self.wls,9) == wavelength_pump_plot)[0][0]
        wl_index2 = np.where(np.round(self.wls,9) == wavelength_signal_plot)[0][0]
        wl_index3 = np.where(np.round(self.wls,9) == np.round(wavelength_idler_plot,9))[0][0]

        mode_index1 = np.where(self.mode_order == mode_pump_plot)[0][0]
        mode_index2 = np.where(self.mode_order == mode_signal_plot)[0][0]
        mode_index3 = np.where(self.mode_order == mode_idler_plot)[0][0]
        
        plt.figure(dpi=175)

        ax1 = plt.subplot(2, 2, 1)
        ax1.plot(1e9*self.wls[self.start_indices[mode_index1]:self.stop_indices[mode_index1]], self.neffs[mode_index1][self.start_indices[mode_index1]:self.stop_indices[mode_index1]], marker='.', linestyle='solid', linewidth=0, markersize=3, label='Pump | '+self.mode_order[mode_index1])
        ax1.plot(1e9*self.wls[self.start_indices[mode_index2]:self.stop_indices[mode_index2]], self.neffs[mode_index2][self.start_indices[mode_index2]:self.stop_indices[mode_index2]], marker='.', linestyle='solid', linewidth=0.01, markersize=1, label='Signal | '+self.mode_order[mode_index2])
        ax1.plot(1e9*self.wls[self.start_indices[mode_index3]:self.stop_indices[mode_index3]], self.neffs[mode_index3][self.start_indices[mode_index3]:self.stop_indices[mode_index3]], marker='.', linestyle='solid', linewidth=0.01, markersize=1, label='Idler | '+self.mode_order[mode_index3])
        
        ax1.plot(1e9*self.wls[wl_index1], self.neffs[mode_index1][wl_index1], marker='x', linestyle='solid', linewidth=1, markersize=8, label='', color='C0')
        ax1.plot(1e9*self.wls[wl_index2], self.neffs[mode_index2][wl_index2], marker='x', linestyle='solid', linewidth=1, markersize=8, label='', color='C1')
        ax1.plot(1e9*self.wls[wl_index3], self.neffs[mode_index3][wl_index3], marker='x', linestyle='solid', linewidth=1, markersize=8, label='', color='C2')
        
        plt.legend(loc="upper right",fontsize=5)
        plt.tick_params(direction="in")
        plt.xlim([1e9*self.wls[0], 1e9*self.wls[-1]])
        plt.xlabel("wavelength (nm)")
        plt.ylabel("effective refractive index")
        plt.title("waveguide dispersion")
        
        plt.subplot(2, 2, 2)
        plt.plot(1e9*self.wls[self.start_indices[mode_index1]:self.stop_indices[mode_index1]], self.group_velocities[mode_index1][self.start_indices[mode_index1]:self.stop_indices[mode_index1]], marker='.', linestyle='solid', linewidth=0, markersize=3, label='Pump | '+self.mode_order[mode_index1], color='C0')
        plt.plot(1e9*self.wls[self.start_indices[mode_index2]:self.stop_indices[mode_index2]], self.group_velocities[mode_index2][self.start_indices[mode_index2]:self.stop_indices[mode_index2]], marker='.', linestyle='dashed', linewidth=0.01, markersize=1, label='Signal | '+self.mode_order[mode_index2], color='C1')
        plt.plot(1e9*self.wls[self.start_indices[mode_index3]:self.stop_indices[mode_index3]], self.group_velocities[mode_index3][self.start_indices[mode_index3]:self.stop_indices[mode_index3]], marker='.', linestyle='dotted', linewidth=0.01, markersize=1, label='Idler | '+self.mode_order[mode_index3], color='C2')
        
        plt.plot(1e9*self.wls[wl_index1], self.group_velocities[mode_index1][wl_index1], marker='x', linestyle='solid', linewidth=1, markersize=8, label='', color='C0')
        plt.plot(1e9*self.wls[wl_index2], self.group_velocities[mode_index2][wl_index2], marker='x', linestyle='solid', linewidth=1, markersize=8, label='', color='C1')
        plt.plot(1e9*self.wls[wl_index3], self.group_velocities[mode_index3][wl_index3], marker='x', linestyle='solid', linewidth=1, markersize=8, label='', color='C2')
        
        plt.legend(loc="upper right",fontsize=5)
        plt.tick_params(direction="in")
        plt.xlim([1e9*self.wls[0], 1e9*self.wls[-1]])
        plt.xlabel("wavelength (nm)")
        plt.ylabel("group velocity (m/s)")
        plt.title("GV dispersion")
        
        plt.tight_layout()
        plt.show()

        print('-------------------------------------------')
        print('PUMP |',self.mode_pump,'mode at',1e9*self.wavelength_pump,'nm:')
        print(np.round(self.neffs[mode_index1][wl_index1],4),'| effective refractive index')
        print(np.round(self.group_velocities[mode_index1][wl_index1],4),'m/s | group velocity')
        print('-------------------------------------------')
        print('-------------------------------------------')
        print('SIGNAL |',self.mode_signal,'mode at',1e9*self.wavelength_signal,'nm:')
        print(np.round(self.neffs[mode_index2][wl_index2],4),'| effective refractive index')
        print(np.round(self.group_velocities[mode_index2][wl_index2],4),'m/s | group velocity')
        print('-------------------------------------------')
        print('-------------------------------------------')
        print('IDLER |',self.mode_idler,'mode at',1e9*self.wavelength_idler,'nm:')
        print(np.round(self.neffs[mode_index3][wl_index3],4),'| effective refractive index')
        print(np.round(self.group_velocities[mode_index3][wl_index3],4),'m/s | group velocity')
        print('-------------------------------------------')
        print('-------------------------------------------')
        if ( ((self.group_velocities[mode_index1][wl_index1])**(-1) - (self.group_velocities[mode_index3][wl_index3])**(-1)) ) == 0:
            print(0,'deg | phase-matching angel due to GVM')
        else:
            print(np.round( (180/np.pi) * np.arctan(-1 * ((self.group_velocities[mode_index1][wl_index1])**(-1) - (self.group_velocities[mode_index2][wl_index2])**(-1)) \
                                                    / ((self.group_velocities[mode_index1][wl_index1])**(-1) - (self.group_velocities[mode_index3][wl_index3])**(-1)) ),4),'deg | phase-matching angel due to GVM')

    def get_neff(self, input_freq, input_mode):
        """
        return the refractie index for the respective angular frequency and waveguide mode
        """
        mode_index = np.where(self.mode_order == input_mode)[0][0]
        wl_index = np.argmin(np.abs(self.wls - 2*np.pi*self.c/input_freq))
        return self.neffs[mode_index][wl_index]
    
    def get_vg(self, input_freq, input_mode):
        """
        return the group vlocity for the respective angular frequency and waveguide mode
        """
        mode_index = np.where(self.mode_order == input_mode)[0][0]
        wl_index = np.argmin(np.abs(self.wls - 2*np.pi*self.c/input_freq))
        return self.group_velocities[mode_index][wl_index]


# ## Overlap class

class NonlinearOverlap:

    """ A class that calculates the nonlinear interaction coefficients from the modal fields

    Attr:
        consider_PDC
        make_plots

        omega_p
        omega_s
        omega_i
        
        D_wg_pump
        D_wg_signal
        D_wg_idler

        D_outside_wg_pump
        D_outside_wg_signal
        D_outside_wg_idler

        WGWidth
        WGHeight
        EtchDepth
        SidewallAngle

        x_grid
        y_grid 

        neff_p
        neff_s
        neff_i

        n_idler
        n_signal
        n_idler

        n_Si02_p
        n_Si02_s
        n_Si02_i

        nonlinear_interaction_coeffts
    """
    hbar = 6.62607015e-34 / (2*np.pi) #reduced Planck constant in J/Hz (SI units)
    epsilon0 = 8.8541878188e-12 # vacuum permittivity in A*s/(V*m) (SI units)
    c = 299792458 # vacuum speed-of-light (SI units)

    # Nonlinear coefficients in reduced form (see Boyd | 'Nonlinear optics', chapter 1) for congruent LiNbO3 from [Nikogosian | 'Nonlinear optical crystals: a complete survey'] and references therein
    d22 = 2.1e-12 # in m/V (SI units)
    d31 = -4.35e-12 # in m/V (SI units)
    d33 = -27.2e-12 # in m/V (SI units)

    chi_diag_fwm = 2779e-24 # in (m^2)/(V^2) (SI units)
    chi_offdiag_fwm = chi_diag_fwm / 3

    def __init__(self, input_wls, input_field_files, waveguide_data, sampling, input_ref_index_data, input_group_velocities,\
                 input_consider_PDC=True, make_plots=True):
        """         
        Params:
            input_wls (contains pump, signal and idler wavelengths)
            input_field_files (contains electric path to files with displacement field profiles of pump, signal and idler fields inside and outside the waveguide, as a 3x3 array structured as [pump/signal/idler][x-component/x-component/x-component])
            waveguide_data (contains WG top width, film thickness, etch depth and sidewall-angle of the waveguide) 
            sampling (contains the x- and y-coordinate grid at which the field is sampled)
            input_field_data_outside_wg (contains electric displacement field profiles of pump, signal and idler fields outside the waveguide)
            input_ref_index_data (contains refractive index data of pump, signal and idler fields)
            input_group_velocities (contains group velocities of the pump, signal and idler fields at the central frequencies)
            consider_PDC
            make_plots
        """
        self.consider_PDC = input_consider_PDC
        self.make_plots = make_plots

        self.omega_p = 2*np.pi*self.c / input_wls[0]
        self.omega_s = 2*np.pi*self.c / input_wls[1]
        self.omega_i = 2*np.pi*self.c / input_wls[2]

        self.WGWidth =  waveguide_data[0] # waveguide top width (in m)
        self.WGHeight =  waveguide_data[1] # thickness of the LN thin film (in m)
        self.EtchDepth = waveguide_data[2] # waveguide etch depth (in m)
        self.SidewallAngle = waveguide_data[3] # waveguide sidewall angle (in deg)

        self.x_grid = sampling[0]
        self.y_grid = sampling[1]     

        print('reading pump field modal data...')
        D_wg_pump, D_outside_wg_pump = self.read_data(input_field_files[0][0], input_field_files[0][1], input_field_files[0][2], self.WGWidth, self.WGHeight, self.EtchDepth, self.SidewallAngle, self.x_grid, self.y_grid)
        print('reading signal field modal data...')
        D_wg_signal, D_outside_wg_signal = self.read_data(input_field_files[1][0], input_field_files[1][1], input_field_files[1][2], self.WGWidth, self.WGHeight, self.EtchDepth, self.SidewallAngle, self.x_grid, self.y_grid)
        print('reading idler field modal data...')
        D_wg_idler, D_outside_wg_idler = self.read_data(input_field_files[2][0], input_field_files[2][1], input_field_files[2][2], self.WGWidth, self.WGHeight, self.EtchDepth, self.SidewallAngle, self.x_grid, self.y_grid)
        print('finished reading modal data')
        print('------------------------------------------------------')
        
        field_data_wg = [D_wg_pump, D_wg_signal, D_wg_idler]
        field_data_outside_wg = [D_outside_wg_pump, D_outside_wg_signal, D_outside_wg_idler]
        
        self.D_wg_pump, self.D_outside_wg_pump, self.neff_p, self.n_pump, self.n_Si02_p, self.v_p_c = field_data_wg[0], field_data_outside_wg[0],\
                                                                                                      input_ref_index_data[0], input_ref_index_data[1], input_ref_index_data[2],\
                                                                                                      input_group_velocities[0]
        self.D_wg_signal, self.D_outside_wg_signal, self.neff_s, self.n_signal, self.n_Si02_s, self.v_s_c = field_data_wg[1], field_data_outside_wg[1],\
                                                                                                            input_ref_index_data[3], input_ref_index_data[4], input_ref_index_data[5],\
                                                                                                            input_group_velocities[1]

        self.D_wg_idler, self.D_outside_wg_idler, self.neff_i, self.n_idler, self.n_Si02_i, self.v_i_c = field_data_wg[2], field_data_outside_wg[2],\
                                                                                                         input_ref_index_data[6], input_ref_index_data[7], input_ref_index_data[8],\
                                                                                                         input_group_velocities[2]

    def vector_norm_sq(self, vector_x, vector_y, vector_z): 
        """
        square of the vector norm
        """
        #return np.abs(Vector[0]*np.conjugate(Vector[0]) + Vector[1]*np.conjugate(Vector[1]) + Vector[2]*np.conjugate(Vector[2]))
        return np.abs(vector_x)**2 + np.abs(vector_y)**2 + np.abs(vector_z)**2
    
    # reads the modal data in and outside the waveguide
    def read_data(self, filename_x, filename_y,  filename_z, wg_width, wg_height, etch_depth, sw_angle, x_array=None, y_array=None): # files correspond to the (complex) x-, y- and z-components of the waveguide optical mode
        """         
        reads the modal data in and outside the waveguide from COMSOL simulation files
        """
        #print('reading modal data...')
        
        COMSOLHeightOffset = (wg_height-etch_depth)/2 # correction due to the bottom-edge of the waveguide not being at y=0 in my COMSOL simulator
    
        # the waveguide width is taken at top of the trapezoid
        SidewallAngle = np.pi*sw_angle/180 # waveguide sidewall-angle in rad
        RidgeOffset = (wg_height-COMSOLHeightOffset) / np.tan(SidewallAngle) # corresponsing to half the difference between top- and bottom-width of the waveguide
    
        # raw data files have x- and y-coordinates with corresponding real and imaginary electric fields in collums 0,1,2,3 respectively
        RawDataX = np.loadtxt(filename_x,comments='%')
        RawDataY = np.loadtxt(filename_y,comments='%')
        RawDataZ = np.loadtxt(filename_z,comments='%')
    
        DataLength = np.shape(RawDataX)
        DataLength = DataLength[0]
        
        XData_wg = np.zeros((DataLength),dtype=np.complex_)
        YData_wg = np.zeros((DataLength),dtype=np.complex_)
        ZData_wg = np.zeros((DataLength),dtype=np.complex_)
        CheckX_wg = np.zeros((DataLength),dtype=np.complex_)
        CheckY_wg = np.zeros((DataLength),dtype=np.complex_)
    
        XData_outside_wg = np.zeros((DataLength),dtype=np.complex_)
        YData_outside_wg = np.zeros((DataLength),dtype=np.complex_)
        ZData_outside_wg = np.zeros((DataLength),dtype=np.complex_)
        CheckX_outside_wg = np.zeros((DataLength),dtype=np.complex_)
        CheckY_outside_wg = np.zeros((DataLength),dtype=np.complex_)
    
        for i in range(np.shape(RawDataX)[0]):
    
            # extract the data in the trapezoid of the WG
            if ((RawDataX[i][1] <= (wg_height-COMSOLHeightOffset) and RawDataX[i][1] >= (0-COMSOLHeightOffset)) \
            and ((abs(RawDataX[i][0]) > wg_width/2 and RawDataX[i][1] <= np.tan(SidewallAngle) * (wg_width/2 + RidgeOffset - np.absolute(RawDataX[i][0])) ) \
            or abs(RawDataX[i][0]) <= wg_width/2)):
    
                XData_wg[i] = RawDataX[i][2] + 1j*RawDataX[i][3]
                YData_wg[i] = RawDataY[i][2] + 1j*RawDataY[i][3]
                ZData_wg[i] = RawDataZ[i][2] + 1j*RawDataZ[i][3]
    
                CheckX_wg[i] = RawDataX[i][0]
                CheckY_wg[i] = RawDataX[i][1]
    
            # extract the data outside the trapezoid of the WG
            else:
    
                XData_outside_wg[i] = RawDataX[i][2] + 1j*RawDataX[i][3]
                YData_outside_wg[i] = RawDataY[i][2] + 1j*RawDataY[i][3]
                ZData_outside_wg[i] = RawDataZ[i][2] + 1j*RawDataZ[i][3]
    
                CheckX_outside_wg[i] = RawDataX[i][0]
                CheckY_outside_wg[i] = RawDataX[i][1]      
                
        DataLength = np.shape(XData_wg)[0]
        Data_wg = np.zeros((3,DataLength),dtype=np.complex_)
        Data_wg[0] = XData_wg 
        Data_wg[1] = YData_wg
        Data_wg[2] = ZData_wg
        #Data_wg[0] = XData_wg.real 
        #Data_wg[1] = YData_wg.real
        #Data_wg[2] = ZData_wg.real
    
        DataLength = np.shape(XData_outside_wg)[0]
        Data_outside_wg = np.zeros((3,DataLength),dtype=np.complex_)
        Data_outside_wg[0] = XData_outside_wg 
        Data_outside_wg[1] = YData_outside_wg
        Data_outside_wg[2] = ZData_outside_wg
        #Data_outside_wg[0] = XData_outside_wg.real 
        #Data_outside_wg[1] = YData_outside_wg.real
        #Data_outside_wg[2] = ZData_outside_wg.real

        # plot the field modes
        if self.make_plots:

            plt.figure(dpi=150)
            plt.subplot(2, 3, 1)
            plt.matshow(np.abs(np.flip(XData_wg.reshape(len(y_array),len(x_array)),0)), fignum=False)
            plt.colorbar(fraction=0.03, pad=0.05)
            plt.title("x-component in waveguide",fontsize = 5)
            plt.xticks([])
            plt.yticks([])
            #plt.tight_layout()
            
            plt.subplot(2, 3, 2)
            plt.matshow(np.abs(np.flip(YData_wg.reshape(len(y_array),len(x_array)),0)), fignum=False)
            plt.colorbar(fraction=0.03, pad=0.05)
            plt.title("y-component in waveguide",fontsize = 5)
            plt.xticks([])
            plt.yticks([])
            #plt.tight_layout()
        
            plt.subplot(2, 3, 3)
            plt.matshow(np.abs(np.flip(ZData_wg.reshape(len(y_array),len(x_array)),0)), fignum=False)
            plt.colorbar(fraction=0.03, pad=0.05)
            plt.title("z-component in waveguide",fontsize = 5)
            plt.xticks([])
            plt.yticks([])
            #plt.tight_layout()
        
            plt.subplot(2, 3, 4)
            plt.matshow(np.abs(np.flip(XData_outside_wg.reshape(len(y_array),len(x_array)),0)), fignum=False)
            plt.colorbar(fraction=0.03, pad=0.05)
            plt.title("x-component outside waveguide",fontsize = 5)
            plt.xticks([])
            plt.yticks([])
            #plt.tight_layout()
            
            plt.subplot(2, 3, 5)
            plt.matshow(np.abs(np.flip(YData_outside_wg.reshape(len(y_array),len(x_array)),0)), fignum=False)
            plt.colorbar(fraction=0.03, pad=0.05)
            plt.title("y-component outside waveguide",fontsize = 5)
            plt.xticks([])
            plt.yticks([])
            #plt.tight_layout()
            
            plt.subplot(2, 3, 6)
            plt.matshow(np.abs(np.flip(ZData_outside_wg.reshape(len(y_array),len(x_array)),0)), fignum=False)
            plt.colorbar(fraction=0.03, pad=0.05)
            plt.title("z-component outside waveguide",fontsize = 5)
            plt.xticks([])
            plt.yticks([])
            #plt.tight_layout()
        
            plt.show()
        
        # # plots all the grid points at which data was taken
        # plt.figure(dpi=150)
        # plt.plot(CheckX_wg, CheckY_wg, marker='x', linestyle='solid', linewidth=0, color="green", markersize=0.5, label="")
        # plt.axis([-2.6e-6, 2.6e-6, -2.1e-6, 2.1e-6])
        # plt.tick_params(direction="in")
        # plt.title("Field locations")
        # plt.xlabel("x")
        # plt.ylabel("y")
        # plt.legend(loc="upper left",fontsize=5)
        # plt.show()
        # #print(len(CheckX),len(CheckY))
        
        # # plots all the grid points at which data was taken
        # plt.figure(dpi=150)
        # plt.plot(CheckX_outside_wg, CheckY_outside_wg, marker='x', linestyle='solid', linewidth=0, color="green", markersize=0.5, label="")
        # plt.axis([-2.6e-6, 2.6e-6, -2.1e-6, 2.1e-6])
        # plt.tick_params(direction="in")
        # plt.title("Field locations")
        # plt.xlabel("x")
        # plt.ylabel("y")
        # plt.legend(loc="upper left",fontsize=5)
        # plt.show()
        # #print(len(CheckX),len(CheckY))
        
        return Data_wg, Data_outside_wg

    def integrate2D(self, Data, XArray, YArray): # XArray and YArray refers to the coordinates of the grid-points at which the field data was evaluated
        """
        calculate the integral in of the 2D array COMSOL field data along first the x-coordinate and then the y-coordinate
        """
        grid_points_Y = len(YArray)
        grid_points_X = len(XArray)
        grid_spacing_X = abs(XArray[1] - XArray[0]) # assumes uniform grid spacing
        grid_spacing_Y = abs(YArray[1] - YArray[0]) # assumes uniform grid spacing
        
        # refers to x,y,z components of the fields
        if len(Data) == 3: # for input of vector with x,y,z - components
            xData = Data[0]
            yData = Data[1]
            zData = Data[2]
            xIntegrated = np.zeros((grid_points_Y),dtype=np.complex_)
            yIntegrated = np.zeros((grid_points_Y),dtype=np.complex_)
            zIntegrated = np.zeros((grid_points_Y),dtype=np.complex_)
        else: # for input of absolute value of vector (skalar)
            xData = Data
            xIntegrated = np.zeros((grid_points_Y),dtype=np.complex_)
        
        for i in range(grid_points_Y): # integrate along the x-coordinate
            if len(Data) == 3: # for input of vector with x,y,z - components
                xIntegrated[i] = np.sum(xData[i*grid_points_X : i*grid_points_X + grid_points_X]) * grid_spacing_X
                yIntegrated[i] = np.sum(yData[i*grid_points_X : i*grid_points_X + grid_points_X]) * grid_spacing_X
                zIntegrated[i] = np.sum(zData[i*grid_points_X : i*grid_points_X + grid_points_X]) * grid_spacing_X
            else: # for input of absolute value of vector (skalar)
                xIntegrated[i] = np.sum(xData[i*grid_points_X : i*grid_points_X + grid_points_X]) * grid_spacing_X
        
        if len(Data) == 3: # for input of vector with x,y,z - components
            XIntegratedData = np.zeros((3,grid_points_Y),dtype=np.complex_)
            XIntegratedData[0] = xIntegrated
            XIntegratedData[1] = yIntegrated
            XIntegratedData[2] = zIntegrated
        else: # for input of absolute value of vector (skalar)
            XIntegratedData = np.zeros((1,grid_points_Y),dtype=np.complex_)
            XIntegratedData[0] = xIntegrated 
        
        return np.sum(XIntegratedData, 1) * grid_spacing_Y
    
    def calculate_Normalizer_D(self, electric_field_in_wg, electric_field_outside_wg, n_in_wg, n_outside_wg, v_g, n_eff):
        """
        Denominator required for normalizeding the modal fields calculated using the mode solver
        (see eq. A2 in Weiss et al. 'Quantum nonlinear parametric interaction in realistic waveguides' 
        and Quesada et al. 'Theory of high-gain twin-beam generation in waveguides: From Maxwell's equations to efficient simultion')
        """
        
        return np.sqrt(((self.c/n_eff)/(self.epsilon0*v_g)) * self.integrate2D(self.vector_norm_sq(electric_field_in_wg[0]/(n_in_wg[0]**2), \
                                                                               electric_field_in_wg[1]/(n_in_wg[1]**2), \
                                                                               electric_field_in_wg[2]/(n_in_wg[2]**2)), self.x_grid, self.y_grid) \
                       + ((self.c/n_eff)/(self.epsilon0*v_g)) * self.integrate2D(self.vector_norm_sq(electric_field_outside_wg[0]/(n_outside_wg**2), \
                                                                                 electric_field_outside_wg[1]/(n_outside_wg**2), \
                                                                                 electric_field_outside_wg[2]/(n_outside_wg**2)), self.x_grid, self.y_grid) )


    """ 
    Nonlinear Overlap integrals
    
    input data is w.r.t. coordiantes, with x,y (indices 0,1) corresponding to the waveguide cross-section (x->horizontal / y->vertical direction) and z (index 3) corresponding to the propagation direction
    for calculting the nonlinear overlap, the z-coordinate is taken along the optical axias (meaning, e.g. d_zzz describes interaction between the field components orientated along the optical axis
    version below assumes Z-Cut (LN) (meaning indices {0,1,2} correspond to coordiantes {x,z,y}
    """
    
    def calculate_Overlap_PDC_D(self, D_chi2_p, D_chi2_s, D_chi2_i, n_p, n_s, n_i): # calculate the overlap integrals between pump, signal and idlder modes
    
        # overlap with the nonlinearity represented in reduced form (see Boyd | 'Nonlinear optics', chapter 1)
        Overlap = self.d33*D_chi2_p[1]*D_chi2_s[1]*D_chi2_i[1] / ((n_p[1]*n_s[1]*n_i[1])**2) \
                  + self.d31*(D_chi2_p[0]*D_chi2_s[1]*D_chi2_i[0] / ((n_p[0]*n_s[1]*n_i[0])**2) + D_chi2_p[0]*D_chi2_s[0]*D_chi2_i[1] / ((n_p[0]*n_s[0]*n_i[1])**2) \
                         + D_chi2_p[2]*D_chi2_s[2]*D_chi2_i[1] / ((n_p[2]*n_s[2]*n_i[1])**2) + D_chi2_p[2]*D_chi2_s[1]*D_chi2_i[2] / ((n_p[2]*n_s[1]*n_i[2])**2) \
                         + D_chi2_p[1]*D_chi2_s[0]*D_chi2_i[0] / ((n_p[1]*n_s[0]*n_i[0])**2) + D_chi2_p[1]*D_chi2_s[2]*D_chi2_i[2] / ((n_p[1]*n_s[2]*n_i[2])**2)) \
                  + self.d22*(D_chi2_p[2]*D_chi2_s[2]*D_chi2_i[2] / ((n_p[2]*n_s[2]*n_i[2])**2) - D_chi2_p[2]*D_chi2_s[0]*D_chi2_i[0] / ((n_p[2]*n_s[0]*n_i[0])**2) \
                         - D_chi2_p[0]*D_chi2_s[0]*D_chi2_i[2] / ((n_p[0]*n_s[0]*n_i[2])**2) - D_chi2_p[0]*D_chi2_s[2]*D_chi2_i[0] / ((n_p[0]*n_s[2]*n_i[0])**2))
              
        print(abs(self.integrate2D(D_chi2_p[1]*D_chi2_s[1]*D_chi2_i[1] / ((n_s[1]*n_i[1]*n_p[1])**2), self.x_grid, self.y_grid)),'d33 contribution')
        print(abs(self.integrate2D(D_chi2_s[0]*D_chi2_i[1]*D_chi2_p[0] / ((n_s[0]*n_i[1]*n_p[0])**2) + D_chi2_s[0]*D_chi2_i[0]*D_chi2_p[1] / ((n_s[0]*n_i[0]*n_p[1])**2) + D_chi2_s[2]*D_chi2_i[2]*D_chi2_p[1] / ((n_s[2]*n_i[2]*n_p[1])**2) + D_chi2_s[2]*D_chi2_i[1]*D_chi2_p[2] / ((n_s[2]*n_i[1]*n_p[2])**2) + D_chi2_s[1]*D_chi2_i[0]*D_chi2_p[0] / ((n_s[1]*n_i[0]*n_p[0])**2) + D_chi2_s[1]*D_chi2_i[2]*D_chi2_p[2] / ((n_s[1]*n_i[2]*n_p[2])**2) , self.x_grid, self.y_grid)),'d31 contribution')
        print(abs(self.integrate2D(D_chi2_s[2]*D_chi2_i[2]*D_chi2_p[2] / ((n_s[2]*n_i[2]*n_p[2])**2) - D_chi2_s[2]*D_chi2_i[0]*D_chi2_p[0] / ((n_s[2]*n_i[0]*n_p[0])**2) - D_chi2_s[0]*D_chi2_i[0]*D_chi2_p[2] / ((n_s[0]*n_i[0]*n_p[2])**2) - D_chi2_s[0]*D_chi2_i[2]*D_chi2_p[0] / ((n_s[0]*n_i[2]*n_p[0])**2), self.x_grid, self.y_grid)),'d22 contribution')
    
        print(abs(self.integrate2D(D_chi2_p[0]*D_chi2_s[1]*D_chi2_i[0] / ((n_s[0]*n_i[1]*n_p[0])**2), self.x_grid, self.y_grid)),'dxzx contribution (d31)')
        print(abs(self.integrate2D(D_chi2_p[0]*D_chi2_s[0]*D_chi2_i[1] / ((n_s[0]*n_i[0]*n_p[1])**2), self.x_grid, self.y_grid)),'dxxz contribution (d31)')
        print(abs(self.integrate2D(D_chi2_p[2]*D_chi2_s[2]*D_chi2_i[1] / ((n_s[2]*n_i[2]*n_p[1])**2), self.x_grid, self.y_grid)),'dyyz contribution (d31)')
        print(abs(self.integrate2D(D_chi2_p[2]*D_chi2_s[1]*D_chi2_i[2] / ((n_s[2]*n_i[1]*n_p[2])**2), self.x_grid, self.y_grid)),'dyzy contribution (d31)')
        print(abs(self.integrate2D(D_chi2_p[1]*D_chi2_s[0]*D_chi2_i[0] / ((n_s[1]*n_i[0]*n_p[0])**2), self.x_grid, self.y_grid)),'dzxx contribution (d31)')
        print(abs(self.integrate2D(D_chi2_p[1]*D_chi2_s[2]*D_chi2_i[2] / ((n_s[1]*n_i[2]*n_p[2])**2), self.x_grid, self.y_grid)),'dzyy contribution (d31)')
        
        print(abs(self.integrate2D(D_chi2_p[2]*D_chi2_s[2]*D_chi2_i[2] / ((n_s[2]*n_i[2]*n_p[2])**2), self.x_grid, self.y_grid)),'dyyy contribution (d22)')
        print(-abs(self.integrate2D(D_chi2_p[2]*D_chi2_s[0]*D_chi2_i[0] / ((n_s[2]*n_i[0]*n_p[0])**2), self.x_grid, self.y_grid)),'dyxx contribution (d22)')
        print(-abs(self.integrate2D(D_chi2_p[0]*D_chi2_s[0]*D_chi2_i[2] / ((n_s[0]*n_i[0]*n_p[2])**2), self.x_grid, self.y_grid)),'dxxy contribution (d22)')
        print(-abs(self.integrate2D(D_chi2_p[0]*D_chi2_s[2]*D_chi2_i[0] / ((n_s[0]*n_i[2]*n_p[0])**2), self.x_grid, self.y_grid)),'dxyx contribution (d22)')
        
        print(-abs(self.integrate2D(D_chi2_p[1]*D_chi2_s[1]*D_chi2_i[1] / ((n_s[1]*n_i[1]*n_p[1])**2), self.x_grid, self.y_grid)),'dzzz contribution (d33)')
        return self.integrate2D(Overlap, self.x_grid, self.y_grid)[0]
    
    def calculate_Overlap_SPM_D(self, D_chi2_p, n_p): # calculate the overlap integrals between pump, signal and idlder modes
        
        # overlap with respect to effective third-order nonlinear interaction
        Overlap = self.chi_diag_fwm * (np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_p[0])*D_chi2_p[0]*D_chi2_p[0] / ((n_p[0]*n_p[0]*n_p[0]*n_p[0])**2) \
                                  + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_p[1])*D_chi2_p[1]*D_chi2_p[1] / ((n_p[1]*n_p[1]*n_p[1]*n_p[1])**2) \
                                  + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_p[2])*D_chi2_p[2]*D_chi2_p[2] / ((n_p[2]*n_p[2]*n_p[2]*n_p[2])**2)) \
                  + self.chi_offdiag_fwm * (np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_p[0])*D_chi2_p[1]*D_chi2_p[1] / ((n_p[0]*n_p[0]*n_p[1]*n_p[1])**2) \
                                       + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_p[0])*D_chi2_p[2]*D_chi2_p[2] / ((n_p[0]*n_p[0]*n_p[2]*n_p[2])**2) \
                                       + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_p[1])*D_chi2_p[0]*D_chi2_p[1] / ((n_p[0]*n_p[1]*n_p[0]*n_p[1])**2) \
                                       + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_p[1])*D_chi2_p[1]*D_chi2_p[0] / ((n_p[0]*n_p[1]*n_p[1]*n_p[0])**2) \
                                       + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_p[2])*D_chi2_p[0]*D_chi2_p[2] / ((n_p[0]*n_p[2]*n_p[0]*n_p[2])**2) \
                                       + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_p[2])*D_chi2_p[2]*D_chi2_p[0] / ((n_p[0]*n_p[2]*n_p[2]*n_p[0])**2) \
                                       + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_p[1])*D_chi2_p[2]*D_chi2_p[2] / ((n_p[1]*n_p[1]*n_p[2]*n_p[2])**2) \
                                       + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_p[0])*D_chi2_p[1]*D_chi2_p[0] / ((n_p[1]*n_p[0]*n_p[1]*n_p[0])**2) \
                                       + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_p[0])*D_chi2_p[0]*D_chi2_p[1] / ((n_p[1]*n_p[0]*n_p[0]*n_p[1])**2) \
                                       + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_p[2])*D_chi2_p[2]*D_chi2_p[1] / ((n_p[1]*n_p[2]*n_p[2]*n_p[1])**2) \
                                       + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_p[2])*D_chi2_p[1]*D_chi2_p[2] / ((n_p[1]*n_p[2]*n_p[1]*n_p[2])**2) \
                                       + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_p[2])*D_chi2_p[1]*D_chi2_p[1] / ((n_p[2]*n_p[2]*n_p[1]*n_p[1])**2) \
                                       + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_p[0])*D_chi2_p[2]*D_chi2_p[0] / ((n_p[2]*n_p[0]*n_p[2]*n_p[0])**2) \
                                       + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_p[0])*D_chi2_p[0]*D_chi2_p[2] / ((n_p[2]*n_p[0]*n_p[0]*n_p[2])**2) \
                                       + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_p[1])*D_chi2_p[2]*D_chi2_p[1] / ((n_p[2]*n_p[1]*n_p[2]*n_p[1])**2) \
                                       + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_p[1])*D_chi2_p[1]*D_chi2_p[2] / ((n_p[2]*n_p[1]*n_p[1]*n_p[2])**2) \
                                       + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_p[2])*D_chi2_p[0]*D_chi2_p[0] / ((n_p[2]*n_p[2]*n_p[0]*n_p[0])**2) \
                                       + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_p[1])*D_chi2_p[0]*D_chi2_p[0] / ((n_p[1]*n_p[1]*n_p[0]*n_p[0])**2) )
        
        return self.integrate2D(Overlap, self.x_grid, self.y_grid)[0]
    
    def calculate_Overlap_XPM_D(self, D_chi2_p, D_chi2_si, n_p, n_si): # calculate the overlap integrals between pump, signal and idlder modes
    
        # overlap with respect to effective third-order nonlinear interaction
        Overlap = self.chi_diag_fwm * (np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_si[0])*D_chi2_p[0]*D_chi2_si[0] / ((n_p[0]*n_si[0]*n_p[0]*n_si[0])**2) \
                                       + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_si[1])*D_chi2_p[1]*D_chi2_si[1] / ((n_p[1]*n_si[1]*n_p[1]*n_si[1])**2) \
                                       + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_si[2])*D_chi2_p[2]*D_chi2_si[2] / ((n_p[2]*n_si[2]*n_p[2]*n_si[2])**2)) \
                  + self.chi_offdiag_fwm * (np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_si[0])*D_chi2_p[1]*D_chi2_si[1] / ((n_p[0]*n_si[0]*n_p[1]*n_si[1])**2) \
                                            + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_si[0])*D_chi2_p[2]*D_chi2_si[2] / ((n_p[0]*n_si[0]*n_p[2]*n_si[2])**2) \
                                            + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_si[1])*D_chi2_p[0]*D_chi2_si[1] / ((n_p[0]*n_si[1]*n_p[0]*n_si[1])**2) \
                                            + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_si[1])*D_chi2_p[1]*D_chi2_si[0] / ((n_p[0]*n_si[1]*n_p[1]*n_si[0])**2) \
                                            + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_si[2])*D_chi2_p[0]*D_chi2_si[2] / ((n_p[0]*n_si[2]*n_p[0]*n_si[2])**2) \
                                            + np.conjugate(D_chi2_p[0])*np.conjugate(D_chi2_si[2])*D_chi2_p[2]*D_chi2_si[0] / ((n_p[0]*n_si[2]*n_p[2]*n_si[0])**2) \
                                            + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_si[1])*D_chi2_p[2]*D_chi2_si[2] / ((n_p[1]*n_si[1]*n_p[2]*n_si[2])**2) \
                                            + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_si[0])*D_chi2_p[1]*D_chi2_si[0] / ((n_p[1]*n_si[0]*n_p[1]*n_si[0])**2) \
                                            + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_si[0])*D_chi2_p[0]*D_chi2_si[1] / ((n_p[1]*n_si[0]*n_p[0]*n_si[1])**2) \
                                            + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_si[2])*D_chi2_p[2]*D_chi2_si[1] / ((n_p[1]*n_si[2]*n_p[2]*n_si[1])**2) \
                                            + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_si[2])*D_chi2_p[1]*D_chi2_si[2] / ((n_p[1]*n_si[2]*n_p[1]*n_si[2])**2) \
                                            + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_si[2])*D_chi2_p[1]*D_chi2_si[1] / ((n_p[2]*n_si[2]*n_p[1]*n_si[1])**2) \
                                            + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_si[0])*D_chi2_p[2]*D_chi2_si[0] / ((n_p[2]*n_si[0]*n_p[2]*n_si[0])**2) \
                                            + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_si[0])*D_chi2_p[0]*D_chi2_si[2] / ((n_p[2]*n_si[0]*n_p[0]*n_si[2])**2) \
                                            + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_si[1])*D_chi2_p[2]*D_chi2_si[1] / ((n_p[2]*n_si[1]*n_p[2]*n_si[1])**2) \
                                            + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_si[1])*D_chi2_p[1]*D_chi2_si[2] / ((n_p[2]*n_si[1]*n_p[1]*n_si[2])**2) \
                                            + np.conjugate(D_chi2_p[2])*np.conjugate(D_chi2_si[2])*D_chi2_p[0]*D_chi2_si[0] / ((n_p[2]*n_si[2]*n_p[0]*n_si[0])**2) \
                                            + np.conjugate(D_chi2_p[1])*np.conjugate(D_chi2_si[1])*D_chi2_p[0]*D_chi2_si[0] / ((n_p[1]*n_si[1]*n_p[0]*n_si[0])**2) )
    
        return self.integrate2D(Overlap, self.x_grid, self.y_grid)[0]

    def calc_nonlinear_interaction_coeffts(self):
        """
        calculated the nonlinear interaction coefficients from the modal field data calculated from a mode solver
        (see eqs. A6 in Weiss et al. 'Quantum nonlinear parametric interaction in realistic waveguides')
        """
        
        # calculate the normalized fields
        D_wg_pump_n = self.D_wg_pump / self.calculate_Normalizer_D(self.D_wg_pump, self.D_outside_wg_pump, self.n_pump, self.n_Si02_p, self.v_p_c, self.neff_p)
        D_wg_signal_n = self.D_wg_signal / self.calculate_Normalizer_D(self.D_wg_signal, self.D_outside_wg_signal, self.n_signal, self.n_Si02_s, self.v_s_c, self.neff_s)
        D_wg_idler_n = self.D_wg_idler / self.calculate_Normalizer_D(self.D_wg_idler, self.D_outside_wg_idler, self.n_idler, self.n_Si02_i, self.v_i_c, self.neff_i)

        # calculate the overlap intergrals
        if self.consider_PDC:
            print('Nonlinear overlap integrals PDC:')
            nl_overlap_PDC = self.calculate_Overlap_PDC_D(D_wg_pump_n, np.conjugate(D_wg_signal_n), np.conjugate(D_wg_idler_n), \
                                                          self.n_pump, self.n_signal, self.n_idler) * 2 # (integral in eq. B1h, excluding the vacuum permittivity) | factor 2 from the definition of the susecptibility in reduces form d =0.5*chi
        else:
            print('Nonlinear Overlap integrals QFC:')
            nl_overlap_QFC = self.calculate_Overlap_PDC_D(D_wg_pump_n, D_wg_signal_n, np.conjugate(D_wg_idler_n), \
                                                          self.n_pump, self.n_signal, self.n_idler) * 2 # (integral in eq. B1h, excluding the vacuum permittivity) | factor 2 from the definition of the susecptibility in reduces form d =0.5*chi
        nl_overlap_SPM = self.calculate_Overlap_SPM_D(D_wg_pump_n, self.n_pump) # (integral in eq. B1b, excluding the vacuum permittivity)
        nl_overlap_XPM_s = self.calculate_Overlap_XPM_D(D_wg_pump_n, D_wg_signal_n, self.n_pump, self.n_signal) # (integral in eq. B1d, excluding the vacuum permittivity)
        nl_overlap_XPM_i = self.calculate_Overlap_XPM_D(D_wg_pump_n, D_wg_idler_n, self.n_pump, self.n_idler)# (integral in eq. B1d, excluding the vacuum permittivity)
        
        print('------------------------------------------------------')
        print('------Calculated nonlinear coupling coefficients------')
        print('--------------as defined in Weiss et al.--------------')
        print('------------------------------------------------------')
        
        # calculate the nonlinear coefficients (see Weiss et al. 'Quantum nonlinear parametric interaction in realistic waveguides')
        if self.consider_PDC:
            c_PDC = (np.sqrt(self.omega_s*self.omega_i / 2) / (self.epsilon0**2) ) * nl_overlap_PDC * (1/np.sqrt(self.v_p_c*self.v_s_c*self.v_i_c)) # (see eq. 47)
            c_chi2 = c_PDC
            print(np.abs(c_PDC),'| PDC nonlinear coupling coefficient')
        else:
            c_QFC = (np.sqrt(self.omega_s*self.omega_i / 2) / (self.epsilon0**2) ) * nl_overlap_QFC * (1/np.sqrt(self.v_p_c*self.v_s_c*self.v_i_c)) # (see eq. 47)
            c_chi2 = c_QFC
            print(np.abs(c_QFC),'| QFC nonlinear coupling coefficient')
        c_SPM = (3*(self.hbar**2)*(self.omega_p**2) / (4*self.hbar*(self.epsilon0**3)) ) * nl_overlap_SPM # (see eq. B1b)
        c_XPM_s = ((3*self.omega_s) / (2*(self.epsilon0**3)) ) * nl_overlap_XPM_s * (1/(self.v_p_c*self.v_s_c)) # (see eq. 45)
        c_XPM_i = ((3*self.omega_i) / (2*(self.epsilon0**3)) ) * nl_overlap_XPM_i * (1/(self.v_p_c*self.v_i_c)) # (see eq. 45)
        print(np.abs(c_SPM),'| SPM nonlinear coupling coefficient')
        print(np.abs(c_XPM_s),'| XPM (signal) nonlinear coupling coefficient')
        print(np.abs(c_XPM_i),'| XPM (idler) nonlinear coupling coefficient')

        self.nonlinear_interaction_coeffts = [c_chi2, c_SPM, c_XPM_s, c_XPM_i]

        return self.nonlinear_interaction_coeffts


# ## Simulator class

class QNPISimulator:
    """ A class to calculate the constituent of the simulation framework equation-of-motion.
    
    Attr:
        consider_PDC
        consider_custom_pm
        consider_perpol
        consider_losses
        consider_domain_wall_errors
        consider_domain_writing_errors
        consider_waveguide_inhomogeneity

        number_of_expansion_steps

        waveguide_loss
        domain_wall_error_uniform
        domain_wall_error_random
        domain_writing_error_rate
        propagation_constant_max_deviation

        amplitude_pump
        pump_amplitude_sampling_step

        c_chi2
        c_SPM
        c_XPM_s
        c_XPM_i
        
        wl_p
        v_p
        photon_number (of pump pulse)
        pump_sampling (sampling for Fourier transform)
        initial_phase (of pump pulse)
        wl_s
        wl_i
        start_nl
        end_nl
        start
        end
        number_of_freq_points
        plotting_range

        Omega_signal
        Omega_signal_step
        Omega_idler
        Omega_idler_step

        v_p
        v_s
        v_i

        delta_k_intrinsic
        domain_width
        number_domains
        k_arrays

        loss_coefficient
    """
    hbar = 6.62607015e-34 / (2*np.pi) #reduced Planck constant in J/Hz (SI units)
    c = 299792458 # vacuum speed-of-light (SI units)

    def __init__(self, input_settings, crystal_settings, number_of_freq_points, plotting_range, input_amplitude_pump, nonlin_interaction_coeffts, dispersion,
                 number_of_expansion_steps=1, simulation_settings=[True,False,False,False,False,False,False], error_data=[0,0,0,0,0]):
        """         
        Params:
            simulation_settings (contains all the 'consider_...' booleans | defaults to considering PDC with no errors)
            input_settings (contains info about attributes pertaining to the pump pulse)
            losses
            crystal_settings (contains info about the start and end of the (non)linear regions)
            error data (info about the strength of the different errors)
            dispersion (dispersion class)
        """
        self.consider_PDC = simulation_settings[0]
        self.consider_custom_pm = simulation_settings[1]
        self.consider_perpol = simulation_settings[2]
        self.consider_losses = simulation_settings[3]
        self.consider_domain_wall_errors = simulation_settings[4]
        self.consider_domain_writing_errors = simulation_settings[5]
        self.consider_waveguide_inhomogeneity = simulation_settings[6]

        self.expansion_steps = number_of_expansion_steps

        self.waveguide_loss = error_data[0]
        self.domain_wall_error_uniform = error_data[1]
        self.domain_wall_error_random = error_data[2]
        self.domain_writing_error_rate = error_data[3]
        self.propagation_constant_max_deviation = error_data[4]

        self.amplitude_pump = input_amplitude_pump

        self.c_chi2 = nonlin_interaction_coeffts[0]
        self.c_SPM = nonlin_interaction_coeffts[1]
        self.c_XPM_s = nonlin_interaction_coeffts[2]
        self.c_XPM_i = nonlin_interaction_coeffts[3]

        self.omega_p = 2*np.pi*self.c / input_settings[0]
        self.omega_s = 2*np.pi*self.c / input_settings[1]
        self.omega_i = 2*np.pi*self.c / input_settings[2]
        self.v_p_c = input_settings[3]
        self.photon_number = input_settings[4]
        self.bandwidth = input_settings[5]
        self.initial_phase = input_settings[6]
        
        self.start_nl = crystal_settings[0]
        self.end_nl = crystal_settings[1]
        self.start = crystal_settings[2]
        self.end = crystal_settings[3]

        self.number_of_freq_points = number_of_freq_points
        self.plotting_range = plotting_range

        # sampling of the pump pulse
        self.pump_amplitude_sampling_step = (self.v_p_c/self.bandwidth)/25 # number of points at which the number density amplitude of the pump is calculated
        self.pump_amplitude_sampling = np.arange(self.start-10*self.v_p_c/self.bandwidth,self.start+10*self.v_p_c/self.bandwidth,self.pump_amplitude_sampling_step)
        
        # sweep-range in terms of angular frequencies
        delta_omega_s = (2*np.pi*self.c/(input_settings[1]-self.plotting_range/2) - 2*np.pi*self.c/(input_settings[1]+self.plotting_range/2))
        delta_omega_i = (2*np.pi*self.c/(input_settings[2]-self.plotting_range/2) - 2*np.pi*self.c/(input_settings[2]+self.plotting_range/2))
        
        # signal frequencies for which the interaction is to be calculated
        Omega_signal_alt = np.linspace(self.omega_s+self.plotting_range/2, self.omega_s-self.plotting_range/2, num=self.number_of_freq_points, endpoint=True, retstep=True)
        self.Omega_signal_step = Omega_signal_alt[1]
        self.Omega_signal = Omega_signal_alt[0]
        
        # idler frequencies for which the interaction is to be calculated
        Omega_idler_alt = np.linspace(self.omega_i+self.plotting_range/2, self.omega_i-self.plotting_range/2, num=self.number_of_freq_points, endpoint=True, retstep=True)
        self.Omega_idler_step = Omega_idler_alt[1]
        self.Omega_idler = Omega_idler_alt[0]

        # Group velocities | calculated using the dispersion class
        self.v_p = lambda ang_freq : dispersion.get_vg(ang_freq, dispersion.mode_pump) 
        self.v_s = lambda ang_freq : dispersion.get_vg(ang_freq, dispersion.mode_signal) 
        self.v_i = lambda ang_freq : dispersion.get_vg(ang_freq, dispersion.mode_idler)

        # Phase-(mis)matching & domain size data
        k_s = lambda freq : freq*dispersion.get_neff(freq, dispersion.mode_signal)  / self.c
        k_i = lambda freq : freq*dispersion.get_neff(freq, dispersion.mode_idler) / self.c
        k_p = lambda freq : freq*dispersion.get_neff(freq, dispersion.mode_pump) / self.c
        if self.consider_PDC:
            delta_k = lambda freq_1,freq_2 : k_p(freq_1+freq_2) - k_s(freq_1) - k_i(freq_2) # phase-missmatch
            self.delta_k_intrinsic = delta_k(self.omega_s, self.omega_i) # intrinsic phase-mismatch
        else:
            delta_k = lambda freq_1,freq_2 : k_p(freq_2-freq_1) + k_s(freq_1) - k_i(freq_2) # phase-missmatch
            self.delta_k_intrinsic = np.abs(delta_k(self.omega_s, self.omega_i)) # intrinsic phase-mismatch
        
        self.domain_width = np.pi/self.delta_k_intrinsic # width of the crystal segments required to compensate the intrinsic phase-missmatch
        self.number_domains = self.round_up_to_even((self.end_nl-self.start_nl) / self.domain_width) # number of said segments

        L = self.number_domains*self.domain_width # lenght of (domain-engineered) nonlinear crystal
        k_range = 200/L
        dk = k_range/401
        self.k_arrays = np.arange(self.delta_k_intrinsic-k_range/2, self.delta_k_intrinsic+k_range/2, dk)

        # calculate the loss coefficient function (if to be considered)
        if self.consider_losses:
            self.loss_coefficient = self.calc_losses()
    
    def round_up_to_even(self, input_number):
        return int(input_number) if ((int(input_number) % 2) == 0) else int(input_number) + 1

    def kronecker(self, a, b):
        """
        a kronecker delta
        """
        if a == b: return 1 
        else: return 0
    
    def dagger(self, A):
        """
        the dagger operator
        """
        return np.transpose(np.conjugate(A))

    def random_walk(self, x_array, width_of_guassian_distribution, initial_value):
        """ 
        generate a random walk (used to simulate waveguide geometry inhomogeneity)
        """
        y = initial_value
        result = []
        for _ in x_array:
            result.append(y)
            y += np.random.normal(scale=width_of_guassian_distribution)
        return np.array(result)

    def smooth(self, input_curve, N):
        """
        smooting function (used to smooth the random walk generated from the function above)
        """
        input_curve = np.concatenate((input_curve, [input_curve[-1]]*N)) 
        smoothed_curve = np.convolve(input_curve, np.ones((N,))/N)[(N-1):]
        return smoothed_curve[0:-N]


    def tailored_crystal(self, target_func):
        """
        set up the poling pattern for a crystal with custom phase-matching function
        (using 'custom-poling' from https://github.com/abranczyk/custom-poling)
        """
        
        # set-up the poling-structure
        tailored_crystal_custom = CustomCrystal(self.domain_width, self.number_domains)
        domain_middles_custom = tailored_crystal_custom.domain_middles
           
        target_custom = Target(target_func, self.k_arrays)
    
        # calculate the target amplitude
        target_amplitude_custom = target_custom.compute_amplitude(self.delta_k_intrinsic, domain_middles_custom)
        
        # calculate the tailored domain structure
        domain_config_custom = tailored_crystal_custom.compute_domains(target_amplitude_custom, self.delta_k_intrinsic)
    
        # calcultate the PMF and amplitude for the tailored crystal
        pmf_tailored_crystal_custom = tailored_crystal_custom.compute_pmf(self.k_arrays)
    
        plt.figure(dpi=175)
        plt.subplot(2, 1, 1)
        # plot targeted and implemented PMF
        plt.plot(self.k_arrays-self.delta_k_intrinsic, np.abs(target_custom.pmf), linestyle='-', label='target', markersize=5, color='green', linewidth=3)
        plt.plot(self.k_arrays-self.delta_k_intrinsic, np.abs(pmf_tailored_crystal_custom), linestyle='-', label='implemented', markersize=5, color='black', linewidth=0.5)
        plt.legend(loc='upper right')
        plt.xlabel(r'$\Delta k-\Delta k_0~(m^{-1})$')
        plt.ylabel(r'')
        
        # plot the corresponding poling pattern
        plt.subplot(2, 1, 2)
        plt.plot(tailored_crystal_custom.domain_walls, np.concatenate(([domain_config_custom[0]],domain_config_custom)), linestyle='-', label='Target2', mfc='w', markersize=8, color='black', linewidth = 0.5)
        plt.xlabel('position (mm)')
        plt.ylabel('g(z)')
        plt.title("poling pattern")
        plt.tight_layout()
        plt.show()
    
        # # plot the implemented PMF
        # tailored_crystal_custom_freq = np.array(func_to_matrix(delta_k, Omega_signal, Omega_idler))
        # pmf_tailored_crystal_custom_freq = tailored_crystal_custom.compute_pmf(tailored_crystal_custom_freq)
        # plt.figure(dpi=175)
        # plt.imshow(np.abs(pmf_tailored_crystal_custom_freq), origin='lower', extent=[(Omega_idler[-1]-omega_i)/bandwidth,(Omega_idler[0]-omega_i)/bandwidth,(Omega_signal[-1]-omega_s)/bandwidth,(Omega_signal[0]-omega_s)/bandwidth], cmap='turbo')
        # cbar = plt.colorbar()
        # plt.show()
        
        return np.array(domain_config_custom)

    def calc_crystal_data(self, input_domain_config=np.array([])):
        """
        sets up the crystal, calculating the positions for the Trotter-Suzuki expansion and the orientation of the nonlinear domains,
        including errors in the placement of the domain walls, if selected
        """

        if (self.consider_custom_pm or self.consider_perpol):
            
            if self.consider_perpol: # for periodic poling
        
                domain_config = np.array([1,-1] * (self.number_domains//2)) 
                
                broadband_domain_lengths = [np.pi/(self.delta_k_intrinsic)]*(self.number_domains//2)
                Length_nl = np.array([self.start_nl])
                position = self.start_nl
                for i in range(self.number_domains//2):
                    position = position + broadband_domain_lengths[i]
                    Length_nl = np.append(Length_nl, position) # corresponds to uninverted domain
                    position = position + broadband_domain_lengths[i]
                    Length_nl = np.append(Length_nl, position) # corresponds to inverted domain
                
                # calculate the steps between the domain walls
                Length_step = np.zeros((len(Length_nl)-1))
                for i in range(len(Length_nl)-1):
                    Length_step[i] = Length_nl[i+1] - Length_nl[i]
                
                print('Number of domains:',self.number_domains)
                print('domain width:',1e6*Length_step[len(Length_step)//2],'\u03bcm')
                
                Length_nl = [Length_nl, Length_step[len(Length_step)//2]] # second argument gives the domain width with respect to which domain wall errors are calculated
                            
            if self.consider_custom_pm: # for custom-phase-matching
        
                domain_config  = input_domain_config
        
                # calculate the positions of the domain walls
                Length_nl = np.array([self.start_nl])
                position = self.start_nl
                for i in range(self.number_domains):
                    position = position + self.domain_width
                    Length_nl = np.append(Length_nl, position)
        
                # calculate the steps between the domain walls
                Length_step = np.zeros((len(Length_nl)-1))
                for i in range(len(Length_nl)-1):
                    Length_step[i] = Length_nl[i+1] - Length_nl[i]
                
                print('Number of domains:',self.number_domains)
                print('Domain width:',self.domain_width*1e6,'\u03bcm')
        
                Length_nl = [Length_nl, self.domain_width] # second argument gives the domain width with respect to which domain wall errors are calculated
            
            if (self.consider_domain_wall_errors): # introduce (random) errors into the beginning- and end-positons of the inverted domains 
        
                error_array_equal = np.zeros((len(Length_nl[0]) - 2))
                error_array_rand = np.zeros((len(Length_nl[0]) - 2))
                # width of the inverted domain (g==-1) is taken as reference
                domain_size = self.domain_width
                for i in range(len(domain_config)-1):
                    
                    if (domain_config[i] == 1 and domain_config[i+1] == -1):
                
                        # equally broadened/narrowed inverted domains
                        error_array_equal[i] = -1 * domain_size * self.domain_wall_error_uniform 
                        # randomly displaced domain walls
                        error_array_rand[i] = domain_size * (2*random.rand() - 1) * self.domain_wall_error_random # the domains are broadened/narrowed with equal probability
                         
                    elif (domain_config[i] == -1 and domain_config[i+1] == 1):
                            
                        # equally broadened/narrowed inverted domains
                        error_array_equal[i] = 1 * domain_size * self.domain_wall_error_uniform
                        # randomly displaced domain walls
                        error_array_rand[i] = domain_size * (2*random.rand() - 1) * self.domain_wall_error_random # the domains are broadened/narrowed with equal probability
                            
                error_array = error_array_equal + error_array_rand  
                  
                # add the errors
                wall_errors = np.concatenate(([0], error_array, [0])) # do not change position of first or last domain wall (interfaces between linear and nonliner regions) 
                Length_nl[0] = Length_nl[0] + wall_errors # calculate the postion of the adapted domain walls
                for i in range(len(Length_nl[0])-1): # calculate the corresponding domain-lengths
                    Length_step[i] = Length_nl[0][i+1] - Length_nl[0][i]           
        
        
        else:
            number_of_length_points = self.expansion_steps # number of expansion points in the nonlinear region
            Length_nl = np.linspace(self.start_nl, self.end_nl, num=(number_of_length_points+1), endpoint=True, retstep=True) # partitioning of the nonlinear region
            Length_step = [Length_nl[1]]*number_of_length_points
            domain_config = np.array([1] * self.expansion_steps)

        if self.consider_domain_writing_errors: # introduce errors corresponding to not-written domains
            domains_nw_count = 0
            for i in range(len(domain_config)-1):
                if (domain_config[i] == 1 and domain_config[i+1] == -1 and random.rand() <= self.domain_writing_error_rate):
                    domains_nw_count = domains_nw_count + 1 # track the number of inverted domains
                    while (domain_config[i+1] == -1 and i<(len(domain_config)-2)):
                        domain_config[i+1] = 1
                        i = i+1
                        
        #print('percentage of domains no written:',100*domains_nw_count/(self.number_domains//2),'%')
        print('End of the nonlinear region:',Length_nl[-2][-1]*1e3,'mm')

        # define postion arry and add the linear waveguide
        Length = Length_nl[0]
        Length_step = np.concatenate(([self.start_nl-self.start],Length_step,[self.end-self.end_nl])) 
        Length = np.concatenate(([self.start],Length,[self.end]))
        
        # create arrays to indicate the sign (g) and presence (h) of the nonlinearity
        if (self.consider_custom_pm or self.consider_perpol):
            g = np.concatenate(([0],domain_config,[0]))
            g[1] = 0
            g[-2] = 0
            h = np.concatenate(([0],np.ones(len(domain_config)),[0]))
        else:
            g = np.concatenate(([0],np.ones(number_of_length_points),[0]))
            h = np.concatenate(([0],np.ones(number_of_length_points),[0]))
        
        # plot part of the crystal poling structure
        plotting_window = 100 # between 0 and len(Length_nl)-1
        plotting_window_start = len(Length) - plotting_window - 1
        plt.figure(dpi=175)
        plt.subplot(2, 1, 1)
        plt.bar(1e3*Length[plotting_window_start:plotting_window_start+plotting_window], g[plotting_window_start:plotting_window_start+plotting_window], width=1e3*Length_step[plotting_window_start:plotting_window_start+plotting_window], color='gray', edgecolor='black', align='edge')
        plt.xlabel('position (mm)')
        plt.ylabel('g(z)')
        plt.title("poling pattern (last 100 domains)")
        plt.show()

        return Length, Length_step, g, h

    def calc_waveguide_inhomogeneity(self, input_Length, input_Length_step): 
        """
        introduce random phase-mismatches induced by inhomogeneity of the waveguide
        """
        smoothing = 20 # amount of smoothing applied to the randomly generated propagation constants
        wg_inhomogeneity = self.smooth(self.random_walk(np.linspace(input_Length[1],input_Length[-2],len(input_Length_step)-2), 1, 0), smoothing) # generate the propagation constants
        wg_inhomogeneity = wg_inhomogeneity * (self.propagation_constant_max_deviation/np.abs(np.max(wg_inhomogeneity)-np.min(wg_inhomogeneity))) # rescale to a total width given by 'propagation_constant_max_deviation'
        wg_inhomogeneity = wg_inhomogeneity - np.sum(wg_inhomogeneity)/len(wg_inhomogeneity) # shift to have average zero phase-mismatch (i.e. waveguide varies uniformely around design)
    
        plt.figure(dpi=175)
        plt.subplot(2, 1, 1)
        plt.bar(1e3*input_Length[1:-2], wg_inhomogeneity, width=1e3*input_Length_step[1:-1], color='blue', align='edge', linewidth=0)
        plt.xlabel('position (mm)')
        plt.ylabel('a.u.')
        plt.title("waveguide-inhomogeneity induced phase-mismatch")
        plt.show()
    
        # argument and increment of the integral which accounts for the phase aquired due to inperfect phase-matching (added '[0]' corresponds to the inconsequetial propagation after the nonlinear region)
        phase_mismatch_integrand =  np.concatenate((input_Length_step[1:-1] * wg_inhomogeneity, [0]))

        return phase_mismatch_integrand

    def calc_losses(self):
        """
        calculate the amplitude reduction for a given interval
        """
        losses = self.waveguide_loss
        return lambda interval_length : np.sqrt(np.exp(-1*losses*interval_length))


    """
    constituents of the EOM
    (see Weiss et al. 'Quantum nonlinear parametric interaction in realistic waveguides' and
    Quesada et al. 'Theory of high-gain twin-beam generation in waveguides: From Maxwell's equations to efficient simultion')
    """
    def calculate_pump_amplitude_n(self, z, omega): # (see A4a in Weiss et al.) (for arbitrary functions with numerical integration) (includes uniform (position independent SPM)
        pn = self.photon_number*np.exp(-1*self.waveguide_loss*z)
        return np.exp(1j*self.initial_phase) * np.sqrt(self.hbar*self.omega_p / (2*np.pi*self.v_p(omega))) * np.sum( np.exp(-1j*self.pump_amplitude_sampling*(omega-self.omega_p)/self.v_p(omega)) \
               * self.amplitude_pump(self.pump_amplitude_sampling,pn) * np.exp(1j*self.amplitude_pump(self.pump_amplitude_sampling,pn) \
               * np.conjugate(self.amplitude_pump(self.pump_amplitude_sampling,pn)) * (self.c_SPM/self.v_p(omega)) * (z-self.pump_amplitude_sampling-self.start_nl)) * self.pump_amplitude_sampling_step )
    
    def calculate_energy_distribution_n(self, z, omega): # (see eq. A5 in Weiss et al.) (for arbitrary functions with numerical integration)
        pn = self.photon_number*np.exp(-1*self.waveguide_loss*z)
        return np.exp(1j*self.initial_phase) * self.hbar * self.omega_p * np.sum( self.amplitude_pump(self.pump_amplitude_sampling,pn) \
               * np.conjugate(self.amplitude_pump(self.pump_amplitude_sampling,pn)) * np.exp(-1j*omega*self.pump_amplitude_sampling/self.v_p(self.omega_p+omega)) * self.pump_amplitude_sampling_step )
    
    def calculate_phase_mismatch(self, z, input_omega_s, input_omega_i, phase_mismatch_integrand=np.array([])): # (see exponential in eq. 3a in Weiss et al.) calculate the phase-aquisition due to imperfect phase-matching induced by waveguide inhomogeneity
        if self.consider_waveguide_inhomogeneity:
            phase_mismatch1 = np.exp(1j*np.sum(phase_mismatch_integrand[0:z]))
        else: phase_mismatch1 = 1
        if (self.consider_perpol or self.consider_custom_pm):
            # phase-mismatch term compensated by the (central) poling-period
            phase_mismatch_integrand_pol = np.concatenate((self.Length_step * ([self.delta_k_intrinsic]*len(self.Length_step)), [0])) # argument and increment of the integral (added '[0]' corresponds to the inconsequetial propagation after the nonlinear region)
            phase_mismatch2 = np.exp(1j*np.sum(phase_mismatch_integrand_pol[0:z]))
        else: phase_mismatch2 = 1
        return phase_mismatch1 * phase_mismatch2

    """
    calculate the matrices of the full equation-of-motion
    """
    def calculate_F(self, z): # (see eq. 3a in Weiss et al.)
        F = np.zeros((self.number_of_freq_points,self.number_of_freq_points),dtype=np.complex128)
        for n in range(self.number_of_freq_points):
            for m in range(self.number_of_freq_points):
                if self.consider_PDC:
                    F[n,m] = (self.c_chi2*self.calculate_phase_mismatch(z-1, self.Omega_signal[n], self.Omega_idler[m])*self.g[z-1]/np.sqrt(2*np.pi)) \
                             * self.calculate_pump_amplitude_n(self.Length[z], self.Omega_signal[n] + self.Omega_idler[m]) * self.Omega_signal_step  
                else:
                    F[n,m] = (self.c_chi2*self.calculate_phase_mismatch(z-1, self.Omega_signal[n], self.Omega_idler[m])*self.g[z-1]/np.sqrt(2*np.pi)) \
                             * self.calculate_pump_amplitude_n(self.Length[z], -self.Omega_signal[n] + self.Omega_idler[m]) * self.Omega_signal_step  
        return F
    
    def calculate_G(self, z): # (see eq. 3b in Weiss et al.)
        G = np.zeros((self.number_of_freq_points,self.number_of_freq_points),dtype=np.complex128)
        for n in range(self.number_of_freq_points):
            for m in range(self.number_of_freq_points):
                if self.consider_PDC:
                    G[n,m] = (1/self.v_s(self.Omega_signal[n]) - 1/self.v_p(self.omega_i+self.Omega_signal[n]))*(self.Omega_signal[n] - self.omega_s) * self.kronecker(n,m) \
                             + (1/(2*np.pi))*self.c_XPM_s*self.h[z-1] * self.calculate_energy_distribution_n(self.Length[z], self.Omega_signal[n] - self.Omega_signal[m]) * self.Omega_signal_step
                else:
                    G[n,m] = (1/self.v_s(self.Omega_signal[n]) - 1/self.v_p(self.omega_i-self.Omega_signal[n]))*(self.Omega_signal[n] - self.omega_s) * self.kronecker(n,m)\
                             + (1/(2*np.pi))*self.c_XPM_s*self.h[z-1] * self.calculate_energy_distribution_n(self.Length[z], self.Omega_signal[n] - self.Omega_signal[m]) * self.Omega_signal_step
        return G
    
    def calculate_H(self, z): # (see eq. 3c in Weiss et al.)
        H = np.zeros((self.number_of_freq_points,self.number_of_freq_points),dtype=np.complex128)
        for n in range(self.number_of_freq_points):
            for m in range(self.number_of_freq_points):
                if self.consider_PDC:
                    H[n,m] = (1/self.v_i(self.Omega_idler[n]) - 1/self.v_p(self.omega_s+self.Omega_idler[n]))*(self.Omega_idler[n] - self.omega_i) * self.kronecker(n,m) + (1/(2*np.pi))*self.c_XPM_i*self.h[z-1] \
                    * self.calculate_energy_distribution_n(self.Length[z], self.Omega_idler[n] - self.Omega_idler[m]) * self.Omega_idler_step  
                else:
                    H[n,m] = (1/self.v_i(self.Omega_idler[n]) - 1/self.v_p(-self.omega_s+self.Omega_idler[n]))*(self.Omega_idler[n] - self.omega_i) * self.kronecker(n,m) + (1/(2*np.pi))*self.c_XPM_i*self.h[z-1] \
                    * self.calculate_energy_distribution_n(self.Length[z], self.Omega_idler[n] - self.Omega_idler[m]) * self.Omega_idler_step  
        return H
    
    def calculate_Q(self, z): # (see eq. 2 in Weiss et al.)
        if self.consider_PDC:
            return np.block([[self.calculate_G(z),self.calculate_F(z)], [-1*self.dagger(self.calculate_F(z)),-1*(self.calculate_H(z))]])
        else:
            return np.block([[self.calculate_G(z),np.conjugate(self.calculate_F(z))], [np.transpose(self.calculate_F(z)), (self.calculate_H(z))]])
    
    def calculate_propagator(self, input_target_func=[]): # (see eq. 5 in Weiss et al.)
        """
        calculate the full propagator given the respective simulation settings
        """
        start_time = time.time()

        # calculate the tailored-poling structure (if to be considered)
        if self.consider_custom_pm:
            self.Length, self.Length_step, self.g, self.h = self.calc_crystal_data(input_domain_config=self.tailored_crystal(input_target_func))
        else:
            self.Length, self.Length_step, self.g, self.h = self.calc_crystal_data()

        # calculate the phase-mismatch due to waveguide inhomogeneity (if to be considered)
        if self.consider_waveguide_inhomogeneity:
            phase_mismatch_integrand = self.calc_waveguide_inhomogeneity(self.Length, self.Length_step)

        # Build the matrices and calculate the propagator
        print('calculating propagator...')
        print('-----------------------------')
        self.propagator = expm(1j * self.calculate_Q(1) * self.Length_step[0])
        for n in tqdm(range(len(self.Length)-2)):
            self.propagator = self.propagator @ expm(1j * self.calculate_Q(n+2) * self.Length_step[n+1])

        end_time = time.time()
        print('-----------------------------')
        print('finished calculating propagator')
        print('total computation time:',str(datetime.timedelta(seconds=int(end_time-start_time))),'s')
        
        return self.propagator

    def calculate_TSE_element_n(self, n, input_target_func=[]):
        """
        calculates the n-th element of the trotter-Suzuki expansion from which the full propagater is calculated (for e.g. parallelization implementation)
        """
        start_time = time.time()

        # calculate the tailored-poling structure (if to be considered)
        if self.consider_custom_pm:
            self.Length, self.Length_step, self.g, self.h = self.calc_crystal_data(input_domain_config=self.tailored_crystal(input_target_func))
        else:
            self.Length, self.Length_step, self.g, self.h = self.calc_crystal_data()

        # calculate the phase-mismatch due to waveguide inhomogeneity (if to be considered)
        if self.consider_waveguide_inhomogeneity:
            phase_mismatch_integrand = self.calc_waveguide_inhomogeneity(self.Length, self.Length_step)       

        # Build the matrices and calculate the propagator
        print('calculating propagator...')
        print('-----------------------------')
        self.propagator = expm(1j * self.calculate_Q(n+1) * self.Length_step[n])

        end_time = time.time()
        print('-----------------------------')
        print('finished calculating propagator')
        print('total computation time:',str(datetime.timedelta(seconds=int(end_time-start_time))),'s')
        
        return self.propagator


# ## Outputs Class

class Outputs:
    """ A class to calculate the various outputs of interest from the propagator.
    
    Attr:
        propagator
        propagator_corr
        propagator_ss
        propagator_si
        propagator_is
        propagator_ii

        num_of_freq_points
        omega_p
        omega_s
        omega_i
        Omega_signal
        Omega_idler
        Omega_signal_step
        Omega_idler_step
        bandwidth
        
        Length
        Length_step

        v_p
        v_s
        v_i

        loss_coefficient
    """
    hbar = 6.62607015e-34 / (2*np.pi) #reduced Planck constant in J/Hz (SI units)
    c = 299792458 # vacuum speed-of-light (SI units)

    def __init__(self, input_simulator_class):

        self.loss_coefficient = input_simulator_class.loss_coefficient
        
        self.consider_PDC = input_simulator_class.consider_PDC
        self.consider_losses = input_simulator_class.consider_losses

        self.propagator = input_simulator_class.propagator

        self.omega_p = input_simulator_class.omega_p 
        self.omega_s = input_simulator_class.omega_s 
        self.omega_i = input_simulator_class.omega_i 
        self.bandwidth = input_simulator_class.bandwidth 
        
        self.plotting_range = input_simulator_class.plotting_range
        self.number_of_freq_points = input_simulator_class.number_of_freq_points

        self.Omega_signal = input_simulator_class.Omega_signal
        self.Omega_idler = input_simulator_class.Omega_idler
        self.Omega_signal_step = input_simulator_class.Omega_signal_step
        self.Omega_idler_step = input_simulator_class.Omega_idler_step

        self.v_p = input_simulator_class.v_p
        self.v_s = input_simulator_class.v_s
        self.v_i = input_simulator_class.v_i

        self.Length = input_simulator_class.Length
        self.Length_step = input_simulator_class.Length_step
        
        self.propagator_corr = self.remove_linear_phase_aquisition(self.propagator)
        self.propagator_ss, self.propagator_si, self.propagator_is, self.propagator_ii = self.extract_transformations(self.propagator_corr)

    def extract_transformations(self, input_propagator): 
        """
        (see eq. 4 in Weiss et al.)
        """
        propagator_ss = input_propagator[0:self.number_of_freq_points,0:self.number_of_freq_points]
        propagator_si = input_propagator[0:self.number_of_freq_points,self.number_of_freq_points:2*self.number_of_freq_points]
        propagator_is = np.conjugate(input_propagator[self.number_of_freq_points:2*self.number_of_freq_points,0:self.number_of_freq_points])
        propagator_ii = np.conjugate(input_propagator[self.number_of_freq_points:2*self.number_of_freq_points,self.number_of_freq_points:2*self.number_of_freq_points])
        return propagator_ss, propagator_si, propagator_is, propagator_ii
    
    def remove_linear_phase_aquisition(self, input_propagator):
        """
        remove the phase aquired due to linear propagation (makes for nicer output modes in the Schmidt decomposition)
        """
        total_crystal_length = (self.Length[-1] - self.Length[0])
    
        lin_prop_s = []
        lin_prop_i = []
        if self.consider_PDC:
            QFC_adaption = 1
            for i in range(self.number_of_freq_points):
                lin_prop_s = np.append(lin_prop_s, (1/self.v_s(self.Omega_signal[i]) - 1/self.v_p(self.omega_i+self.Omega_signal[i])) )
                lin_prop_i = np.append(lin_prop_i, (1/self.v_s(self.Omega_idler[i]) - 1/self.v_p(self.omega_s+self.Omega_idler[i])) )
        else:
            QFC_adaption = -1 # factor to accout for description in terms of a_s and a_i in QFC model (instead of a_s and a_i^dagger in PDC model)
            for i in range(self.number_of_freq_points):
                lin_prop_s = np.append(lin_prop_s, (1/self.v_s(self.Omega_signal[i]) - 1/self.v_p(self.omega_i-self.Omega_signal[i])) )
                lin_prop_i = np.append(lin_prop_i, (1/self.v_s(self.Omega_idler[i]) - 1/self.v_p(-self.omega_s+self.Omega_idler[i])) )
    
        K_ss_corr = np.diag(np.exp(-1j*lin_prop_s*(self.Omega_signal - self.omega_s) * total_crystal_length/2)) \
                    @ input_propagator[0:self.number_of_freq_points,0:self.number_of_freq_points] \
                    @ np.diag(np.exp(-1j*lin_prop_s*(self.Omega_signal - self.omega_s) * total_crystal_length/2)) 
        K_si_corr = np.diag(np.exp(-1j*lin_prop_s*(self.Omega_signal - self.omega_s) * total_crystal_length/2)) \
                    @ input_propagator[0:self.number_of_freq_points,self.number_of_freq_points:2*self.number_of_freq_points] \
                    @ np.diag(np.exp(QFC_adaption*1j*lin_prop_i*(self.Omega_idler - self.omega_i) * total_crystal_length/2)) 
        K_is_corr = np.diag(np.exp(QFC_adaption*1j*lin_prop_i*(self.Omega_idler - self.omega_i) * total_crystal_length/2)) \
                    @ input_propagator[self.number_of_freq_points:2*self.number_of_freq_points,0:self.number_of_freq_points] \
                    @ np.diag(np.exp(-1j*lin_prop_s*(self.Omega_signal - self.omega_s) * total_crystal_length/2))
        K_ii_corr = np.diag(np.exp(QFC_adaption*1j*lin_prop_i*(self.Omega_idler - self.omega_i) * total_crystal_length/2)) \
                    @ input_propagator[self.number_of_freq_points:2*self.number_of_freq_points,self.number_of_freq_points:2*self.number_of_freq_points] \
                    @ np.diag(np.exp(QFC_adaption*1j*lin_prop_i*(self.Omega_idler - self.omega_i) * total_crystal_length/2)) 
        
        return np.block([[K_ss_corr,K_si_corr], [K_is_corr,K_ii_corr]])
    
    def calculate_moments_PDC(self, make_plots=True, schmidt_mode_number=0):
        """
        (see eq. 6 and A11 in Weiss et al)
        """
        phase_sensitive_moment_M = self.propagator_ss @ np.transpose(self.propagator_is)
        phase_insensitive_moment_N_s = np.conjugate(self.propagator_si) @ np.transpose(self.propagator_si)
        phase_insensitive_moment_N_i = np.conjugate(self.propagator_is) @ np.transpose(self.propagator_is)
        if self.consider_losses:
            phase_sensitive_moment_M = (self.loss_coefficient(np.sum(self.Length_step[1:len(self.Length)-1]))**2) * phase_sensitive_moment_M
            phase_insensitive_moment_N_s = (self.loss_coefficient(np.sum(self.Length_step[1:len(self.Length)-1]))**2) * phase_insensitive_moment_N_s
            phase_insensitive_moment_N_i = (self.loss_coefficient(np.sum(self.Length_step[1:len(self.Length)-1]))**2) * phase_insensitive_moment_N_i
        print('diagonalizing matrices...')
        J_M,S_diag_M,J_t_M = np.linalg.svd(phase_sensitive_moment_M)
        SM_s_ev, SM_s = np.linalg.eigh(phase_insensitive_moment_N_s)
        SM_i_ev, SM_i = np.linalg.eigh(phase_insensitive_moment_N_i)
        print('finished diagonalizing matrices')
        squeezing_parameters_M = 0.5*np.arcsinh(2*S_diag_M)
        K = (np.sum((np.sinh(squeezing_parameters_M))**2))**2 / np.sum((np.sinh(squeezing_parameters_M))**4)

        M, N_s, N_i, Squeezing_M, JSA_M, SchmidtModes_s, SchmidtModes_i, SchmidtNum = phase_sensitive_moment_M, phase_insensitive_moment_N_s, phase_insensitive_moment_N_i, squeezing_parameters_M, \
                                                                                      J_M @ np.diag(squeezing_parameters_M) @ J_t_M / self.Omega_signal_step, [SM_s_ev[::-1],np.flip(SM_s,axis=1)], \
                                                                                      [SM_i_ev[::-1], np.flip(SM_i,axis=1)], K

        if make_plots:
            wl_range_signal =1e6* 2*np.pi*self.c/self.Omega_signal
            wl_range_idler = 1e6* 2*np.pi*self.c/self.Omega_idler
            XData, YData = np.meshgrid(wl_range_signal, wl_range_idler)
            XData_freq, YData_freq = np.meshgrid((self.Omega_signal-self.omega_s)/self.bandwidth, (self.Omega_idler-self.omega_i)/self.bandwidth)

            # plot the JSA
            plt.figure(dpi=250)            
            plt.subplot(2, 2, 1)
            plt.pcolormesh(XData, YData, np.abs(JSA_M), snap=True, shading='auto', cmap='turbo')
            cbar = plt.colorbar()
            plt.xlabel("Signal Wavelength (\u03bcm)")
            plt.tick_params(direction="in")
            plt.title("")
            plt.tight_layout()
            plt.show()

            print('down-converted signal/idler photon number:',abs(np.matrix.trace(N_s)),'/',abs(np.matrix.trace(N_i)))
            print('Schmidt number:',SchmidtNum)

            mode_number = schmidt_mode_number

            SM_prevalence_s = SchmidtModes_s[0]
            Schmidt_modes_s = SchmidtModes_s[1]
            SM_prevalence_i = SchmidtModes_i[0]
            Schmidt_modes_i = SchmidtModes_i[1]

            # plot the n-th Schmidt mode and the first few Schmidt numbers and squeezing parameters
            plt.figure(dpi=175)        
            plt.subplot(2, 2, 1)
            plt.plot(wl_range_signal, np.real(np.exp(-1j*np.angle(Schmidt_modes_s[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_s[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label=" ") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            plt.plot(wl_range_signal, np.imag(np.exp(-1j*np.angle(Schmidt_modes_s[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_s[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label=" ") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            
            #plt.axis([x1, x2, y1, y2])
            plt.tick_params(direction="in")
            plt.title("Signal Schmidt modes")
            plt.xlabel("Signal Wavelength (\u03bcm)")
            plt.ylabel("")
            
            plt.subplot(2, 2, 2)
            plt.plot(wl_range_idler, np.real(np.exp(-1j*np.angle(Schmidt_modes_i[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_i[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label=" ") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            plt.plot(wl_range_idler, np.imag(np.exp(-1j*np.angle(Schmidt_modes_i[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_i[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label=" ") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            # #plt.axis([x1, x2, y1, y2])
            plt.tick_params(direction="in")
            plt.title("Idler Schmidt modes")
            plt.xlabel("Idler Wavelength (\u03bcm)")
            plt.ylabel("")
            
            plt.subplot(2, 2, 3)
            mode_numbers = ['1','2','3','4','5']
            plt.bar(np.arange(len(mode_numbers))-0.15, SM_prevalence_s[0:5], 0.3, label='signal')
            plt.bar(np.arange(len(mode_numbers))+0.15, SM_prevalence_i[0:5], 0.3, label='idler')
            plt.title("Schmidt coefficients")
            plt.legend() 
            
            J_N_s,S_diag_N_s,J_t_N_s = np.linalg.svd(N_s)
            J_N_i,S_diag_N_i,J_t_N_i = np.linalg.svd(N_i)
            plt.subplot(2, 2, 4)
            mode_numbers = ['1','2','3','4','5']
            plt.bar(np.arange(len(mode_numbers)), Squeezing_M[0:5], 0.1, label='from M')
            plt.bar(np.arange(len(mode_numbers))-0.2, np.arcsinh(np.sqrt(S_diag_N_s))[0:5], 0.1, label='from N_s (SVD)',alpha=0.2)
            plt.bar(np.arange(len(mode_numbers))-0.1, np.arcsinh(np.sqrt(S_diag_N_i))[0:5], 0.1, label='from N_i (SVD)',alpha=0.2)
            plt.bar(np.arange(len(mode_numbers))+0.1, np.arcsinh(np.sqrt(SM_prevalence_s))[0:5], 0.1, label='from N_s (EVD)',alpha=0.2)
            plt.bar(np.arange(len(mode_numbers))+0.2, np.arcsinh(np.sqrt(SM_prevalence_i))[0:5], 0.1, label='from N_i (EVD)',alpha=0.2)
            plt.title("Schmidt mode squeezing")
            plt.legend() 
            plt.tight_layout()
            plt.show()
            
            print('Schmidt number:',SchmidtNum)

        return phase_sensitive_moment_M, phase_insensitive_moment_N_s, phase_insensitive_moment_N_i, squeezing_parameters_M, \
               J_M @ np.diag(squeezing_parameters_M) @ J_t_M / self.Omega_signal_step, [SM_s_ev[::-1],np.flip(SM_s,axis=1)], \
               [SM_i_ev[::-1], np.flip(SM_i,axis=1)], K
    
    def calculate_moments_QFC(self, make_plots=True, schmidt_mode_number=0):
        """
        (see eq. 6 and A15 in Weiss et al.)
        """
        if self.consider_losses:
            self.propagator_si = self.loss_coefficient(np.sum(self.Length_step[1:len(self.Length)-1])) * self.propagator_si
            self.propagator_is = self.loss_coefficient(np.sum(self.Length_step[1:len(self.Length)-1])) * self.propagator_is
        print('diagonalizing matrices...')
        J_QFC_si,S_diag_QFC_si,J_t_QFC_si = np.linalg.svd(self.propagator_si)
        J_QFC_is,S_diag_QFC_is,J_t_QFC_is = np.linalg.svd(self.propagator_is)
        print('finished diagonalizing matrices')
        conversion_eff = [S_diag_QFC_si**2, S_diag_QFC_is**2]
        SM_ev_s = np.arcsin(S_diag_QFC_si)
        SM_ev_i = np.arcsin(S_diag_QFC_is)

        Conversion_Efficiency, SchmidtMode_EVs, SchmidtModes_s_QFC, SchmidtModes_i_QFC = conversion_eff, [SM_ev_s, SM_ev_i], [J_QFC_is,J_t_QFC_si.T], [J_QFC_si,J_t_QFC_is.T]

        if make_plots:
            wl_range_signal =1e6* 2*np.pi*self.c/self.Omega_signal
            wl_range_idler = 1e6* 2*np.pi*self.c/self.Omega_idler
            XData, YData = np.meshgrid(wl_range_signal, wl_range_idler)
            XData_freq, YData_freq = np.meshgrid((self.Omega_signal-self.omega_s)/self.bandwidth, (self.Omega_idler-self.omega_i)/self.bandwidth)

            # plot the process transfer functions
            plt.figure(dpi=250)
            plt.subplot(2, 2, 1)
            plt.pcolormesh(XData, YData, np.transpose(np.abs(self.propagator_si)), snap=True, shading='auto', cmap='turbo')
            cbar = plt.colorbar()
            plt.ylabel("Idler Wavelength (\u03bcm)")
            plt.xlabel("Signal Wavelength (\u03bcm)")
            plt.tick_params(direction="in")
            plt.title("")
        
            plt.subplot(2, 2, 2)
            plt.pcolormesh(XData, YData, np.abs(self.propagator_is), snap=True, shading='auto', cmap='turbo')
            cbar = plt.colorbar()
            plt.ylabel("Idler Wavelength (\u03bcm)")
            plt.xlabel("Signal Wavelength (\u03bcm)")
            plt.tick_params(direction="in")
            plt.title("")
            
            plt.tight_layout()
            plt.show()

            Schmidt_mode_prevalences = SchmidtMode_EVs[0] / np.sum(SchmidtMode_EVs[0])

            print('conversion efficiency (first Schmidt mode):',Conversion_Efficiency[0][0])
            print('conversion efficiency (total):',np.sum(Conversion_Efficiency[0] * Schmidt_mode_prevalences),'|',(np.sin(np.sum(SchmidtMode_EVs[1])))**2,'|',np.prod((np.sin(SchmidtMode_EVs[0])))**2)
            print('selectivity (first Schmidt mode):',(np.arcsin(np.sqrt(Conversion_Efficiency[0][0]))**2) / np.sum(np.arcsin(np.sqrt(Conversion_Efficiency[0]))) )
            print('separability (first Schmidt mode):',np.arcsin(np.sqrt(Conversion_Efficiency[0][0])) / np.sum(np.arcsin(np.sqrt(Conversion_Efficiency[0]))) )

            mode_number = schmidt_mode_number
            
            SM_prevalence_s_QFC = SchmidtMode_EVs[0]
            Schmidt_modes_s_QFC_out = np.conjugate(SchmidtModes_s_QFC[0])
            Schmidt_modes_s_QFC_in = SchmidtModes_s_QFC[1]
            SM_prevalence_i_QFC = SchmidtMode_EVs[1]
            Schmidt_modes_i_QFC_out = np.conjugate(SchmidtModes_i_QFC[0])
            Schmidt_modes_i_QFC_in = SchmidtModes_i_QFC[1]

            # plot the n-th Schmidt mode of the interaction and the first few Schmidt numbersand squeezing parameters
            plt.figure(dpi=175)
            
            plt.subplot(2, 2, 1)
            plt.plot(wl_range_signal, np.real(np.exp(-1j*np.angle(Schmidt_modes_s_QFC_in[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_s_QFC_in[:,mode_number]), marker='^', linestyle='dotted', linewidth=2, markersize=0, label="input mode real") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            plt.plot(wl_range_signal, np.imag(np.exp(-1j*np.angle(Schmidt_modes_s_QFC_in[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_s_QFC_in[:,mode_number]), marker='^', linestyle='dotted', linewidth=2, markersize=0, label="input mode imag") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
        
            plt.plot(wl_range_signal, np.real(np.exp(-1j*np.angle(Schmidt_modes_s_QFC_out[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_s_QFC_out[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label="output mode real") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            plt.plot(wl_range_signal, np.imag(np.exp(-1j*np.angle(Schmidt_modes_s_QFC_out[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_s_QFC_out[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label="output mode imag") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
        
            #plt.axis([x1, x2, y1, y2])
            plt.tick_params(direction="in")
            plt.title("Signal Schmidt modes")
            plt.xlabel("Signal Wavelength (\u03bcm)")
            plt.ylabel("")
            #plt.legend()
            
            plt.subplot(2, 2, 2)
            plt.plot(wl_range_idler, np.real(np.exp(-1j*np.angle(Schmidt_modes_i_QFC_in[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_i_QFC_in[:,mode_number]), marker='^', linestyle='dotted', linewidth=2, markersize=0, label="inpu mode real") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            plt.plot(wl_range_idler, np.imag(np.exp(-1j*np.angle(Schmidt_modes_i_QFC_in[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_i_QFC_in[:,mode_number]), marker='^', linestyle='dotted', linewidth=2, markersize=0, label="input mode imag") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
        
            plt.plot(wl_range_idler, np.real(np.exp(-1j*np.angle(Schmidt_modes_i_QFC_out[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_i_QFC_out[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label="output mode real") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
            plt.plot(wl_range_idler, np.imag(np.exp(-1j*np.angle(Schmidt_modes_i_QFC_out[(self.number_of_freq_points-1)//2,mode_number]))*Schmidt_modes_i_QFC_out[:,mode_number]), marker='^', linestyle='-', linewidth=1, markersize=0, label="output mode imag") # prefactor ensures the imaginary component is zero for the central frequency (prettier plots)
        
            # #plt.axis([x1, x2, y1, y2])
            plt.tick_params(direction="in")
            plt.title("Idler Schmidt modes")
            plt.xlabel("Idler Wavelength (\u03bcm)")
            plt.ylabel("")
            #plt.legend() 
            
            plt.subplot(2, 2, 3)
            mode_numbers = ['1','2','3','4','5']
            mode_numbers = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15']
            plt.bar(np.arange(len(mode_numbers))-0.15, Conversion_Efficiency[0][0:15], 0.3, label='signal')
            plt.bar(np.arange(len(mode_numbers))+0.15, Conversion_Efficiency[1][0:15], 0.3, label='idler')
            #plt.bar(np.arange(len(mode_numbers))+0.45, (np.sin(SchmidtMode_EVs[0][0:15]))**2, 0.3, label='raw')
            plt.title("Schmidt mode conversion efficiency")
            plt.legend() 
            
            #print('Schmidt number:',SchmidtNum)
        
            plt.tight_layout()
            plt.show()
            
        return self.propagator_si, self.propagator_is, SchmidtModes_s_QFC, SchmidtModes_i_QFC, Conversion_Efficiency


