import equinox as eqx
import jax.numpy as jnp
from typing import Dict, Any
from matinverse.geometry2D import Geometry2D
from matinverse.geometry3D import Geometry3D
from matinverse.IO import WriteVTR
import equinox as eqx
import jax.numpy as jnp
from typing import Dict, Any

class Fields(eqx.Module):

    # required fields first
    field_dict: Dict[str, dict] = eqx.field(default_factory=dict)

    # static metadata fields can have defaults
    meta_dict: Dict[str, Dict[str, Any]] = eqx.field(static=True, default_factory=dict)


    def add_field(self, name, data, surface=False, units="ad", 
                  batch_size=1, time_stamps=jnp.array([0])):
        
        new_field_dict = dict(self.field_dict)
        new_field_dict[name] = {'data':data,'time_stamps':time_stamps}
        new_meta_dict = dict(self.meta_dict)
        new_meta_dict[name] = {
            "surface": surface, 
            "units": units,                # safe: static
            "batch_size": batch_size, 
        }

        return Fields(field_dict=new_field_dict, meta_dict=new_meta_dict)

    def __getitem__(self, key):
            if key not in self.field_dict:
                raise KeyError(f"No field with name '{key}'")
            data = self.field_dict[key]['data']

            #This is the case of the density
            if data.ndim == 3 and self.meta_dict[key]['batch_size'] == 1:
                return data

            if len(self.field_dict[key]['time_stamps']) == 1:
             return data[0] #Return only the first time step for now
            else:
             return data

    def integrate(self,geometry: Geometry2D | Geometry3D, 
                   name: str, 
                   condition) -> jnp.ndarray:
         
         if name not in self.field_dict:
             raise KeyError(f"No field with name '{name}'")

         f = self.field_dict[name]
         data = f["data"]
         time_stamps = f["time_stamps"]
         meta = self.meta_dict[name]
         surface  = meta['surface']
         batch_size = meta['batch_size']
        

         if not surface:
             raise ValueError(f"Field '{name}' is not a surface field and cannot be integrated.")

         inds = geometry.select_boundary(condition)
         P = jnp.einsum("tbs,s -> tb", data[:, :, inds], geometry.boundary_areas[inds])
        

         if batch_size == 1 and len(time_stamps) == 1:
              return P[0, 0]
         elif batch_size == 1 and len(time_stamps) > 1:
              return P[:, 0]
         elif batch_size > 1 and len(time_stamps) == 1:

              return P[0]
         else:
             return P

    def write(self, geometry: Geometry2D | Geometry3D,
               filename: str):

        WriteVTR(geometry, self.field_dict, self.meta_dict, filename=filename)