import numpy as np
from sys import argv,exit
from pptx import Presentation

if __name__ == '__main__':

    # Read in the file provided by the user
    prs = Presentation(argv[1])

    # Get the slides in memory
    slides_list = []
    for slide in prs.slides:
        slides_list.append(slide)

    # Leads are supposed to always be the last four pages
    for slide_cnt,slide in enumerate(slides_list[-4:]):
        
        # Read in the table data
        output = []
        for shape in slide.shapes:
            values = []
            if hasattr(shape, "table"):
                cells = shape.table.iter_cells()
                for icell in cells:
                    values.append(icell.text)

            # Clean up the ocassional character array (versus strings)
            flag = True
            for idx,ivalue in enumerate(values):
                if ivalue == '':
                    if flag:
                        output.append(ivalue)
                        flag = False
                else:
                    output.append(ivalue)
                    flag = True

        # Clean up and setup logic to split
        output = np.array(output)
        ncol   = 16+1   # +1 because of the annoying whitespace object for headers
        nrow   = 2
        if slide_cnt in [0,2]:
            badind = [0,ncol,2*ncol,4*ncol-1,6*ncol-2,7*ncol-2]
            mask   = np.ones(output.size).astype('bool')
            mask[badind] = False
            output = output[mask]

        # Make a formatted output
        ncol   = 16
        output = output.reshape((-1,ncol))
        keys   = output[::2]
        values = output[1::2]

        chmap = dict(zip(keys.ravel(),values.ravel()))
        keys  = list(chmap.keys())
        for ikey in keys:
            print(f"{ikey} | {chmap[ikey]}")
        exit()