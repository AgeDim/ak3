import re
import sys

from isa import Opcode, write_code

type2opcode = {
    "st": Opcode.ST,
    "input": Opcode.INPUT,
    "print": Opcode.PRINT,
    "jump": Opcode.JUMP,
    ">": Opcode.JLE,
    ">=": Opcode.JL,
    "<": Opcode.JGE,
    "<=": Opcode.JG,
    "==": Opcode.JNE,
    "%": Opcode.MOD,
    "-": Opcode.SUB,
    "+": Opcode.ADD,
    "!=": Opcode.JE,
    "/": Opcode.DIV,
    "*": Opcode.MUL,
    "inc": Opcode.INC,
    "dec": Opcode.DEC,
    "push": Opcode.PUSH,
    "pop": Opcode.POP
}

address_data_mem = 0x0
address_instr_mem = 0x0
address2var = []
stack = 0
variables = set()
reg_counter = 3


def get_prev_data_reg():
    if reg_counter == 3:
        return 11
    else:
        return reg_counter - 1


condition_signs = {">", ">=", "<", "<=", "==", "!="}
simple_operations = {"*", "/", "%", "+", "-"}
div_operations = {"/", "%"}

regex_patterns = {
    "ld": r"let[\s]+[a-zA-z]+[\s]+=[\s]+([0-9]+|(\"|\').*(\"|\'));",
    "whileWithExtraActions": r"while[\s]*\(([a-zA-z]+[\s]*(\%|\/|\+|\-|\*)[\s]*([0-9]+|[a-zA-z]+)"
                             r"|[a-zA-z]+[\s]*)[\s]+(>|>=|<|<=|!=|==)[\s]+([0-9]+|[a-zA-Z]+|([a-zA-Z]+[\s]*"
                             r"(\%|\/|\+|\-|\*)[\s]*([0-9]+|[a-zA-Z]+))|"
                             r"([a-zA-Z]+(\%|\/|\+|\-|\*)([0-9]+|[a-zA-Z]+)))\)",
    "ifWithExtraActions": r"if[\s]*\(([a-zA-z]+[\s]*(\%|\/|\+|\-|\*)[\s]*([0-9]+|[a-zA-z]+)|"
                          r"[a-zA-z]+[\s]*)[\s]+(>|>=|<|<=|!=|==)[\s]+([0-9]+|[a-zA-Z]+|([a-zA-Z]+[\s]*(\%|\/|\+|\-|\*)"
                          r"[\s]*([0-9]+|[a-zA-Z]+))|([a-zA-Z]+(\%|\/|\+|\-|\*)([0-9]+|[a-zA-Z]+)))\)",
    "assign": r"[a-zA-Z]+[\s]+=[\s]+((([a-zA-Z]+|[0-9]+)[\s]+(\%|\/|\+|\-|\*)[\s]*"
              r"([a-zA-Z]+|[0-9]+))|[0-9]+|[a-zA-Z]+);",
    "alternative": r"else",
    "input": r"input\([a-zA-Z]+\);",
    "print": r"print\([a-zA-Z]+\);"
}

banned_symbols = {'{', '}'}

res_code = []
jmp_stack = []
last_op = ''


def parse(filename):
    with open(filename, encoding="utf-8") as file:
        code = file.read()
    code = code.split("\n")
    return code


def translate(filename):
    global address_instr_mem, stack
    temp = parse(filename)
    code = []
    for i in temp:
        i = i.strip()
        code.append(i)

    for i in range(0, len(code)):
        if re.fullmatch(regex_patterns.get("ld"), code[i]) is not None:
            parse_ld_instr(code[i])

        elif re.fullmatch(regex_patterns.get("whileWithExtraActions"), code[i]) is not None:
            last_operation = "while"
            jmp_stack.append({"com_addr": address_instr_mem, "arg": 0, "type": "while"})
            res_code.append(parse_condition(code[i], last_operation))
            address_instr_mem += 1

        elif re.fullmatch(regex_patterns.get("ifWithExtraActions"), code[i]) is not None:
            last_operation = "if"
            address_instr_mem += 1
            jmp_stack.append({"com_addr": address_instr_mem, "arg": 0, "type": "if"})
            res_code.append(parse_condition(code[i], last_operation))

        elif re.fullmatch(regex_patterns.get("assign"), code[i]) is not None:
            parse_assign_condition(code[i])

        elif re.fullmatch(regex_patterns.get("input"), code[i]) is not None:
            parse_input(code[i])

        elif re.fullmatch(regex_patterns.get("print"), code[i]) is not None:
            name_of_variable = code[i].replace("print", "").replace("(", "").replace(")", "").replace(";", "")
            var_out(name_of_variable)

        elif re.fullmatch(regex_patterns.get("alternative"), code[i]) is not None:
            jmp_stack.append({"com_addr": address_instr_mem, "arg1": 0, "type": "else"})
            res_code.append({"opcode": type2opcode.get("jump").value})
            address_instr_mem += 1
        elif code[i] == "}":
            jmp_arg = jmp_stack.pop()
            if jmp_arg["type"] == "while":
                res_code.append({"opcode": type2opcode.get("jump").value, "arg2": jmp_arg["com_addr"] + 1})
                address_instr_mem += 1
                res_code[jmp_arg["com_addr"] + 1].update({"arg2": address_instr_mem + 1})
            elif jmp_arg["type"] == "if" and code[i + 1] == "else":
                res_code[jmp_arg["com_addr"] + 1].update({"arg2": address_instr_mem + 2})
            else:
                res_code[jmp_arg["com_addr"]].update({"arg2": address_instr_mem + 1})

    res_code.append({"opcode": Opcode.HALT.value})
    address_instr_mem += 1
    return res_code


def parse_input(row):
    global address_instr_mem
    var_name = row.replace("input(", "").replace(");", "")
    res_code.append({"opcode": type2opcode.get("input").value})
    add_st_instr(get_var_addr_in_mem(var_name))
    address_instr_mem += 1


def parse_ld_instr(row):
    global address_data_mem
    row = row.split(" ")
    value = []
    name = row[1]
    for el in range(0, len(row)):
        if row[el] == "=":
            value = row[el + 1:]
    value[len(value) - 1] = value[len(value) - 1].replace(";", "")

    if value[0][0] == "\"" and value[len(value) - 1][len(value[len(value) - 1]) - 1] == "\"":
        if value[0] == "\"\"":
            add_load_instr(0, 1)
            add_var_to_map(0, row[1], "string")
            add_st_instr(get_var_addr_in_mem(name))
            return
        string_to_load = ""
        for i in value:
            string_to_load += i
            string_to_load += " "
        string_to_load = string_to_load.strip().replace("\"", "")
        if string_to_load == "":
            add_load_instr(0, 1)
        else:
            res = " ".join(row[3:])
            res = res[1:]
            res = res[:-2]
            add_var_to_map(res, row[1], "string")
            addr = get_var_addr_in_mem(row[1])
            for ch in range(0, len(string_to_load)):
                ch_in_ord = ord(string_to_load[ch])
                add_load_instr(ch_in_ord, 1)
                add_st_instr(addr)
                if len(addr) > 3:
                    temp = int(addr[2:])
                    temp += 1
                    addr = "0x" + str(temp)
                else:
                    temp = int(addr[-1])
                    temp +=1
                    addr = "0x" + str(temp)

    else:
        add_var_to_map(row[-1], row[1], "int")
        add_load_instr(int(row[len(row) - 1].replace(";", "")), 1)
        add_st_instr(get_var_addr_in_mem(name))


def parse_condition(row, parsed_type):
    global address_instr_mem
    result = {
        "opcode": 0,
        "arg1": 0
    }
    row = row.replace("(", "").replace(")", "").split(" ")
    if parsed_type == "if":
        row.remove("if")
    else:
        row.remove("while")
    left = []
    right = []
    index = 0
    for i in range(0, len(row)):
        if row[i] in condition_signs:
            index = i
            left = row[:i]
            right = row[i + 1:]
    if len(left) > 1:
        parse_extra_action(left)
    else:
        if left[0] in variables:
            add_load_instr(get_var_addr_in_mem(left[0]), 1)
        elif check_number_in_arg(left[0]):
            add_load_instr(int(left[0]), 1)
    result.update({"opcode": type2opcode.get(row[index]).value})
    if len(right) > 1:
        parse_extra_action(right)
    else:
        if right[0] in variables:
            add_load_instr(get_var_addr_in_mem(right[0]), 1)
            result.update({"arg1": get_var_addr_in_mem(right[0])})
        elif check_number_in_arg(right[0]):
            result.update({"arg1": int(right[0])})
        elif right[0] == "EOF":
            result.update({"arg1": "0"})
    return result


def parse_extra_action(part_to_parse):
    global address_instr_mem
    result = {
        "opcode": 0
    }
    if part_to_parse[1] in simple_operations and part_to_parse[2] != "1":
        result.update({
            "opcode": type2opcode.get(part_to_parse[1]).value
        })
        ## это проверка на число.
        if check_number_in_arg(part_to_parse[0]):
            add_load_instr(part_to_parse[0], 1)
        ## это проверка на переменную.
        else:
            add_load_instr(get_var_addr_in_mem(part_to_parse[0]), 1)
        if check_number_in_arg(part_to_parse[2]):
            result = {
                "opcode": type2opcode.get(part_to_parse[1]).value,
                "arg1": part_to_parse[2]
            }
        else:
            result = {
                "opcode": type2opcode.get(part_to_parse[1]).value,
                "arg1": get_var_addr_in_mem(part_to_parse[2])
            }
        res_code.append(result)
        address_instr_mem += 1
    else:
        if part_to_parse[1] == "+":
            add_load_instr(get_var_addr_in_mem(part_to_parse[0]), 1)
            result.update({
                "opcode": type2opcode.get("inc").value
            })
            res_code.append(result)
            address_instr_mem += 1
        elif part_to_parse[1] == "-":
            add_load_instr(get_var_addr_in_mem(part_to_parse[0]), 1)
            result.update({
                "opcode": type2opcode.get("dec").value
            })
            res_code.append(result)
            address_instr_mem += 1
        else:
            add_load_instr(get_var_addr_in_mem(part_to_parse[0]), 1)
            result = {
                "opcode": type2opcode.get(part_to_parse[1]).value,
                "arg1": part_to_parse[2]
            }
            res_code.append(result)
            address_instr_mem += 1


def parse_assign_condition(row):
    row = row.replace(";", "").split()
    if len(row) == 3:
        if check_number_in_arg(row[2]):
            add_load_instr(row[2], 1)
    else:
        parse_extra_action(row[2:])
    add_st_instr(get_var_addr_in_mem(row[0]))


def var_out(var_name):
    global address_instr_mem
    for var in address2var:
        if var["name"] == var_name:
            if var["type"] == "string":
                addr = get_var_addr_in_mem(var["name"])
                addr = int(addr[2:])
                length = len(str(get_var_value_in_mem(var["name"])))
                for i in range(0, length):
                    add_load_instr(addr, 0)
                    res_code.append({"opcode": "print", "arg1": 1})
                    addr += 1
            else:
                add_load_instr(var["addr"], 1)
                res_code.append({"opcode": "print", "arg1": 0})
            address_instr_mem += 1


def check_number_in_arg(row):
    try:
        float(row)
        return True
    except ValueError:
        return False


def add_load_instr(value, ld_type):
    global address_instr_mem
    if ld_type == 1:
        res_code.append({"opcode": "ld", "arg1": value})
    else:
        res_code.append({"opcode": "ld", "arg1": "0x" + str(value)})
    address_instr_mem += 1


def add_st_instr(addr):
    global address_instr_mem, address_data_mem
    res_code.append({"opcode": "st", "arg1": addr})
    address_instr_mem += 1
    address_data_mem += 1


def add_var_to_map(value, name, var_type):
    global address_data_mem
    variables.add(name)
    if var_type == "string":
        var = {
            "addr": "0x" + str(address_data_mem),
            "name": name,
            "type": var_type,
            "value": value
        }
    else:
        var = {
            "addr": "0x" + str(address_data_mem),
            "name": name,
            "type": var_type
        }
    address2var.append(var)


def add_push_instr():
    global stack, address_instr_mem
    res_code.append({"opcode": type2opcode.get("push").value, "arg1": "rx2"})
    address_instr_mem += 1
    stack += 1


def add_pop_instr():
    global address_instr_mem, stack
    res_code.append({"opcode": type2opcode.get("pop").value, "arg1": "rx2"})
    address_instr_mem += 1
    stack -= 1


def get_var_addr_in_mem(name):
    for var in address2var:
        if var["name"] == name:
            return var["addr"]


def get_var_value_in_mem(name):
    for var in address2var:
        if var["name"] == name:
            return var["value"]

def main(args):
    assert len(args) == 2, "Wrong arguments"
    source, target = args
    opcodes = translate(source)
    write_code(target, opcodes)


if __name__ == '__main__':
    main(sys.argv[1:])
