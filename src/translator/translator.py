from esprima import esprima


def parse(filename):
    with open(filename, encoding="utf-8") as file:
        code = file.read()
    res = esprima.parseScript(code)
    print(res)


if __name__ == '__main__':
    parse('test')
