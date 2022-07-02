from enum import Enum
from dataclasses import dataclass

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
    "DM": "011",
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


class InstType(Enum):
    A_Inst = 1
    C_Inst = 2
    L_Inst = 3


@dataclass
class CInstruction:
    dest: str
    comp: str
    jump: str


def load_file(filename: str) -> str:
    with open(filename) as fh:
        return fh.read()


def translate_c_instruction(inst: CInstruction) -> str:
    return f"111{comp_binary_map[inst.comp]}{dest_binary_map[inst.dest]}{jump_binary_map[inst.jump]}"


def translate_a_instruction(constant: str) -> str:
    constant = int(constant)
    if constant >= 2 ** 14 or constant <= -2 ** 14:
        raise ValueError("Number outside of range [-16384,16383]")
    two_complement = format(constant if constant >= 0 else (1 << 15) + constant, '015b')
    return f"0{two_complement}"


class Parser:
    def __init__(self, file_content: str) -> None:
        super().__init__()
        self.file_content = file_content.splitlines()
        self.total_lines = len(self.file_content)
        self.current_line = None
        self.current_inst = None

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
        else:
            raise ValueError("Does not start with '(' or '@'")

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
            expression = expression.split("")[0]
        expression.replace(" ", "")
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


if __name__ == '__main__':
    filepath = "xxx"
    content = load_file(filepath)
    parser = Parser(content)
    translated_output = ""
    while parser.has_more_lines():
        parser.advance()
        type = parser.get_current_inst_type()
        if type == InstType.C_Inst:
            translated_inst = translate_c_instruction(parser.decode_current_c_inst())
        elif type == InstType.A_Inst:
            translated_inst = translate_a_instruction(parser.get_current_inst_symbol())
        else:
            raise NotImplementedError("Type not implemented")
        translated_output += f"{translated_inst}\n"

    with open(filepath.split(".")[0] + ".hack", "w") as fh:
        fh.write(translated_output)
