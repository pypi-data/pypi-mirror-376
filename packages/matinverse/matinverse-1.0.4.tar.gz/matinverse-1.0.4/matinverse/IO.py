import gdspy
import numpy as np
from scipy.ndimage import gaussian_filter
from skimage import measure
import matplotlib.pylab as plt
import xml.etree.ElementTree as ET
from typing import Any, List,Literal



def WriteVTR(geo,
             fields: dict,
             metadata: dict = None,
             filename="output"):

    dim = geo.dim

    vtkfile = ET.Element("VTKFile",
                         type="RectilinearGrid",
                         version="0.1",
                         byte_order="LittleEndian")

    nx, ny, nz = geo.grid[0]+1, geo.grid[1]+1, geo.grid[2]+1
    grid = ET.SubElement(vtkfile, "RectilinearGrid",
                         WholeExtent=f"0 {nx-1} 0 {ny-1} 0 {nz-1}")
    piece = ET.SubElement(grid, "Piece",
                          Extent=f"0 {nx-1} 0 {ny-1} 0 {nz-1}")

    # Coordinates
    coords = ET.SubElement(piece, "Coordinates")
    for name, arr in zip(["X","Y","Z"], [geo.x_nodes,geo.y_nodes,geo.z_nodes]):
        da = ET.SubElement(coords, "DataArray",
                           type="Float32", Name=name,
                           NumberOfComponents="1", format="ascii")
       
        da.text = ' '.join(map(str, arr))

    # Always create CellData container
    celldata = ET.SubElement(piece, "CellData")

    # Variables
    for variable_name, field in fields.items():
        meta = metadata[variable_name]
        if meta['surface']:
            continue

        data = field['data']

        for b in range(meta['batch_size']):
            name = f"{variable_name}[{b}]_[{meta['units']}]" if meta['batch_size'] > 1 else f"{variable_name}_[{meta['units']}]"

            if data.ndim == dim:
                #this is a special case of a scalar field with no batch and no time marching (e.g. density field)
                arr = np.array(data) #No time marching for now
            else:
                arr = np.array(data)[0, b] #Zero is because we consider only the first time step for now

            if arr.ndim == 3:
                da = ET.SubElement(celldata, "DataArray",
                                   type="Float32", Name=name,
                                   NumberOfComponents="1", format="ascii")
                
                da.text = ' '.join(map(str, arr.flatten(order="F")))

            elif arr.ndim == 4:
                
                da = ET.SubElement(celldata, "DataArray",
                                   type="Float32", Name=name,
                                   NumberOfComponents=str(dim), format="ascii")

                lines = [' '.join(map(str, row)) for row in arr.reshape((-1, dim), order="F")]
                da.text = '\n'.join(lines)

            elif arr.ndim == 5:
                da = ET.SubElement(celldata, "DataArray",
                                   type="Float32", Name=name,
                                   NumberOfComponents=str(dim*dim), format="ascii")
                
                lines = [' '.join(map(str, row.flatten())) for row in arr.reshape((-1, dim*dim), order="F")]
                da.text = '\n'.join(lines)

            else:
                raise ValueError(f"Unsupported shape for {name}: {arr.shape}")

    # Write file
    ET.ElementTree(vtkfile).write(filename + ".vtr", encoding="utf-8", xml_declaration=True)
   




def plot_paths(paths,L,x,flip=False):

 #fig = plt.figure()
 for p in paths:
    a = np.array(p)
    if flip: a = np.flip(a)
    plt.plot(a[:,0],a[:,1],'g',lw=3)

 plt.gca().set_aspect('equal')
 plt.imshow(x)
 #plt.plot([-L/2,-L/2,L/2,L/2,-L/2],[-L/2,L/2,L/2,-L/2,-L/2],ls='--')
 plt.axis('off')
 plt.show()

def find_irreducible_shapes(cs,L) :

    #find all close circles
    output = []
    for c in cs:
        if np.linalg.norm(c[0]-c[-1]) == 0:
           output.append(c)

    pp = np.array([[-L,0],[-L,L],[0,L],[L,L],[L,0],[L,-L],[0,-L],[-L,-L],\
                   [-2*L,0],[-2*L,L],[-2*L,2*L],[-L,2*L],[0,2*L],[L,2*L],[2*L,2*L],[2*L,L],[2*L,0],[2*L,-L],[2*L,-2*L],[L,-2*L],[0,-2*L],[-L,-2*L],[-2*L,-2*L],[-2*L,-L]])

    n = len(output)
    ##find irredicuble shape

    new = []
    for i in range(n):
        repeated = False
        for c2 in new:
            for p in pp:
              f = output[i] + p[np.newaxis,:]
              d = np.linalg.norm(np.mean(f,axis=0) - np.mean(c2,axis=0))
              if d < 1e-1:
                  repeated = True
                  pass

        if not repeated:
             new.append(output[i])

    #center to the first shape---
    c = np.mean(new[0],axis=0)

    cs = [i - c[np.newaxis,:]  for i in new]

    return cs

def periodic_numpy2gds(x,L,D,filename,plot_contour=False):

  x = np.where(x<0.5,1e-12,1)
  grid = int(np.sqrt(x.shape[0]))
  x = x.reshape((grid,grid))

  x = 1-np.array(x)
  N = x.shape[0]
  resolution = x.shape[0]/L #pixel/um
  x = np.pad(x,N,mode='wrap')

  #Find contour
  x = gaussian_filter(x, sigma=1)
  #for the paper it was 0.8
  contours = measure.find_contours(x,0.5)
  if plot_contour:
   plot_paths(contours)

  new_contours = []
  for contour in contours:
        new_contours.append(np.array(contour)/resolution)

  contours = find_irreducible_shapes(new_contours,L)


  unit_cell = gdspy.Cell("Unit", exclude_from_current=True)
  unit_cell.add(gdspy.PolygonSet(contours))

  #Repeat
  num = int(D/L/2)
  circle_cell = gdspy.Cell("Circular", exclude_from_current=True)

  # Iterate over each potential position for a unit cell
  contours_tot = []
  n_rep = 0
  for i in range(-num,num):
    for j in range(-num,num):
        # Calculate the center of the current unit cell
        center_x = (i+0.5)  * L
        center_y = (j+0.5)  * L

        # Check if the center is within the circle
        if np.sqrt(center_x ** 2 + center_y ** 2) <= D/2:
            # If it is, create a new instance of the unit cell at this position
            circle_cell.add(gdspy.CellReference(unit_cell, (center_x, center_y)))
            n_rep +=1

            for c in contours:
                    contours_tot.append(np.array(c) + np.array([[center_x,center_y]]))


  # IO.save('paths_to_FIB',{'paths':contours_tot,'L':L})
  #if write_path:
  #     with open('path.json','wb') as f:
  #      pickle.dump(contours_tot,f)

  lib = gdspy.GdsLibrary()
  lib.add(circle_cell)
  lib.write_gds(filename + '.gds')

   





    



