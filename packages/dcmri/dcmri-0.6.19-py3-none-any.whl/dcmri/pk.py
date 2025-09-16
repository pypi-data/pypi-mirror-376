import math
import numpy as np
from scipy.integrate import trapezoid
from scipy.special import lambertw

import dcmri.utils as utils

# Wrappers


def flux(J: np.ndarray, *params, t=None, dt=1.0, model='comp', **kwargs) -> np.ndarray:
    """Flux out of an arbitrary pharmacokinetic system.

    This is a wrapper function offering a standard interface to calculate the 
    flux out of a specific system, with the system architecture specified in 
    the dictionary. It offers a convenient way to build more complex models 
    with variable configurations, such as `dcmri.flux_aorta`.

    Args:
        J (array_like): the indicator flux entering the trap.
        params (tuple): model parameters.
        t (array_like, optional): the time points of the indicator flux J. If 
          t=None, the time points are assumed to be uniformly spaced with 
          spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly 
          spaced time points. This parameter is ignored if t is explicity 
          provided. Defaults to 1.0.
        model (str, optional): Model to use, options are 'trap', 'pass', 
          'comp', 'plug', 'chain', 'step', 'free', 'ncomp', 'nscomp', 
          'pfcomp', 'mmcomp', '2cxm'. Defaults to 'comp'.
        kwargs (dict): any optional parameters required by the model.

    Raises:
        ValueError: If a system is specified that is nto yet implemented.

    Returns:
        np.ndarray: Total outflux out of the system.

    """

    if model == 'trap':
        return flux_trap(J)
    if model == 'pass':
        return flux_pass(J)
    if model == 'comp':
        return flux_comp(J, *params, t=t, dt=dt, **kwargs)
    if model == 'plug':
        return flux_plug(J, *params, t=t, dt=dt, **kwargs)
    if model == 'chain':
        return flux_chain(J, *params, t=t, dt=dt, **kwargs)
    if model == 'step':
        return flux_step(J, *params, t=t, dt=dt, **kwargs)
    if model == 'free':
        return flux_free(J, *params, t=t, dt=dt, **kwargs)
    if model == 'ncomp':
        return flux_ncomp(J, *params, t=t, dt=dt, **kwargs)
    if model == 'nscomp':
        return flux_nscomp(J, *params, t=t, dt=dt)
    if model == 'pfcomp':
        return flux_pfcomp(J, *params, t=t, dt=dt, **kwargs)
    if model == 'mmcomp':
        return flux_mmcomp(J, *params, t=t, dt=dt, **kwargs)
    if model == '2cxm':
        return flux_2cxm(J, *params, t=t, dt=dt, **kwargs)
    msg = 'Model ' + model + ' is not currently implemented.'
    raise ValueError(msg)


def conc(J: np.ndarray, *params, t=None, dt=1.0, model='comp', 
         **kwargs) -> np.ndarray:
    """Concentration in an arbitrary pharmacokinetic system.

    Args:
        J (array_like): the indicator flux entering the trap.
        params (tuple): model parameters.
        t (array_like, optional): the time points of the indicator flux J. 
          If t=None, the time points are assumed to be uniformly spaced with 
          spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly 
          spaced time points. This parameter is ignored if t is explicity 
          provided. Defaults to 1.0.
        model (str, optional): Model to use, options are 'trap', 'pass', 
          'comp', 'plug', 'chain', 'step', 'free', 'ncomp', 'nscomp', 
          'mmcomp', '2cxm'. Defaults to 'comp'.

    This is a wrapper function offering a standard interface to calculate the concentration in a specific system.

    Raises:
        ValueError: If a system is specified that is not yet implemented.

    Returns:
        np.ndarray: Concentration in the system.
    """

    if model == 'trap':
        return conc_trap(J, t=t, dt=dt)
    if model == 'pass':
        return conc_pass(J, *params)
    if model == 'comp':
        return conc_comp(J, *params, t=t, dt=dt, **kwargs)
    if model == 'plug':
        return conc_plug(J, *params, t=t, dt=dt, **kwargs)
    if model == 'chain':
        return conc_chain(J, *params, t=t, dt=dt, **kwargs)
    if model == 'step':
        return conc_step(J, *params, t=t, dt=dt, **kwargs)
    if model == 'free':
        return conc_free(J, *params, t=t, dt=dt, **kwargs)
    if model == 'ncomp':
        return conc_ncomp(J, *params, t=t, dt=dt, **kwargs)
    if model == 'nscomp':
        return conc_nscomp(J, *params, t=t, dt=dt)
    if model == 'mmcomp':
        return conc_mmcomp(J, *params, t=t, dt=dt, **kwargs)
    if model == '2cxm':
        return conc_2cxm(J, *params, t=t, dt=dt, **kwargs)
    msg = 'Model ' + model + ' is not currently implemented.'
    raise ValueError(msg)


# 0 Parameters

# Trap

def res_trap(t):
    """Residue function of a trap.

    See section :ref:`define-trap` for more detail. 

    Args:
        t (array_like): Time points where the residue function is calculated.

    Returns:
        numpy.ndarray: residue function as a 1D array.

    See Also:
        `prop_trap`, `conc_trap`, `flux_trap`

    Example:
        >>> import dcmri as dc
        >>> t = [0,1,2,3,4]
        >>> dc.res_trap(t)
        array([1., 1., 1., 1., 1.])  
    """
    return np.ones(len(t))


def prop_trap(t):
    """Propagator or transit time distribution of a trap.

    See section :ref:`define-trap` for more detail. 
     
    Args:
        t (array_like): Time points where the propagator is calculated.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    See Also:
        `res_trap`, `conc_trap`, `flux_trap`

    Example:
        >>> import dcmri as dc
        >>> t = [0,1,2,3,4]
        >>> dc.prop_trap(t)
        array([0., 0., 0., 0., 0.])  
    """
    return np.zeros(len(t))


def conc_trap(J, t=None, dt=1.0):
    """Indicator tissue concentration inside a trap.

    See section :ref:`define-trap` for more detail.

    Args:
        J (array_like): the indicator flux entering the trap.
        t (array_like, optional): the time points of the indicator flux J. If 
          t=None, the time points are assumed to be uniformly spaced with 
          spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly 
          spaced time points. This parameter is ignored if t is explicity 
          provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    See Also:
        `res_trap`, `prop_trap`, `flux_trap`

    Example:
        >>> import dcmri as dc
        >>> J = [1,2,3,3,2]
        >>> dc.conc_trap(J, dt=2.0)
        array([ 0.,  3.,  8., 14., 19.])
    """
    return utils.trapz(J, t=t, dt=dt)


def flux_trap(J):
    """Indicator flux out of a trap.

    See section :ref:`define-trap` for more detail. 

    Args:
        J (array_like): the indicator flux entering the trap.

    Returns:
        numpy.ndarray: outflux as a 1D array.

    See Also:
        `res_trap`, `conc_trap`, `prop_trap`

    Example:
        >>> import dcmri as dc
        >>> J = [1,2,3,3,2]
        >>> dc.flux_trap(J, dt=2.0)
        array([0., 0., 0., 0., 0.])  
    """
    return np.zeros(len(J))


# 1 Parameter

# Pass (no dispersion)

def res_pass(T, t):
    """Residue function of a pass.

    See section :ref:`define-pass` for more detail.

    Args:
        T (float): transit time of the pass.
        t (array_like): Time points where the residue function is calculated.

    Returns:
        numpy.ndarray: residue function of the pass as a 1D array.

    See Also:
        `prop_pass`, `conc_pass`, `flux_pass`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.res_pass(5,t)
        array([3.33333333, 0.        , 0.        , 0.        ])  
    """
    return T*utils.ddelta(0, t)


def prop_pass(t):
    """Propagator or transit time distribution of a pass.

    See section :ref:`define-pass` for more detail.
    
    Args:
        t (array_like): Time points where the propagator is calculated.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    See Also:
        `res_pass`, `conc_pass`, `flux_pass`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.prop_pass(t)
        array([0.66666667, 0.        , 0.        , 0.        ])  
    """
    return utils.ddelta(0, t)


def conc_pass(J, T):
    """Indicator concentration inside a pass.

    See section :ref:`define-pass` for more detail.
    
    Args:
        J (array_like): the indicator flux entering the pass.
        T (float): transit time of the pass.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    See Also:
        `res_pass`, `prop_pass`, `flux_pass`

    Example:
        >>> import dcmri as dc
        >>> J = [1,2,3,3,2]
        >>> dc.conc_pass(J, 5)
        array([ 5, 10, 15, 15, 10])
    """
    return T*np.array(J)


def flux_pass(J):
    """Indicator flux out of a pass.

    See section :ref:`define-pass` for more detail.
    
    Args:
        J (array_like): the indicator flux entering the pass.

    Returns:
        numpy.ndarray: outflux as a 1D array.

    See Also:
        `res_pass`, `conc_pass`, `prop_pass`

    Example:
        >>> import dcmri as dc
        >>> J = [1,2,3,3,2]
        >>> dc.flux_pass(J)
        array([1, 2, 3, 3, 2]) 
    """
    return np.array(J)


# Compartment

def res_comp(T, t):
    """Residue function of a compartment.

    See section :ref:`define-compartment` for more detail.

    Args:
        T (float): mean transit time of the compartment. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        t (array_like): time points where the residue function is calculated, in the same units as T.

    Returns:
        numpy.ndarray: residue function of the compartment as a 1D array.

    See Also:
        `prop_comp`, `conc_comp`, `flux_comp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.res_comp(5,t)
        array([1.        , 0.54881164, 0.44932896, 0.30119421])  
    """
    if T == np.inf:
        return res_trap(t)
    if T == 0:
        r = np.zeros(len(t))
        r[0] = 1
        return r
    return np.exp(-np.array(t)/T)


def prop_comp(T, t):
    """Propagator or transit time distribution of a compartment.

    See section :ref:`define-compartment` for more detail.

    Args:
        T (float): mean transit time of the compartment. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        t (array_like): time points where the propagator is calculated, in the same units as T.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    See Also:
        `res_comp`, `conc_comp`, `flux_comp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.prop_comp(5,t)
        array([0.2       , 0.10976233, 0.08986579, 0.06023884])  
    """
    if T == np.inf:
        return prop_trap(t)
    if T == 0:
        return utils.ddelta(T, t)
    return np.exp(-np.array(t)/T)/T


def conc_comp(J, T, t=None, dt=1.0):
    """Indicator concentration inside a compartment.

    See section :ref:`define-compartment` for more detail. 

    Args:
        J (array_like): the indicator flux entering the compartment.
        T (float): mean transit time of the compartment. Any non-negative 
          value is allowed, including :math:`T=0` and :math:`T=\\infty`, in 
          which case the compartment is a trap.
        t (array_like, optional): the time points of the indicator flux J, in 
          the same units as T. If t=None, the time points are assumed to be 
          uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced 
          time points, in the same units as T. This parameter is ignored if t 
          is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    See Also:
        `res_comp`, `prop_comp`, `flux_comp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.conc_comp(J, 5, t)
        array([ 0.        ,  5.        , 12.16166179, 14.85868746, 10.83091743])
    """
    if T == np.inf:
        return conc_trap(J, t=t, dt=dt)
    return T*utils.expconv(J, T, t=t, dt=dt)


def flux_comp(J, T, t=None, dt=1.0):
    """Indicator flux out of a compartment.

    See section :ref:`define-compartment` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment.
        T (float): mean transit time of the compartment. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: outflux as a 1D array.

    See Also:
        `res_comp`, `conc_comp`, `prop_comp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.flux_comp(J, 5, t)
        array([0.        , 1.        , 2.43233236, 2.97173749, 2.16618349]) 
    """
    if T == np.inf:
        return flux_trap(J)
    return utils.expconv(J, T, t=t, dt=dt)


# Plug flow

def prop_plug(T, t):
    """Propagator or transit time distribution of a plug flow system.

    See section :ref:`define-plug-flow` for more detail.

    Args:
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the system is a trap.
        t (array_like): time points where the propagator is calculated, in the same units as T.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    See Also:
        `res_plug`, `conc_plug`, `flux_plug`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.prop_plug(5,t)
        array([0.        , 0.        , 0.33333333, 0.5       ])  
    """
    return utils.ddelta(T, t)


def res_plug(T, t):
    """Residue function of a plug flow system.

    See section :ref:`define-plug-flow` for more detail.

    Args:
        T (float): mean transit time of the system. Any non-negative value is 
          allowed, including :math:`T=0` and :math:`T=\\infty`, in which 
          case the system is a trap.
        t (array_like): time points where the residue function is calculated, 
          in the same units as T.

    Returns:
        numpy.ndarray: residue function as a 1D array.

    See Also:
        `prop_plug`, `conc_plug`, `flux_plug`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.res_plug(5,t)
        array([1.00000000e+00, 1.00000000e+00, 8.33333333e-01, 1.11022302e-16])  
    """
    h = prop_plug(T, t)
    return 1-utils.trapz(h, t)


def conc_plug(J, T, t=None, dt=1.0, solver='interp'):
    """Indicator concentration inside a plug flow system.

    See section :ref:`define-plug-flow` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.
        solver (str, optional): solver for the system, either 'conv' for explicit convolution with a discrete impulse response (slow) or 'interp' for interpolation (fast). Defaults to 'interp'.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    See Also:
        `res_plug`, `prop_plug`, `flux_plug`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.conc_plug(J, 5, t)
        array([ 0.        ,  6.38888889, 18.61111111, 22.5       , 16.25      ])
    """
    if T == np.inf:
        return conc_trap(J)
    if T == 0:
        return 0*J
    t = utils.tarray(len(J), t=t, dt=dt)
    if solver == 'conv':
        r = res_plug(T, t)
        return utils.conv(r, J, t=t, dt=dt)
    elif solver == 'interp':
        Jo = np.interp(t-T, t, J, left=0)
        return utils.trapz(J-Jo, t)


def flux_plug(J, T, t=None, dt=1.0, solver='interp'):
    """Indicator flux out of a plug flow system.

    See section :ref:`define-plug-flow` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the system is a trap.
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.
        solver (str, optional): solver for the system, either 'conv' for explicit convolution with a discrete impulse response (slow) or 'interp' for interpolation (fast). Defaults to 'interp'.

    Returns:
        numpy.ndarray: outflux as a 1D array.

    See Also:
        `res_plug`, `conc_plug`, `prop_plug`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.flux_plug(J, 5, t)
        array([0.        , 0.44444444, 23.0555556, 3.        , 2.22222222]) 
    """
    if T == np.inf:
        return flux_trap(J)
    if T == 0:
        return J
    t = utils.tarray(len(J), t=t, dt=dt)
    if solver == 'conv':
        h = prop_plug(T, t)
        return utils.conv(h, J, t=t, dt=dt)
    elif solver == 'interp':
        return np.interp(t-T, t, J, left=0)
    else:
        raise ValueError('Solver ' + solver + ' does not exist.')


# 2 Parameters

# Chain

def prop_chain(T, D, t):
    """Propagator or transit time distribution of a chain system.

    See section :ref:`define-chain` for more detail.

    Args:
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the system is a trap.
        D (float): dispersion of the system. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like): time points where the propagator is calculated, in the same units as T.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    Raises:
        ValueError: if one of the parameters is out of bounds.

    See Also:
        `res_chain`, `conc_chain`, `flux_chain`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.prop_chain(5, 0.5, t)
        array([0.        , 0.14457322, 0.12921377, 0.08708924])  
    """
    if T < 0:
        raise ValueError('T must be non-negative')
    if D < 0:
        raise ValueError('D cannot be negative')
    if D > 1:
        raise ValueError('D cannot be larger than 1')
    if D == 0:
        return prop_plug(T, t)
    if D == 1:
        return prop_comp(T, t)
    n = 1/D
    g = utils.nexpconv(n, T/n, t)
    return g


def res_chain(T, D, t):
    """Residue function of a chain system.

    See section :ref:`define-chain` for more detail.

    Args:
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the system is a trap.
        D (float): dispersion of the system. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like): time points where the residue function is calculated, in the same units as T.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    See Also:
        `prop_chain`, `conc_chain`, `flux_chain`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.res_chain(5, 0.5, t)
        array([1.        , 0.78314017, 0.64624667, 0.42994366])  
    """
    if D == 0:
        return res_plug(T, t)
    if D == 1:
        return res_comp(T, t)
    h = prop_chain(T, D, t)
    return 1-utils.trapz(h, t)


def conc_chain(J, T, D, t=None, dt=1.0, solver='step'):
    """Indicator concentration inside a chain system.

    See section :ref:`define-chain` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        D (float): dispersion of the system. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    See Also:
        `res_chain`, `prop_chain`, `flux_chain`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.conc_chain(J, 5, 0.5, t)
        array([ 0.        ,  6.59776478, 20.98038139, 30.80370764, 33.53283379])
    """
    if D == 0:
        return conc_plug(J, T, t=t, dt=dt)
    if D == 1:
        return conc_comp(J, T, t=t, dt=dt)

    # TODO: THIS NEEDS DEBUGGING
    # if solver=='diag':
    #     n0 = np.floor(1/D)
    #     Tc, Ec = _chain_ncomp(n0, T)
    #     Ji = np.zeros((n0,len(J)))
    #     Ji[0,:] = J
    #     C = conc_ncomp(Ji, Tc, Ec, t=t, dt=dt).sum(axis=0)
    #     if n0==1/D:
    #         return C
    #     Tc, Ec = _chain_ncomp(n0+1, T)
    #     C += conc_ncomp(Ji, Tc, Ec, t=t, dt=dt).sum(axis=0)
    #     return C/2

    tr = utils.tarray(len(J), t=t, dt=dt)
    r = res_chain(T, D, tr)
    return utils.conv(r, J, t=t, dt=dt, solver=solver)


def flux_chain(J, T, D, t=None, dt=1.0, solver='step'):
    """Indicator flux out of a chain system.

    See section :ref:`define-chain` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        D (float): dispersion of the system. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: Outflux as a 1D array.

    See Also:
        `res_chain`, `prop_chain`, `conc_chain`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.flux_chain(J, 5, 0.5, t)
        array([0.        , 0.36089409, 1.92047375, 2.63639739, 1.99640464])
    """
    if D == 0:
        return flux_plug(J, T, t=t, dt=dt)
    if D == 1:
        return flux_comp(J, T, t=t, dt=dt)

    # TODO: This needs debugging
    # if solver=='diag':
    #     n0 = int(np.floor(1/D))
    #     Tc, Ec = _chain_ncomp(n0, T)
    #     Ji = np.zeros((n0,len(J)))
    #     Ji[0,:] = J
    #     Jo = flux_ncomp(Ji, Tc, Ec, t=t, dt=dt)[n0-1,n0-1,:]
    #     if n0==1/D:
    #         return Jo
    #     Tc, Ec = _chain_ncomp(n0+1, T)
    #     Jo += flux_ncomp(Ji, Tc, Ec, t=t, dt=dt)[n0,n0,:]
    #     return Jo/2

    th = utils.tarray(len(J), t=t, dt=dt)
    h = prop_chain(T, D, th)
    return utils.conv(h, J, t=t, dt=dt, solver=solver)

# Helper function in diag solver for chain model
# def _chain_ncomp(n, T):
#     # Helper function
#     Tarr = np.full(n, T/n)
#     E = np.zeros((n,n))
#     for i in range(n-1):
#         E[i+1,i] = 1
#     E[n-1,n-1] = 1
#     return Tarr, E


# Step

def prop_step(T, D, t):
    """Propagator or transit time distribution of a step system.

    See section :ref:`define-step` for more detail.

    Args:
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the system is a trap.
        D (float): dispersion of the system, or half-width of the step given as a fraction of T. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like): time points where the propagator is calculated, in the same units as T.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    Raises:
        ValueError: if one of the parameters is out of bounds.

    See Also:
        `res_step`, `conc_step`, `flux_step`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.prop_step(5, 0.5, t)
        array([0.03508772, 0.21052632, 0.21052632, 0.21052632])  
    """
    if not isinstance(t, np.ndarray):
        t = np.array(t)
    if T < 0:
        raise ValueError('T must be non-negative')
    if D < 0:
        raise ValueError('D cannot be negative')
    if D > 1:
        raise ValueError('D cannot be larger than 1')
    if T == np.inf:
        return prop_trap(t)
    if D == 0:
        return prop_plug(T, t)
    return utils.dstep(T-D*T, T+D*T, t)


def res_step(T, D, t):
    """Residue function of a step system.

    See section :ref:`define-step` for more detail.

    Args:
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the system is a trap.
        D (float): dispersion of the system, or half-width of the step given as a fraction of T. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like): time points where the residue function is calculated, in the same units as T.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    See Also:
        `prop_step`, `conc_step`, `flux_step`

    Example:
        >>> import dcmri as dc
        >>> t = [0,3,4,6]
        >>> dc.res_step(5, 0.5, t)
        array([1.        , 0.63157895, 0.42105263, 0.        ])  
    """
    h = prop_step(T, D, t)
    return 1-utils.trapz(h, t)


def conc_step(J, T, D, t=None, dt=1.0):
    """Indicator concentration inside a step system.

    See section :ref:`define-step` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        D (float): dispersion of the system, or half-width of the step given as a fraction of T. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    See Also:
        `res_step`, `prop_step`, `flux_step`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.conc_step(J, 5, 0.5, t)
        array([ 0.        ,  6.44736842, 20.19736842, 28.20175439, 21.58625731])
    """
    if D == 0:
        return conc_plug(J, T, t=t, dt=dt)
    t = utils.tarray(len(J), t=t, dt=dt)
    r = res_step(T, D, t)
    return utils.conv(r, J, t)


def flux_step(J, T, D, t=None, dt=1.0):
    """Indicator flux out of a step system.

    See section :ref:`define-step` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        T (float): mean transit time of the system. Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        D (float): dispersion of the system, or half-width of the step given as a fraction of T. Values must be between 0 (no dispersion) and 1 (maximal dispersion).
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: Outflux as a 1D array.

    See Also:
        `res_step`, `prop_step`, `conc_step`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> dc.flux_step(J, 5, 0.5, t)
        array([0.        , 0.45614035, 1.9254386 , 2.91812865, 2.29239766])
    """
    if D == 0:
        return flux_plug(J, T, t=t, dt=dt)
    t = utils.tarray(len(J), t=t, dt=dt)
    h = prop_step(T, D, t)
    return utils.conv(h, J, t)


def flux_pfcomp(J, T, D, t=None, dt=1.0, solver='interp'):
    """Indicator flux out of a serial arrangement of a plug flow 
    system and a compartment.

    See section :ref:`define-pfcomp` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment (mmol/sec).
        T (float): mean transit time of the compartment (sec). Any non-negative value is allowed, including :math:`T=0` and :math:`T=\\infty`, in which case the compartment is a trap.
        D (float): Dispersion of the systemd defined as the ratio of the compartmental mean transit time versus the total mean transit time.
        t (array_like, optional): the time points of the indicator flux J (sec). If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points (sec). This parameter is ignored if t is explicity provided. Defaults to 1.0.
        solver (str, optional): solver for the system, either 'conv' for explicit convolution with a discrete impulse response (slow) or 'interp' for interpolation (fast). Defaults to 'interp'.

    Returns:
        np.ndarrayx: Outflux in mmol/sec
    """
    if D < 0 or D > 1:
        raise ValueError('Dispersion must be in the range [0,1]')
    if D == 0:
        return flux_plug(J, T, t=t, dt=dt, solver=solver)
    if D == 1:
        return flux_comp(J, T, t=t, dt=dt)
    Tc = D*T
    Tp = (1-D)*T
    J = flux_comp(J, Tc, t=t, dt=dt)
    J = flux_plug(J, Tp, t=t, dt=dt, solver=solver)
    return J



# N parameters

# Free


def prop_free(H, t, TT=None, TTmin=0, TTmax=None):
    """Propagator or transit time distribution of a free system.

    See section :ref:`define-free` for more detail.

    Args:
        H (array_like): frequencies of the transit time histogram in each transit time bin. These do not have to be normalized - the function normalizes to unit area by default.
        t (array_like): time points where the propagator is calculated, in the same units as T.
        TT (array_like): boundaries of the transit time histogram bins. The number of elements in this array must be one more than the number of elements in H. If TT is not provided, the boundaries are equally distributed between TTmin and TTmax. Defaults to None.
        TTmin (float): Minimal transit time to be considered. If TT is provided, this argument is ignored. Defaults to 0.
        TTmax (float): Maximal transit time to be considered. If TT is provided, this argument is ignored. Defaults to the maximum of t.

    Returns:
        numpy.ndarray: propagator as a 1D array.

    Raises:
        ValueError: if the array of transit times has the incorrect length.

    See Also:
        `res_free`, `conc_free`, `flux_free`

    Example:
        >>> import dcmri as dc
        >>> t = [0,1,2,3]

        Assume the transit time histogram is provided by two equally sized bins covering the entire time interval, with frequencies 2 and 1, respectively:

        >>> dc.prop_free([2,1], t)
        array([0.33333333, 0.41666667, 0.33333333, 0.16666667]) 

        Assume the transit time has two equally sized bins, but between the values [0.5, 2.5]: 

        >>> dc.prop_free([2,1], t, TTmin=0.5, TTmax=2.5)
        array([0.19047619, 0.47619048, 0.38095238, 0.0952381 ])

        Assume the transit time histogram is provided by two bins in the same range, but with different sizes: one from 0.5 to 1 and the other from 1 to 2.5. The frequencies in the bins are the same as in the previous example:

        >>> dc.prop_free([2,1], t, TT=[0.5,1.0,2.5])
        array([0.33333333, 0.64814815, 0.14814815, 0.07407407]) 
    """
    nTT = len(H)
    if TT is None:
        if TTmax is None:
            TTmax = np.amax(t)
        TT = np.linspace(TTmin, TTmax, nTT+1)
    else:
        if len(TT) != nTT+1:
            msg = 'The array of transit time boundaries needs to have length N+1, '
            msg += '\n with N the size of the transit time distribution H.'
            raise ValueError(msg)
    h = utils.ddist(H, TT, t)
    return h/trapezoid(h, t)


def res_free(H, t, TT=None, TTmin=0, TTmax=None):
    """Residue function of a free system.

    See section :ref:`define-free` for more detail.

    Args:
        H (array_like): frequencies of the transit time histogram in each transit time bin. These do not have to be normalized - the function normalizes to unit area by default.
        t (array_like): time points where the residue function is calculated, in the same units as T.
        TT (array_like): boundaries of the transit time histogram bins. The number of elements in this array must be one more than the number of elements in H. If TT is not provided, the boundaries are equally distributed between TTmin and TTmax. Defaults to None.
        TTmin (float): Minimal transit time to be considered. If TT is provided, this argument is ignored. Defaults to 0.
        TTmax (float): Maximal transit time to be considered. If TT is provided, this argument is ignored. Defaults to the maximum of t.

    Returns:
        numpy.ndarray: residue function as a 1D array.

    Raises:
        ValueError: if the array of transit times has the incorrect length.

    See Also:
        `prop_free`, `conc_free`, `flux_free`

    Example:
        >>> import dcmri as dc
        >>> t = [0,1,2,3]

        Assume the transit time histogram is provided by two equally sized bins covering the entire time interval, with frequencies 2 and 1, respectively:

        >>> dc.res_free([2,1], t)
        array([1.   , 0.625, 0.25 , 0.   ]) 

        Assume the transit time has two equally sized bins, but between the values [0.5, 2.5]: 

        >>> dc.res_free([2,1], t, TTmin=0.5, TTmax=2.5)
        array([1.00000000e+00, 6.66666667e-01, 2.38095238e-01, 2.22044605e-16])

        Assume the transit time histogram is provided by two bins in the same range, but with different sizes: one from 0.5 to 1 and the other from 1 to 2.5. The frequencies in the bins are the same as in the previous example:

        >>> dc.res_free([2,1], t, TT=[0.5,1.0,2.5])
        array([1.00000000e+00, 5.09259259e-01, 1.11111111e-01, 2.22044605e-16])
    """
    h = prop_free(H, t, TT=TT, TTmin=TTmin, TTmax=TTmax)
    r = 1 - utils.trapz(h, t)
    r[r < 0] = 0
    return r


def conc_free(J, H, t=None, dt=1.0, TT=None, TTmin=0, TTmax=None, solver='trap'):
    """Indicator concentration inside a free system.

    See section :ref:`define-free` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        H (array_like): frequencies of the transit time histogram in each transit time bin. These do not have to be normalized - the function normalizes to unit area by default.
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.
        TT (array_like): boundaries of the transit time histogram bins. The number of elements in this array must be one more than the number of elements in H. If TT is not provided, the boundaries are equally distributed between TTmin and TTmax. Defaults to None.
        TTmin (float): Minimal transit time to be considered. If TT is provided, this argument is ignored. Defaults to 0.
        TTmax (float): Maximal transit time to be considered. If TT is provided, this argument is ignored. Defaults to the maximum of t.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    See Also:
        `res_free`, `prop_free`, `flux_free`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]

        Assume the transit time histogram is provided by two equally sized bins covering the entire time interval, with frequencies 2 and 1, respectively:

        >>> dc.conc_free(J, [2,1], t)
        array([ 0.        ,  7.25308642, 29.41358025, 61.41975309, 77.56944444])

        Assume the transit time has two equally sized bins, but between the values [0.5, 2.5]: 

        >>> dc.conc_free(J, [2,1], t, TTmin=0.5, TTmax=2.5)
        array([ 0.        ,  4.75925926, 10.15740741, 11.5       ,  8.10185185])

        Assume the transit time histogram is provided by two bins in the same range, but with different sizes: one from 0.5 to 1 and the other from 1 to 2.5. The frequencies in the bins are the same as in the previous example:

        >>> dc.conc_free(J, [2,1], t, TT=[0.5,1.0,2.5])
        array([ 0.        ,  4.64814815,  9.58101852, 10.75      ,  7.5462963 ])

        If the time array is not provided, the function assumes uniform time resolution with time step = 1:

        >>> dc.conc_free(J, [2,1], TT=[0.5,1.0,2.5])
        array([0.        , 1.17777778, 2.45555556, 3.25277778, 3.075     ])

        If the time step is different from 1, it needs to be provided explicitly:

        >>> dc.conc_free(J, [2,1], dt=2.0, TT=[0.5,1.0,2.5])
        array([0.        , 2.05555556, 3.87037037, 4.76388889, 4.14351852])
    """
    u = utils.tarray(len(J), t=t, dt=dt)
    r = res_free(H, u, TT=TT, TTmin=TTmin, TTmax=TTmax)
    return utils.conv(r, J, t=t, dt=dt, solver=solver)


def flux_free(J, H, t=None, dt=1.0, TT=None, TTmin=0, TTmax=None):
    """Indicator flux out of a free system.

    See section :ref:`define-free` for more detail.

    Args:
        J (array_like): the indicator flux entering the system.
        H (array_like): frequencies of the transit time histogram in each 
          transit time bin. These do not have to be normalized - the function 
          normalizes to unit area by default.
        t (array_like, optional): the time points of the indicator flux J, in 
          the same units as T. If t=None, the time points are assumed to be 
          uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly 
          spaced time points, in the same units as T. This parameter is 
          ignored if t is explicity provided. Defaults to 1.0.
        TT (array_like): boundaries of the transit time histogram bins. The 
          number of elements in this array must be one more than the number 
          of elements in H. If TT is not provided, the boundaries are equally 
          distributed between TTmin and TTmax. Defaults to None.
        TTmin (float): Minimal transit time to be considered. If TT is 
          provided, this argument is ignored. Defaults to 0.
        TTmax (float): Maximal transit time to be considered. If TT is 
          provided, this argument is ignored. Defaults to the maximum of t.

    Returns:
        numpy.ndarray: Outflux as a 1D array.

    See Also:
        `res_free`, `prop_free`, `conc_free`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]

        Assume the transit time histogram is provided by two equally sized bins covering the entire time interval, with frequencies 2 and 1, respectively:

        >>> dc.flux_free(J, [2,1], t)
        array([0.        , 0.11111111, 0.48148148, 1.25102881, 2.60802469])

        Assume the transit time has two equally sized bins, but between the values [0.5, 2.5]: 

        >>> dc.flux_free(J, [2,1], t, TTmin=0.5, TTmax=2.5)
        array([0.        , 1.34074074, 2.69259259, 3.        , 2.1       ])

        Assume the transit time histogram is provided by two bins in the same range, but with different sizes: one from 0.5 to 1 and the other from 1 to 2.5. The frequencies in the bins are the same as in the previous example:

        >>> dc.flux_free(J, [2,1], t, TT=[0.5,1.0,2.5])
        array([0.        , 1.40185185, 2.71898148, 3.        , 2.09166667])

        If the time array is not provided, the function assumes uniform time resolution with time step = 1:

        >>> dc.flux_free(J, [2,1], TT=[0.5,1.0,2.5])
        array([0.        , 0.7       , 1.8       , 2.60555556, 2.69444444])

        If the time step is different from 1, it needs to be provided explicitly:

        >>> dc.flux_free(J, [2,1], dt=2.0, TT=[0.5,1.0,2.5])
        array([0.        , 1.10185185, 2.24074074, 2.86574074, 2.59722222])
    """
    u = utils.tarray(len(J), t=t, dt=dt)
    h = prop_free(H, u, TT=TT, TTmin=TTmin, TTmax=TTmax)
    return utils.conv(h, J, t=t, dt=dt)


# N compartments

# TODO: check that the sum of E's for a compartment = 1. Is it true that it can be something else? No sure..
# Maybe trapping and creation needs to be modelled with extra constants?
# The amounts trapped or created are not proportional to the amount inside.
def _K_ncomp(T, E):
    # dC/dt = J - KC
    if not isinstance(T, np.ndarray):
        T = np.array(T)
    if not isinstance(E, np.ndarray):
        E = np.array(E)
    # Helper function
    if np.amin(E) < 0:
        raise ValueError('Extraction fractions cannot be negative.')
    n = T.size
    K = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            if j == i:
                # Diagonal elements
                # sum of column i
                Ei = np.sum(E[:, i])
                if Ei == 0:
                    K[i, i] = 0
                else:
                    K[i, i] = Ei/T[i]
            else:
                # Off-diagonal elements
                if E[j, i] == 0:
                    K[j, i] = 0
                else:
                    K[j, i] = -E[j, i]/T[i]
    return K


def _J_ncomp(C, T, E):
    K = _K_ncomp(T, E)
    nc, nt = C.shape[0], C.shape[1]
    J = np.zeros((nc, nc, nt))
    for i in range(C.shape[0]):
        for j in range(C.shape[0]):
            if i == j:
                # Flux to outside
                Kii = np.sum(K[:, i])
                J[i, i, :] = Kii*C[i, :]
            else:
                # Flux to other compartments
                J[j, i, :] = -K[j, i]*C[i, :]
    return J

# Helper function


def conc_ncomp_prop(J, T, E, t=None, dt=1.0, dt_prop=None):
    t = utils.tarray(len(J[0, :]), t=t, dt=dt)
    K = _K_ncomp(T, E)
    nt, nc = len(t), len(T)
    C = np.zeros((nc, nt))
    Kmax = K.diagonal().max()
    for k in range(nt-1):
        # Dk/nk <= 1/Kmax
        # Dk*Kmax <= nk
        Dk = t[k+1]-t[k]
        SJk = (J[:, k+1]-J[:, k])/Dk
        nk = int(np.ceil(Dk*Kmax))
        if dt_prop is not None:
            nk = np.amax([int(np.ceil(Dk/dt_prop)), nk])
        dk = Dk/nk
        Jk = J[:, k]
        Ck = C[:, k]
        for _ in range(nk):
            Jk_next = Jk + dk*SJk
            Ck_in = dk*(Jk+Jk_next)/2
            Ck = Ck + Ck_in - dk*np.matmul(K, Ck)
            Jk = Jk_next
        C[:, k+1] = Ck
    return C

# Helper function


def conc_ncomp_diag(J, T, E, t=None, dt=1.0):
    t = utils.tarray(J.shape[1], t=t, dt=dt)
    # Calculate system matrix, eigenvalues and eigenvectors
    K = _K_ncomp(T, E)
    # From here, create generic function that solves n-comp system
    K, Q = np.linalg.eig(K)
    Qi = np.linalg.inv(Q)
    # Initialize concentration-time array
    nc, nt = len(T), len(t)
    C = np.zeros((nc, nt), dtype=K.dtype)
    Ei = np.zeros((nc, nt), dtype=K.dtype)
    # Loop over the inlets
    for i in range(nc):
        # Loop over the eigenvalues
        for d in range(nc):
            # Calculate elements of diagonal matrix
            Ei[d, :] = conc_comp(J[i, :], 1/K[d], t)
            # Right-multiply with inverse eigenvector matrix
            Ei[d, :] *= Qi[d, i]
        # Left-multiply with eigenvector matrix
        C += np.matmul(Q, Ei)
    # Absolute value because K can be complex
    return np.absolute(C)


def conc_ncomp(J, T, E, t=None, dt=1.0, solver='diag', dt_prop=None):
    """Concentration in a linear and stationary n-compartment system.

    See section :ref:`define-ncomp` for more detail.

    Args:
        J (array_like): the indicator flux entering the system, as a 
          rectangular 2D array with dimensions *(n,k)*, where *n* is the 
          number of compartments and *k* is the number of time points in *J*. 
        T (array_like): n-element array with mean transit times of each 
          compartment.
        E (array_like): dimensionless and square *n x n* matrix. An 
          off-diagonal element *E[j,i]* is the extraction fraction from 
          compartment *i* to compartment *j*. A diagonal element *E[i,i]* is 
          the extraction fraction from compartment *i* to the outside. 
        t (array_like, optional): the time points of the indicator flux *J*, 
          in the same units as *T*. If *t* is not provided, the time points 
          are assumed to be uniformly spaced with spacing *dt*. Defaults to 
          None.
        dt (float, optional): spacing between time points for uniformly 
          spaced time points, in the same units as *T*. This parameter is 
          ignored if t is explicity provided. Defaults to 1.0.
        solver (str, optional): A string specifying the numerical method for 
          solving the system. Two options are available: with 
          `solver = 'diag'` the system is solved by diagonalising the system 
          matrix, with `solver = 'prop'` the system is solved by forward 
          propagation. The default is `'diag'`.
        dt_prop (float, optional): internal time resolution for the forward 
          propagation when `solver = 'prop'`. This must be in the same units 
          as *T*. If *dt_prop* is not provided, it defaults to the sampling 
          interval, or the smallest time step needed for stable results 
          (whichever is smaller). This argument is ignored when 
          `solver = 'diag'`. Defaults to None. 

    Returns:
        numpy.ndarray: Concentration in each compartment, and at each time point, as a 2D array with dimensions *(n,k)*, where *n* is the number of compartments and *k* is the number of time points in *J*. 

    See Also:
        `res_ncomp`, `prop_ncomp`, `flux_ncomp`

    Note:
        The default solver `'diag'` should be most accurate and fastest, but currently does not allow for compartments that trap the tracer. It relies on matrix diagonalization which may be more problematic in very large systems, such as spatiotemporal models. The alternative solver `'prop'` is simple and robust and is a suitable alternative in such cases. It is slower and less accurate, though the accuracy can be improved at the cost of larger computation times by setting a smaller *dt_prop*. 

    Example:
        >>> import numpy as np
        >>> import dcmri as dc

        Consider a measurement with 10 time points from 0 to 20s, and a 2-compartment system with a constant influx in each compartment. The influx in compartment 1 is twice a large than in compartment 0:

        >>> t = np.linspace(0, 20, 10)
        >>> J = np.zeros((2, t.size))
        >>> J[0,:] = 1
        >>> J[1,:] = 2

        The transit times are 6s for compartment 0 and 12s for compartment 1. 

        >>> T = [6,12]

        The extraction fraction from compartment 0 to compartment 1 is 0.3 and the extraction fraction from 1 to 0 is 0.8. These are the off-diagonal elements of *E*. No indicator is trapped or created inside the system so the extraction fractions for each compartment must add up to 1. The extraction fractions to the outside are therefore 0.7 and 0.2 for compartment 0 and 1, respectively. These are the diagonal elements of *E*:

        >>> E = [
        ...  [0.7, 0.8],
        ...  [0.3, 0.2]]

        Calculate the concentrations in both compartments of the system:

        >>> C = dc.conc_ncomp(J, T, E, t)

        The concentrations in compartment 0 are:

        >>> C[0,:]
        array([ 0.        ,  2.13668993,  4.09491578,  5.87276879,  7.47633644,
        8.91605167, 10.20442515, 11.3546615 , 12.37983769, 13.29243667])

        The concentrations in compartment 1 are:

        >>> C[1,:]
        array([ 0.        ,  4.170364  ,  7.84318653, 11.0842876 , 13.94862323, 
        16.48272778, 18.72645063, 20.71421877, 22.47597717, 24.03790679])

        Solving by forward propagation produces a different result because of the relatively low time resolution:

        >>> C = dc.conc_ncomp(J, T, E, t, solver='prop')
        >>> C[1,:]
        array([ 0.        ,  4.44444444,  8.3127572 , 11.69333943, 14.65551209,
        17.25550803, 19.54012974, 21.54905722, 23.31636527, 24.87156916])

        But the difference can be made arbitrarily small by choosing a smaller *dt_prop* (at the cost of some computation time). In this case the results become very close with `dt_prop = 0.01`:

        >>> C = dc.conc_ncomp(J, T, E, t, solver='prop', dt_prop=0.01)
        >>> C[1,:]
        array([ 0.        ,  4.17147736,  7.84511918, 11.08681805, 13.95158088,
        16.48597905, 18.72988986, 20.71776196, 22.47955758, 24.04147164])
    """
    if solver == 'prop':
        return conc_ncomp_prop(J, T, E, t=t, dt=dt, dt_prop=dt_prop)
    if solver == 'diag':
        if len(T) == 2:
            return _conc_2comp(J, T, E, t=t, dt=dt)
        return conc_ncomp_diag(J, T, E, t=t, dt=dt)


def flux_ncomp(J, T, E, t=None, dt=1.0, solver='diag', dt_prop=None):
    """Outfluxes out of a linear and stationary n-compartment system.

    See section :ref:`define-ncomp` for more detail.

    Args:
        J (array_like): the indicator flux entering the system, as a rectangular 2D array with dimensions *(n,k)*, where *n* is the number of compartments and *k* is the number of time points in *J*.
        T (array_like): n-element array with mean transit times of each compartment.
        E (array_like): dimensionless and square *n x n* matrix. An off-diagonal element *E[j,i]* is the extraction fraction from compartment *i* to compartment *j*. A diagonal element *E[i,i]* is the extraction fraction from compartment *i* to the outside. 
        t (array_like, optional): the time points of the indicator flux *J*, in the same units as *T*. If *t* is not provided, the time points are assumed to be uniformly spaced with spacing *dt*. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as *T*. This parameter is ignored if t is explicity provided. Defaults to 1.0.
        solver (str, optional): A string specifying the numerical method for solving the system. Two options are available: with `solver = 'diag'` the system is solved by diagonalising the system matrix, with `solver = 'prop'` the system is solved by forward propagation. The default is `'diag'`.
        dt_prop (float, optional): internal time resolution for the forward propagation when `solver = 'prop'`. This must be in the same units as *T*. If *dt_prop* is not provided, it defaults to the sampling interval, or the smallest time step needed for stable results (whichever is smaller). This argument is ignored when `solver = 'diag'`. Defaults to None. 

    Returns:
        numpy.ndarray: Outflux out of each compartment, and at each time point, as a 3D array with dimensions *(n,n,k)*, where *n* is the number of compartments and *k* is the number of time points in *J*. Encoding of the first two indices is the same as for *E*: *J[j,i,:]* is the flux from compartment *i* to *j*, and *J[i,i,:]* is the flux from *i* directly to the outside.

    See Also:
        `res_ncomp`, `prop_ncomp`, `conc_ncomp`

    Example:
        >>> import numpy as np
        >>> import dcmri as dc

        Consider a measurement with 10 time points from 0 to 20s, and a 2-compartment system with a constant influx in each compartment. The influx in compartment 1 is twice a large than in compartment 0:

        >>> t = np.linspace(0, 20, 10)
        >>> J = np.zeros((2, t.size))
        >>> J[0,:] = 1
        >>> J[1,:] = 2

        The transit times are 6s for compartment 0 and 12s for compartment 1. 

        >>> T = [6,12]

        The extraction fraction from compartment 0 to compartment 1 is 0.3 and the extraction fraction from 1 to 0 is 0.8. These are the off-diagonal elements of *E*. No indicator is trapped or created inside the system so the extraction fractions for each compartment must add up to 1. The extraction fractions to the outside are therefore 0.7 and 0.2 for compartment 0 and 1, respectively. These are the diagonal elements of *E*:

        >>> E = [
        ...  [0.7, 0.8],
        ...  [0.3, 0.2]]

        Calculate the outflux out of both compartments:

        >>> J = dc.flux_ncomp(J, T, E, t)

        The indicator flux out of compartment 0 to the outside is:

        >>> J[0,0,:]
        array([0.        , 0.25925926, 0.49931413, 0.71731951, 0.91301198,
        1.0874238 , 1.24217685, 1.37910125, 1.50003511, 1.60672472])

        The indicator flux from compartment 1 to 0 is:

        >>> J[1,0,:]
        array([0.        , 0.11111111, 0.21399177, 0.30742265, 0.39129085,
        0.46603877, 0.53236151, 0.59104339, 0.64287219, 0.68859631])
    """
    C = conc_ncomp(J, T, E, t=t, dt=dt, solver=solver, dt_prop=dt_prop)
    return _J_ncomp(C, T, E)


def res_ncomp(T, E, t):
    """Residue function of an n-compartment system.

    See section :ref:`define-ncomp` for more detail.

    Args:
        T (array_like): n-element array with mean transit times of each compartment.
        E (array_like): dimensionless and square *n x n* matrix. An off-diagonal element *E[j,i]* is the extraction fraction from compartment *i* to compartment *j*. A diagonal element *E[i,i]* is the extraction fraction from compartment *i* to the outside. 
        t (array_like): the time points of the indicator flux *J*, in the same units as *T*. If *t* is not provided, the time points are assumed to be uniformly spaced with spacing *dt*. Defaults to None.

    Returns:
        numpy.ndarray: Residue in each compartment, and at each time point, as a 3D array with dimensions *(n,n,k)*, where *n* is the number of compartments and *k* is the number of time points in *t*. Encoding of the first two indices is as follows: *R[j,i,:]* is the residue in compartment *i* from an impulse injected into compartment *J*.

    See Also:
        `flux_ncomp`, `prop_ncomp`, `conc_ncomp`

    Example:
        >>> import numpy as np
        >>> import dcmri as dc

        Consider a measurement with 10 time points from 0 to 20s, and a 2-compartment system defined by *T* and *E* as follows:

        >>> t = np.linspace(0, 20, 10)
        >>> T = [20,2]
        >>> E = [[0.7, 0.9], [0.3, 0.1]]

        Calculate the residue in both compartments:

        >>> R = dc.res_ncomp(T, E, t)

        Given an impulse in compartment 1 at time *t=0*, the residue in compartment 1 is strictly decreasing: 

        >>> R[1,1,:]
        array([1.        , 0.337098  , 0.12441734, 0.05534255, 0.03213718,
        0.02364203, 0.01991879, 0.01779349, 0.01624864, 0.01495455])

        Given an impulse in compartment 1 at time *t=0*, the residue in compartment 0 is zero initially and peaks at a later time:

        >>> R[1,0,:]
        array([0.        , 0.01895809, 0.02356375, 0.02370372, 0.02252098,
        0.02100968, 0.01947964, 0.01802307, 0.01666336, 0.0154024 ])
    """
    if len(T) == 2:
        return _res_2comp(T, E, t)
    # Calculate system matrix, eigenvalues and eigenvectors
    K = _K_ncomp(T, E)
    K, Q = np.linalg.eig(K)
    Qi = np.linalg.inv(Q)
    # Initialize concentration-time array
    nc, nt = len(T), len(t)
    R = np.zeros((nc, nc, nt), dtype=K.dtype)
    Ei = np.zeros((nc, nt), dtype=K.dtype)
    # Loop over the inlets
    for i in range(nc):
        # Loop over the eigenvalues
        for d in range(nc):
            # Calculate elements of diagonal matrix
            Ei[d, :] = np.exp(-t*K[d])
            # Right-multiply with inverse eigenvector matrix
            Ei[d, :] *= Qi[d, i]
        # Left-multiply with eigenvector matrix
        R[i, :, :] = np.matmul(Q, Ei)
    # Absolute because K can be complex
    return np.absolute(R)


def prop_ncomp(T, E, t):
    """Propagator of an n-compartment system.

    See section :ref:`define-ncomp` for more detail.

    Args:
        T (array_like): n-element array with mean transit times of each compartment.
        E (array_like): dimensionless and square *n x n* matrix. An off-diagonal element *E[j,i]* is the extraction fraction from compartment *i* to compartment *j*. A diagonal element *E[i,i]* is the extraction fraction from compartment *i* to the outside. 
        t (array_like): the time points of the indicator flux *J*, in the same units as *T*. If *t* is not provided, the time points are assumed to be uniformly spaced with spacing *dt*. Defaults to None.

    Returns:
        numpy.ndarray: Propagator for each arrow as a 4D array with dimensions *(n,n,n,k)*, where *n* is the number of compartments and *k* is the number of time points in *t*. Encoding of the first indices is as follows: *H[i,k,j,:]* is the propagator from the inlet at compartment *i* to the outlet from *j* to *k*. The diagonal element *H[i,j,j,:]* is the propagator from the inlet at *i* to the outlet of *j* to the environment.

    See Also:
        `flux_ncomp`, `res_ncomp`, `conc_ncomp`

    Example:
        >>> import numpy as np
        >>> import dcmri as dc

        Consider a measurement with 10 time points from 0 to 20s, and a 2-compartment system defined by *T* and *E* as follows:

        >>> t = np.linspace(0, 20, 10)
        >>> T = [20,2]
        >>> E = [[0.7, 0.9], [0.3, 0.1]]

        Calculate the propagator for the system:

        >>> H = dc.prop_ncomp(T, E, t)

        The propagator from the inlet at 1 (first index = 1) to the outlet of compartment 0 is: 

        >>> H[1,0,0,:]
        array([0.        , 0.019906  , 0.02474194, 0.0248889 , 0.02364703,
        0.02206017, 0.02045362, 0.01892422, 0.01749653, 0.01617252])

        The propagator from the inlet at 1 (first index = 1) to the outlet from 0 to 1 is:

        >>> H[1,1,0,:]
        array([0.        , 0.00853114, 0.01060369, 0.01066667, 0.01013444,
        0.00945436, 0.00876584, 0.00811038, 0.00749851, 0.00693108])
    """
    R = res_ncomp(T, E, t)
    nc, nt = len(T), len(t)
    H = np.zeros((nc, nc, nc, nt))
    for i in range(nc):
        H[i, :, :, :] = _J_ncomp(R[i, :, :], T, E)
    return H


# 2 compartments (analytical)

def _K_2comp(T, E):
    K = _K_ncomp(T, E)
    if np.array_equal(K, np.identity(2)):
        return K, np.ones(2), K
    # Calculate the eigenvalues Ke
    D = math.sqrt((K[0, 0]-K[1, 1])**2 + 4*K[0, 1]*K[1, 0])
    Ke = [0.5*(K[0, 0]+K[1, 1]+D),
          0.5*(K[0, 0]+K[1, 1]-D)]
    # Build the matrix of eigenvectors (one per column)
    Q = np.array([
        [K[1, 1]-Ke[0], -K[0, 1]],
        [-K[1, 0], K[0, 0]-Ke[1]],
    ])
    # Build the inverse of the eigenvector matrix
    Qi = np.array([
        [K[0, 0]-Ke[1], K[0, 1]],
        [K[1, 0], K[1, 1]-Ke[0]]
    ])
    N = (K[0, 0]-Ke[1])*(K[1, 1]-Ke[0]) - K[0, 1]*K[1, 0]
    Qi /= N
    return Q, Ke, Qi


def _conc_2comp(J, T, E, t=None, dt=1.0):
    # Check input parameters
    if np.amin(T) <= 0:
        raise ValueError('T must be strictly positive.')
    if not isinstance(J, np.ndarray):
        J = np.array(J)
    if not isinstance(T, np.ndarray):
        T = np.array(T)
    if not isinstance(E, np.ndarray):
        E = np.array(E)
    # Build the system matrix K
    Q, K, Qi = _K_2comp(T, E)
    # Initialize concentration-time array
    t = utils.tarray(len(J[0, :]), t=t, dt=dt)
    C = np.zeros((2, len(t)))
    Ei = np.empty((2, len(t)))
    # Loop over the inlets
    for i in [0, 1]:
        # Loop over th eigenvalues
        for d in [0, 1]:
            # Calculate elements of diagonal matrix
            Ei[d, :] = conc_comp(J[i, :], 1/K[d], t)
            # Right-multiply with inverse eigenvector matrix
            Ei[d, :] *= Qi[d, i]
        # Left-multiply with eigenvector matrix
        C += np.matmul(Q, Ei)
    return C


def _res_2comp(T, E, t):
    # Calculate system matrix, eigenvalues and eigenvectors
    Q, K, Qi = _K_2comp(T, E)
    # Initialize concentration-time array
    nc, nt = len(T), len(t)
    R = np.zeros((nc, nc, nt))
    Ei = np.empty((nc, nt))
    # Loop over the inlets
    for i in range(nc):
        # Loop over the eigenvalues
        for d in range(nc):
            # Calculate elements of diagonal matrix
            Ei[d, :] = np.exp(-t*K[d])
            # Right-multiply with inverse eigenvector matrix
            Ei[d, :] *= Qi[d, i]
        # Left-multiply with eigenvector matrix
        R[i, :, :] = np.matmul(Q, Ei)
    return R


# Non-stationary compartment


def conc_nscomp(J, T, t=None, dt=1.0):
    """Indicator concentration inside a non-stationary compartment.

    See section :ref:`define-nscomp` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment.
        T (array_like): array with the mean transit time as a function of time, with the same length as *J*. Only finite and strictly positive values are allowed.
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    Raises:
        ValueError: if one of the parameters is out of bounds.

    See Also:
        `flux_nscomp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> T = [1,2,3,4,5]
        >>> dc.conc_nscomp(J, T, t)
        array([ 0.        ,  3.09885687,  7.96130923, 11.53123615, 10.28639254])
    """
    if np.isscalar(T):
        raise ValueError('T must be an array of the same length as J.')
    if len(T) != len(J):
        raise ValueError('T and J must have the same length.')
    if np.amin(T) <= 0:
        raise ValueError('T must be strictly positive.')
    t = utils.tarray(len(J), t=t, dt=dt)
    n = len(t)
    C = np.zeros(n)
    for k in range(n-1):
        Dk = t[k+1]-t[k]
        Tk = (T[k]+T[k+1])/2
        Fk = Dk/Tk
        if Fk <= 1:
            Jk = (J[k]+J[k+1])/2
            C[k+1] = C[k] + Dk*Jk - Fk*C[k]
        else:
            nk = int(np.ceil(Dk/np.min(T[k:k+2])))
            STk = (T[k+1]-T[k])/Dk
            SJk = (J[k+1]-J[k])/Dk
            Jk = J[k]
            Tk = T[k]
            Ck = C[k]
            dk = Dk/nk
            for _ in range(nk):
                Jk_next = Jk + dk*SJk
                Tk_next = Tk + dk*STk
                Jk_curr = (Jk+Jk_next)/2
                Tk_curr = (Tk+Tk_next)/2
                Ck = Ck + dk*Jk_curr - dk*Ck/Tk_curr
                Jk = Jk_next
                Tk = Tk_next
            C[k+1] = Ck
    return C


def flux_nscomp(J, T, t=None, dt=1.0):
    """Indicator flux out of a non-stationary compartment.

    See section :ref:`define-nscomp` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment.
        T (array_like): array with the mean transit time as a function of time, with the same length as *J*. Only finite and strictly positive values are allowed.
        t (array_like, optional): the time points of the indicator flux J, in the same units as T. If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points, in the same units as T. This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Returns:
        numpy.ndarray: outflux as a 1D array.

    See Also:
        `conc_nscomp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> T = [1,2,3,4,5]
        >>> dc.flux_nscomp(J, T, t)
        array([0.        , 1.54942844, 2.65376974, 2.88280904, 2.05727851])
    """
    C = conc_nscomp(J, T, t=t, dt=dt)
    return C/T

# TODO: Defaults for solver to None - everywhere




# Michaelis-Menten compartment

def _mmcomp_solve(J, Vmax, Km, t):
    # Schnell-Mendoza
    n = len(t)
    C = np.zeros(n)
    for k in range(n-1):
        Dk = t[k+1]-t[k]
        Jk = (J[k]+J[k+1])/2
        u = (C[k]/Km) * np.exp((C[k]-Vmax*Dk)/Km)
        C[k+1] = Jk*Dk + Km*np.real(lambertw(u))
    return C


def _mmcomp_prop(J, Vmax, Km, t):
    n = len(t)
    C = np.zeros(n)
    for k in range(n-1):
        Dk = t[k+1]-t[k]
        SJk = (J[k+1]-J[k])/Dk
        Jk = J[k]
        Ck = C[k]
        Tk = (Km+Ck)/Vmax
        nk = int(np.ceil(Dk/Tk))
        dk = Dk/nk
        for _ in range(nk):
            Jk_next = Jk + dk*SJk
            Jk_curr = (Jk+Jk_next)/2
            Ck = Ck + dk*Jk_curr - dk*Ck*Vmax/(Km+Ck)
            Jk = Jk_next
            Ck = np.amax([Ck, 0])
        C[k+1] = Ck
    return C


def conc_mmcomp(J, Vmax, Km, t=None, dt=1.0, solver='SM'):
    """Indicator concentration inside a Michaelis-Menten compartment.

    See section :ref:`define-mmcomp` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment.
        Vmax (float): Limiting rate in the same units as J. Must be 
          non-negative.
        Km (float): Michaelis-Menten constant in units of concentration (or 
          flux x time). Must be non-negative.
        t (array_like, optional): the time points of the indicator flux J, in 
          the same units as Km/Vmax. If t=None, the time points are assumed 
          to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced 
          time points, in the same units as Km/Vmax. This parameter is ignored 
          if t is explicity provided. Defaults to 1.0.
        solver (str, optional): choose which solver to use. The options are 
          'SM' for the Schnell and Mendoza solution or 'prop' for a numerical 
          solution by forward propagation. Defaults to 'SM'.

    Returns:
        numpy.ndarray: Concentration as a 1D array.

    Raises:
        ValueError: if one of the parameters is out of bounds.

    See Also:
        `flux_mmcomp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> Vmax, Km = 1, 12
        >>> dc.conc_mmcomp(J, Vmax, Km, t)
        array([  0.        ,   7.5       ,  29.26723718,  64.27756059,
        114.97656637])
    """
    if Vmax < 0:
        raise ValueError('Vmax must be non-negative.')
    if Km < 0:
        raise ValueError('Km must be non-negative.')
    t = utils.tarray(len(J), t=t, dt=dt)
    if solver == 'SM':
        return _mmcomp_solve(J, Vmax, Km, t)
    if solver == 'prop':
        return _mmcomp_prop(J, Vmax, Km, t)


def flux_mmcomp(J, Vmax, Km, t=None, solver='SM', dt=1.0):
    """Indicator flux out of a Michaelis-Menten compartment.

    See section :ref:`define-mmcomp` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment.
        Vmax (float): Limiting rate in the same units as J. Must be 
          non-negative.
        Km (float): Michaelis-Menten constant in units of concentration (or 
          flux x time). Must be non-negative.
        t (array_like, optional): the time points of the indicator flux J, in 
          the same units as Km/Vmax. If t=None, the time points are assumed to 
          be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced 
          time points, in the same units as Km/Vmax. This parameter is ignored 
          if t is explicity provided. Defaults to 1.0.
        solver (str, optional): choose which solver to use. The options are 
          'SM' for the Schnell and Mendoza solution, 
          or 'prop' for a numerical solution by forward propagation. 
          Defaults to 'SM'.

    Returns:
        numpy.ndarray: Outflux as a 1D array.

    Raises:
        ValueError: if one of the parameters is out of bounds.

    See Also:
        `conc_mmcomp`

    Example:
        >>> import dcmri as dc
        >>> t = [0,5,15,30,60]
        >>> J = [1,2,3,3,2]
        >>> Vmax, Km = 1, 12
        >>> dc.flux_mmcomp(J, Vmax, Km, t)
        array([0.        , 0.38461538, 0.70921242, 0.84267981, 0.90549437])
    """
    C = conc_mmcomp(J, Vmax, Km, t=t, solver=solver, dt=dt)
    return C*Vmax/(Km+C)


# Two-compartment exchange

def conc_2cxm(J, T, E, t=None, dt=1.0) -> np.ndarray:
    """Indicator flux out of a 2-compartment exchange model.

    See section :ref:`define-2comp` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment (mmol/sec).
        T (array-like): 2-element array with mean transit times of plasma and extravascular compartment. Mean transit times can take any value, including 0 and inf. Negative values are unphysical but will only trigger an error if no solution exists.
        E (float): Extraction fraction out of the plasma compartment. E is a value between 0 and 1, and boundary values E=0 and E=1 are correctly handled. Values outside that range are unphysical but will only trigger an error if no solution exists.        
        t (array_like, optional): the time points of the indicator flux J (sec). If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points (sec). This parameter is ignored if t is explicity provided. Defaults to 1.0.

    Raises:
        ValueError: if no real solution exists because of unphysical parameter values (usually E<0).

    Returns:
        numpy.ndarray: Concentration in each compartment, and at each time point, as a 2D array with dimensions *(2,k)*, where 2 is the number of compartments and *k* is the number of time points in *J*. 
    """
    # T = [ Tp, Te]

    # Definition
    # ----------
    # vp cp' = Fpca - Fpcp + PSci - PScp
    # vi ci' = PScp - PSci
    #
    # vp, vi, Fp, PS


    # C-form
    # ------
    # Cp' = Fpca - (Fp/vp)Cp + (PS/vi)Ci - (PS/vp)Cp
    # Ci' = (PS/vp)Cp - (PS/vi)Ci
    #
    # Cp' = Ja - Cp/Tp + Ci/Ti
    # Ci' = Cp*E/Tp - Ci/Ti
    #
    # E, Tp, Ti
    #
    # Cp        ca       1/Tp  -1/Ti      Cp
    #     = Fp      - 
    # Ci         0      -E/Tp   1/Ti      Ci


    # c-form
    # ------
    # cp' = (Fp/vp)ca - (Fp/vp)cp + (PS/vp)ci - (PS/vp)cp
    # ci' = (PS/vi)cp - (PS/vi)ci   
    # 
    # cp' = Ja - cp/Tp + ci*E/Tp 
    # ci' = cp/Ti - ci/Ti 
    #
    # E, Tp, Ti

    #
    # cp           ca       1/Tp  -E/Tp      cp
    #     = Fp/vp      - 
    # ci            0      -1/Ti   1/Ti      ci

    if E == 0:
        Cp = conc_comp(J, T[0], t=t, dt=dt)
        Ce = np.zeros(len(J))
        return np.stack((Cp, Ce))

    if E == 1:
        # D
        # = sqrt( (Kp-Ke)**2 + 4 E Kp Ke  )
        # = sqrt( (Kp+Ke)**2 -4KeKp + 4 E Kp Ke  )
        # = sqrt( (Kp+Ke)**2 - 4(1-E)KeKp)
        # D(x) = sqrt( (Kp+Ke)**2 - 4 x KeKp)
        # D(0) = Kp+Ke
        # D'(x) = 0.5 ( (Kp+Ke)**2 - 4 x KeKp)**(-0.5) (-4 KeKp)
        # D'(0) = -2 KeKp/(Kp+Ke)
        # D = Kp+Ke -2 (1-E) KeKp/(Kp+Ke)

        # KT = Kp + Ke
        # Kpos = Kp + Ke
        # Kneg = (1-E) KeKp/(Kp+Ke)

        # Jpos
        # = utils.expconv(J, 1/Kpos, t=t, dt=dt)
        # Jneg
        # = Kneg exp(-tKneg) * J

        # Eneg
        # = (Kp+Ke - (1-E)Kp) / (Kp+Ke - (1-E) KeKp/(Kp+Ke))

        # 1 - Eneg
        # = [Kp+Ke - (1-E) KeKp/(Kp+Ke) - (Kp+Ke - (1-E)Kp)] / (Kp+Ke - (1-E) KeKp/(Kp+Ke))
        # = [(1-E)Kp - (1-E) KeKp/(Kp+Ke)] / (Kp+Ke - (1-E) KeKp/(Kp+Ke))
        # = (1-E) [Kp - KeKp/(Kp+Ke)] / (Kp+Ke - (1-E) KeKp/(Kp+Ke))

        # 1- Eneg = Epos
        # approx  [Kp - KeKp/(Kp+Ke)] (1-E) / (Kp+Ke)
        # (1-E) [Kp - KeKp/(Kp+Ke)] / (Kp+Ke)
        # (1-E) Rpos

        # Cp
        # = [ Epos*Jpos + Eneg*Jneg ] (1/Kp) / (1-E)
        # = [ Rpos*Jpos + (KeKp/(Kp+Ke)) exp(-tKneg) * J  ] (1/Kp)
        # = [ Rpos*Jpos + (KeKp/(Kp+Ke)) * J  ] (1/Kp)
        # = [ Jpos [Kp - KeKp/(Kp+Ke)] / (Kp+Ke) + (KeKp/(Kp+Ke)) * J  ] (1/Kp)
        # = [ Jpos [Kp - KeKp/(Kp+Ke)]  + KeKp * J  ] (1/Kp)  / (Kp+Ke)
        # Ce
        # = [(Kneg exp(-tKneg) * J*Kpos - Jpos*Kneg) / (Kpos - Kneg)] (1/Ke) E / (1-E)
        # = [Kpos exp(-tKneg) * J - Jpos) / (Kpos - Kneg)] Kneg (1/Ke) E / (1-E)
        # = [Kpos exp(-tKneg) * J - Jpos) / (Kpos - Kneg)] KeKp/(Kp+Ke) (1/Ke)
        # = [(Ke + Kp) exp(-tKneg) * J - Jpos) / (Ke + Kp)] KeKp/(Kp+Ke) (1/Ke)
        # = [(Ke + Kp) * J - Jpos) / (Ke + Kp)] KeKp/(Kp+Ke) (1/Ke)

        # Kp, Ke = 1/T[0], 1/T[1]
        # Kpos = Kp + Ke
        # Jpos = utils.expconv(J, 1/Kpos, t=t, dt=dt)

        # Jint = conc_trap(J, t=t, dt=dt)

        # K = Ke*Kp/(Kp+Ke)

        # Cp = ( Jpos*(Kp - K)  + Ke*Kp * Jint  ) * (1/Kp)  / (Kp+Ke)
        # Ce = ( (Jint - Jpos/(Ke + Kp))  ) * (1/Ke) * K

        # Cp = ( Jpos*(Kp - Ke*Kp/(Kp+Ke))  + Ke*Kp * Jint  ) * (1/Kp)  / (Kp+Ke)
        # Ce = ( (Jint - Jpos/(Ke + Kp))  ) * (1/Ke) * Ke*Kp/(Kp+Ke)

        # Cp = ( Jpos*(1/Ke - 1/(Kp+Ke))  +  Jint  ) * Ke/(Kp+Ke)
        # Ce = ( (Jint - Jpos/(Ke + Kp))  ) * Kp/(Kp+Ke)

        # Solution In Kp-representation
        # Cp = ( Jpos* Kp/(Kp+Ke)  +  Ke*Jint  ) /(Kp+Ke)
        # Ce = ( (Jint - Jpos/(Ke + Kp))  ) *Kp/(Kp+Ke)

        # Solution In Tp-representation
        # Tp, Te = T[0], T[1]

        # Cp = ( Jpos* Te/(Tp+Te)  +  Jint /Te ) *Tp*Te/(Tp+Te)
        # Ce = ( (Jint - Jpos*Tp*Te/(Tp + Te))  ) *Te/(Tp+Te)

        Jint = conc_trap(J, t=t, dt=dt)

        if T[0] == 0:
            Cp = np.zeros(len(J))
            Ce = Jint
            return np.stack((Cp, Ce))

        if T[1] == 0:
            Cp = Jint
            Ce = np.zeros(len(J))
            return np.stack((Cp, Ce))

        if np.isinf(T[0]):
            Cp = Jint
            Ce = np.zeros(len(J))
            return np.stack((Cp, Ce))

        if np.isinf(T[1]):
            # T[0] is not inf - covered above
            Jpos = utils.expconv(J, T[0], t=t, dt=dt)
            Cp = Jpos*T[0]
            Ce = Jint - Jpos*T[0]
            return np.stack((Cp, Ce))

        Kpos = 1/T[0] + 1/T[1]
        Jpos = utils.expconv(J, 1/Kpos, t=t, dt=dt)

        X = T[0]*T[1]/(T[0]+T[1])
        Cp = (Jpos * X/T[0] + Jint / T[1]) * X
        Ce = (Jint - Jpos*X) * X/T[0]

        # Check:
        # Cp + Ce
        # Jint (X/T[1] + X/T[0]) + Jpos(X*X/T[0] - X*X/T[0])
        # = Jint

        return np.stack((Cp, Ce))

    if T[0] == 0:
        # D = sqrt( (1/TP-1/TE)**2 + 4 * E * (1/TP) * (1/TE)  )
        # D = (1/TP) * sqrt( (1-TP/TE)**2 + 4 * E * TP/TE)
        # KT = 1/TP + 1/TE
        # KT = (1/TP) (1 + TP/TE)
        # Kpos = 0.5/TP * [ 1 + TP/TE + sqrt( (1-TP/TE)**2 + 4 * E * TP/TE) ]
        # Kneg = 0.5/TP * [ 1 + TP/TE - sqrt( (1-TP/TE)**2 + 4 * E * TP/TE) ]
        # First order term in Kneg dominates so need power expansion:
        # f(x) = sqrt( (1-x)**2 + 4E*x )
        # f(0) = 1
        # f'(x) = 1/2 * ((1-x)**2 + 4E*x)**(-1/2) * (-2*(1-x)+4E)
        # f'(0) = 1/2 * (-2+4E) = -1+2E
        # f(x) = 1 + (-1+2E)*x
        # TP->0:
        # Kpos = 0.5/TP * 2
        # Kpos = 1/TP
        # Kneg = 0.5/TP * [ TP/TE - (-1+2E) TP/TE]
        # Kneg = 0.5 * [1 - (-1+2E)] / TE
        # Kneg = (1-E)/TE
        # Then:
        # KB = (1-E)/TP
        # Eneg = (1/TP - (1-E)/TP) / (1/TP - (1-E)/TE)
        # Eneg = E / (1 - (1-E) TP/TE)
        # Eneg -> E

        # Jpos = J
        Jneg = utils.expconv(J, T[1]/(1-E), t=t, dt=dt)

        # Je = (Jneg/TP - Jpos*(1-E)/TE) / (1/TP - (1-E)/TE)
        # Je = (Jneg - TP*Jpos*(1-E)/TE) / (1 - TP(1-E)/TE)
        # Je = Jneg

        # Jp = (1-E)*Jpos + E*Jneg
        # Je = Jneg

        # Cp = 0*Jp
        Cp = np.zeros(len(J))
        Ce = Jneg*T[1]*E/(1-E)

        return np.stack((Cp, Ce))

    if T[1] == 0:
        # D symmetric in TP and TE, so power expansion in TE is:
        # Kpos = 1/TE
        # Kneg = (1-E)/TP

        # Jpos = J
        Jneg = utils.expconv(J, T[0]/(1-E), t=t, dt=dt)

        # KB = (1-E)/TP
        # Eneg = (1/TE - (1-E)/TP) / (1/TE - (1-E)/TP) = 1

        Jp = Jneg
        # Je
        # = (Jneg/TE - Jpos*(1-E)/TP) / (1/TE - (1-E)/TP)
        # = Jneg
        # Je = Jneg

        Cp = Jp*T[0]/(1-E)
        # Ce = Je*0
        Ce = np.zeros(len(J))

        return np.stack((Cp, Ce))

    if np.isinf(T[0]):
        Cp = conc_trap(J, t=t, dt=dt)
        Ce = np.zeros(len(J))
        return np.stack((Cp, Ce))

    if np.isinf(T[1]):
        Cp = conc_comp(J, T[0], t=t, dt=dt)
        Jp = Cp/T[0]
        Ce = conc_trap(E*Jp, t=t, dt=dt)
        return np.stack((Cp, Ce))

    K = np.array([
        [1/T[0], -1/T[1]],
        [-E/T[0], 1/T[1]],
    ])

    Dsq = (K[0, 0]-K[1, 1])**2 + 4*K[0, 1]*K[1, 0]
    if Dsq < 0:
        msg = 'No real solution to the 2CXM exists because of unphysical parameter values.'
        if E < 0:
            msg += '\n-> The extraction fraction is negative (E = '+str(E)+').'
        raise ValueError(msg)
    D = np.sqrt(Dsq)

    KT = K[0, 0] + K[1, 1]
    Kpos = 0.5*(KT + D)
    Kneg = 0.5*(KT - D)

    Jpos = utils.expconv(J, 1/Kpos, t=t, dt=dt)
    Jneg = utils.expconv(J, 1/Kneg, t=t, dt=dt)

    KB = K[0, 0] + K[1, 0]
    Eneg = (Kpos - KB)/(Kpos - Kneg)

    Jp = (1-Eneg)*Jpos + Eneg*Jneg
    Je = (Jneg*Kpos - Jpos*Kneg) / (Kpos - Kneg)

    # Jp = Fp*cp, Cp = vp*cp -> Jp/Cp = Fp/vp = (1-E)/TP -> Cp = Jp*TP/(1-E)
    # Je = Fp*ce, Ce = ve*ce -> Je/Ce = Fp/ve = (1-E)/E * 1/TE -> Ce = Je*TE * E/(1-E)

    Cp = Jp*T[0]/(1-E)
    Ce = Je*T[1]*E/(1-E)

    return np.stack((Cp, Ce))


def flux_2cxm(J, T, E, t=None, dt=1.0):
    """Indicator flux out of a 2-compartment exchange model.

    See section :ref:`define-2comp` for more detail.

    Args:
        J (array_like): the indicator flux entering the compartment (mmol/sec).
        T (array-like): 2-element array with mean transit times of plasma and extravascular compartment. Mean transit times can take any value, including 0 and inf. Negative values are unphysical but will only trigger an error if no solution exists.
        E (float): Extraction fraction out of the plasma compartment. E is a value between 0 and 1, and boundary values E=0 and E=1 are correctly handled. Values outside that range are unphysical but will only trigger an error if no solution exists.
        t (array_like, optional): the time points of the indicator flux J (sec). If t=None, the time points are assumed to be uniformly spaced with spacing dt. Defaults to None.
        dt (float, optional): spacing between time points for uniformly spaced time points (sec). This parameter is ignored if t is explicity provided. Defaults to 1.0.
        solver (str, optional): solver for the system, either 'conv' for explicit convolution with a discrete impulse response (slow) or 'interp' for interpolation (fast). Defaults to 'interp'.

    Returns:
        np.ndarray: Outflux in mmol/sec 
    """
    # T = [ Tp, Te]

    # Jp = Fp*cp, Cp = vp*cp -> Jp/Cp = Fp/vp = (1-E)/TP -> Cp = Jp*TP/(1-E)
    # Jp = Cp*(1-E)/Tp

    if E == 1:
        return np.zeros(len(J))

    if T[0] == 0:
        # D = sqrt( (1/TP-1/TE)**2 + 4 * E * (1/TP) * (1/TE)  )
        # D = (1/TP) * sqrt( (1-TP/TE)**2 + 4 * E * TP/TE)
        # KT = 1/TP + 1/TE
        # KT = (1/TP) (1 + TP/TE)
        # Kpos = 0.5/TP * [ 1 + TP/TE + sqrt( (1-TP/TE)**2 + 4 * E * TP/TE) ]
        # Kneg = 0.5/TP * [ 1 + TP/TE - sqrt( (1-TP/TE)**2 + 4 * E * TP/TE) ]
        # First order term in Kneg dominates so need power expansion:
        # f(x) = sqrt( (1-x)**2 + 4E*x )
        # f(0) = 1
        # f'(x) = 1/2 * ((1-x)**2 + 4E*x)**(-1/2) * (-2*(1-x)+4E)
        # f'(0) = 1/2 * (-2+4E) = -1+2E
        # f(x) = 1 + (-1+2E)*x
        # TP->0:
        # Kpos = 0.5/TP * 2
        # Kpos = 1/TP
        # Kneg = 0.5/TP * [ TP/TE - (-1+2E) TP/TE]
        # Kneg = 0.5 * [1 - (-1+2E)] / TE
        # Kneg = (1-E)/TE
        # Then:
        # KB = (1-E)/TP
        # Eneg = (1/TP - (1-E)/TP) / (1/TP - (1-E)/TE)
        # Eneg = E / (1 - (1-E) TP/TE)
        # Eneg -> E
        # Jpos = J
        # Jneg = utils.expconv(J, T[1]/(1-E), t=t, dt=dt)

        # Je = (Jneg/TP - Jpos*(1-E)/TE) / (1/TP - (1-E)/TE)
        # Je = (Jneg - TP*Jpos*(1-E)/TE) / (1 - TP(1-E)/TE)
        # Je = Jneg

        # Jp = (1-E)*Jpos + E*Jneg
        # Je = Jneg

        # The case E=1 is already handled above

        if np.isinf(T[1]):
            return (1-E)*J

        Jpos = J
        Jneg = utils.expconv(J, T[1]/(1-E), t=t, dt=dt)
        return (1-E)*Jpos + E*Jneg

    C = conc_2cxm(J, T, E, t=t, dt=dt)
    Jp = C[0, :]*(1-E)/T[0]

    return Jp

    # K = np.array([
    #     [1/T[0], -1/T[1]],
    #     [-E/T[0], 1/T[1]],
    # ])

    # D = np.sqrt((K[0,0]-K[1,1])**2 + 4*K[0,1]*K[1,0])

    # KT = K[0,0] + K[1,1]
    # Kpos = 0.5*(KT + D)
    # Kneg = 0.5*(KT - D)

    # Jpos = utils.expconv(J, 1/Kpos, t=t, dt=dt)
    # Jneg = utils.expconv(J, 1/Kneg, t=t, dt=dt)

    # KB = K[0,0] + K[1,0]
    # Eneg = (Kpos - KB)/(Kpos - Kneg)

    # Jp = (1-Eneg)*Jpos + Eneg*Jneg

    # return Jp
