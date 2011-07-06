# Copyright (C) 1996-2011 Power System Engineering Research Center
# Copyright (C) 2010-2011 Richard Lincoln
#
# PYPOWER is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# PYPOWER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PYPOWER. If not, see <http://www.gnu.org/licenses/>.

"""Solves the power flow using a Gauss-Seidel method.
"""

import sys

from numpy import linalg, conj, r_, Inf, asscalar

from ppoption import ppoption


def gausspf(Ybus, Sbus, V0, ref, pv, pq, ppopt=None):
    """Solves the power flow using a Gauss-Seidel method.

    Solves for bus voltages given the full system admittance matrix (for
    all buses), the complex bus power injection vector (for all buses),
    the initial vector of complex bus voltages, and column vectors with
    the lists of bus indices for the swing bus, PV buses, and PQ buses,
    respectively. The bus voltage vector contains the set point for
    generator (including ref bus) buses, and the reference angle of the
    swing bus, as well as an initial guess for remaining magnitudes and
    angles. C{ppopt} is a PYPOWER options vector which can be used to
    set the termination tolerance, maximum number of iterations, and
    output options (see C{ppoption} for details). Uses default options
    if this parameter is not given. Returns the final complex voltages,
    a flag which indicates whether it converged or not, and the number
    of iterations performed.

    @see: L{runpf}
    """
    ## default arguments
    if ppopt is None:
        ppopt = ppoption()

    ## options
    tol     = ppopt['PF_TOL']
    max_it  = ppopt['PF_MAX_IT_GS']
    verbose = ppopt['VERBOSE']

    ## initialize
    converged = 0
    i = 0
    V = V0.copy()
    #Va = angle(V)
    Vm = abs(V)

    ## set up indexing for updating V
    npv = len(pv)
    npq = len(pq)
    pvpq = r_[pv, pq]

    ## evaluate F(x0)
    mis = V * conj(Ybus * V) - Sbus
    F = r_[  mis[pvpq].real,
             mis[pq].imag   ]

    ## check tolerance
    normF = linalg.norm(F, Inf)
    if verbose > 0:
        sys.stdout.write('(Gauss-Seidel)\n')
    if verbose > 1:
        sys.stdout.write('\n it    max P & Q mismatch (p.u.)')
        sys.stdout.write('\n----  ---------------------------')
        sys.stdout.write('\n%3d        %10.3e' % (i, normF))
    if normF < tol:
        converged = 1
        if verbose > 1:
            sys.stdout.write('\nConverged!\n')

    ## do Gauss-Seidel iterations
    while (not converged and i < max_it):
        ## update iteration counter
        i = i + 1

        ## update voltage
        ## at PQ buses
        for k in pq[range(npq)]:
            tmp = (conj(Sbus[k] / V[k]) - Ybus[k, :] * V) / Ybus[k, k]
            V[k] = V[k] + asscalar(tmp)

        ## at PV buses
        if npv:
            for k in pv[range(npv)]:
                tmp = (V[k] * conj(Ybus[k,:] * V)).imag
                Sbus[k] = Sbus[k].real + 1j * asscalar(tmp)
                tmp = (conj(Sbus[k] / V[k]) - Ybus[k, :] * V) / Ybus[k, k]
                V[k] = V[k] + asscalar(tmp)
#               V[k] = Vm[k] * V[k] / abs(V[k])
            V[pv] = Vm[pv] * V[pv] / abs(V[pv])

        ## evalute F(x)
        mis = V * conj(Ybus * V) - Sbus
        F = r_[  mis[pv].real,
                 mis[pq].real,
                 mis[pq].imag  ]

        ## check for convergence
        normF = linalg.norm(F, Inf)
        if verbose > 1:
            sys.stdout.write('\n%3d        %10.3e' % (i, normF))
        if normF < tol:
            converged = 1
            if verbose:
                sys.stdout.write('\nGauss-Seidel power flow converged in '
                                 '%d iterations.\n' % i)

    if verbose:
        if not converged:
            sys.stdout.write('Gauss-Seidel power did not converge in %d '
                             'iterations.' % i)

    return V, converged, i
