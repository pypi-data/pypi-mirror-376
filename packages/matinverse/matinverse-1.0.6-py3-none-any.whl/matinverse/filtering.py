from jax import numpy as jnp
from jax.scipy.signal import convolve2d,convolve,fftconvolve
import jax
import numpy as np
import matplotlib.pylab as plt
import time


@jax.jit
def convolve_shortcut(x,y):

    return jax.scipy.signal.convolve(x,y,mode='same',method='fft')

@jax.jit
def convolve_periodic(x,y):

    N = x.shape[0]
    x = jnp.pad(x,N,mode='wrap')

    return jax.scipy.signal.convolve(x,y,mode='same')[N:2*N,N:2*N]



def Conic2D(geometry, R, \
                    mask     = [],
                    normalize_at_border = True,
                    FFT = True,
                    ):
    
  
    C_norm = jnp.linalg.norm(geometry.centroids, axis=1)
    grid = np.array(geometry.grid)
    tmp = C_norm / R
    kernel = jnp.where(tmp < 1, 1 - tmp, 0).reshape(grid)


    kernel_shifted_FFT = jnp.fft.fft2(jnp.fft.ifftshift(kernel))



    def get_convolve_function():
     
    
     #return lambda x, y: jax.scipy.signal.convolve(x, y, mode='same', method='fft')  
     if geometry.periodic[0] and not geometry.periodic[1]:
        # Periodic in the first axis only
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((grid[0], grid[0]), (0, 0)), mode='wrap'), y, mode='same', method='fft'
        )[grid[0]:2*grid[0], :]

     elif geometry.periodic[1] and not geometry.periodic[0]:
        # Periodic in the second axis only
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((0, 0), (grid[1], grid[1])), mode='wrap'), y, mode='same', method='fft'
        )[:, grid[1]:2*grid[1]]

     elif not geometry.periodic[1] and not geometry.periodic[0]:
        # Non-periodic in both axes
        return lambda x, y: jax.scipy.signal.convolve(x, y, mode='same', method='fft')

     elif geometry.periodic[1] and geometry.periodic[0]:
        
        if FFT: 
         return lambda x, y: jnp.real(jnp.fft.ifft2(jnp.fft.fft2(x) * kernel_shifted_FFT))
        else:
         return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((grid[0], grid[0]), (grid[1], grid[1])), mode='wrap'), y, mode='same', method='fft'
        )[grid[0]:2*grid[0], grid[1]:2*grid[1]]  
 

        #return lambda x, y: jnp.real(jnp.fft.ifft2(jnp.fft.fft2(x) * jnp.fft.fft2(kernel)))
     
        # Periodic in both axes
        #
    convolve = get_convolve_function()

    if len(mask)==0:
       mask = jnp.ones_like(kernel)
    mask  = mask.reshape((grid[0],grid[1]))   

    # Precompute the scaling factor
    if normalize_at_border:
        normalization = convolve(mask,kernel)
        scale = jnp.where( normalization > 0, 1 /  normalization, 0)
    else:
     scale = 1/kernel.sum()

  
    #@jax.jit
    def convolution(x):

        x = x.reshape(grid)
       
        # Perform convolution on the masked input
        output = convolve(x*mask,kernel)

        return jnp.where(mask, output*scale, x)

    return convolution




def Conic3D(geometry, R, \
                      mask     = [],
                      normalize_at_border = True
                      ):
    
  
    C_norm = jnp.linalg.norm(geometry.centroids, axis=1)
    grid = np.array(geometry.grid)
    tmp = C_norm / R
    kernel = jnp.where(tmp < 1, 1 - tmp, 0).reshape(grid)

    kernel_shifted_FFT = jnp.fft.fftn(jnp.fft.ifftshift(kernel))

    #dx = geometry.size[0]/geometry.grid[0]


    def get_convolve_function():
     
    
       
     if geometry.periodic[0] and not geometry.periodic[1] and not geometry.periodic[2]:
        # [1,0,0]
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((grid[0], grid[0]), (0, 0),(0, 0)), mode='wrap'), y, mode='same', method='fft'
        )[grid[0]:2*grid[0], :,:]

     elif not geometry.periodic[0] and geometry.periodic[1] and not geometry.periodic[2]:
        # [0,1,0]
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((0, 0), (grid[1], grid[1]),(0,0)), mode='wrap'), y, mode='same', method='fft'
        )[:, grid[1]:2*grid[1],:]

     elif not geometry.periodic[0] and not geometry.periodic[1] and not geometry.periodic[2]:
        # [0,0,0]
        
        return lambda x, y: jax.scipy.signal.convolve(x, y, mode='same', method='fft')

     elif geometry.periodic[0] and geometry.periodic[1] and geometry.periodic[2]:
        # [1,1,1]

        return lambda x, y: jnp.real(jnp.fft.ifftn(jnp.fft.fftn(x) *  kernel_shifted_FFT))
        # return lambda x, y: jax.scipy.signal.convolve(
        #     jnp.pad(x, ((grid[0], grid[0]), (grid[1], grid[1]),(grid[2],grid[2])), mode='wrap'), y, mode='same', method='fft'
        # )[grid[0]:2*grid[0], grid[1]:2*grid[1],grid[2]:2*grid[2]]  
     

     elif not geometry.periodic[0] and not geometry.periodic[1] and geometry.periodic[2]:
        # [0,0,1]
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((0,0), (0, 0),(grid[2],grid[2])), mode='wrap'), y, mode='same', method='fft'
        )[:,:,grid[2]:2*grid[2]]  
     
     elif not geometry.periodic[0] and geometry.periodic[1] and geometry.periodic[2]:
        # [0,1,1]
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((0,0), (grid[1], grid[1]),(grid[2],grid[2])), mode='wrap'), y, mode='same', method='fft'
        )[:,grid[1]:2*grid[1],grid[2]:2*grid[2]]  
     
     elif  geometry.periodic[0] and  not geometry.periodic[1] and geometry.periodic[2]:
        # [1,0,1]
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((grid[0],grid[0]), (0, 0),(grid[2],grid[2])), mode='wrap'), y, mode='same', method='fft'
        )[grid[0]:2*grid[0],:,grid[2]:2*grid[2]] 
     
     elif  geometry.periodic[0] and  geometry.periodic[1] and not geometry.periodic[2]:
        # [1,1,0]
        return lambda x, y: jax.scipy.signal.convolve(
            jnp.pad(x, ((grid[0],grid[0]), (grid[1], grid[1]),(0,0)), mode='wrap'), y, mode='same', method='fft'
        )[grid[0]:2*grid[0],grid[1]:2*grid[1],:] 
     
     
 
    convolve = get_convolve_function()

    if len(mask)==0:
       mask = jnp.ones_like(kernel)
    mask  = mask.reshape(grid)   

    # Precompute the scaling factor
    if normalize_at_border:
        normalization = convolve(mask,kernel)
        scale = jnp.where( normalization > 0, 1 /  normalization, 0)
    else:
     scale = 1/kernel.sum()

  

    @jax.jit
    def convolution(x):

        x = x.reshape(grid)
      
        # Perform convolution on the masked input
        output = convolve(x*mask,kernel)
 
        return jnp.where(mask, output*scale, x)

    return convolution








