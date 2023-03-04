import logging
import re
import sys
from src.isa import Opcode, read_code


class DataPath:
    def __init__(self, data_mem_size, instr_mem_size, input_buffer):
        self.data_mem = [0] * data_mem_size
        self.instr_mem = [None] * instr_mem_size
        self.zero_flag = False
        self.neg_flag = False
        self.output_buffer = []
        self.input_buffer = input_buffer
        self.acc = 0
        self.registers = {
            'ir': 0,  # input register
            'or': 0,  # output register
            'ip': 0,  # instruction pointer
            'dp': 0,  # data pointer
            'dr': 0,  # data register

        }

    def set_flags(self, acc):
        if acc == 0:
            self.zero_flag = True
        if acc < 0:
            self.neg_flag = True

    def drop_flags(self):
        self.zero_flag = False
        self.neg_flag = False

    def output(self, string_mode):
        ch = 0
        if string_mode == 1:
            ch = chr(self.acc)
        else:
            ch = self.acc
        logging.info('output: %s << %s', repr(self.output_buffer), repr(ch))
        self.output_buffer.append(ch)

    def write(self, addr):
        self.data_mem[addr] = self.acc

    def latch_program_counter(self, sel_next):
        if sel_next:
            self.registers['ip'] += 1
        else:
            self.registers['ip'] = self.val_to_ld

        assert self.registers['ip'] < len(self.data_mem), "Out of instruction memory: {}".format(self.registers['ip'])

    def latch_register(self, reg):
        self.registers[reg] = self.val_to_ld

    def latch_data_mem_counter(self, sel_next):
        if sel_next:
            self.registers['dp'] += 1
        else:
            self.registers['dp'] = self.val_to_ld

        assert self.registers['dp'] < len(self.instr_mem), "Out of data memory: {}".format(self.registers['dp'])


class ALU:
    def __init__(self, data_path):
        self.data_path = data_path

    def inc(self, acc):
        acc += 1
        self.data_path.set_flags(acc)
        return acc

    def dec(self, acc):
        acc -= 1
        self.data_path.set_flags(acc)
        return acc

    def add(self, acc, right):
        acc = int(acc) + int(right)
        self.data_path.set_flags(acc)
        return acc

    def sub(self, acc, right):
        acc = int(acc) - int(right)
        self.data_path.set_flags(acc)
        return acc

    def mul(self, acc, right):
        acc = int(acc) * int(right)
        self.data_path.set_flags(acc)
        return acc

    def div(self, acc, right):
        return int(int(acc) / int(right))

    def mod(self, acc, right):
        return int(acc) % int(right)


class ControlUnit:
    def __init__(self, program, data_path, alu):
        self.program = program
        self.data_path = data_path
        self.alu = alu
        self._tick = 0

    def __repr__(self):
        return "{{TICK: {}, ACC: {}, IR: {}, OR: {}, IP: {}, DP: {}, DR: {}}}".format(self._tick,self.data_path.acc,
                    self.data_path.registers.get("ir"),
                    self.data_path.registers.get("or"),
                    self.data_path.registers.get("ip"),
                    self.data_path.registers.get("dp"),
                    self.data_path.registers.get("dr"))

    def tick(self):
        self._tick += 1

    def get_current_tick(self):
        return self._tick

    def load_program(self):
        for i in range(0, len(self.program)):
            self.data_path.instr_mem[i] = self.program[i]

    def decode_and_execute_instruction(self):
        cur_instr = self.data_path.instr_mem[self.data_path.registers.get('ip')]
        opcode = cur_instr['opcode']
        jmp_instr = False

        if opcode is Opcode.HALT:
            raise StopIteration()

        if opcode is Opcode.LD:
            if re.match(r'0x\d*', str(cur_instr['arg1'])) is not None:
                temp = int(cur_instr['arg1'].split("x")[1])
                self.data_path.acc = self.data_path.data_mem[temp]
            else:
                self.data_path.acc = cur_instr['arg1']

        if opcode is Opcode.ST:
            self.data_path.write(int(cur_instr['arg1'].split("x")[1]))
            self.data_path.latch_data_mem_counter(True)

        if opcode is Opcode.JUMP:
            self.data_path.val_to_ld = cur_instr['arg2'] + 1
            self.data_path.latch_program_counter(False)
            jmp_instr = True

        if opcode in {Opcode.INC, Opcode.DEC}:
            if opcode is Opcode.INC:
                self.data_path.acc = self.alu.inc(self.data_path.acc)
            if opcode is Opcode.DEC:
                self.data_path.acc = self.alu.dec(self.data_path.acc)

        # сделать адресное
        if opcode in {Opcode.ADD, Opcode.SUB, Opcode.MUL, Opcode.MOD, Opcode.DIV}:
            if re.match(r'0x\d*', str(cur_instr['arg1'])) is not None:
                temp = self.data_path.data_mem[int(cur_instr['arg1'].split("x")[1])]
            else:
                temp = cur_instr['arg1']
            if opcode is Opcode.ADD:
                self.data_path.acc = self.alu.add(self.data_path.acc, temp)
            if opcode is Opcode.SUB:
                self.data_path.acc = self.alu.sub(self.data_path.acc, temp)
            if opcode is Opcode.MUL:
                self.data_path.acc = self.alu.mul(self.data_path.acc, temp)
            if opcode is Opcode.MOD:
                self.data_path.acc = self.alu.mod(self.data_path.acc, temp)
            if opcode is Opcode.DIV:
                self.data_path.acc = self.alu.div(self.data_path.acc, temp)

        # посмотреть прыги
        if opcode in {Opcode.JLE, Opcode.JL, Opcode.JNE, Opcode.JE, Opcode.JG, Opcode.JGE}:
            arg1 = cur_instr['arg1']
            self.data_path.acc = self.alu.sub(self.data_path.acc, arg1)
            self.data_path.val_to_ld = cur_instr['arg2']
            if opcode is Opcode.JLE:
                if self.data_path.zero_flag or self.data_path.neg_flag:
                    self.data_path.latch_program_counter(False)
                    jmp_instr = True

            if opcode is Opcode.JL:
                if not self.data_path.zero_flag and self.data_path.neg_flag:
                    self.data_path.latch_program_counter(False)
                    jmp_instr = True

            if opcode is Opcode.JNE:
                if not self.data_path.zero_flag:
                    self.data_path.latch_program_counter(False)
                    jmp_instr = True

            if opcode is Opcode.JE:
                if self.data_path.zero_flag:
                    self.data_path.latch_program_counter(False)
                    jmp_instr = True

            if opcode is Opcode.JGE:
                if self.data_path.zero_flag or not self.data_path.neg_flag:
                    self.data_path.latch_program_counter(False)
                    jmp_instr = True

            if opcode is Opcode.JG:
                if not self.data_path.zero_flag and not self.data_path.neg_flag:
                    self.data_path.latch_program_counter(False)
                    jmp_instr = True

        if opcode is Opcode.PRINT:
            self.data_path.output(cur_instr['arg1'])

        if opcode is Opcode.INPUT:
            self.data_path.input()
            self.data_path.latch_data_mem_counter(True)
        self.data_path.drop_flags()
        if not jmp_instr:
            self.data_path.latch_program_counter(True)


def simulation(code, input_token, instr_limit, iter_limit):
    data_path = DataPath(2048, instr_limit, input_token)
    alu = ALU(data_path)
    control_unit = ControlUnit(code, data_path, alu)
    instr_counter = 0
    try:
        control_unit.load_program()
    except IndexError:
        logging.error("Too many instructions. Please, increase size of instruction memory.")

    try:
        while True:
            assert iter_limit > instr_counter, "Too many iterations. " \
                                               "Please, increase iteration limit or correct your program."
            control_unit.decode_and_execute_instruction()
            instr_counter += 1
            logging.debug(repr(control_unit))
    except EOFError:
        logging.info('Input buffer is empty!')
    except StopIteration:
        instr_counter += 1
        pass
    return control_unit.data_path.output_buffer, control_unit.get_current_tick(), instr_counter


def main(args):
    code_file = ""
    input_file = ""
    assert len(args) == 2, "Wrong amount of arguments. Please, read instruction carefully."
    if len(args) == 2:
        code_file, input_file = args

    input_token = ""
    if input_file != "":
        with open(input_file, encoding="utf-8") as file:
            input_text = file.read()
            input_token = []
            for ch in input_text:
                input_token.append(ch)

    code = read_code(code_file)
    output, ticks, instr_amount = simulation(code, input_token, instr_limit=2048, iter_limit=100000000)
    logging.info("output:  %s, ticks: %s", repr(output), repr(ticks))
    print("Output buffer: {} | ticks: {} | amount_instr: {}".format(
        ''.join(map(str, output)),
        repr(ticks),
        repr(instr_amount))
    )


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.DEBUG)
    main(sys.argv[1:])
