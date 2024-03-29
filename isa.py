import json
from enum import Enum
from collections import namedtuple


class Opcode(str, Enum):
    ST = "st"
    LD = "ld"
    INPUT = "input"
    PRINT = "print"
    JLE = "jle"  # jump if less or equals
    JL = "jl"  # jump if less
    JGE = "jge"  # jump if greater or equals
    JG = "jg"  # jump if greater
    JNE = "jne"  # jump if not equals
    JE = "je"  # jump if equals
    DIV = "div"
    ADD = "add"
    SUB = "sub"
    MUL = "mul"
    INC = "inc"
    DEC = "dec"
    JUMP = "jmp"
    PUSH = "push"
    POP = "pop"
    HALT = "halt"
    MOD = "mod"


class Term(namedtuple("Term", "name arg1 arg2")):
    """"""

def write_code(filename, code):
    with open(filename, "w", encoding='utf-8') as file:
        # for i in code:
        #     file.write(str(i) + "\n")
        file.write(json.dumps(code, indent=4))


def read_code(filename):
    with open(filename, encoding='utf-8') as file:
        code = json.loads(file.read())

    for instr in code:
        instr["opcode"] = Opcode(instr["opcode"])
    return code