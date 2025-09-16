
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
import json

# get the current program
# here currentProgram is predefined

out = {}

program = currentProgram
decompinterface = DecompInterface()
decompinterface.openProgram(program);
functions = program.getFunctionManager().getFunctions(True)
for function in list(functions):
    #print(function)
    # decompile each function
    tokengrp = decompinterface.decompileFunction(function, 0, ConsoleTaskMonitor())
    #print(tokengrp.getDecompiledFunction().getC())
    out[function.getName()] = { "c": tokengrp.getDecompiledFunction().getC(), "sig": tokengrp.getDecompiledFunction().getSignature() }

print("===REAL JSON OUTPUT===")
print(json.dumps(out))
print("===END JSON OUTPUT===")