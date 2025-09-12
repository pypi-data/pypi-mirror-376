from dataclasses import dataclass
from typing import Any, List,Literal
import jax.numpy as jnp
from matinverse.geometry2D import Geometry2D
from matinverse.geometry3D import Geometry3D
from dataclasses import dataclass, field
from matinverse.IO import WriteVTR
import jax



@dataclass
class Field:
    name:           str
    data:           jnp.ndarray
    surface:        bool = False
    units:          str = 'ad'


@dataclass
class Fields:
    geometry:   Geometry2D | Geometry3D          
    batch_size: int = 1
    time_steps: jnp.ndarray = field(default_factory=lambda: jnp.array([0.0]))
    fields:     List[Any]   = field(default_factory=list)


    def add_field(self, *args,**kwargs):
        """Add a field to the Fields object."""
         # snapshot, no tracers
        self.fields.append(Field(*args,**kwargs))

    def __getitem__(self, key: str) -> jnp.ndarray:
        """Get a field by its name."""
        Nx, Ny, Nz = self.geometry.grid
        for f in self.fields:
            if f.name == key:
               
                if self.batch_size == 1 and self.time_steps.size == 1:
                    x = f.data[0,0]
                    return x.reshape((Nx, Ny, Nz, *x.shape[1:]), order="F")
                elif self.batch_size == 1 and self.time_steps.size > 1:
                    #TO RESHAPE
                    return f.data[:,0,...]
                elif self.batch_size > 1 and self.time_steps.size == 1:
                    x = f.data[0]
                    return x.reshape((x.shape[0], Nx, Ny, Nz, *x.shape[2:]), order="F")
                
                else:
                    #TO RESHAPE
                    return f.data
        raise KeyError(f"No field with name '{key}'")
    
    def integrate(self,name,condition) -> Field:
        """Integrate a surface field over a boundary"""
    
        for f in self.fields:
            if f.name == name:
                if f.surface is False:
                    raise ValueError(f"Field '{name}' is not a surface field and cannot be integrated.")
                
                inds = self.geometry.select_boundary(condition)

                P = jnp.einsum('tbs,s -> tb',f.data[:,:,inds],self.geometry.boundary_areas[inds])

                if self.batch_size == 1 and self.time_steps.size == 1:
                    return P[0,0]
                elif self.batch_size == 1 and self.time_steps.size > 1:
                    return P[:,0]
                elif self.batch_size > 1 and self.time_steps.size == 1:
                    return P[0]
                else:
                    return P

        raise KeyError(f"No field with name '{name}'")        
    

    def write_vtr(self, filename: str, regions: jnp.ndarray = None):
        """Write the fields to a VTR file."""

        WriteVTR(self.geometry,self.fields,self.batch_size,regions=regions, filename=filename)


