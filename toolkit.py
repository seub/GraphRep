import numpy as np

def mod2pi(t):
    q= int(t/(2*np.pi))
    if t<0:
        q -= 1
    return t - 2*np.pi*q
    
def qnorm(z):
    return z.real*z.real+z.imag*z.imag
