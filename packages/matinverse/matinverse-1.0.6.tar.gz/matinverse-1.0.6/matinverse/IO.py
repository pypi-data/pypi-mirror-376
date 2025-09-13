import numpy as np
import xml.etree.ElementTree as ET


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
   






    



