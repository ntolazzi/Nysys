from enum import Enum
from dataclasses import dataclass
import sys

comp_binary_map = {
    "0": "0101010",
    "1": "0111111",
    "-1": "0111010",
    "D": "0001100",
    "A": "0110000",
    "M": "1110000",
    "!D": "0001101",
    "!A": "0110001",
    "!M": "1110001",
    "-D": "0001111",
    "-A": "0110011",
    "-M": "1110011",
    "D+1": "0011111",
    "A+1": "0110111",
    "M+1": "1110111",
    "D-1": "0001110",
    "A-1": "0110010",
    "M-1": "1110010",
    "D+A": "0000010",
    "D+M": "1000010",
    "D-A": "0010011",
    "D-M": "1010011",
    "A-D": "0000111",
    "M-D": "1000111",
    "D&A": "0000000",
    "D&M": "1000000",
    "D|A": "0010101",
    "D|M": "1010101"
}

dest_binary_map = {
    "null": "000",
    "M": "001",
    "D": "010",
    "MD": "011",
    "A": "100",
    "AM": "101",
    "AD": "110",
    "ADM": "111",
}

jump_binary_map = {
    "null": "000",
    "JGT": "001",
    "JEQ": "010",
    "JGE": "011",
    "JLT": "100",
    "JNE": "101",
    "JLE": "110",
    "JMP": "111",
}

predefined_symbols = {
    "R0": 0,
    "R1": 1,
    "R2": 2,
    "R3": 3,
    "R4": 4,
    "R5": 5,
    "R6": 6,
    "R7": 7,
    "R8": 8,
    "R9": 9,
    "R10": 10,
    "R11": 11,
    "R12": 12,
    "R13": 13,
    "R14": 14,
    "R15": 15,
    "SP": 0,
    "LCL": 1,
    "ARG": 2,
    "THIS": 3,
    "THAT": 4,
    "SCREEN": 16384,
    "KBD": 24576,

}


class InstType(Enum):
    A_Inst = 1
    C_Inst = 2
    L_Inst = 3


@dataclass
class CInstruction:
    dest: str
    comp: str
    jump: str

    def __str__(self):
        return f"dest={self.dest},comp={self.comp},jump={self.jump}"


def load_file(filename: str) -> str:
    with open(filename) as fh:
        return fh.read()


def translate_c_instruction(inst: CInstruction) -> str:
    # print(inst)
    return f"111{comp_binary_map[inst.comp]}{dest_binary_map[inst.dest]}{jump_binary_map[inst.jump]}"


def translate_a_instruction(constant: int) -> str:
    if constant >= 2 ** 15:
        raise ValueError("Number outside of range [0,32767]")
    two_complement = format(constant, '015b')
    return f"0{two_complement}"


class SymbolTable:
    def __init__(self):
        self.symbols = predefined_symbols
        self.variable_counter = 16

    def __contains__(self, item):
        return item in self.symbols

    def add(self, symbol, address):
        self.symbols[symbol] = address
        # print(f"Added label {symbol} to {address}")

    def add_free(self, symbol):
        self.symbols[symbol] = self.variable_counter
        # print(f"Added variable {symbol} to {self.variable_counter}")
        self.variable_counter += 1

    def get(self, symbol):
        return self.symbols[symbol]


class Parser:
    def __init__(self, file_content: str) -> None:
        super().__init__()
        self.file_content = file_content.splitlines()
        self.total_lines = len(self.file_content)
        self.current_line = None
        self.current_inst_index = None
        self.current_inst = None
        self.symbols = SymbolTable()

    def has_more_lines(self) -> bool:
        if self.current_line is None:
            return True

        if self.total_lines - self.current_line <= 1:
            return False
        else:
            return True

    def get_current_inst_type(self) -> InstType:
        if self.current_inst.startswith("("):
            return InstType.L_Inst
        elif self.current_inst.startswith("@"):
            return InstType.A_Inst
        else:
            return InstType.C_Inst

    def get_current_inst_symbol(self) -> str:
        if self.current_inst.startswith("("):
            return self.current_inst.strip("()")
        elif self.current_inst.startswith("@"):
            return self.current_inst.strip("@")

    def decode_current_c_inst(self) -> CInstruction:
        inst = self.current_inst

        if "=" in inst:
            inst_split = inst.split("=")
            dest = inst_split[0]
            inst = inst_split[1]
        else:
            dest = "null"

        if ";" in inst:
            inst_split = inst.split(";")
            jump = inst_split[1]
            inst = inst_split[0]
        else:
            jump = "null"

        comp = inst

        return CInstruction(dest, comp, jump)

    @staticmethod
    def clear_expression(expression: str) -> str:
        expression = expression.strip()
        if expression.startswith("//"):
            return ""
        if "//" in expression:
            expression = expression.split("//")[0]
        expression = expression.replace(" ", "")
        return expression

    def advance(self):
        is_valid_line = False
        while not is_valid_line:
            if not self.has_more_lines():
                raise EOFError("EOF reached")
            if self.current_line is None:
                self.current_line = 0
            else:
                self.current_line += 1

            candidate = self.clear_expression(self.file_content[self.current_line])
            if candidate:
                is_valid_line = True
                self.current_inst = candidate

    def increment_inst_index(self):
        if self.current_inst_index is None:
            self.current_inst_index = 0
        else:
            self.current_inst_index += 1



def assemble(parser: Parser) -> str:
    translated_output = ""

    while parser.has_more_lines():
        parser.advance()
        inst_type = parser.get_current_inst_type()
        if inst_type == InstType.L_Inst:
            label = parser.get_current_inst_symbol()
            if label not in parser.symbols:
                parser.symbols.add(label, parser.current_inst_index + 1)
            else:
                raise ValueError(f"{parser.current_line}: {label} already defined")
            continue
        parser.increment_inst_index()

    parser.current_line = None
    parser.current_inst = None
    parser.current_inst_index = None

    while parser.has_more_lines():
        parser.advance()
        inst_type = parser.get_current_inst_type()
        if inst_type == InstType.C_Inst:
            translated_inst = translate_c_instruction(parser.decode_current_c_inst())
        elif inst_type == InstType.A_Inst:
            a_target = parser.get_current_inst_symbol()
            try:
                value = int(a_target)
            except ValueError:
                if a_target not in parser.symbols:
                    parser.symbols.add_free(a_target)
                value = parser.symbols.get(a_target)
                # print(f"{a_target} = {value}")
            translated_inst = translate_a_instruction(value)
        elif inst_type == InstType.L_Inst:
            continue
        else:
            raise ValueError(f"{parser.current_line}: Could not decode line")

        parser.increment_inst_index()
        translated_output += f"{translated_inst}\n"

    return translated_output[:-1]


def write_file(filepath: str, content: str):
    with open(filepath.split(".")[0] + ".hack", "w") as fh:
        fh.write(content)


def main():
    try:
        filepath = sys.argv[1]
    except IndexError:
        print("Error: Input file missing\nUsage: python assembler.py inputfile.asm")
        sys.exit(1)
    content = load_file(filepath)
    parser = Parser(content)
    assembled_content = assemble(parser)
    write_file(filepath, assembled_content)


if __name__ == '__main__':
    main()
