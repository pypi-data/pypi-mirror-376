import numpy as np
from nhatc import ATCVariable, Coordinator, ProgrammaticSubProblem

np.random.seed(0)

coordinator = Coordinator(verbose=True)
coordinator.set_variables([
    ATCVariable('a1', 0, 0, True, [3], 0.1, 10),
    ATCVariable('b1', 1, 0, False, [4], 0.1, 10),
    ATCVariable('w1', 2, 0, False, [5], 0.1, 10),
    ATCVariable('a2', 3, 1, False, [0], 0.1, 10),
    ATCVariable('b2', 4, 1, True, [1], 0.1, 10),
    ATCVariable('w2', 5, 1, False, [2], 0.1, 10),
])


def sp1_objective(X):
    b, w = X[[1, 2]]
    a = w + (1/(b**2))
    f = (a + b) / w
    y = [a]
    return f, y


def sp2_objective(X):
    a, w = X[[3, 5]]
    b = (a/2) * w
    y = [b]
    f = 0
    return f, y


def sp2_ineq(X):
    # g(x) ≥ 0
    b, w = X[[4, 5]]
    return 3 - (b + w)  # 3 - ( b + w ) ≥ 0


sp1 = ProgrammaticSubProblem(0)
sp1.set_objective(sp1_objective)
sp2 = ProgrammaticSubProblem(1)
sp2.set_objective(sp2_objective)
sp2.set_ineqs([sp2_ineq])

coordinator.set_subproblems([sp1, sp2])

x0 = coordinator.get_midpoint_x0()

print(f'x0 = \t {x0}')
res = coordinator.optimize(1000, x0,
                           beta=2.0,
                           gamma=0.25,
                           convergence_threshold=1e-6,
                           NI=60,
                           method='slsqp')

if res:
    if res.successful_convergence:
        print(f'Reached convergence')
    else:
        print(f'FAILED to reach convergence')

    print(f'Process time: {res.time} seconds')
    print("Verification against objectives:")
    print(f'f* = {res.f_star[0]}')
    print(f'Epsilon = {res.epsilon} ')

    print('x*:')
    for i, x_i in enumerate(res.x_star):
        name = coordinator.variables[i].name
        lb = coordinator.variables[i].lb
        ub = coordinator.variables[i].ub

        print(f'{name}\t[{lb}; {ub}]\tvalue: {x_i}')
else:
    print('Catastrophic failure')


