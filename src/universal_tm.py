"""
通用图灵机模块 (UTM)
基于3带图灵机实现
"""

import time
import os
from typing import Dict, List, Tuple, Optional
from .multi_tape_tm import MultiTapeTM, Tape, BLANK
from .tm_encoder import TuringMachineEncoder


class UniversalTM:
    # 运行阶段
    PHASE_INIT = "初始化"
    PHASE_STEP2 = "Step 2: 检查M编码，确定符号表示位数"
    PHASE_STEP3_T2 = "Step 3: 初始化磁带2（M的工作磁带）"
    PHASE_STEP3_T3 = "Step 3: 初始化磁带3（M的状态）"
    PHASE_LOOK = "查找转移: 在磁带1上查找匹配的转移"
    PHASE_EXEC = "执行转移: 修改符号、移动磁头、更新状态"
    PHASE_ACCEPT = "M接受"
    PHASE_HALT = "M停机"
    
    def __init__(self):
        self.mtm = MultiTapeTM(3, "UTM")
        self.phase = self.PHASE_INIT
        self.phase_detail = ""
        
        self.tm_encoding = ""
        self.tm_input = ""
        
        self.parsed_trans: List[Tuple] = []
        self.state_map: Dict[str, int] = {}
        self.symbol_map: Dict[str, int] = {}
        self.inv_state: Dict[int, str] = {}
        self.inv_symbol: Dict[int, str] = {}
        
        self.sim_state = 1
        self.tape2: Dict[int, int] = {}
        self.tape2_head = 0
        
        self.steps = 0
        self.halted = False
        self.accepted = False
        
        self.mtm.display_extra = self._phase_info
        
    def _phase_info(self) -> str:
        lines = [f"阶段: {self.phase}"]
        if self.phase_detail:
            lines.append(f"说明: {self.phase_detail}")
        if self.sim_state > 0:
            name = self.inv_state.get(self.sim_state, f"q{self.sim_state}")
            lines.append(f"M当前状态: {name}")
        return "\n".join(lines)
    
    def load(self, json_path: str = None, tm_def: dict = None):
        encoder = TuringMachineEncoder()
        if json_path:
            tm_def = encoder.load_from_json(json_path)
        self.tm_encoding = encoder.encode(tm_def)
        
        self.state_map = encoder.get_state_map()
        self.symbol_map = encoder.get_symbol_map()
        self.inv_state = {v: k for k, v in self.state_map.items()}
        self.inv_symbol = {v: k for k, v in self.symbol_map.items()}
        self.tm_input = encoder.get_input_string()
        
        self._parse_transitions()
        encoder.print_info()
        print(f"\n编码: {self.tm_encoding}")
        print(f"输入: {self.tm_input}")
        
    def _parse_transitions(self):
        self.parsed_trans = []
        for t in self.tm_encoding.split('00'):
            parts = t.split('0')
            if len(parts) == 5:
                self.parsed_trans.append(tuple(len(p) for p in parts))
                
    def _sym_to_code(self, sym: str) -> int:
        if sym in (BLANK, ' '):
            return 1
        return self.symbol_map.get(sym, 1)
    
    def init(self):
        self.phase = self.PHASE_INIT
        self.steps = 0
        self.halted = False
        self.accepted = False
        self.sim_state = 1
        
        # 磁带1: M111w
        tape1 = self.tm_encoding + "111"
        for c in self.tm_input:
            if c in (BLANK, '_'):
                tape1 += '1'
            else:
                tape1 += '1' * self._sym_to_code(c)
            tape1 += '0'
        if tape1.endswith('0') and self.tm_input:
            tape1 = tape1[:-1]
        
        self.mtm.tapes[0].init(tape1)
        self.mtm.tapes[0].name = "T1(M编码)"
        self.mtm.tapes[1].init("")
        self.mtm.tapes[1].name = "T2(M磁带)"
        self.mtm.tapes[2].init("")
        self.mtm.tapes[2].name = "T3(M状态)"
        
        # 初始化磁带2
        self.tape2 = {}
        self.tape2_head = 0
        for i, c in enumerate(self.tm_input.replace('_', ' ')):
            if c != ' ':
                code = self._sym_to_code(c)
                self.tape2[i] = code
                self.mtm.tapes[1].content[i] = '1' * code
                
        # 磁带3: 起始状态
        self.mtm.tapes[2].content[0] = '1'
        self.sim_state = 1
        
    def _find_trans(self, state: int, symbol: int) -> Optional[Tuple]:
        for t in self.parsed_trans:
            if t[0] == state and t[1] == symbol:
                return (t[2], t[3], t[4])
        return None
    
    def _cur_symbol(self) -> int:
        return self.tape2.get(self.tape2_head, 1)
    
    def step(self) -> bool:
        if self.halted:
            return False
        self.steps += 1
        
        if self.steps == 1:
            self.phase = self.PHASE_STEP2
            self.phase_detail = "The UTM examines M to see how many tape squares needed per symbol."
            return True
        if self.steps == 2:
            self.phase = self.PHASE_STEP3_T2
            self.phase_detail = "Initialize Tape 2 to represent the tape of M with input w."
            return True
        if self.steps == 3:
            self.phase = self.PHASE_STEP3_T3
            self.phase_detail = "Initialize Tape 3 to hold the start state."
            return True
        
        # 查找转移
        self.phase = self.PHASE_LOOK
        cur_sym = self._cur_symbol()
        state_name = self.inv_state.get(self.sim_state, f"q{self.sim_state}")
        sym_name = self.inv_symbol.get(cur_sym, f"s{cur_sym}")
        self.phase_detail = f"查找 δ({state_name}, '{sym_name}')"
        
        trans = self._find_trans(self.sim_state, cur_sym)
        if trans is None:
            self.phase = self.PHASE_HALT
            self.phase_detail = "无匹配转移"
            self.halted = True
            return False
            
        write, direction, next_state = trans
        
        self.phase = self.PHASE_EXEC
        w_name = self.inv_symbol.get(write, f"s{write}")
        n_name = self.inv_state.get(next_state, f"q{next_state}")
        d_name = "L" if direction == 1 else "R"
        self.phase_detail = f"写'{w_name}', 移动{d_name}, 转到{n_name}"
        
        # 写
        if write == 1:
            self.tape2.pop(self.tape2_head, None)
            self.mtm.tapes[1].content.pop(self.tape2_head, None)
        else:
            self.tape2[self.tape2_head] = write
            self.mtm.tapes[1].content[self.tape2_head] = '1' * write
            
        # 移动
        if direction == 1:
            self.tape2_head -= 1
            self.mtm.tapes[1].head -= 1
        else:
            self.tape2_head += 1
            self.mtm.tapes[1].head += 1
            
        # 更新状态
        self.sim_state = next_state
        self.mtm.tapes[2].content = {0: '1' * next_state}
        
        return True
    
    def show(self, clear: bool = False) -> str:
        if clear:
            os.system('cls' if os.name == 'nt' else 'clear')
            
        lines = [f"=== UTM 步数:{self.steps} ==="]
        
        for tape in self.mtm.tapes:
            t, h = tape.display(3)
            lines.append(f"{tape.name}: {t}")
            lines.append(f"{'':>{len(tape.name)+2}}{h}")
            
        lines.append("-" * 40)
        lines.append(f"阶段: {self.phase}")
        if self.phase_detail:
            lines.append(f"说明: {self.phase_detail}")
            
        if self.sim_state > 0:
            name = self.inv_state.get(self.sim_state, f"q{self.sim_state}")
            lines.append(f"M状态: {name}")
            
            # 显示M的磁带内容
            if self.tape2:
                lo, hi = min(self.tape2.keys()), max(self.tape2.keys())
                tape_disp = ''.join(
                    self.inv_symbol.get(self.tape2.get(p, 1), '_').replace(' ', '_')
                    for p in range(lo, hi + 1)
                )
                lines.append(f"M磁带: {tape_disp}")
        
        out = "\n".join(lines)
        print(out)
        return out
    
    def run_interactive(self, max_steps: int = 1000) -> bool:
        self.show(True)
        while not self.halted and self.steps < max_steps:
            input("按Enter继续...")
            self.step()
            self.show(True)
        return self.accepted
    
    def run_auto(self, delay: float = 0.5, max_steps: int = 1000) -> bool:
        self.show(True)
        while not self.halted and self.steps < max_steps:
            time.sleep(delay)
            self.step()
            self.show(True)
        return self.accepted
    
    def run_silent(self, max_steps: int = 10000) -> bool:
        while not self.halted and self.steps < max_steps:
            self.step()
        return self.accepted


if __name__ == '__main__':
    test = {
        "q1": {
            "0": {"write": "0", "move": "right", "nextState": "q1"},
            " ": {"write": " ", "move": "left", "nextState": "q2"}
        },
        "q2": {
            "0": {"write": "1", "move": "left", "nextState": "q2"},
            " ": {"write": " ", "move": "right", "nextState": "qf"}
        },
        "input": ["00"]
    }
    
    utm = UniversalTM()
    utm.load(tm_def=test)
    utm.init()
    utm.run_interactive(50)
