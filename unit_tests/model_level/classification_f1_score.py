import numpy as np
import pandas as PD
from sys import exit
from sklearn.metrics import f1_score

def main(truth,prediction,order='columnar'):
    """
    Calculate the f1-score for two matrices. 
    Used for unit testing, but symbolically linked to in the scripts folder.

    Parameters
    ----------
    truth : array-type or dataframe object
        A 1 or 2 dimensional dataset containing the expected output.
    prediction : array-type or dataframe object
        A 1 or 2 dimensional dataset containing the predicted output.

    Returns
    -------
    If ndim == 1:
        Return array of f1-scores for each classification label.
    If ndim == 2:
        Return dictionary of f1-scores for each classification label following input order and with each key correposnding
        to a data slice.

    """
    
    # Check that the objects have the same shape
    try:
        assert(truth.ndim == prediction.ndim)
    except AssertionError:
        print("Dimensions for truth and prediction do not match.")
        exit()
        
    # Conditional logic based on array structure
    if truth.ndim == 1:
        return f1_score(truth,prediction,average=None)
    elif truth.ndim == 2:

        # Make sure the order is recognized and then alert user of type used.
        order = order.lower()
        if order not in ['columnar','row']:
            print("Array order type %s not recognized. Please use 'columnar' or 'row'.")
            exit()
        print("Assuming input vectors are in %s format." %(order))
        scores = {}
        
        # Loop over columns if columnar and row if row order
        if order == 'columnar':
            for icol in range(truth.shape[1]):
                if isinstance(truth,np.ndarray):
                    itruth = truth[:,icol]
                    ipred  = prediction[:,icol]
                elif isinstance(truth,PD.DataFrame):
                    itruth = truth[:,icol]
                    ipred  = prediction[:,icol]
                scores['column_%04d' %(icol)] = f1_score(itruth,ipred,average=None)
        elif order == 'row':
            for icol in range(truth.shape[0]):
                if isinstance(truth,np.ndarray):
                    itruth = truth[icol]
                    ipred  = prediction[icol]
                elif isinstance(truth,PD.DataFrame):
                    itruth = truth[icol]
                    ipred  = prediction[icol]
                scores['row_%04d' %(icol)] = f1_score(itruth,ipred,average=None)
    else:
        print("Input number of dimensions of %02d is not supported. Please pass only 1 or 2 dimensional structures.")
        exit()
    return scores

if __name__ == '__main__':
    main(truth,prediction)