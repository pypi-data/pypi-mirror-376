# Quantum Nonlinear Parametric Interaction in Realistic Waveguides

The `QNPI_InRealisticWaveguides` is a module for modelling quantum nonlinear interaction in waveguides affected by imperfections and deviations-from-design typically associated with realistic fabrication processes. The modelling framework assumes an undepleted pump field, leading to an effectively Gaussian evolution.

This module contains a consolidated and streamlined version of the scripts that were used to generate the results in 

> Weiss, T. F., Youssry, A., & Peruzzo, A. (2025). Quantum nonlinear parametric interaction in realistic waveguides: a comprehensive study. [arXiv:2506.20184](https://doi.org/10.48550/arXiv.2506.20184)



## Installation

Install via pip:

pip install QNPI-InRealisticWaveguides



## Examples and related material

An exemplary jupyter notebook introducing the capabilities and the workflow of the module can be found in the `example` directory.

A detailed description of the theory behind the modelling framework can be found in 

> Weiss, T. F., Youssry, A., & Peruzzo, A. (2025). Quantum nonlinear parametric interaction in realistic waveguides: a comprehensive study. [arXiv:2506.20184](https://doi.org/10.48550/arXiv.2506.20184)

> Quesada, N., et al. (2020). Theory of high-gain twin-beam generation in waveguides: From Maxwell's equations to efficient simulation. Phys. Rev. A 102, 033519 (https://doi.org/10.1103/PhysRevA.102.033519)


## Features & Comments

Quantitatively connecting the modelling framework with an explicit waveguide requires calculation of the respective dispersion and modal-field data. Exemplary data is provided in the files under `ModeSolverData` together with a COMSOL file capable of generating them for arbitrary waveguides. 
While the module can be used without the files containing the waveguide modes by directly supplying the nonlinear interaction coefficients calculated from them, a file containing dispersion data is strictly required.

In its current state, the module is (in all likelihood) far from computationally optimized, and requires implementation alongside significant parallelization when treating complex cases.  