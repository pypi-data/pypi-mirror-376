import os

import numpy as np
import matplotlib.pyplot as plt
from tqdm import tqdm

from dcmri import rel, sig, pk_inv, pk_aorta



PARAMS = {
    'dt': {
        'init': 1.0,
        'name': 'Time step',
        'unit': 'sec',
    },
    'ca': {
        'init': None,
        'name': 'Arterial Input concentration',
        'unit': 'mL/sec/cm3',
    },
    'irf': {
        'init': None, 
        'name': 'Impulse response function',
        'unit': 'mL/sec/cm3',
    },
    'r1': {
        'init': 5000.0,
        'name': 'Contrast agent relaxivity',
        'unit': 'Hz/M',
    },
    'R10a': {
        'init': 0.7,
        'name': 'Arterial precontrast R1',
        'unit': 'Hz',
    },
    'S0a': {
        'init': 1.0,
        'name': 'Arterial signal scaling factor',
        'unit': 'a.u.',
    },
    'B1corr_a': {
        'init': 1,
        'name': 'Arterial B1-correction factor',
        'unit': '',
    },
    'B1corr': {
        'name': 'Tissue B1-correction factor',
        'unit': '',
    },
    'FA': {
        'init': 15,
        'name': 'Flip angle',
        'unit': 'deg',
    },
    'TR': {
        'init': 0.005,
        'name': 'Repetition time',
        'unit': 'sec',
    },
    'TC': {
        'init': 0.2,
        'name': 'Time to k-space center',
        'unit': 'sec',
    },
    'TS': {
        'init': 0,
        'name': 'Sampling time',
        'unit': 'sec',
    },
    'R10': {
        'name': 'Tissue precontrast R1',
        'unit': 'Hz',
    },
    'S0': {
        'name': 'Signal scaling factor',
        'unit': 'a.u.',
    },
    'H': {
        'init': 0.45,
        'name': 'Tissue Hematocrit',
        'unit': '',
    },
    'Fb': {
        'name': 'Parenchymal blood flow',
        'unit': 'mL/sec/cm3',
    },
    've': {
        'name': 'Extracellular volume',
        'unit': 'mL/cm3',
    },
    'Te': {
        'name': 'Extracellular mean transit time',
        'unit': 'sec',
    },
}





class TissueLS():
    """Array of linear and stationary tissues with a single inlet.

    These are generic model-free tissue types. Their response to 
    an indicator injection is proportional to the dose (linear) and 
    independent of the time of injection (stationary).

    Args:
        shape (array-like, required): shape of the tissue array (spatial dimensions only). 
          Any number of dimensions is allowed.
        aif (array-like, required): Signal-time curve in the blood of the
          feeding artery. 
        dt (float, optional): Time interval between values of the arterial
          input function. Defaults to 1.0.
        sequence (str, optional): imaging sequence. Possible values 
          are 'SS', 'SR' and 'lin' (linear). Defaults to 'SS'.
        params (dict, optional): values for the parameters of the tissue,
          specified as keyword parameters. Defaults are used for any that are
          not provided. 

    See Also:
        `TissueLS`, `TissueArray`

    Example:

        Fit a linear and stationary model to the synthetic test data:

    .. plot::
        :include-source:
        :context: close-figs

        >>> import numpy as np
        >>> import dcmri as dc

        Generate synthetic test data:

        >>> time, aif, roi, gt = dc.fake_tissue()

        The correct ground truth for ve in model-free analysis is the 
        extracellular part of the distribution space:

        >>> gt['ve'] = gt['vp'] + gt['vi'] if gt['PS'] > 0 else gt['vp']

        Build a tissue and set the constants to match the
        experimental conditions of the synthetic test data. 

        >>> tissue = dc.TissueLS(
        ...     dt = time[1],
        ...     sequence = 'SS',
        ...     r1 = dc.relaxivity(3, 'blood','gadodiamide'),
        ...     TR = 0.005,
        ...     FA = 15,
        ...     R10a = 1/dc.T1(3.0,'blood'),
        ...     R10 = 1/dc.T1(3.0,'muscle'),
        ... )

        Train the tissue on the data. Since have noise-free synthetic 
        data we use a lower tolerance than the default, which is optimized 
        for noisy data:

        >>> tissue.train(roi, aif, n0=10, tol=0.01)

        Plot the reconstructed signals along with the concentrations 
        and the impulse response function.

        >>> tissue.plot(roi)

    """

    def __init__(self, sequence='SS', **kwargs):

        # Configuration
        if sequence not in ['SS', 'SR', 'lin']:
            raise ValueError(
                f"Sequence {sequence} is not recognized. "
                f"Current options are 'SS', 'SR', 'lin'."
            )
        self.sequence = sequence
        self.pars = {}
        
        # Initialize scalar parameters
        params = ['dt', 'H', 'R10a', 'S0a', 'r1']
        if self.sequence == 'SR':
            params += ['TC']
        elif self.sequence == 'SS':
            params += ['TR', 'B1corr_a', 'FA']
        elif self.sequence == 'lin':
            params += []
        for par in params:
            self.pars[par] = PARAMS[par]['init']

        # Initialize array parameters
        nt = 120
        time = self.pars['dt'] * np.arange(nt)
        Kb = 1 / 5.0
        self.pars['ca'] = pk_aorta.aif_tristan(time)
        self.pars['irf'] = 0.01 * np.exp(-Kb * time)
        self.pars['S0'] = 1
        self.pars['R10'] = 1
        if self.sequence == 'SS':
            self.pars['B1corr'] = 1

        # Override parameter defaults
        for par in kwargs:
            self.pars[par] = kwargs[par]


    def predict_aif(self):
        """Predict the signal at specific time points

        Returns:
            np.ndarray: Array of predicted signals for each time point.
        """
        # Predict arterial signal
        R1a = rel.relax(self.pars['ca'], self.pars['R10a'], self.pars['r1'])
        if self.sequence == 'SS':
            Sa = sig.signal_ss(self.pars['S0a'], R1a, self.pars['TR'], self.pars['B1corr']*self.pars['FA'])
        elif self.sequence == 'SR':
            Sa = sig.signal_src(self.pars['S0a'], R1a, self.pars['TC'])
        elif self.sequence == 'lin':
            Sa = sig.signal_lin(self.pars['S0a'], R1a) 
        return Sa
 
    def predict_conc(self):
        """Return the tissue concentration

        Returns:
            np.ndarray: Concentration in M
        """
        ca_mat = self.pars['dt'] * pk_inv.convmat(self.pars['ca'])
        irf_mat = self.pars['irf']
        conc = ca_mat @ irf_mat.T
        return conc.T

    def predict(self):
        """Predict the signal at specific time points

        Returns:
            np.ndarray: Array of predicted signals for each time point.
        """ 
        conc = self.predict_conc()
        R1 = rel.relax(conc, self.pars['R10'], self.pars['r1'])
        S0 = self.pars['S0']
        if self.sequence == 'SS':
            signal = sig.signal_ss(S0, R1, self.pars['TR'], self.pars['B1corr']*self.pars['FA'])
        elif self.sequence == 'SR':
            signal = sig.signal_src(S0, R1, self.pars['TC'])
        elif self.sequence == 'lin':
            signal = sig.signal_lin(S0, R1) 
        return signal

    

    def train(self, signal, signal_aif, n0=1, tol=0.1, init_s0=True):
        """Train the free parameters

        Args:
            signal (array-like): Array with measured signals.
            tol: cut-off value for the singular values in the 
                computation of the matrix pseudo-inverse.

        Returns:
            self
        """ 

        # Fit baselines if needed
        if init_s0:
            if self.sequence == 'SR':
                scla = sig.signal_src(1, self.pars['R10a'],  self.pars['TC'])
                scl = sig.signal_src(1, self.pars['R10'],  self.pars['TC'])
            elif self.sequence == 'SS':
                scla = sig.signal_ss(1, self.pars['R10a'],  self.pars['TR'], self.pars['B1corr_a'] * self.pars['FA'])
                scl = sig.signal_ss(1, self.pars['R10'], self.pars['TR'], self.pars['B1corr'] * self.pars['FA'])
            elif self.sequence == 'lin':
                scla = sig.signal_lin(1, self.pars['R10a'])
                scl = sig.signal_lin(1, self.pars['R10'])
            self.pars['S0a'] = np.mean(signal_aif[:n0]) / scla if scla > 0 else 0
            self.pars['S0'] = np.mean(signal[...,:n0]) / scl if scl > 0 else 0

        # Derive concentrations
        T10a = 1/self.pars['R10a'] if self.pars['R10a'] > 0 else 0
        T10 = 1/self.pars['R10'] if self.pars['R10'] > 0 else 0

        if self.sequence == 'SR':
            self.pars['ca'] = sig.conc_src(
                signal_aif, self.pars['TC'], T10a, 
                self.pars['r1'], S0=self.pars['S0a'])
            conc = sig.conc_src(
                signal, self.pars['TC'], T10, 
                self.pars['r1'], S0=self.pars['S0'])
            
        elif self.sequence == 'SS':
            self.pars['ca'] = sig.conc_ss(
                signal_aif, self.pars['TR'], self.pars['B1corr_a'] * self.pars['FA'],
                T10a, self.pars['r1'], S0=self.pars['S0a'])
            conc = sig.conc_ss(
                signal, self.pars['TR'], self.pars['B1corr_a'] * self.pars['FA'],
                T10, self.pars['r1'], S0=self.pars['S0'])
            
        elif self.sequence == 'lin':
            self.pars['ca'] = sig.conc_lin(
                signal_aif, T10a, 
                self.pars['r1'], S0=self.pars['S0a'])
            conc = sig.conc_lin(
                signal, T10, self.pars['r1'], S0=self.pars['S0'])

        conc[np.isnan(conc)] = 0
        irf_mat = pk_inv.deconv(conc, self.pars['ca'], self.pars['dt'], tol=tol)
        self.pars['irf'] = irf_mat

        return self
    
    
    def params(self, *args):
        """Export the tissue parameters

        Args:
            args (tuple): parameters to get. If no arguments are 
                provided, all available parameters are returned.    

        Returns:
            dict: Dictionary with tissue parameters.
        """
        amax = np.max(self.pars['irf'])
        auc = np.sum(self.pars['irf']) * self.pars['dt']
        params = {
            'IRF': self.pars['irf'],
            'Fb': amax,
            'Te': auc / amax if amax > 0 else 0,
            've': auc * (1-self.pars['H']),
            'S0': self.pars['S0'],
        }
        if args == ():
            return params
        elif len(args) == 1:
            return params[args[0]]
        else:
            return {p: params[p] for p in args}


    def print_params(self, round_to=None):
        """Print the model parameters

        Args:
            round_to (int, optional): Round to how many digits. If this is
              not provided, the values are not rounded. Defaults to None.
        """

        print('')
        print('----------------------------------------------------')
        print('Derived parameters for linear and stationary tissues')
        print('----------------------------------------------------')
        print('')  

        p = self.params()

        par = p['Fb']
        par = round(par, round_to) if round_to is not None else par
        print(f"Parenchymal blood flow: {par} mL/sec/cm3")  

        par = p['Te']
        par = round(par, round_to) if round_to is not None else par 
        print(f"Extracellular transit time: {par} sec") 

        par = p['ve']
        par = round(par, round_to) if round_to is not None else par
        print(f"Extracellular volume fraction: {par} mL/cm3")



    def plot(self, signal=None, round_to=None, fname=None, show=True):
        """Plot the model fit against data

        Args:
            signal (array-like, optional): Array with measured signals.
            round_to (int, optional): Rounding for the model parameters.
            fname (path, optional): Filepath to save the image. If no value is
              provided, the image is not saved. Defaults to None.
            show (bool, optional): If True, the plot is shown. Defaults to
              True.
        """
        
        fig, ax = plt.subplots(1, 4, figsize=(20, 5))
    
        t = self.pars['dt'] * np.arange(len(self.pars['ca']))

        # Plot predicted signals and measured signals
        ax[0].set_title('MRI signals')
        ax[0].set(ylabel='MRI signal (a.u.)', xlabel='Time (min)')
        ax[0].plot(
            t / 60, self.predict(), linestyle='-', 
            linewidth=3.0, color='cornflowerblue', 
            label='Tissue (predicted)',
        )
        if signal is not None:
            ax[0].plot(
                t / 60, signal, marker='x', linestyle='None',
                color='darkblue', label='Tissue (measured)',
            )
        ax[0].legend()

        # Plot predicted concentrations and measured concentrations
        ax[1].set_title('Tissue concentrations')
        ax[1].set(ylabel='Concentration (mM)', xlabel='Time (min)')
        ax[1].plot(
            t / 60, 1000 * self.pars['ca'], linestyle='-', linewidth=5.0,
            color='lightcoral', label='Arterial blood',
        )
        ax[1].plot(
            t / 60, 1000 * self.predict_conc(), linestyle='-', linewidth=3.0, 
            color='cornflowerblue', label='Tissue (predicted)', 
        )
        ax[1].legend()

        # Plot impulse response
        ax[2].set_title('Impulse response function')
        ax[2].set(ylabel='IRF (mL/sec/cm3)', xlabel='Time (min)')
        ax[2].plot(
            t / 60, self.pars['irf'], linestyle='-', linewidth=3.0,
            color='cornflowerblue', label='IRF', 
        )
        ax[2].legend()

        # Plot text
        pars = self.params()
        msg = []
        for par in ['Fb', 've', 'Te', 'S0']:
            value = pars[par]
            if round_to is not None:
                value = round(value, round_to)
            msg.append(f"{PARAMS[par]['name']} ({par}): {value} {PARAMS[par]['unit']} \n")
        
        msg = "\n".join(msg)
        ax[3].set_title('Free parameters')
        ax[3].axis("off")  # hide axes
        ax[3].text(0, 0.9, msg, fontsize=10, transform=ax[3].transAxes, ha="left", va="top")

        # Show and/or save plot
        if fname is not None:
            plt.savefig(fname=fname)
        if show:
            plt.show()
        else:
            plt.close()

        