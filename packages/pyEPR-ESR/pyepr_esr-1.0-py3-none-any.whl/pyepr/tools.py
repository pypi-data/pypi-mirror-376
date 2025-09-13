import os
import deerlab as dl
import numpy as np
import logging
from pyepr.dataset import create_dataset_from_bruker
from pyepr.hardware.ETH_awg_load import uwb_load, uwb_eval_match
from scipy.io import loadmat
from scipy.io.matlab import MatReadError
import xarray as xr

log = logging.getLogger('autoDEER.Tools')


def eprload(
        path: str, experiment: str = None, type: str = None,
        **kwargs):
    """ A general versions of eprload

    Parameters
    ----------
    path : str
        The file path of the data that should be loaded.
    experiment : str, optional
        _description_, by default None
    type : str, optional
        _description_, by default None

    Returns
    -------
    xarray.Dataarray
        _description_

    Raises
    ------
    ValueError
        _description_
    RuntimeError
        _description_
    """

    if type is None:  # Use the file ending to guess file type
        _, file_extension = os.path.splitext(path)

        if (file_extension == ".DSC") | (file_extension == ".DTA"):
            log.debug('File detected as Bruker')
            type = 'BRUKER'

        elif (file_extension == ".h5") | (file_extension == ".hdf5"):
            log.debug('File detected as HDF5')
            type = 'HDF5'

        elif (file_extension == ".csv") | (file_extension == ".txt"):
            log.debug('File detected as csv or txt file')
            type = 'TXT'

        elif file_extension == '.mat':
            log.debug('File detecetd as Matlab')
            type = 'MAT'
        
        else:
            log.error("Can't detect file type")
            raise ValueError(
                "Can't detect file type. Please choose the correct file or"
                " set type manually \n Valid file types: '.DSC','.DTA','.h5',"
                "'.hdf5','.csv','.txt','.mat'")
    
    if type == 'BRUKER':
        return create_dataset_from_bruker(path)

    elif type == 'TXT':
        if 'full_output' in kwargs:
            full_output = kwargs['full_output']
            del kwargs['full_output']
            if full_output:
                print("WARNING: Can't get metadata from text file")
        data = np.loadtxt(path, *kwargs)
        return data

    elif type == 'MAT':
        try:
            Matfile = loadmat(path, simplify_cells=True, squeeze_me=True)
        except Exception as e:
            raise MatReadError("Error opening MatFile")


        # Params = Matfile[Matfile["expname"]]
        if "options" in kwargs:
            opts=kwargs["options"]
        else:
            opts={}
        # if 'ref_echo_2D_idx' not in opts:
        #     opts['ref_echo_2D_idx'] = 'end'
        # uwb_output = uwb_load(Matfile,opts)
        uwb_output = uwb_eval_match(Matfile,**kwargs)
        # axes = uwb_output.dta_x
        # data = uwb_output.dta_ev

        return uwb_output
    
    elif type == 'HDF5':
        return xr.load_dataarray(path,engine='h5netcdf',invalid_netcdf=True)


def progress_bar(progress, post=""):

    num_hash = round(progress // 0.05)
    num_space = 20-num_hash

    print(
        "Progress: "+"|"+"#"*num_hash + " " * num_space + "|" + post,
        end='\r')


def progress_bar_frac(num, den):
    
    progress_bar(num/den, f"{num:d} out of {den:d}")
