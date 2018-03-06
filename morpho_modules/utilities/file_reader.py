#======================================================
# file_reader.py
#
# Author: J. Johnston
# Date: Mar. 1, 2018
#
# Read data from different file types
#=======================================================

import logging
logger = logging.getLogger(__name__)

import numpy as np
import pystan

try:
    import ROOT
except ImportError as e:
    logger.info("ROOT could not be imported, error: %s"%e)
    logger.info("Continuing without ROOT")

def read_txt_array(file_path, idx=None):
    """Read an array from a text file created with np.savetxt

    Only works for 1D or 2D array (Such as those saved by np.savetxt)

    Args:
        file_path: Path to the text file
        idx: String specifying elements to return. None returns the
            entire array. "1,2" will return the element at index (1,2).
            "1" or "1,:" will return the second row, and ":,1" will
            return the second column.

    Returns:
        np.array: Array with the selected column

    Throws:
        IOError: If the given file does not exist
    """
    result = np.loadtxt(file_path)

    if idx is None:
        return result
    else:
        indices = idx.split(',')
        if len(indices)==1:
            if indices[0]==":":
                return result
            else:
                return result[int(indices[0])]
        elif len(indices)==2:
            if indices[0]==":":
                if indices[1]==":":
                    return result
                else:
                    return result[:,int(indices[1])]
            else:
                if indices[1]==":":
                    return result[int(indices[0]),:]
                else:
                    return result[int(indices[0]),
                                  int(indices[1])]
        else:
            logger.error("Invalid index %s, returning full array"%idx)
            return result

def read_root_branch(file_path, tree_name, branch_name):
    """Get a branch from a root file

    Args:
        file_path: Path to the root file
        tree_name: Name of the tree to access
        branch_name: Name of branch to return

    Returns:
        list: Containing all elements of the branch

    Throws:
        IOError: If the given file does not exist
    """
    myfile = ROOT.TFile(file_path,"READ")
    tree = myfile.Get(tree_name)
    result = []
    for elt in tree:
        result.append(getattr(elt,branch_name))
    myfile.Close()
    return result

def read_R_variable(file_path, var_name):
    """Read an array from an R file

    Args:
        file_path: Path to the R file
        var_name: Name of the variable to return

    Returns:
        Variable from R file

    Throws:
        IOError: If the given file does not exist
        KeyError: If the given variable is not in the R file
    """
    r_dict = pystan.misc.read_rdump(file_path)
    return r_dict[var_name]

def evaluate_python_fcn(xvals, module_name, fcn_name):
    return []

def get_variable_from_file(path, file_format, variable=None):
    """Get a variable from file

    Args:
        path: Path to the file
        file_format: Format of the file. Options are "text",
            "root", "R", or "python"
        variable: Variable to access. The form depends on the file
            format:
          - "text": The file will be loaded with np.loadtxt. Pass a
            string specifying elements to return. None returns the
            entire array. "1,2" will return the element at index (1,2).
            "1" or "1,:" will return the second row, and ":,1" will
            return the second column.
          - "root": variable is a length 2 list of str specifying the
            tree name and branch name.
          - "R": variable is a string specifying the variable name
          - "python": variable is a length 2 list specifying the
            the path to the module and the function name

    Returns:
        Depends on the file format:
          - "text", "root": np.array containing the specified array
          - "R": Returns the specified variable (can be any type)
          - "python": python function

    Throws:
        IOError: If the given file does not exist
    """
    if file_format=="text":
        res_variable = read_txt_array(path, variable)
    elif file_format=="root":
        res_variable = read_root_branch(path, variable[0], variable[1])
    elif file_format=="R":
        res_variable = read_R_variable(path, variable)
    elif file_format=="python":
        print("reading python not yet implemented")
    else:
        logger.warn("Invalid file_format. Returning None")
        res_variable = None
    return res_variable
    

def get_histo_shape_from_file(binning, path, file_format, variables):
    """Get a histogram shape from file

    Args:
        binning: List giving the bin edges for the histogram
        path: String giving path to the data.
        file_format: Format used to save the data. Currently supported
            options are "text values", "text counts", "text function",
            "root values", "root counts", "root function", "R values",
            "R counts", "R function", "python function".
            "text", "root", "R", or "python" specifies the filetype.
            "values" specifies that there will be a 1D list of values to
            be histogrammed. "counts" specifies that the number of counts
            in each bin will be specified (assuming bins from binning_file
            or n_bins). "function" specifies that there will be two columns
            of points defining the spectrum, which will then be integrated
            in each bin.
        variables: Dictionary containing the variables used to access
            the data. The formatting depends on the file format:
          - "text": variables should containg a key "columns",
            containing a list of columns containing the data. There
            should be one column for "values" or "counts",and two
            columns for "function".
          - "root": variables should contain a key "tree" with
            the name of the tree, and a key "branches" with a list of
            branches (one for "values" or "counts", two for "function")
          - "R": variables should contain a key "variable_names" with
            a list of variable names (one for "values" or "counts", two
            for "function".
          - "python": variables should contain a key "module" and a key
            "method_name" specifying the path to the module to load, and
            the name of the method defining the function.
    Returns:
        A 3-tupe containing (np.array, float64, float64).
        np.array specifies the number of counts in each bin described by
        binning. If the format was a function, then the value for each bin
        is the number of counts per unit x. The first float64 gives the
        mean of the histogram, and the second gives the standard deviation.

    Throws:
        IOError: If the given file does not exist
    """
    if "text" in file_format:
        print("text not yet implemented")
        return None
    elif "root" in file_format:
        if "counts" in file_format or "values" in file_format:
            res_arr = get_variable_from_file(path, "root",
                                             [variables["tree"], variables["branches"][0]])
        elif "function" in file_format:
            x_arr = get_variable_from_file(path, "root",
                                           [variables["tree"], variables["branches"][0]])
            y_arr = get_variable_from_file(path, "root",
                                           [variables["tree"], variables["branches"][1]])
    elif "R" in file_format:
        if "counts" in file_format or "values" in file_format:
            res_arr = get_variable_from_file(path, "R", variables["variable_names"][0])
        elif "function" in file_format:
            x_arr = get_variable_from_file(path, "R", variables["variable_names"][0])
            y_arr = get_variable_from_file(path, "R", variables["variable_names"][1])
    elif "python" in file_format:
        print("python not yet implemented")
        return None
    else:
        logger.warn("Invalid file_format given (%s), returning None")
        return None

    total = 0.
    nelts = 0
    sigma = 0.0

    # For values, histogram the given array
    if "values" in file_format:
        average = np.mean(res_arr)
        sigma = np.std(res_arr)
        res_arr = np.histogram(res_arr, binning)

    # For a spectrum, integrate over each bin
    if "function" in file_format:
        pass

    if "counts" in file_format or "function" in file_format:
        bin_centers = []
        for i in range(len(binning)-1):
            bin_centers.append(binning[i] +
                              (binning[i+1]-binning[i])/2.0)
        for i in range(len(res_arr)):
            total += res_arr[i]*bin_centers[i]
            nelts += res_arr[i]
        average = total/float(nelts)
        if nelts>1:
            for i in range(len(res_arr)):
                sigma += (bin_centers[i]-average)**2*res_arr[i]
            sigma = np.sqrt(sigma/(nelts-1))
        else:
            sigma = float('inf')

    return (np.array(res_arr), average, sigma)