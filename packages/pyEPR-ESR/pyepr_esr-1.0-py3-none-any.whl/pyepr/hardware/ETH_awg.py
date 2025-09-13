import matlab.engine
from pyepr.classes import  Interface, Parameter
from pyepr.pulses import Pulse, RectPulse, ChirpPulse, HSPulse, Delay, Detection
from pyepr.sequences import Sequence, HahnEchoSequence, FieldSweepSequence
import numpy as np
import re
import time
from deerlab import correctphase
import scipy.signal as sig
from scipy.io import loadmat
from scipy.io.matlab import MatReadError
from pyepr.utils import transpose_list_of_dicts
from pyepr.hardware.ETH_awg_load import uwb_eval_match
from pyepr.utils import save_file, transpose_list_of_dicts, transpose_dict_of_list
from pyepr import create_dataset_from_sequence
import datetime
import copy
import threading
import warnings
import logging
import collections


log = logging.getLogger("interface")


class ETH_awg_interface(Interface):
    """
    Represents the interface for connecting to Andrin Doll style spectrometers.
    """
    def __init__(self,config_file:dict, awg_freq=1.5, dig_rate=2) -> None:
        """An interface for connecting to a Andrin Doll style spectrometer,
        commonly in use at ETH Zürich.

        System Requirements
        -------------------
        - Matlab 2022b or later
        - Matlab engine for python
        - Python (3.10+ recommended)

        Parameters
        -----------
        awg_freq : float
            The normal operating AWG frequency. 
            Sequence.freq = AWG.LO + AWG.awg_freq 

        dig_rate : float
            The speed of the digitser in GSa/s
        """
        super().__init__(config_file)

        self.spec_config = self.config["Spectrometer"]
        self.bridge_config = self.spec_config["Bridge"]
        
        
        self.IF_freq = self.bridge_config['IF Freq']
        self.dig_rate = self.bridge_config['Det Freq']
        self.pulses = {}
        self.cur_exp = None
        self.bg_data = None
        self.bg_thread = None
        self.IFgain_options = np.array(self.bridge_config['IFgain'])
        self.IFgain = 2

        self.filter = {}
        self.filter['filter_type'] = 'cheby2'
        self.filter['filter_width'] = 0.01 # GHz

        print(self.amp_nonlinearity)
        
        pass

    @property
    def savefolder(self):
        return self._savefolder
    
    @savefolder.setter
    def savefolder(self, folder):
        self._savefolder = folder
        if hasattr(self, 'engine'):
            self.engine.cd(folder)


    def connect(self, session=None):
        """Connect to a running matlab session. If more than one session has 
        been started this will choose the first one. It is recomended that only
        one session is open at one time, or that the engine is started with a
        known name.

        Parameters
        ----------
        session : str, optional
            The string denoting a specific session to connect to
            , by default None
        """

        if session is None:
            matlab_sessions = matlab.engine.find_matlab()

            if len(matlab_sessions) > 1:
                print("More than one session, picking the first.")
                session = matlab_sessions[0]
            elif len(matlab_sessions) == 0:
                raise RuntimeError(
                    "A matlab python session must be started. \n"+
                    "Please type into matlab session: "
                    "matlab.engine.shareEngine"
                    )
        
        self.engine = matlab.engine.connect_matlab(session)
        self.workspace = self.engine.workspace
        self.engine.cd(self._savefolder)

    def acquire_dataset(self, verbosity=0,**kwargs):
        if self.bg_data is None:

            current_acq, current_scan, _, _ = self.engine.dig_interface('progress', nargout=4)
            if current_scan == 0:
                while current_acq == 0:
                    time.sleep(2)
                    current_acq, current_scan, _, _ = self.engine.dig_interface('progress', nargout=4)
                data = self.get_buffer(verbosity=verbosity)
            else:
                data = self.read_dataset(verbosity=verbosity,**kwargs)
            # data = self.acquire_dataset_from_matlab(verbosity=verbosity)
        else:
            data = self.bg_data

        return super().acquire_dataset(data)
    
    def acquire_dataset_from_matlab(self, verbosity=0,**kwargs):
        """ Acquire and return the current or most recent dataset.

        Returns
        -------
        dict
            The dataset
        """
        cur_exp = self.workspace['currexp']
        folder_path = cur_exp['savepath']
        # filename = cur_exp['savename']
        # files = os.listdir(folder_path)

        curexpname = self.workspace['currexpname']
        # def extract_date_time(str):
        #     output = re.findall(r"(\d{8})_(\d{4})", str)
        #     if output != []:
        #         date = int(output[0][0])
        #         start_time = int(output[0][1])
        #         return date*10000 + start_time
        #     else:
        #         return 0
        
        # newest = max([extract_date_time(file) for file in files])
        # date = newest // 10000
        # start_time = newest - date * 10000
        # path = folder_path + "\\" \
        #     + f"{date:08d}_{start_time:04d}_{filename}.mat"

        # Remove filter from kwargs if present
        kwargs.pop('filter_type',None)
        kwargs.pop('filter_width',None) # GHz
        
        path = folder_path + "\\" + curexpname + ".mat"
        
        for i in range(0, 50):
            try:
                e = 'None'
                # self.engine.dig_interface('savenow')
                try:
                    Matfile = loadmat(path, simplify_cells=True, squeeze_me=True)
                except:
                    raise MatReadError()
                # data = uwb_load(Matfile, options=options, verbosity=verbosity,sequence=self.cur_exp)
                if 'cur_exp' in kwargs:
                    exp = kwargs['cur_exp']
                else:
                    exp = self.cur_exp
                if isinstance(exp, FieldSweepSequence):
                    data = uwb_eval_match(Matfile, exp, verbosity=verbosity, filter_type='cheby2', filter_width=0.01,**kwargs)
                else:
                    data = uwb_eval_match(Matfile, exp, verbosity=verbosity, **self.filter,**kwargs)

                if np.all(data.data == 0+0j) and not (hasattr(self,'stop_flag') and self.stop_flag.is_set()):
                    time.sleep(10)
                    print("Data is all zeros")
                    continue
            except OSError as e:
                time.sleep(10)
            except IndexError as e:
                time.sleep(10)
            except ValueError as e:
                time.sleep(10)
            except MatReadError as e:
                time.sleep(10)
            else:
                return data
        raise RuntimeError("Data was unable to be retrieved")
    
    def _wait_for_scan(self, target_scan=None):
        if target_scan is None:
            target_scan = self.cur_exp.averages.value
        _, current_scan, _, _ = self.engine.dig_interface('progress', nargout=4)
        scan_time = self.cur_exp._estimate_time() / self.cur_exp.averages.value
        while True:
            _, scan, _, _ = self.engine.dig_interface('progress', nargout=4)
            if scan >= target_scan:
                break
            elif scan > current_scan:
                break
            time.sleep(np.min([scan_time/10, 2]))

    def get_buffer(self, verbosity=0,**kwargs):
        _, current_scan, _, _ = self.engine.dig_interface('progress', nargout=4)

        dta = np.array(self.engine.dig_interface('get'))
        conf = dict(self.engine.workspace['conf'])
        awg = dict(self.engine.workspace['awg'])
        exp = dict(self.engine.workspace['exp'])
        ext = dict(self.engine.workspace['ext'])
        expname = 'exp'
        nAvgs = current_scan

        Matfile = {
            'dta': dta,
            'conf': conf,
            'awg': awg,
            'exp': exp,
            'ext': ext,
            'nAvgs': nAvgs,
            'expname': expname
        }

        if 'cur_exp' in kwargs:
            exp = kwargs['cur_exp']
        else:
            exp = self.cur_exp

        # Remove filter from kwargs if present
        kwargs.pop('filter_type',None)
        kwargs.pop('filter_width',None) # GHz

        if isinstance(self.cur_exp, FieldSweepSequence):
            data = uwb_eval_match(Matfile, exp, verbosity=verbosity, filter_type='cheby2', filter_width=0.01,**kwargs)
        else:
            data = uwb_eval_match(Matfile, exp, verbosity=verbosity, **self.filter,**kwargs)

        if np.all(data.data == 0+0j) and not (hasattr(self, 'stop_flag') and self.stop_flag.is_set()):
            time.sleep(10)
            print("Data is all zeros")

        return data


    def read_dataset(self, verbosity=0,savenow=False, **kwargs):
        cur_exp = self.workspace['currexp']
        folder_path = cur_exp['savepath']
        curexpname = self.workspace['currexpname']

        path = folder_path + "\\" + curexpname + ".mat"

         # Remove filter from kwargs if present
        kwargs.pop('filter_type',None)
        kwargs.pop('filter_width',None) # GHz


        for i in range(0, 50):
            try:
                e = 'None'
                if savenow:
                    self.engine.dig_interface('savenow')
                try:
                    Matfile = loadmat(path, simplify_cells=True, squeeze_me=True)
                except:
                    raise MatReadError()
                if 'cur_exp' in kwargs:
                    exp = kwargs['cur_exp']
                else:
                    exp = self.cur_exp
                if isinstance(exp, FieldSweepSequence):
                    data = uwb_eval_match(Matfile, exp,verbosity=verbosity,filter_type='cheby2',filter_width=0.01,**kwargs)
                else:
                    data = uwb_eval_match(Matfile, exp,verbosity=verbosity, **self.filter,**kwargs)

                if np.all(data.data == 0+0j) and not (hasattr(self, 'stop_flag') and self.stop_flag.is_set()):
                    time.sleep(10)
                    print("Data is all zeros")
                    continue
            except OSError as e:
                time.sleep(10)
            except IndexError as e:
                time.sleep(10)
            except ValueError as e:
                time.sleep(10)
            except MatReadError as e:
                time.sleep(10)
            else:
                return data
        raise RuntimeError("Data was unable to be retrieved")
        

    def launch(self, sequence: Sequence , savename: str, IFgain=None, *args,**kwargs):
        
        if IFgain is None:
            test_IF = True
            while test_IF:
                self.terminate()
                print(self.IFgain)
                self.launch_withIFGain(sequence, savename, self.IFgain)
                scan_time = sequence._estimate_time() / sequence.averages.value
                check_1stScan = True
                while check_1stScan:
                    # self._wait_for_scan(1)
                    time.sleep(np.max([scan_time/10, 5]))
                    dataset = self.acquire_dataset()

                    dig_level = dataset.attrs['diglevel'] / (2**13 * sequence.shots.value * sequence.pcyc_dets.shape[0])
                    pos_levels = dig_level * self.IFgain_options / self.IFgain_options[self.IFgain]
                    pos_levels[pos_levels > 0.85] = 0
                    if dig_level == 0:
                        continue
                    if (pos_levels[self.IFgain] > 0.85) or  (pos_levels[self.IFgain] < 0.02):
                        best_IFgain = np.argmax(pos_levels)
                    else:
                        best_IFgain = self.IFgain

                    if np.all(pos_levels==0):
                        log.critical('Saturation detected with IF gain 0. Please check the power levels.')
                        raise RuntimeError('Saturation detected with IF gain 0. Please check the power levels.')
                    elif (best_IFgain < self.IFgain) and (dataset.nAvgs == 0):
                        new_IFgain = np.max([self.IFgain - 1,best_IFgain])
                        log.warning(f"IF gain changed from {self.IFgain} to {new_IFgain}")
                        self.IFgain = new_IFgain
                        check_1stScan = False
                    elif (best_IFgain != self.IFgain) and (dataset.nAvgs >= 1):
                        new_IFgain = np.min([self.IFgain +1,best_IFgain])
                        log.warning(f"IF gain changed from {self.IFgain} to {new_IFgain}")
                        self.IFgain = new_IFgain
                        check_1stScan = False
                    elif dataset.nAvgs >=1:
                        log.debug(f"IF gain {self.IFgain} is optimal")
                        check_1stScan = False
                        test_IF = False
        elif IFgain is not None:
            
            self.launch_withIFGain(sequence,savename,IFgain)


    def launch_withIFGain(self, sequence , savename: str, IFgain: int = 0):
        """Launch a sequence on the spectrometer.

        Parameters
        ----------
        sequence : Sequence
            The pulse sequence to launched.
        savename : str
            The save name for the file.
        IFgain : int
            The IF gain, either [0,1,2], default 0.
        """

        def detect_incompatible(seq):
            # Check if two pulse parameters are shifted by diffent axes
            duplicates = [item for item, count in collections.Counter(seq.progTable['EventID']).items() if count > 1]

            for duplicate in duplicates:
                indices = [i for i, x in enumerate(seq.progTable['EventID']) if x == duplicate]
                print(indices)
                axIDs = [seq.progTable['axID'][i] for i in indices]
                axIDs.sort()
                vars = [seq.progTable['Variable'][i] for i in indices]
                vars.sort()
                unique_vars = list(set(vars))
                unique_vars.sort()
                axIDs.sort()
                unique_axIDs = list(set(axIDs))
                unique_axIDs.sort()
                if len(axIDs) == 1:
                    return False
                elif vars == unique_vars:
                    return False
                elif axIDs == unique_axIDs:
                    return True
                else:
                    raise ValueError('Pulse time is not unique for the same eventID')
                
            return False

        if self.bg_thread is not None:
            if self.bg_thread.is_alive():
                log.warning('Background thread still running. Terminating it now.')
                self.stop_flag.set()
                self.bg_thread.join(timeout=120)
                if self.bg_thread.is_alive():
                        log.critical('Background thread still running. Unable to launch new sequence.')
                else:
                    log.debug('Background thread terminated.')


        self.bg_thread=None
        self.bg_data = None
        timestamp = datetime.datetime.now().strftime(r'%Y%m%d_%H%M_')
        self.savename = timestamp + savename + '.h5'
        if sequence.seqtable_steps > 2**18:
            log.warning('Sequence too long. Breaking the problem down...')
            self.launch_long(sequence,savename,IFgain)
        elif detect_incompatible(sequence):
            log.warning('Incompatible axes detected. Breaking the problem down...')
            self.launch_long(sequence,savename,IFgain)
        try:
            self.launch_normal(sequence,savename,IFgain)
        except matlab.engine.MatlabExecutionError:
            log.warning('Matlab error trying to launch sequence. Breaking the problem down...')
            self.launch_long(sequence,savename,IFgain)

    def launch_normal(self, sequence , savename: str, IFgain: int = 0,reset_cur_exp=True):
        struct = self._build_exp_struct(sequence)
        struct['savename'] = savename
        struct['IFgain'] = IFgain
        if reset_cur_exp:
            self.cur_exp = sequence
        self.workspace['exp'] = struct
        self.engine.eval('launch(exp)', nargout=0)


    def launch_long(self, sequence , savename: str, IFgain: int = 0, axID=-1):
        """Launch a sequence on the spectrometer that is too long for a single file.
        This is to get around the issues with the sequence table by running a background loop
        that takes control. 

        **current issues**:
        - uses some bruker tools functions
        - only works for a single averages
        - creates many extra files

        Parameters
        ----------
        sequence : Sequence
            The pulse sequence to launched.
        savename : str
            The save name for the file.
        IFgain : int
            The IF gain, either [0,1,2], default 0.
        """
        dim = []
        for p in sequence.evo_params:
            if (p.uuid not in sequence.reduce_uuid):
                for item in p.dim:
                    dim.append(item)
        self.cur_exp = sequence
        init_data = np.zeros(dim,dtype=np.complex128)
        self.bg_data = create_dataset_from_sequence(init_data,self.cur_exp,extra_params={'nAvgs':0,'diglevel':0})
        
        self.stop_flag = threading.Event()
        self.bg_thread = threading.Thread(target=bg_thread,args=[self,sequence,savename,IFgain,axID,self.stop_flag])
        self.bg_thread.start()
        log.debug('Background thread starting')

    def isrunning(self) -> bool:
        if self.bg_thread is None:
            # state = bool(self.engine.dig_interface('savenow'))
            _,_,_,state = self.engine.dig_interface('progress', nargout=4)

            if state == 0:
                state = False
            elif state == 1:
                state = True
            else:
                state = False

            return state
        else:
            state= self.bg_thread.is_alive()
        return state
    
    def tune_rectpulse(self,*,tp, freq, B, reptime, shots=400):
        """Generates a rectangular pi and pi/2 pulse of the given length at 
        the given field position. This value is stored in the pulse cache. 

        Parameters
        ----------
        tp : float
            Pulse length of pi/2 pulse in ns
        freq : float
            Central frequency of this pulse in GHz
        B : float
            Magnetic B0 field position in Gauss
        reptime: float
            Shot repetion time in us.
        shots: int
            The number of shots

        Returns
        -------
        p90: RectPulse
            A tuned rectangular pi/2 pulse of length tp
        p180: RectPulse
            A tuned rectangular pi pulse of length tp
        """

        amp_tune =HahnEchoSequence(
            B=B, freq=freq, reptime=reptime, averages=1, shots=shots
        )

        scale = Parameter("scale",0,dim=45,step=0.02)
        amp_tune.pulses[0].tp.value = tp
        amp_tune.pulses[0].scale = scale
        amp_tune.pulses[1].tp.value = tp * 2
        amp_tune.pulses[1].scale = scale

        amp_tune.evolution([scale])
        
        self.launch(amp_tune, "autoDEER_amptune", IFgain=0)

        while self.isrunning():
            time.sleep(10)
        dataset = self.read_dataset()
        dataset = dataset.epr.correctphase

        data = np.abs(dataset.data)
        scale = np.around(dataset.pulse0_scale[data.argmax()].data,2)
        if scale > 0.9:
            raise RuntimeError("Not enough power avaliable.")
        
        if scale == 0:
            warnings.warn("Pulse tuned with a scale of zero!")
        p90 = amp_tune.pulses[0].copy(
            scale=scale, freq=0)
        
        p180 = amp_tune.pulses[1].copy(
            scale=scale, freq=0)

        return p90, p180

    
    def tune_pulse(self, pulse, mode, freq, B , reptime, shots=400):
        """Tunes a single pulse a range of methods.

        Parameters
        ----------
        pulse : Pulse
            The Pulse object in need of tuning.
        mode : str
            The method to be used.
        freq : float
            The local oscilator frequency in GHz
        B : float
            Magnetic B0 field position in Gauss
        reptime : us
            Shot repetion time in us.
        shots: int
            The number of shots

        Returns
        -------
        Tunned Pulse: Pulse
            The returned pulse object that is now tunned.
        """
        # Check pulse is a pulse
        if type(pulse) == Delay:
            pass
        if type(pulse) == Detection:
            pass
        
        # Get absolute central frequency
        if hasattr(pulse,"freq"):
            c_frq = pulse.freq.value + freq
        elif hasattr(pulse, "init_freq") & hasattr(pulse, "BW"):
            c_frq = pulse.init_freq.value + 0.5*pulse.BW.value + freq
        elif hasattr(pulse, "final_freq") & hasattr(pulse, "BW"):
            c_frq = pulse.final_freq.value - 0.5*pulse.BW.value + freq
        elif hasattr(pulse, "init_freq") & hasattr(pulse, "final_freq"):
            c_frq = 0.5*(pulse.final_freq.value + pulse.final_freq.value) + freq

        # Find rect pulses
        if mode == "amp_hahn":
            if pulse.flipangle.value == np.pi:
                tp = pulse.tp.value / 2
            elif pulse.flipangle.value == np.pi/2:
                tp = pulse.tp.value

            pi2_pulse, pi_pulse = self.tune_rectpulse(tp=tp, B=B, freq=c_frq, reptime=reptime,shots=shots)
            amp_tune =HahnEchoSequence(
                B=B, freq=freq, 
                reptime=reptime, averages=1, shots=shots,
                pi2_pulse = pulse, pi_pulse=pi_pulse
            )

            scale = Parameter('scale',0,unit=None,step=0.02, dim=45, description='The amplitude of the pulse 0-1')
            amp_tune.pulses[0].scale = scale

            amp_tune.evolution([scale])

            self.launch(amp_tune, "autoDEER_amptune", IFgain=0)

            while self.isrunning():
                time.sleep(10)
            dataset = self.read_dataset()
            dataset = dataset.epr.correctphase
            data = np.abs(dataset.data)

            new_amp = np.around(dataset.pulse0_scale[dataset.data.argmax()].data,2)
            if new_amp > 0.9:
                raise RuntimeError("Not enough power avaliable.")
        
            if new_amp == 0:
                warnings.warn("Pulse tuned with a scale of zero!")

            pulse.scale = Parameter('scale',new_amp,unit=None,description='The amplitude of the pulse 0-1')
            return pulse

        elif mode == "amp_nut":
            pi2_pulse, pi_pulse = self.tune_rectpulse(tp=12, B=B, freq=c_frq, reptime=reptime,shots=shots)
            nut_tune = Sequence(
                name="nut_tune", B=(B/freq*c_frq), freq=freq, reptime=reptime,
                averages=1,shots=shots
            )
            nut_tune.addPulse(pulse.copy(
                t=0, pcyc={"phases":[0],"dets":[1]}, scale=0))
            nut_tune.addPulse(
                pi2_pulse.copy(t=2e3,
                               pcyc={"phases":[0, np.pi],"dets":[1, -1]},
                               freq=c_frq-freq))
            nut_tune.addPulse(
                pi_pulse.copy(t=2.5e3, pcyc={"phases":[0],"dets":[1]},
                              freq=c_frq-freq))
            nut_tune.addPulse(Detection(t=3e3, tp=512, freq=c_frq-freq))

            scale = Parameter('scale',0,unit=None,step=0.02, dim=45, description='The amplitude of the pulse 0-1')
            nut_tune.pulses[0].scale = scale
            nut_tune.evolution([scale])


            # nut_tune.addPulsesProg(
            #     pulses=[0],
            #     variables=["scale"],
            #     axis_id = 0,
            #     axis= np.arange(0,0.9,0.02)
            # )
            self.launch(nut_tune, "autoDEER_amptune", IFgain=0)

            while self.isrunning():
                time.sleep(10)
            dataset = self.read_dataset()
            dataset = dataset.epr.correctphase
            data = dataset.data
            axis = dataset.pulse0_scale
            # data = correctphase(dataset.data)
            if data[0] < 0:
                data *= -1

            if np.isclose(pulse.flipangle.value, np.pi):
                new_amp = np.around(axis[data.argmin()].data,2)
            elif np.isclose(pulse.flipangle.value, np.pi/2):
                sign_changes = np.diff(np.sign(np.real(data)))
                new_amp = np.around(axis[np.nonzero(sign_changes)[0][0]].data,2)
            else:
                raise RuntimeError("Target pulse can only have a flip angle of either: ",
                                "pi or pi/2.")
            pulse.scale = Parameter('scale',new_amp,unit=None,description='The amplitude of the pulse 0-1')
        
            return pulse
    
    def tune(self,*, sequence=None, mode="amp_hahn", freq=None, gyro=None):

        if mode == "rect_tune":
            if freq is None:
                raise ValueError("freq must be given for rect_tune")
            if gyro is None:
                raise ValueError("gyro must be give")
            elif gyro >1:
                raise ValueError("Gyromagnetic ratio must be give in GHz/G")
            
            amp_tune =HahnEchoSequence(
                B=freq/gyro, freq=freq, reptime=2e3, averages=1, shots=400
            )
            tp = 12
            amp_tune.pulses[0].tp.value = tp
            amp_tune.pulses[0].scale.value = 0
            amp_tune.pulses[1].tp.value = tp*2
            amp_tune.pulses[1].scale.value = 0
            
            amp_tune.addPulsesProg(
                pulses=[0,1],
                variables=['scale','scale'],
                axis_id=0,
                axis=np.arange(0,0.9,0.02),
            )

            self.launch(amp_tune, "autoDEER_amptune", IFgain=0)

            while self.isrunning():
                time.sleep(10)
            dataset = self.read_dataset()
            scale = np.around(dataset.pulse0_scale[dataset.data.argmax()].data,2)
            if scale > 0.9:
                raise RuntimeError("Not enough power avaliable.")
            
            self.pulses[f"p90_{tp}"] = amp_tune.pulses[0].copy(
                scale=scale, freq=0)
            self.pulses[f"p180_{tp*2}"] = amp_tune.pulses[1].copy(
                scale=scale, freq=0)
        
        elif mode == "amp_hahn":
            for pulse in sequence.pulses:
                if type(pulse) == Delay:
                    continue
                if type(pulse) == Detection:
                    continue

                all_pulses = list(self.pulses.keys())
                pulse_matches = []
                for pulse_name in all_pulses:
                    if not re.match(r"^p180_",pulse_name):
                        continue
                    if not np.abs((self.pulses[pulse_name].freq.value + self.pulses[pulse_name].freq.value) - (sequence.freq.value + pulse.freq.value)) < 0.01:
                        continue
                    pulse_matches.append(pulse_name)
                    
                    ps_length_best =1e6
                for pulse_name in pulse_matches:
                    ps_length = int(re.search(r"p180_(\d+)",pulse_name).groups()[0])
                    if ps_length < ps_length_best:
                        ps_length_best = ps_length
                
                pi_pulse = self.pulses[f"p180_{ps_length_best}"]
                

                amp_tune =HahnEchoSequence(
                    B=sequence.B.value, freq=sequence.freq.value, 
                    reptime=sequence.reptime.value, averages=1, shots=400,
                    pi2_pulse = pulse, pi_pulse=pi_pulse
                )
        
                amp_tune.pulses[0].scale.value = 0

                amp_tune.addPulsesProg(
                    pulses=[0],
                    variables=['scale'],
                    axis_id=0,
                    axis=np.arange(0,0.9,0.02),
                )

                self.launch(amp_tune, "autoDEER_amptune", IFgain=0)

                while self.isrunning():
                    time.sleep(10)
                dataset = self.read_dataset()
                scale = np.around(dataset.pulse0_scale[dataset.data.argmax()].data,2)
                pulse.scale.value = scale

            return sequence
                    

    def _build_exp_struct(self, sequence) -> dict:

        struc = {}

        struc["avgs"] = float(sequence.averages.value)
        struc["reptime"] = round(float(sequence.reptime.value * 1e3), 0)
        struc["shots"] = float(sequence.shots.value)
        struc['B'] = round(float(sequence.B.value), 0)
        struc['name'] = sequence.name
        # Build pulse/detection events
        struc["events"] = list(map(self._build_pulse, sequence.pulses))
        struc["store_avgs"] = int(self.bridge_config.get('Store Averages', True))

        unique_parvars = np.unique(sequence.progTable["axID"])

        # Build parvars
        struc["parvars"] = []
        if hasattr(sequence, 'pcyc_vars'):
            pcyc_parvar = self._build_phase_cycle(sequence)
            if pcyc_parvar["vec"].shape[0] != 1:
                struc["parvars"].append(pcyc_parvar)
        for i in unique_parvars:
            struc["parvars"].append(self._build_parvar(i, sequence))
        
        struc["LO"] = round(float(sequence.freq.value - self.IF_freq), 3)

        return struc

    def _build_pulse(self, pulse) -> dict:

        event = {}
        event["t"] = float(pulse.t.value)

        if type(pulse) is Detection:
            # event["det_len"] = float(pulse.tp.value * self.dig_rate)
            event["det_len"] = float(1024*2)
            event["det_frq"] = float(pulse.freq.value) + self.IF_freq
            event["name"] = "det"
            return event

        # Assuming we now have an actual pulse not detection event
        event["pulsedef"] = {}
        event["pulsedef"]["scale"] = float(pulse.scale.value)
        event["pulsedef"]["tp"] = float(pulse.tp.value)

        if type(pulse) is RectPulse:
            event["pulsedef"]["type"] = 'chirp'
            event["pulsedef"]["nu_init"] = pulse.freq.value + self.IF_freq
        
        elif type(pulse) is ChirpPulse:
            event["pulsedef"]["type"] = 'chirp'
            
            if hasattr(pulse, "init_freq"):
                event["pulsedef"]["nu_init"] = pulse.init_freq.value +\
                     self.IF_freq
            else:
                nu_init = pulse.final_freq.value - pulse.BW.value
                event["pulsedef"]["nu_init"] = nu_init + self.IF_freq
            
            if hasattr(pulse, "final_freq"):
                event["pulsedef"]["nu_final"] = pulse.final_freq.value +\
                     self.IF_freq
            else:
                nu_final = pulse.init_freq.value + pulse.BW.value
                event["pulsedef"]["nu_final"] = nu_final + self.IF_freq
            
        elif type(pulse) is HSPulse:
            event["pulsedef"]["type"] = 'HS'
            if hasattr(pulse, "init_freq"):
                event["pulsedef"]["nu_init"] = pulse.init_freq.value +\
                     self.IF_freq
            else:
                nu_init = pulse.final_freq.value - pulse.BW.value
                event["pulsedef"]["nu_init"] = nu_init + self.IF_freq
            
            if hasattr(pulse, "final_freq"):
                event["pulsedef"]["nu_final"] = pulse.final_freq.value +\
                     self.IF_freq
            else:
                nu_final = pulse.init_freq.value + pulse.BW.value
                event["pulsedef"]["nu_final"] = nu_final + self.IF_freq

            event["pulsedef"]["HSorder"] = float(pulse.order1.value)
            event["pulsedef"]["HSorder2"] = float(pulse.order2.value)
            event["pulsedef"]["HSbeta"] = float(pulse.beta.value)

        elif type(pulse) is Pulse:
            event["pulsedef"]["type"] = 'FMAM'
            raise RuntimeError("Not yet implemented")
        
        if self.resonator is not None:
            resonator = {}

            resonator['LO'] = self.resonator.freq_c - self.IF_freq#- 1.5 # Change to LO after shifting resonator profile definition
            resonator['nu1'] = self.resonator.profile
            resonator['range'] = self.resonator.freqs.values - resonator['LO']
            resonator['scale'] = self.resonator.dataset.pulse0_scale

            event["pulsedef"]["resonator"] = resonator

        return event

    def _build_phase_cycle(self, sequence) -> dict:

        parvar = {}
        parvar["reduce"] = 1
        parvar["ax_id"] = 1
        parvar["name"] = "phase_cycle"

        pulse_str = lambda x: f"events{{{x+1}}}.pulsedef.phase"
        parvar["variables"] = list(map(pulse_str, sequence.pcyc_vars))

        # Find detection pulse
        for i, pulse in enumerate(sequence.pulses):
            if type(pulse) == Detection:
                det_id = i

        det_str = "events{{{}}}.det_sign".format(det_id+1)
        parvar["variables"].append(det_str)

        parvar["vec"] = np.vstack(
            [sequence.pcyc_cycles.T, sequence.pcyc_dets]).T

        return parvar

    def _build_parvar(self, id, sequence) -> dict:
        """This interface takes a dictionary called a parvar for all 
        progressive elements. It is this object that controls how the
        sequence changes with time.


        .. note::
            This interface interprets any change in `freq` as being a 
            change in the IF frequency of all pulses and detections.
             I.e. the physcial LO **does not** change. 

        Parameters
        ----------
        id : _type_
            _description_
        sequence : _type_
            _description_

        Returns
        -------
        dict
            _description_
        """

        def get_vec(seq,EventID,variable,uuid):

            if EventID is None:
                attr = getattr(seq, variable)
            else:
                attr = getattr(seq.pulses[EventID], variable)

            # Find local position
            axis_T = transpose_list_of_dicts(attr.axis)
            i = axis_T['uuid'].index(uuid)
            vec = attr.value + attr.axis[i]['axis']

            if attr.unit == 'us':
                vec *=1e3
            elif attr.unit == 'ms':
                vec *=1e6
            
            return vec.astype(float)

        prog_table = sequence.progTable
        prog_table_n = len(prog_table["axID"])
        parvar = {}
        parvar["name"] = f"parvar{id+1}"

        parvar["variables"] = []
        parvar["vec"] = []

        for i in range(0, prog_table_n):

            if prog_table["axID"][i] == id:
                pulse_num = prog_table["EventID"][i]
                var = prog_table["Variable"][i]
                uuid = prog_table["uuid"][i]
                # vec = prog_table["axis"][i].astype(float)
                vec = get_vec(sequence,pulse_num,var,uuid)
                if pulse_num is not None:
                    if var in ["freq", "init_freq"]:
                        vec += self.IF_freq
                        if isinstance(sequence.pulses[pulse_num],Detection):
                            var = 'det_frq'
                        else:
                            var = "nu_init"
                    elif var == "final_freq":
                        vec += self.IF_freq
                        var = "nu_final"

                    if var == "t":
                        pulse_str = f"events{{{pulse_num+1}}}.t"
                    elif var =='det_frq':
                        pulse_str = f"events{{{pulse_num+1}}}.det_frq"
                    else:
                        pulse_str = f"events{{{pulse_num+1}}}.pulsedef.{var}"
                    
                    parvar["variables"].append(pulse_str)
                    parvar["vec"].append(vec)

                elif (var == "freq") or (var == "freq_axis"):
                    # Instead of stepping the freq we will step the frequency
                    # all the pulses and detection events.
                    pulse_strings = []
                    # vec = prog_table["axis"][i].astype(float)
                    centre_freq = (vec[-1] + vec[0])/2
                    LO = centre_freq - self.IF_freq
                    sequence.freq.value = centre_freq
                    vec = vec - LO
                    vecs = []
                    pulse_str = lambda i: f"events{{{i+1}}}.pulsedef.nu_init"
                    det_str = lambda i: f"events{{{i+1}}}.det_frq"
                    for i,pulses in enumerate(sequence.pulses):
                        if type(pulses) is Delay:
                            continue
                        elif type(pulses) is Detection:
                            pulse_strings.append(det_str(i))
                            vecs.append(vec)
                        else:
                            pulse_strings.append(pulse_str(i))
                            vecs.append(vec)

                    parvar["variables"].extend(pulse_strings)
                    parvar["vec"].extend(vecs)                
                
                else:
                    pulse_str = var
                    parvar["variables"].append(pulse_str)
                    parvar["vec"].append(vec)
                


        parvar["vec"] = np.stack(parvar["vec"]).T
        return parvar

    def terminate(self):
        """ Stops the current experiment
        """
        if self.bg_thread is None:
            self.engine.dig_interface('terminate', nargout=0)
        else:
            self.engine.dig_interface('terminate', nargout=0)
            self.stop_flag.set()
            self.bg_thread.join()
            self.bg_thread = None
            
        pass



def bg_thread(interface,seq,savename,IFgain,axID,stop_flag):

    # Add averaging loop here
    dim = []
    for p in seq.evo_params:
        if (p.uuid not in seq.reduce_uuid):
            for item in p.dim:
                dim.append(item)

    OG_seq_progTable = seq.progTable
    new_seq = seq.copy()
    new_seq.averages.value=1
    new_params = copy.copy(seq.evo_params)
    droped_param = new_params.pop(axID)
    fixed_param = seq.evo_params[axID]

    # is removed axis a reduced axis
    if fixed_param.uuid in seq.reduce_uuid:
        reduced = True
    else:
        reduced = False
    new_reduce_param = []
    for p in new_params:
        if p.uuid == fixed_param.uuid:
            continue
        elif p.uuid in seq.reduce_uuid:
            new_reduce_param.append(p)

    def set_params_by_uuid(new_seq, progTable,uuid,index):
        n_elements = len(progTable['EventID'])
        for i in range(n_elements):
            ele_uuid = progTable['uuid'][i]
            if ele_uuid != uuid:
                continue

            var = progTable['Variable'][i]
            axis = progTable['axis'][i]
            if progTable['EventID'][i] is None:
                # A sequence parameter
                param = getattr(new_seq, var)
                new_value = param.value + axis[index]
            else:
                param = getattr(new_seq.pulses[progTable['EventID'][i]], var)
                new_value = param.value + axis[index]
            param.value = new_value
    
    nAvg=seq.averages.value
    dig_level=0
    for iavg in range(nAvg): 
        if stop_flag.is_set():
            break   
        single_scan_data = np.zeros(dim, dtype=np.complex128)
        
        for i in range(fixed_param.dim[0]):
            if stop_flag.is_set():
                break
            # droped_param.value = fixed_param.get_axis()[i]
            tmp_seq = new_seq.copy()
            set_params_by_uuid(tmp_seq, OG_seq_progTable, droped_param.uuid, i)
            tmp_seq.evolution(new_params,new_reduce_param)
            
            interface.launch_normal(tmp_seq, savename=f"{savename}_avg{iavg+1}of{nAvg}_{i+1}of{fixed_param.dim[0]}", IFgain=IFgain, reset_cur_exp=False)
            scan_time = tmp_seq._estimate_time()
            time.sleep(np.max([scan_time, 5]))
            while True:
                _, _,_,state = interface.engine.dig_interface('progress', nargout=4)
                if state != 1:
                    break
                time.sleep(np.min([scan_time/4, 10]))
            
            single_scan = interface.get_buffer(cur_exp=tmp_seq)
            if reduced:
                single_scan_data = single_scan.data
            else:
                single_scan_data[:,i] = single_scan.data
        
        if stop_flag.is_set():
            break
        interface.bg_data.data += single_scan_data
        if single_scan.attrs['diglevel'] > dig_level:
            dig_level = single_scan.attrs['diglevel']
        interface.bg_data.attrs['diglevel'] = dig_level
        interface.bg_data.attrs['nAvgs'] = iavg+1

    print("Background thread finished")