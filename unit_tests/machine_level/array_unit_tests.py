import numpy as np
import pandas as PD
from tabulate import tabulate

class TestArrayProperties:
    def __init__(self,in_Arr,verbose=True):
        self.in_Arr  = in_Arr
        self.verbose = verbose
    
    def test_dim(self,M,N):
        """
        Confirm shape of array is correct.
        
        Parameters
        ----------
        M : Integer
            Expected number of rows. -1 indicates that we should skip this check.
        N : Integer
            Exepected number of columns.

        Returns
        -------
        Assertion.

        """
        if M==-1:M=self.in_Arr.shape[0]
        try:
            assert(self.in_Arr.shape==(M,N))
            if self.verbose: print("Array Shape Correct.")
            return True
        except AssertionError:
            print("Input Array is of shape (%d,%d). Expected shape is (%d,%d)." %(self.in_Arr.shape[0],self.in_Arr.shape[1],M,N))
            return False
            
    def test_type(self,dtype):
        """
        Confirm the type of the array is correct.
        
        Parameters
        ----------
        dtype : TYPE
            Expected data type.

        Returns
        -------
        Assertion.

        """
        
        if isinstance(self.in_Arr,np.ndarray):
            try:
                assert(self.in_Arr.dtype==dtype)
                if self.verbose: print("Array Type Correct.")
                return True
            except AssertionError:
                print("Input Array is of type %s. Expected type is %s." %(self.in_Arr.dtype,dtype))
                return False
        elif isinstance(self.in_Arr,PD.DataFrame):
            try:
                assert((self.in_Arr.dtypes.values==dtype).all())
                if self.verbose: print("Dataframe Type Correct.")
                return True
            except AssertionError:
                print("Dataframe has a mismatched type to expected input.")
                return False
            
    def test_inf(self):
        """
        Check for inf.

        Returns
        -------
        None.

        """

        if isinstance(self.in_Arr,np.ndarray):        
            try:
                assert(np.isinf(self.in_Arr).any()==False)
                if self.verbose: print("No INFs found.")
                return True
            except AssertionError:
                print("Infinity found within input array.")
                return False
        elif isinstance(self.in_Arr,PD.DataFrame):
            try:
                assert(np.isinf(self.in_Arr.values).any()==False)
                if self.verbose: print("No INFs found.")
                return True
            except AssertionError:
                print("Infinity found within input array.")
                return False


    def test_nan(self):
        """
        Check for nan.

        Returns
        -------
        None.

        """
        
        if isinstance(self.in_Arr,np.ndarray):        
            try:
                assert(np.isnan(self.in_Arr).any()==False)
                if self.verbose: print("No NaNs found.")
                return True
            except AssertionError:
                print("NaNs found within input array.")
                return False
        elif isinstance(self.in_Arr,PD.DataFrame):
            try:
                assert(np.isnan(self.in_Arr.values).any()==False)
                if self.verbose: print("No NaNs found.")
                return True
            except AssertionError:
                print("NaNs found within input array.")
                return False
            

class TestArraySimilarity:
    def __init__(self,in_Arr,ref_Arr):
        self.in_Arr  = in_Arr
        self.ref_Arr = ref_Arr
        
    def deviations(self):
        """
        Calculate deviations between input and reference array structure.
        
        NOTE: Due to differences in libraries and seeds, exact matches may not be expected.
        This is to provide the user with a quick approximation that their results are within
        some bound of confidence.

        Returns
        -------
        On-screen display of statistics.

        """
        
        if isinstance(self.in_Arr,np.ndarray):
            print("Array comparison")
            DF  = PD.DataFrame(index=['Minimum Expected','Maximum Expected','Median Expected', 'Median Absolute Deviation'],columns=np.arange(self.ref_Arr.shape[1]))
            DF.loc['Minimum Expected'] = [np.min(self.ref_Arr[:,idx]) for idx in range(self.ref_Arr.shape[1])]
            DF.loc['Maximum Expected'] = [np.max(self.ref_Arr[:,idx]) for idx in range(self.ref_Arr.shape[1])]
            DF.loc['Median Expected']  = [np.median(self.ref_Arr[:,idx]) for idx in range(self.ref_Arr.shape[1])]
            DF.loc['Median Absolute Deviation'] = [np.median(np.fabs(self.ref_Arr[:,idx]-self.in_Arr[:,idx])) for idx in range(self.ref_Arr.shape[1])]            
            
            print(tabulate(DF,headers='keys',tablefmt='psql'))
            
        if isinstance(self.in_Arr,PD.DataFrame):
            print("Dataframe comparison")
            numeric_columns     = self.ref_Arr.select_dtypes(include=np.number).columns.tolist()
            categorical_columns = np.setdiff1d(self.ref_Arr.columns,numeric_columns)
            
            DF  = PD.DataFrame(index=['Minimum Expected','Maximum Expected','Median Expected', 'Median Absolute Deviation'],columns=numeric_columns)
            DF.loc['Minimum Expected'] = [np.min(self.ref_Arr.values[:,idx]) for idx in numeric_columns]
            DF.loc['Maximum Expected'] = [np.max(self.ref_Arr.values[:,idx]) for idx in numeric_columns]
            DF.loc['Median Expected']  = [np.median(self.ref_Arr.values[:,idx]) for idx in numeric_columns]
            DF.loc['Median Absolute Deviation'] = [np.median(np.fabs((self.ref_Arr.values[:,idx]-self.in_Arr.values[:,idx]))) for idx in numeric_columns]
            
            print("Numerical Columns:")
            print(tabulate(DF,headers='keys',tablefmt='psql'))
            
            DF  = PD.DataFrame(index=['Percent Match'],columns=categorical_columns)
            DF.loc['Percent Match'] = [100*(self.ref_Arr.values[:,idx]==self.in_Arr.values[:,idx]).sum()/self.ref_Arr.values[:,idx].size for idx in categorical_columns]
            
            print("Categorical Columns:")
            print(tabulate(DF,headers='keys',tablefmt='psql'))
            
            
class TestTransformation:
    def __init__(self,in_Arr):
        self.in_Arr = in_Arr
        
    def array_bounding(self,arr_min,arr_max):
        """
        Assert if the array exists within expected bounds.

        Parameters
        ----------
        arr_min : numeric type
            Minimum expected value.
        arr_max : numeric type
            Maximum expected value.

        Returns
        -------
        Assertion.

        """
        
        imin = np.amin(self.in_Arr)
        imax = np.amax(self.in_Arr)
        
        try:
            assert(imin>=arr_min)
        except AssertionError:
            print("Input array minimum of %3.2e greater than expected minimum %3.2e" %(imin,arr_min))
        
        try:
            assert(imin<=arr_max)
        except AssertionError:
            print("Input array maximum of %3.2e greater than expected maximum %3.2e" %(imax,arr_max))
        
            
if __name__ == '__main__':

    np.random.seed(42)    

    # Create dummy arrays and dataframe for unit test development
    M         = 40
    N         = 20
    arr1      = 100*np.random.random(size=(M,N))
    arr2      = np.random.normal(arr1)
    arr3      = np.copy(arr2)
    arr4      = np.copy(arr2)
    arr3[0,0] = np.nan
    arr4[0,0] = np.inf
    DF1       = PD.DataFrame(arr1,columns=np.arange(N))
    DF2       = PD.DataFrame(arr2,columns=np.arange(N))
    DF3       = PD.DataFrame(arr3,columns=np.arange(N))
    DF4       = PD.DataFrame(arr4,columns=np.arange(N))
    
    # Change typing as needed
    DF3           = DF2.copy().apply(np.floor)
    DF3.iloc[:,0] = PD.to_numeric(DF3.values[:,0],downcast='integer')
    
    # Some reference variables for tests
    min1   = np.amin(arr1)
    min2   = np.amin(arr2)
    max1   = np.amax(arr1)
    max2   = np.amax(arr2)
    dtype  = arr1.dtype 
    dtypes = DF1.dtypes
    
    ### Run each unit test. When applicable, pair-wise, with success then failure.
    
    # Dimension test
    TAP = TestArrayProperties(arr1)
    TAP.test_dim(M, N) # Success
    TAP.test_dim(M+1,N+1) # Failure
    print("===")
    
    # Type test
    TAP.test_type(dtype)
    TAP.test_type('str')
    print("===")
    TAP = TestArrayProperties(DF1)
    TAP.test_type(dtypes)
    TAP = TestArrayProperties(DF3)
    TAP.test_type(dtypes)
    print("===")    
            
    # Undefined type tests
    TAP = TestArrayProperties(arr1)
    TAP.test_nan()
    TAP = TestArrayProperties(arr3)
    TAP.test_nan()    
    print("===")
    TAP = TestArrayProperties(arr1)
    TAP.test_inf()
    TAP = TestArrayProperties(arr4)
    TAP.test_inf()

    # Dataframe comparison
    TAS = TestArraySimilarity(arr1, arr2)
    TAS.deviations()
    TAS = TestArraySimilarity(DF1, DF2)
    TAS.deviations()
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
