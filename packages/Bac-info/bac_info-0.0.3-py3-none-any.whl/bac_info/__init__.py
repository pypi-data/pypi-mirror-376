"""
My Library - A collection of utility functions for common programming tasks.

This package provides utilities for:
- Input validation and collection
- Array and matrix manipulation  
- String and character operations
- Mathematical computations
- Data structure searches

Author: Your Name
Version: 0.1.0
"""

from .core import (
    # Input validation functions
    saisir_n,
    saisir_f, 
    saisir_ch,
    
    # Array operations
    remplir_t,
    remplir_t_f,
    remplir_t_ch,
    afficher_t,
    
    # Matrix operations
    remplir_m,
    remplir_m_f, 
    remplir_m_ch,
    afficher_m,
    
    # Search functions
    existance_t,
    existance_ch,
    existance_int,
    
    # Mathematical functions
    pgcd,
    puissance,
    sommechiffre,
    
    # String processing
    palindrom
)

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

# Define what gets imported with "from my_library import *"
__all__ = [
    'saisir_n', 'saisir_f', 'saisir_ch',
    'remplir_t', 'remplir_t_f', 'remplir_t_ch', 'afficher_t',
    'remplir_m', 'remplir_m_f', 'remplir_m_ch', 'afficher_m',
    'existance_t', 'existance_ch', 'existance_int',
    'pgcd', 'puissance', 'sommechiffre', 'palindrom'
]