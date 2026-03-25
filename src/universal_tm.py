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
    PHASE_INIT = "初始化"
    PHASE_STEP2 = "第2步: 通用图灵机检查被模拟图灵机M，以确定它需要多少个磁带方格来表示M的一个符号。"
    PHASE_STEP3 = "第3步: 初始化磁带2，表示带有输入w的M的磁带，并初始化磁带3以保存起始状态。"
    PHASE_LOOK = "查找转移: 在磁带1上寻找与磁带3上的状态和磁带2当前磁头下的符号相匹配的动作。"
    PHASE_EXEC = "执行转移: 如果找到，修改符号，移动磁带2上的磁头，并改变磁带3上的状态。"
    PHASE_ACCEPT = "接受: M接受，通用图灵机也接受。"
    PHASE_HALT = "停机: M未找到转移规则，拒绝并停机。"
    
    def __init__(self):
        self.mtm = MultiTapeTM(3, "UTM")
        self.phase = self.PHASE_INIT
        self.phase_detail = ""
        self.history = []
        
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
        lines = [f"当前阶段说明: {self.phase}"]
        if self.phase_detail:
            lines.append(f"({self.phase_detail})")
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
        # Offset head and content by 3 units as requested
        offset = 3
        self.tape2_head = offset
        self.mtm.tapes[1].head = offset  # Allows display to track head correctly
        for i, c in enumerate(self.tm_input.replace('_', ' ')):
            code = self._sym_to_code(c)
            self.tape2[i + offset] = code
            # 每个符号后加分隔符0
            self.mtm.tapes[1].content[i + offset] = '1' * code + '0'
                
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
            self.phase_detail = ""
            return True
        if self.steps == 2:
            self.phase = self.PHASE_STEP3
            self.phase_detail = ""
            return True
        
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
        else:
            self.tape2[self.tape2_head] = write
            
        if direction == 1:
            self.tape2_head -= 1
        else:
            self.tape2_head += 1
            
        self.sim_state = next_state
        self.mtm.tapes[2].content = {0: '1' * next_state}
        
        self.mtm.tapes[1].content.clear()
        if self.tape2:
            min_pos = min(self.tape2.keys())
            max_pos = max(self.tape2.keys())
            start_idx = min(min_pos, self.tape2_head)
            end_idx = max(max_pos, self.tape2_head)
        else:
            start_idx = end_idx = self.tape2_head
            
        for p in range(start_idx, end_idx + 1):
            code = self.tape2.get(p)
            if code is not None:
                # 每个符号后加分隔符0
                self.mtm.tapes[1].content[p] = '1' * code + '0'

        self.mtm.tapes[1].head = self.tape2_head
        
        return True

    def _predict_next_instruction(self) -> str:
        if self.halted:
            return "已停机"
        
        # steps is current executed steps.
        # Next step will be steps + 1 logic.
        if self.steps == 0:
             return self.PHASE_STEP2
        if self.steps == 1:
             return self.PHASE_STEP3
        
        # Predicting next transition
        cur_sym = self._cur_symbol()
        state_name = self.inv_state.get(self.sim_state, f"q{self.sim_state}")
        sym_name = self.inv_symbol.get(cur_sym, f"s{cur_sym}")
        
        trans = self._find_trans(self.sim_state, cur_sym)
        if trans is None:
            return "即将停机 (无匹配转移)"
            
        write, direction, next_state = trans
        w_name = self.inv_symbol.get(write, f"s{write}")
        n_name = self.inv_state.get(next_state, f"q{next_state}")
        d_name = "L" if direction == 1 else "R"
        
        return f"查找 δ({state_name}, '{sym_name}') -> 写'{w_name}', 移动{d_name}, 转到{n_name}"

    def show(self, clear: bool = False) -> str:
        if clear:
            os.system('cls' if os.name == 'nt' else 'clear')
            
        lines = [f"=== UTM 步数:{self.steps} ==="]
        
        for tape in self.mtm.tapes:
            t, h = tape.display(3)
            lines.append(f"{tape.name}: {t}")
            
            if "T2" in tape.name:
                 h = " " * 3 + h  # User requested offset

            lines.append(f"{'':>{len(tape.name)+2}}{h}")
            
        lines.append("-" * 40)
        
        # Replace past phase description with Next Action prediction as requested
        next_info = self._predict_next_instruction()
        lines.append(f"下一步操作: {next_info}")
            
        if self.sim_state > 0:
            name = self.inv_state.get(self.sim_state, f"q{self.sim_state}")
            lines.append(f"M状态: {name}")
            
            # 显示M的磁带内容
            if self.tape2:
                lo, hi = min(self.tape2.keys()), max(self.tape2.keys())
                # 确保显示范围包含磁头位置
                lo = min(lo, self.tape2_head)
                hi = max(hi, self.tape2_head)
                tape_disp = ''.join(
                    self.inv_symbol.get(self.tape2.get(p, 1), '_').replace(' ', '_')
                    for p in range(lo, hi + 1)
                )
                lines.append(f"M磁带: {tape_disp}")
        
        out = "\n".join(lines)
        self.history.append(out)
        print(out)
        return out
    
    def save_history(self, filename: str = "utm_execution_log.txt"):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(("\n\n" + "="*50 + "\n\n").join(self.history))
        print(f"\n[提示] 完整运行日志已保存至: {os.path.abspath(filename)}")

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
            self.show()
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
