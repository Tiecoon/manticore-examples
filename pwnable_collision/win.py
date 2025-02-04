#!/usr/bin/env python3.6
"""
pwnable - collision challenge

    $ python win.py 
    
    Solves collision challenge from pwnable.kr,
    using symbolic execution to determine edge cases that
    can trigger a hash collision.

"""
from manticore.native import Manticore
from manticore.core.smtlib import operators


# initialize Manticore object with symbolic input in
# argv[1]. We can eventually solve for this through
# state.input_symbol
m = Manticore('./col', ['+' * 20])
m.context['solution'] = None
m.context['argv1'] = None


@m.init
def init(initial_state):
    """ define constraints for symbolic ARGV before execution """

    # determine argv[1] from state.input_symbols by label name
    argv1 = next(sym for sym in initial_state.input_symbols if sym.name == 'ARGV1')
    if argv1 is None:
        raise Exception("ARGV was not made symbolic")

    # apply constraint for only ASCII characters
    for i in range(20):
        initial_state.constrain(operators.AND(ord(' ') <= argv1[i], argv1[i] <= ord('}')))

    # store argv1 in global state
    with m.locked_context() as context:
        context['argv1'] = argv1


# add fail_state callback to abandon
# paths we don't care about
def fail_state(state):
    print("Fail state! Abandoning.")
    state.abandon()


for addr in [0x400c2f, 0x400be7, 0x400bac]:
    m.add_hook(addr, fail_state)


@m.hook(0x400ba6)
def skip_syscalls(state):
    """ skip error-checking syscalls """
    state.cpu.EIP = 0x400bfa


@m.hook(0x400c1c)
def success_state(state):
    """ since input is symbolicated in argv, we search in 
    state.input_symbols to find the label """
    with m.locked_context() as context:
        context['solution'] = state.solve_one(context['argv1'], 20)
    m.terminate()


# run Manticore, and print solution
m.verbosity(2)
m.run()

print("EDGE CASE: ", m.context['solution'])
