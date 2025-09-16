import numpy as np
from scipy.integrate import trapezoid

import dcmri as dc
import dcmri.pk as pk

import matplotlib.pyplot as plt

def test_res_trap():
    t = np.linspace(0, 100, 20)
    r = dc.res_trap(t)
    assert np.sum(r) == 20

def test_prop_trap():
    t = np.linspace(0, 100, 20)
    h = dc.prop_trap(t)
    assert np.linalg.norm(h) == 0

def test_conc_trap():
    t = np.linspace(0, 100, 20)
    J = np.ones(len(t))
    C = dc.conc(J, t=t, model='trap')
    assert C[-1] == 100
    C = dc.conc(J, dt=t[1], model='trap')
    assert C[-1] == 100
    C0 = dc.conv(dc.res_trap(t), J, t)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) == 0

def test_flux_trap():
    t = np.linspace(0, 100, 20)
    J = np.ones(len(t))
    Jo = dc.flux(J, model='trap')
    assert np.linalg.norm(Jo) == 0
    Jo0 = dc.conv(dc.prop_trap(t), J, t)
    assert np.linalg.norm(Jo-Jo0) == 0

def test_res_pass():
    T = 30
    t = np.linspace(0, 100, 20)
    r = dc.res_pass(T, t)
    assert round(r[0] * t[1]/2) == T
    assert np.linalg.norm(r[1:]) == 0
    
def test_prop_pass():
    T = 30
    t = np.linspace(0, 100, 20)
    h = dc.prop_pass(t)
    assert round(h[0] * t[1]/2) == 1
    assert np.linalg.norm(h[1:]) == 0

def test_conc_pass():
    T = 30
    t = np.linspace(0, 100, 20)
    J = np.ones(len(t))
    C = dc.conc(J, T, model='pass')
    assert np.unique(C)[0] == T
    C0 = dc.conv(dc.res_pass(T,t), J, t)
    assert np.linalg.norm(C[1:]-C0[1:])/np.linalg.norm(C0[1:]) < 1e-12

def test_flux_pass():
    T = 30
    t = np.linspace(0, 100, 20)
    J = np.ones(len(t))
    Jo = dc.flux(J, model='pass')
    assert np.linalg.norm(J-Jo)/np.linalg.norm(J) < 1e-12
    Jo0 = dc.conv(dc.prop_pass(t), J, t)
    assert np.linalg.norm(Jo[1:]-Jo0[1:])/np.linalg.norm(Jo[1:]) < 1e-12


def test_res_comp():
    T = 25
    t = np.linspace(0, 150, 20)
    r = dc.res_comp(T, t)
    assert np.round(trapezoid(r,t)) == T
    t = [0,5,15,30,60,90,150]
    r = dc.res_comp(T, t)
    assert (trapezoid(r,t)-T)**2/T**2 < 1e-2
    r = dc.res_comp(np.inf, t)
    assert np.sum(np.unique(r))== 1
    r = dc.res_comp(0, t)
    assert np.sum(r) == 1

def test_prop_comp():
    T = 25
    t = np.linspace(0, 150, 20)
    h = dc.prop_comp(T, t)
    assert np.round(trapezoid(h,t)) == 1
    t = [0,5,15,30,60,90,150]
    h = dc.prop_comp(T, t)
    assert (trapezoid(h,t)-1)**2 < 1e-2
    h = dc.prop_comp(np.inf, t)
    assert np.linalg.norm(h)==0
    h = dc.prop_comp(0, t)
    assert (trapezoid(h,t)-1)**2 < 1e-2

def test_conc_comp():
    T = 25
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_comp(T,t), J, t)
    C = dc.conc(J, T, t=t, model='comp')
    assert np.linalg.norm(C[1:]-C0[1:])/np.linalg.norm(C0[1:]) < 1e-2
    C = dc.conc(J, T, dt=t[1], model='comp')
    assert np.linalg.norm(C[1:]-C0[1:])/np.linalg.norm(C0[1:]) < 1e-2
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_comp(T,t), J, t)
    C = dc.conc(J, T, t=t, model='comp')
    assert np.linalg.norm(C[1:]-C0[1:])/np.linalg.norm(C0[1:]) < 1e-1
    C = dc.conc(J, np.inf, t=t, model='comp')
    C0 = dc.conc(J,t=t, model='trap')
    assert np.linalg.norm(C[1:]-C0[1:])/np.linalg.norm(C0[1:]) < 1e-1

def test_flux_comp():
    T = 25
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_comp(T,t), J, t)
    Jo = dc.flux(J, T, t=t, model='comp')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-2
    Jo = dc.flux(J, T, dt=t[1], model='comp')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-2
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_comp(T,t), J, t)
    Jo = dc.flux(J, T, t=t, model='comp')
    assert np.linalg.norm(J0-Jo)/np.linalg.norm(J0) < 1e-1
    Jo = dc.flux(J, np.inf, t=t, model='comp')
    assert np.linalg.norm(Jo) == 0

def test_res_plug():
    T = 25
    t = np.linspace(0, 150, 20)
    r = dc.res_plug(T, t)
    assert (trapezoid(r,t)-T)**2/T**2 < 0.02
    t = [0,5,15,30,60,90,150]
    r = dc.res_plug(T, t)
    assert (trapezoid(r,t)-T)**2/T**2 < 0.06

def test_prop_plug():
    T = 25
    t = np.linspace(0, 150, 500)
    h = dc.prop_plug(T, t)
    assert np.abs((trapezoid(h,t)-1)) < 1e-12
    t = [0,5,15,30,60,90,150]
    h = dc.prop_plug(T, t)
    assert np.abs((trapezoid(h,t)-1)) < 1e-12

def test_conc_plug():
    T = 25
    t = np.linspace(0, 150, 40)
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_plug(T,t), J, t)
    C = dc.conc(J, T, t=t, model='plug')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-2
    C = dc.conc_plug(J, T, t, solver='conv')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-2
    C = dc.conc_plug(J, T, dt=t[1])
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-2
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_plug(T,t), J, t)
    C = dc.conc_plug(J, T, t)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1
    C = dc.conc_plug(J, np.inf, t)
    C0 = dc.conc_trap(J)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-2
    C = dc.conc_plug(J, 0, t)
    assert np.linalg.norm(C) == 0

def test_flux_plug():
    T = 25
    t = np.linspace(0, 150, 40)
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_plug(T,t), J, t)
    Jo = dc.flux(J, T, t=t, model='plug')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 0.2
    Jo = dc.flux(J, T, t=t, model='plug', solver='conv')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 0.2
    Jo = dc.flux(J, T, dt=t[1], model='plug')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 0.2
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_plug(T,t), J, t)
    Jo = dc.flux(J, T, t=t, model='plug')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 0.3
    Jo = dc.flux(J, np.inf, t=t, model='plug')
    assert np.linalg.norm(Jo) == 0
    Jo = dc.flux(J, 0, t=t, model='plug')
    assert np.linalg.norm(Jo-J) == 0

    try:
        Jo = dc.flux(J, T, t=t, model='plug', solver='blabla')
    except:
        assert True
    else:
        assert False


def test_prop_chain():
    T = 25
    D = 0.5
    t = np.linspace(0, 150, 500)
    h = dc.prop_chain(T, D, t)
    assert np.abs(trapezoid(h,t)-1) < 0.001
    assert np.abs(trapezoid(t*h,t)-T) < 0.02
    t = [0,5,15,30,60,90,150]
    h = dc.prop_chain(T, D, t)
    assert np.abs(trapezoid(h,t)-1) < 0.03
    assert np.abs(trapezoid(t*h,t)-T) < 0.5
    try:
        h = dc.prop_chain(-1, D, t)
    except:
        assert True
    else:
        assert False
    try:
        h = dc.prop_chain(T, -1, t)
    except:
        assert True
    else:
        assert False
    try:
        h = dc.prop_chain(T, 2, t)
    except:
        assert True
    else:
        assert False
    h = dc.prop_chain(T, 0, t)
    h0 = dc.prop_plug(T,t)
    assert np.linalg.norm(h-h0)==0
    h = dc.prop_chain(T, 1, t)
    h0 = dc.prop_comp(T, t)
    assert np.linalg.norm(h-h0)==0


def test_res_chain():
    T = 25
    D = 0.5
    t = np.linspace(0, 150, 500)
    h = dc.res_chain(T, D, t)
    assert (trapezoid(h,t)-T)**2/T**2 < 1e-6
    t = [0,5,15,30,60,90,150]
    h = dc.res_chain(T, D, t)
    assert (trapezoid(h,t)-T)**2/T**2 < 1e-3
    h = dc.res_chain(T, 0, t)
    h0 = dc.res_plug(T,t)
    assert np.linalg.norm(h-h0)==0
    h = dc.res_chain(T, 1, t)
    h0 = dc.res_comp(T, t)
    assert np.linalg.norm(h-h0)==0

def test_conc_chain():
    T = 25
    D = 0.5
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_chain(T,D,t), J, t)
    C = dc.conc(J, T, D, t=t, model='chain')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    C = dc.conc_chain(J, T, D, dt=t[1])
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_chain(T,D,t), J, t)
    C = dc.conc_chain(J, T, D, t)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    h = dc.conc_chain(J, T, 0, t)
    h0 = dc.conc_plug(J, T,t)
    assert np.linalg.norm(h-h0)==0
    h = dc.conc_chain(J, T, 1, t)
    h0 = dc.conc_comp(J, T, t)
    assert np.linalg.norm(h-h0)==0

def test_flux_chain():
    T = 25
    D = 0.5
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_chain(T,D,t), J, t)
    Jo = dc.flux(J, T, D, t=t, model='chain')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    Jo = dc.flux(J, T, D, dt=t[1], model='chain')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_chain(T,D,t), J, t)
    Jo = dc.flux(J, T, D, t=t, model='chain')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    h = dc.flux(J, T, 0, t=t, model='chain')
    h0 = dc.flux(J, T, t=t, model='plug')
    assert np.linalg.norm(h-h0)==0
    h = dc.flux(J, T, 1, t=t, model='chain')
    h0 = dc.flux(J, T, t=t, model='comp')
    assert np.linalg.norm(h-h0)==0



def test_flux_pfcomp():
    T = 10
    D = 0.5
    t = np.linspace(0, 300, 1000)
    J = np.exp(-t/20)/20

    # Check that the function preserves areas
    Jo = dc.flux(J, T, D, t=t, model='pfcomp')
    assert np.sum(Jo)*t[1]-1 < 1e-2

    # D=0
    Jo = dc.flux(J, T, 0, t=t, model='pfcomp')
    assert np.sum(Jo)*t[1]-1 < 1e-2

    # D=1
    Jo = dc.flux(J, T, 1, t=t, model='pfcomp')
    assert np.sum(Jo)*t[1]-1 < 1e-2

    try:
        Jo = dc.flux(J, T, -1, t=t, model='pfcomp')
    except:
        assert True
    else:
        assert False
    try:
        Jo = dc.flux(J, T, 2, t=t, model='pfcomp')
    except:
        assert True
    else:
        assert False


def test_prop_step():
    T, D = 25, 0.5
    t = np.linspace(0, 150, 100)
    h = dc.prop_step(T, D, t)
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    assert np.abs(trapezoid(t*h,t)-T) < 1e-12
    h = dc.prop_step(T, 1, t)
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    h = dc.prop_step(120, 0.5, t)
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    h = dc.prop_step(120, 0.5, t)
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    t = [0,5,15,30,60,90,150]
    h = dc.prop_step(T, D, t)
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    try:
        h = dc.prop_step(-1, D, t)
    except:
        assert True
    else:
        assert False
    try:
        h = dc.prop_step(T, -1, t)
    except:
        assert True
    else:
        assert False
    try:
        h = dc.prop_step(T, 2, t)
    except:
        assert True
    else:
        assert False
    h = dc.prop_step(np.inf, D, t)
    assert np.linalg.norm(h)==0
    h = dc.prop_step(T, 0, t)
    h0 = dc.prop_plug(T, t)
    assert np.linalg.norm(h-h0)==0

def test_res_step():
    T, D = 25, 0.5
    t = np.linspace(0, 150, 500)
    h = dc.res_step(T, D, t)
    assert (trapezoid(h,t)-T)**2/T**2 < 1e-9
    t = [0,5,15,30,60,90,150]
    h = dc.res_step(T, D, t)
    assert (trapezoid(h,t)-T)**2/T**2 < 0.5

def test_conc_step():
    T, D = 25, 0.5
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_step(T,D,t), J, t)
    C = dc.conc(J, T, D, t=t, model='step')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    C = dc.conc_step(J, T, D, dt=t[1])
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_step(T,D,t), J, t)
    C = dc.conc_step(J, T, D, t)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    C = dc.conc_step(J, T, 0, t)
    C0 = dc.conc_plug(J, T, t)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12


def test_flux_step():
    T, D = 25, 0.5
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_step(T,D,t), J, t)
    Jo = dc.flux(J, T, D, t=t, model='step')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    Jo = dc.flux(J, T, D, dt=t[1], model='step')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_step(T,D,t), J, t)
    Jo = dc.flux(J, T, D, t=t, model='step')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    Jo = dc.flux(J, T, 0, t=t, model='step')
    J0 = dc.flux(J, T, t=t, model='plug')
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12


def test_prop_free():
    t = np.linspace(0, 150, 100)
    h = dc.prop_free([1,1], t, TT=[30,60,90])
    T = 60
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    assert (trapezoid(t*h,t)-T)**2/T**2 < 1e-9
    h = dc.prop_free([2,2], t, TT=[30,60,90])
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    assert (trapezoid(t*h,t)-T)**2/T**2 < 1e-9
    h = dc.prop_free([2,5], t, TT=[30,60,90])
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    h = dc.prop_free([2,5], t, TT=[30,60,120])
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    h = dc.prop_free([2,5], t, TT=[30.5,60.5,120.5])
    assert np.abs(trapezoid(h,t)-1) < 1e-12
    h = dc.prop_free([1,1], t)
    h0 = dc.prop_free([1,1], t, TTmax=np.amax(t))
    assert np.linalg.norm(h-h0)/np.linalg.norm(h0) < 1e-12
    try:
        h = dc.prop_free([1,1,1], t, TT=[30,60,90])
    except:
        assert True
    else:
        assert False


def test_res_free():
    t = np.linspace(0, 150, 100)
    h = dc.res_free([1,1], t, TT=[30,60,90])
    T = 60
    assert (trapezoid(h,t)-T)**2/T**2 < 1e-9

def test_conc_free():
    H = [1,1]
    TT = [30,60,90]
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_free(H,t,TT), J, t)
    C = dc.conc(J, H, t=t, model='free', TT=TT)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    C = dc.conc_free(J, H, t, dt=t[1], TT=TT)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C0 = dc.conv(dc.res_free(H,t,TT=TT), J, t)
    C = dc.conc_free(J, H, t, TT=TT)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-12

def test_flux_free():
    H = [1,1]
    TT = [30,60,90]
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_free(H,t,TT), J, t)
    Jo = dc.flux(J, H, t=t, model='free', TT=TT)
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    Jo = dc.flux(J, H, dt=t[1], model='free', TT=TT)
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    J0 = dc.conv(dc.prop_free(H,t,TT=TT), J, t)
    Jo = dc.flux(J, H, t=t, model='free', TT=TT)
    assert np.linalg.norm(Jo-J0)/np.linalg.norm(J0) < 1e-12


def test__K_ncomp():
    T1, T2 = 2, 7
    E11, E12, E21, E22 = 1, 3, 9, 2
    K = pk._K_ncomp([T1,T2], [[E11,E12],[E21,E22]])
    K0 = [[(E11+E21)/T1, -E12/T2],[-E21/T1, (E12+E22)/T2]]
    assert np.array_equal(K, K0)
    assert np.array_equal(np.matmul(K, [1,0]), [(E11+E21)/T1,-E21/T1])
    assert np.array_equal(np.matmul(K, [0,1]), [-E12/T2,(E12+E22)/T2])
    assert np.array_equal(np.matmul(K, [1,0]), K[:,0]) # col 0
    assert np.array_equal(np.matmul(K, [0,1]), K[:,1]) # col 1
    try:
        pk._K_ncomp([T1,T2], [[E11,-1],[E21,E22]])
    except:
        assert True
    else:
        assert False
    K = pk._K_ncomp([T1,T2], [[0,E12],[0,E22]])
    assert K[0,0] == 0

def test__J_ncomp():
    T = [1,2]
    E = [[1,0],[0,1]]
    C = [[1],
         [3]]
    J = pk._J_ncomp(np.array(C), T, E)
    assert J[0,0,:] == 1
    assert J[0,1,:] == 0
    assert J[1,0,:] == 0
    assert J[1,1,:] == 1.5

def test_conc_ncomp_prop():
    # Compare a decoupled system against analytical 1-comp model solutions
    t = np.linspace(0, 20, 10)
    J = np.ones((2,len(t)))
    J[1,:] = 2
    T = [6,12]
    E = [[1,0],[0,1]]
    C0 = dc.conc_comp(J[0,:], T[0], t)
    C1 = dc.conc_comp(J[1,:], T[1], t)
    prec = [1e-1, 1e-2, 1e-3]
    for i, dt_prop in enumerate([None, 0.1, 0.01]):
        C = dc.conc_ncomp_prop(J, T, E, t, dt_prop=dt_prop)
        assert np.linalg.norm(C[0,:]-C0)/np.linalg.norm(C0) < prec[i]
        assert np.linalg.norm(C[1,:]-C1)/np.linalg.norm(C1) < prec[i]

def test_conc_ncomp_diag():
    # Compare a decoupled system against analytical 1-comp model solutions
    t = np.linspace(0, 20, 10)
    J = np.ones((2,len(t)))
    J[1,:] = 2
    T = [6,12]
    E = [[1,0],[0,1]]
    C0 = dc.conc_comp(J[0,:], T[0], t)
    C1 = dc.conc_comp(J[1,:], T[1], t)
    C = dc.conc_ncomp_diag(J, T, E, t)
    assert np.linalg.norm(C[0,:]-C0)/np.linalg.norm(C0) < 1e-6
    assert np.linalg.norm(C[1,:]-C1)/np.linalg.norm(C1) < 1e-6

def test_conc_ncomp():

    # Compare a decoupled system against analytical 1-comp model solutions
    t = np.linspace(0, 20, 10)
    J = np.ones((2,len(t)))
    J[1,:] = 2
    T = [6,12]
    E = [[1,0],[0,1]]
    C0 = dc.conc_comp(J[0,:], T[0], t)
    C1 = dc.conc_comp(J[1,:], T[1], t)
    prec = [1e-1, 1e-2, 1e-3]
    for i, dt_prop in enumerate([None, 0.1, 0.01]):
        C = dc.conc(J, T, E, t=t, model='ncomp', dt_prop=dt_prop)
        assert np.linalg.norm(C[0,:]-C0)/np.linalg.norm(C0) < prec[i]
        assert np.linalg.norm(C[1,:]-C1)/np.linalg.norm(C1) < prec[i]

    # Compare both solvers for a few coupled systems
    E = [[1,0.5],[0.5,1]]
    C = dc.conc_ncomp(J, T, E, t, solver='prop', dt_prop=0.01)
    C0 = dc.conc_ncomp(J, T, E, t, solver='diag')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C) < 1e-3
    E = [[0.2,0.6],[0.8,0.4]]
    C = dc.conc_ncomp(J, T, E, t, solver='prop', dt_prop=0.01)
    C0 = dc.conc_ncomp(J, T, E, t, solver='diag')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C) < 1e-3
    E = [[0.6, 0.5, 0.0], [0.1, 0.2, 0.5], [0.3, 0.3, 0.5]]
    T3 = [6,12,6]
    J3 = np.ones((3,len(t)))
    C = dc.conc_ncomp(J3, T3, E, t, solver='prop', dt_prop=0.01)
    C0 = dc.conc_ncomp(J3, T3, E, t, solver='diag')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C) < 1e-1

    # Compare both solvers for a 2CXM
    J = np.ones(len(t))
    J = np.stack((J, np.zeros(J.size)))
    E = 0.1
    E = [[1-E,1],[E,0]]
    C = dc.conc(J, T, E, t=t, model='ncomp', solver='prop', dt_prop=0.01)
    C0 = dc.conc(J, T, E, t=t, model='ncomp', solver='diag')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C) < 1e-3

def test_flux_ncomp():
    # Compare a decoupled system against analytical 1-comp model solutions
    t = np.linspace(0, 20, 10)
    J = np.ones((2,len(t)))
    J[1,:] = 2
    T = [6,12]
    E = [[1,0],[0,1]]
    J0 = dc.conc_comp(J[0,:], T[0], t) / T[0]
    J1 = dc.conc_comp(J[1,:], T[1], t) / T[1]
    J = dc.flux(J, T, E, t=t, dt_prop=0.01, model='ncomp')
    assert np.linalg.norm(J[0,0,:]-J0)/np.linalg.norm(J0) < 1e-3
    assert np.linalg.norm(J[1,1,:]-J1)/np.linalg.norm(J1) < 1e-3
    assert np.linalg.norm(J[1,0,:]) == 0
    assert np.linalg.norm(J[0,1,:]) == 0

def test_res_ncomp():
    # Compare a decoupled system against analytical 1-comp model solutions.
    t = np.linspace(0, 20, 10)
    T = [6,12]
    E = [[1,0],[0,1]]
    R0 = dc.res_comp(T[0], t)
    R1 = dc.res_comp(T[1], t)
    R = dc.res_ncomp(T, E, t)
    assert np.linalg.norm(R[0,0,:]-R0)/np.linalg.norm(R0) < 1e-12
    assert np.linalg.norm(R[1,1,:]-R1)/np.linalg.norm(R1) < 1e-12
    assert np.linalg.norm(R[1,0,:]) == 0
    assert np.linalg.norm(R[0,1,:]) == 0
    # Compare against convolution on a coupled system.
    E = [[0.6, 0.5, 0.0], [0.1, 0.2, 0.5], [0.3, 0.3, 0.5]]
    T = [6, 12, 6]
    J = np.ones((3,len(t)))
    C = dc.conc_ncomp(J, T, E, t, solver='prop', dt_prop=0.01)
    R = dc.res_ncomp(T, E, t)
    C0 = dc.conv(R[0,0,:], J[0,:], t) + dc.conv(R[1,0,:], J[1,:], t)
    C1 = dc.conv(R[0,1,:], J[0,:], t) + dc.conv(R[1,1,:], J[1,:], t)
    assert np.linalg.norm(C[0,:]-C0)/np.linalg.norm(C0) < 0.1
    assert np.linalg.norm(C[1,:]-C1)/np.linalg.norm(C1) < 0.5

def test_prop_ncomp():
    # Compare a decoupled system against analytical 1-comp model solutions
    t = np.linspace(0, 20, 10)
    T = [6,12]
    E = [[1,0],[0,1]]
    H0 = dc.prop_comp(T[0], t) 
    H1 = dc.prop_comp(T[1], t)
    H = dc.prop_ncomp(T, E, t)
    assert np.linalg.norm(H[0,0,0,:]-H0)/np.linalg.norm(H0) < 1e-12
    assert np.linalg.norm(H[1,1,1,:]-H1)/np.linalg.norm(H1) < 1e-12
    assert np.linalg.norm(H[:,1,0,:]) == 0
    assert np.linalg.norm(H[:,0,1,:]) == 0
    # Compare against convolution on a coupled system
    J = np.ones((2,len(t)))
    J[1,:] = 2
    E = [[1,0.5],[0.5,1]]
    Jo = dc.flux_ncomp(J, T, E, t, solver='prop', dt_prop=0.01)
    H = dc.prop_ncomp(T, E, t)
    Jo0 = dc.conv(H[0,0,0,:], J[0,:], t) + dc.conv(H[1,0,0,:], J[1,:], t)
    Jo1 = dc.conv(H[0,1,1,:], J[0,:], t) + dc.conv(H[1,1,1,:], J[1,:], t)
    assert np.linalg.norm(Jo[0,0,:]-Jo0)/np.linalg.norm(Jo0) < 0.1
    assert np.linalg.norm(Jo[1,1,:]-Jo1)/np.linalg.norm(Jo1) < 0.01


def test__K_2comp():
    # Compare against numerical computation
    T = [6,12]
    E = [[1,0.5],[0.5,1]]
    # Analytical
    _, K, _ = pk._K_2comp(T,E)
    # Numerical
    Knum = pk._K_ncomp(T, E)
    Knum, _ = np.linalg.eig(Knum)
    assert np.linalg.norm(K-Knum)/np.linalg.norm(Knum) < 1e-12

def test_conc_2comp():

    # Compare a coupled system against numerical solutions
    t = np.linspace(0, 20, 10)
    J = np.ones((2,len(t)))
    J[1,:] = 2
    T = [6,12]
    E = [[1,0.5],[0.5,1]]
    C0 = dc.conc(J, T, E, t=t, model='ncomp') 
    C = dc.conc_ncomp(J, T, E, t, dt_prop=0.1)
    assert np.linalg.norm(C[0,:]-C0[0,:])/np.linalg.norm(C[0,:]) < 1e-2
    assert np.linalg.norm(C[1,:]-C0[1,:])/np.linalg.norm(C[1,:]) < 1e-2

    # Compare a decoupled system against individual solutions
    E = [[1,0],[0,1]]
    C = dc.conc_ncomp(J, T, E, t)
    C0 = dc.conc_comp(J[0,:], T[0], t)
    C1 = dc.conc_comp(J[1,:], T[1], t)
    assert np.linalg.norm(C[0,:]-C0)/np.linalg.norm(C0) < 1e-12
    assert np.linalg.norm(C[1,:]-C1)/np.linalg.norm(C1) < 1e-12

    # Test exceptions
    try:
        dc.conc_ncomp(J, [6,0], E, t)
    except:
        assert True
    else:
        assert False
    C = dc.conc_ncomp([[1,1],[1,1]], [1,1], [[1,0],[0,1]])
    assert C[0,0]==0


def test_flux_2comp():
    # Compare a decoupled system against analytical 1-comp model solutions
    t = np.linspace(0, 20, 10)
    J = np.ones((2,len(t)))
    J[1,:] = 2
    T = [6,12]
    E = [[1,0],[0,1]]
    J0 = dc.conc_comp(J[0,:], T[0], t) / T[0]
    J1 = dc.conc_comp(J[1,:], T[1], t) / T[1]
    J = dc.flux(J, T, E, t=t, model='ncomp')
    assert np.linalg.norm(J[0,0,:]-J0)/np.linalg.norm(J0) < 1e-3
    assert np.linalg.norm(J[1,1,:]-J1)/np.linalg.norm(J1) < 1e-3
    assert np.linalg.norm(J[1,0,:]) == 0
    assert np.linalg.norm(J[0,1,:]) == 0

def test_res_2comp():
    # Compare a decoupled system against analytical 1-comp model solutions.
    t = np.linspace(0, 20, 10)
    T = [6,12]
    E = [[1,0],[0,1]]
    R0 = dc.res_comp(T[0], t)
    R1 = dc.res_comp(T[1], t)
    R = dc.res_ncomp(T, E, t)
    assert np.linalg.norm(R[0,0,:]-R0)/np.linalg.norm(R0) < 1e-12
    assert np.linalg.norm(R[1,1,:]-R1)/np.linalg.norm(R1) < 1e-12
    assert np.linalg.norm(R[1,0,:]) == 0
    assert np.linalg.norm(R[0,1,:]) == 0
    # Compare against convolution on a coupled system.
    J = np.ones((2,len(t)))
    J[1,:] = 2
    E = [[1,0.5],[0.5,1]]
    C = dc.conc_ncomp(J, T, E, t)
    R = dc.res_ncomp(T, E, t)
    C0 = dc.conv(R[0,0,:], J[0,:], t) + dc.conv(R[1,0,:], J[1,:], t)
    C1 = dc.conv(R[0,1,:], J[0,:], t) + dc.conv(R[1,1,:], J[1,:], t)
    assert np.linalg.norm(C[0,:]-C0)/np.linalg.norm(C0) < 0.1
    assert np.linalg.norm(C[1,:]-C1)/np.linalg.norm(C1) < 0.01

def test_prop_2comp():
    # Compare a decoupled system against analytical 1-comp model solutions
    t = np.linspace(0, 20, 10)
    T = [6,12]
    E = [[1,0],[0,1]]
    H0 = dc.prop_comp(T[0], t) 
    H1 = dc.prop_comp(T[1], t)
    H = dc.prop_ncomp(T, E, t)
    assert np.linalg.norm(H[0,0,0,:]-H0)/np.linalg.norm(H0) < 1e-12
    assert np.linalg.norm(H[1,1,1,:]-H1)/np.linalg.norm(H1) < 1e-12
    assert np.linalg.norm(H[:,1,0,:]) == 0
    assert np.linalg.norm(H[:,0,1,:]) == 0
    # Compare against convolution on a coupled system
    J = np.ones((2,len(t)))
    J[1,:] = 2
    E = [[1,0.5],[0.5,1]]
    Jo = dc.flux_ncomp(J, T, E, t)
    H = dc.prop_ncomp(T, E, t)
    Jo0 = dc.conv(H[0,0,0,:], J[0,:], t) + dc.conv(H[1,0,0,:], J[1,:], t)
    Jo1 = dc.conv(H[0,1,1,:], J[0,:], t) + dc.conv(H[1,1,1,:], J[1,:], t)
    assert np.linalg.norm(Jo[0,0,:]-Jo0)/np.linalg.norm(Jo0) < 0.1
    assert np.linalg.norm(Jo[1,1,:]-Jo1)/np.linalg.norm(Jo1) < 0.01

def test_conc_nscomp():

    # Some inputs
    T = 25
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))

    # Test exceptions
    try:
        dc.conc_nscomp(J, T, t)
    except:
        assert True
    try:
        dc.conc_nscomp(J, [T,T], t)
    except:
        assert True
    try:
        dc.conc_nscomp(J, -T*np.ones(len(t)), t)
    except:
        assert True

    # Test functionality
    C = dc.conc_comp(J, T, t)
    C0 = dc.conc(J, T*np.ones(len(t)), t=t, model='nscomp')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 0.1
    
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C = dc.conc_comp(J, T, t)
    C0 = dc.conc_nscomp(J, T*np.ones(len(t)), t)
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 0.1


def test_flux_nscomp():

    # Some inputs
    T = 25
    t = np.linspace(0, 150, 20)
    J = np.ones(len(t))

    # Test functionality
    C = dc.flux(J, T, t=t, model='comp')
    C0 = dc.flux(J, T*np.ones(len(t)), t=t, model='nscomp')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 0.1
    
    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C = dc.flux(J, T, t=t, model='comp')
    C0 = dc.flux(J, T*np.ones(len(t)), t=t, model='nscomp')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 0.1


def test_conc_mmcomp():
    T = 25
    t = np.linspace(0, 150, 500)
    J = np.ones(len(t))
    C = dc.conc_comp(J, T, t)
    Km = np.amax(C)/2
    Vmax = np.amax(C)/np.amax(T)
    C = dc.conc(J, Vmax, Km, t=t, model='mmcomp', solver='SM')
    C0 = dc.conc_mmcomp(J, Vmax, Km, t, solver='prop')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-2

    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C = dc.conc_mmcomp(J, Vmax, Km, t, solver='SM')
    C0 = dc.conc_mmcomp(J, Vmax, Km, t, solver='prop')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 0.3

    try:
        C = dc.conc_mmcomp(J, -Vmax, Km, t, solver='SM')
    except:
        True
    try:
        C = dc.conc_mmcomp(J, Vmax, -Km, t, solver='SM')
    except:
        True

def test_flux_mmcomp():
    T = 25
    t = np.linspace(0, 150, 500)
    J = np.ones(len(t))
    C = dc.conc_comp(J, T, t)
    Km = np.amax(C)/2
    Vmax = np.amax(C)/np.amax(T)
    C = dc.flux(J, Vmax, Km, t=t, model='mmcomp', solver='SM')
    C0 = dc.flux(J, Vmax, Km, t=t, model='mmcomp', solver='prop')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 1e-2

    t = [0,5,15,30,60,90,150]
    J = np.ones(len(t))
    C = dc.flux(J, Vmax, Km, t=t, model='mmcomp', solver='SM')
    C0 = dc.flux(J, Vmax, Km, t=t, model='mmcomp', solver='prop')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C0) < 0.3

def test_conc_2cxm():
    # Test against general 2-compartment model
    t = np.linspace(0, 20, 10)
    J = np.ones(len(t))
    J2c = np.stack((J, np.zeros(J.size)))
    
    T = [6,12]
    E = 0.1
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = [[1-E,1],[E,0]]
    C = dc.conc(J2c, T, E, t=t, model='ncomp')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C) < 1e-9

    E = 0.5
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = [[1-E,1],[E,0]]
    C = dc.conc(J2c, T, E, t=t, model='ncomp')
    assert np.linalg.norm(C-C0)/np.linalg.norm(C) < 1e-9

    # # test boundary case: TP=0
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = 0.1
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = 0.01
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = 0.0
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    err0 = np.linalg.norm(C0-C)
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    assert err1 < err0
    assert err2 < err1
    assert err2/np.linalg.norm(C) < 1e-2

    # # test boundary case: TE=0
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = 0.1
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = 0.01
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = 0.0
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    err0 = np.linalg.norm(C0-C)
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    assert err1 < err0
    assert err2 < err1
    assert err2/np.linalg.norm(C) < 1e-2

    # # test boundary case: TP=inf
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = 100
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = 1000
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = np.inf
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    err0 = np.linalg.norm(C0-C)
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    assert err1 < err0
    assert err2 < err1
    assert err2/np.linalg.norm(C) < 1e-2

    # # test boundary case: TE=inf
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = 100
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = 1000
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = np.inf
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    err0 = np.linalg.norm(C0-C)
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    assert err1 < err0
    assert err2 < err1
    assert err2/np.linalg.norm(C) < 1e-2

    # # test boundary case: E=0
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.05
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.005
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    err0 = np.linalg.norm(C0-C)
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    assert err1 < err0
    assert err2 < err1
    assert err2/np.linalg.norm(C) < 1e-2

    # # test boundary case: E=1
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.95
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.995
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 1
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    err0 = np.linalg.norm(C0-C)
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    assert err1 < err0
    assert err2 < err1
    assert err2/np.linalg.norm(C) < 1e-2

    # # test boundary case: E=1, Tp=0
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.95
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = 0.1
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.99
    T[0] = 0.01
    C3 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 1
    T[0] = 0
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    err0 = np.linalg.norm(C0-C)
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    err3 = np.linalg.norm(C3-C)
    assert err1 < err0
    assert err2 < err1
    assert err3 < err2
    assert err3/np.linalg.norm(C) < 1e-1

    # # test boundary case: E=1, Te=0
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.95
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = 0.1
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.99
    T[1] = 0.01
    C3 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 1
    T[1] = 0
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    #err0 = np.linalg.norm(C0-C) # diverges before it converges
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    err3 = np.linalg.norm(C3-C)
    #assert err1 < err0
    assert err2 < err1
    assert err3 < err2
    assert err3/np.linalg.norm(C) < 1e-1

    # # test boundary case: E=1, Tp=inf
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.95
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[0] = 100
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.99
    T[0] = 1000
    C3 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 1
    T[0] = np.inf
    C = dc.conc(J, T, E, t=t, model='2cxm')
    plt.show()
    # Check convergence to T=0 solution
    #err0 = np.linalg.norm(C0-C) # diverges before convergence
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    err3 = np.linalg.norm(C3-C)
    #assert err1 < err0
    assert err2 < err1
    assert err3 < err2
    assert err3/np.linalg.norm(C) < 1e-1

    # # test boundary case: E=1, Te=inf
    E = 0.5
    T = [6,12]
    C0 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.95
    C1 = dc.conc(J, T, E, t=t, model='2cxm')
    T[1] = 100
    C2 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 0.99
    T[1] = 1000
    C3 = dc.conc(J, T, E, t=t, model='2cxm')
    E = 1
    T[1] = np.inf
    C = dc.conc(J, T, E, t=t, model='2cxm')
    # Check convergence to T=0 solution
    #err0 = np.linalg.norm(C0-C) # diverges before convergence
    err1 = np.linalg.norm(C1-C)
    err2 = np.linalg.norm(C2-C)
    err3 = np.linalg.norm(C3-C)
    #assert err1 < err0
    assert err2 < err1
    assert err3 < err2
    assert err3/np.linalg.norm(C) < 1e-1

    # Check exceptions
    E = -0.5
    T = [6,12]
    try:
        C2 = dc.conc(J, T, E, t=t, model='2cxm')
    except:
        assert True
    else:
        assert False



def test_flux_2cxm():
    # Compare against ncomp
    t = np.linspace(0, 20, 10)
    J = np.ones(len(t))
    J2c = np.stack((J, np.zeros(J.size)))

    T = [6,12]
    E = 0.1
    J0 = dc.flux(J, T, E, t=t, model='2cxm')
    E = [[1-E,1],[E,0]]
    J1 = dc.flux(J2c, T, E, t=t, model='ncomp')[0,0,:]
    assert np.linalg.norm(J1-J0)/np.linalg.norm(J1) < 1e-9

    E = 0.5
    J0 = dc.flux(J, T, E, t=t, model='2cxm')
    E = [[1-E,1],[E,0]]
    J1 = dc.flux(J2c, T, E, t=t, model='ncomp')[0,0,:]
    assert np.linalg.norm(J1-J0)/np.linalg.norm(J1) < 1e-9


    # # test boundary case: E=1
    E = 0.5
    T = [6,12]
    J0 = dc.flux(J, T, E, t=t, model='2cxm')
    E = 0.95
    J1 = dc.flux(J, T, E, t=t, model='2cxm')
    E = 0.999
    J2 = dc.flux(J, T, E, t=t, model='2cxm')
    E = 1
    J3 = dc.flux(J, T, E, t=t, model='2cxm')
    # Check convergence to solution
    err0 = np.linalg.norm(J0-J3)
    err1 = np.linalg.norm(J1-J3)
    err2 = np.linalg.norm(J2-J3)
    assert err1 < err0
    assert err2 < err1
    assert err2 < 1e-2

    # # test boundary case: Tp=0
    E = 0.5
    T = [6,12]
    J0 = dc.flux(J, T, E, t=t, model='2cxm')
    T[0] = 1
    J1 = dc.flux(J, T, E, t=t, model='2cxm')
    T[0] = 0.1
    J2 = dc.flux(J, T, E, t=t, model='2cxm')
    T[0] = 0.01
    J3 = dc.flux(J, T, E, t=t, model='2cxm')
    # Check convergence to solution
    err0 = np.linalg.norm(J0-J3)
    err1 = np.linalg.norm(J1-J3)
    err2 = np.linalg.norm(J2-J3)
    assert err1 < err0
    assert err2 < err1
    assert err2 < 1e-2

    # # test boundary case: Tp=0, Te=inf
    E = 0.5
    T = [6,12]
    J0 = dc.flux(J, T, E, t=t, model='2cxm')
    T[0] = 0.1
    T[1] = 100
    J1 = dc.flux(J, T, E, t=t, model='2cxm')
    T[0] = 0.01
    T[1] = 1000
    J2 = dc.flux(J, T, E, t=t, model='2cxm')
    T[0] = 0
    T[1] = np.inf
    J3 = dc.flux(J, T, E, t=t, model='2cxm')
    # Check convergence to solution
    err0 = np.linalg.norm(J0[1:]-J3[1:])
    err1 = np.linalg.norm(J1[1:]-J3[1:])
    err2 = np.linalg.norm(J2[1:]-J3[1:])
    assert err1 < err0
    assert err2 < err1
    assert err2 < 1e-2

    T[0] = 0.0001
    T[1] = 100
    J1 = dc.flux(J, T, E, t=t, model='2cxm')
    T[0] = 0.0
    T[1] = 100
    J2 = dc.flux(J, T, E, t=t, model='2cxm')
    assert np.linalg.norm(J1[1:]-J2[1:]) < 1e-6*np.linalg.norm(J2[1:])


def test_conc():
    # We only need to check the exceptions 
    # as all other conditions are already covered by above tests
    t = np.linspace(0, 20, 10)
    J = np.ones(len(t))
    T = [6,12]
    E = 0.1
    try:
        dc.conc(J, T, E, t=t, model='blabla') 
    except:
        assert True
    else:
        assert False  

def test_flux():
    # We only need to check the exceptions 
    # as all other conditions are already covered by above tests
    t = np.linspace(0, 20, 10)
    J = np.ones(len(t))
    T = [6,12]
    E = 0.1
    try:
        J1 = dc.flux(J, T, E, t=t, model='blabla') 
    except:
        assert True
    else:
        assert False   


if __name__ == "__main__":

    test_res_trap()
    test_prop_trap()
    test_conc_trap()
    test_flux_trap()

    test_conc_pass()
    test_flux_pass()
    test_res_pass()
    test_prop_pass()

    test_conc_comp()
    test_flux_comp()
    test_res_comp()
    test_prop_comp()

    test_conc_plug()
    test_flux_plug()
    test_res_plug()
    test_prop_plug()

    test_conc_chain()
    test_flux_chain()
    test_prop_chain()
    test_res_chain()

    test_conc_step()
    test_flux_step()
    test_prop_step()
    test_res_step()

    test_conc_free()
    test_flux_free()
    test_prop_free()
    test_res_free()

    test__K_2comp()
    test__K_ncomp()
    test__J_ncomp()
    test_conc_ncomp_prop()
    test_conc_ncomp_diag()

    test_conc_ncomp()
    test_flux_ncomp()
    test_res_ncomp()
    test_prop_ncomp()

    test_conc_2comp()
    test_flux_2comp()
    test_res_2comp()
    test_prop_2comp()

    test_conc_nscomp()
    test_flux_nscomp()

    test_conc_mmcomp()
    test_flux_mmcomp()

    test_flux_pfcomp()

    test_conc_2cxm()
    test_flux_2cxm()

    test_conc()
    test_flux()

    print('All pk tests passed!!')