"""
多带图灵机模块
"""

import time
import os
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field

BLANK = '_'


@dataclass
class Tape:
    content: Dict[int, str] = field(default_factory=dict)
    head: int = 0
    name: str = ""
    
    def read(self) -> str:
        return self.content.get(self.head, BLANK)
    
    def write(self, symbol: str) -> None:
        if symbol == BLANK:
            self.content.pop(self.head, None)
        else:
            self.content[self.head] = symbol
    
    def move(self, direction: str) -> None:
        d = direction.upper()
        if d in ('L', 'LEFT'):
            self.head -= 1
        elif d in ('R', 'RIGHT'):
            self.head += 1
    
    def get_bounds(self) -> Tuple[int, int]:
        if not self.content:
            return (self.head, self.head)
        return (min(min(self.content.keys()), self.head),
                max(max(self.content.keys()), self.head))
    
    def init(self, content: str, pos: int = 0) -> None:
        self.content = {}
        self.head = pos
        for i, c in enumerate(content):
            if c != BLANK:
                self.content[pos + i] = c
    
    def display(self, padding: int = 5) -> Tuple[str, str]:
        lo, hi = self.get_bounds()
        lo -= padding
        hi += padding
        
        tape_str = ""
        head_str = ""
        for p in range(lo, hi + 1):
            tape_str += self.content.get(p, BLANK)
            head_str += "^" if p == self.head else " "
        return tape_str, head_str


class MultiTapeTM:
    def __init__(self, num_tapes: int = 1, name: str = "TM"):
        self.name = name
        self.num_tapes = num_tapes
        self.tapes = [Tape(name=f"Tape{i+1}") for i in range(num_tapes)]
        self.state = ""
        self.init_state = ""
        self.accept_states: set = set()
        self.transitions: Dict = {}
        
        self.steps = 0
        self.halted = False
        self.accepted = False
        self.display_extra: Optional[Callable[[], str]] = None
        
    def set_init_state(self, state: str):
        self.init_state = state
        self.state = state
        
    def add_accept(self, state: str):
        self.accept_states.add(state)
        
    def add_transition(self, from_state: str, read: Tuple[str, ...],
                       write: Tuple[str, ...], moves: Tuple[str, ...], to_state: str):
        self.transitions[(from_state, read)] = (write, moves, to_state)
        
    def init_tape(self, idx: int, content: str, pos: int = 0):
        if 0 <= idx < self.num_tapes:
            self.tapes[idx].init(content, pos)
            
    def reset(self):
        self.state = self.init_state
        self.steps = 0
        self.halted = False
        self.accepted = False
        for tape in self.tapes:
            tape.content = {}
            tape.head = 0
            
    def step(self) -> bool:
        if self.halted:
            return False
            
        if self.state in self.accept_states:
            self.halted = True
            self.accepted = True
            return False
            
        read = tuple(t.read() for t in self.tapes)
        key = (self.state, read)
        
        if key not in self.transitions:
            self.halted = True
            return False
            
        write, moves, next_state = self.transitions[key]
        for i, (w, m) in enumerate(zip(write, moves)):
            self.tapes[i].write(w)
            self.tapes[i].move(m)
        self.state = next_state
        self.steps += 1
        return True
        
    def show(self, clear: bool = False) -> str:
        if clear:
            os.system('cls' if os.name == 'nt' else 'clear')
        
        lines = [f"[{self.name}] 步数:{self.steps} 状态:{self.state}"]
        if self.halted:
            lines[0] += " [已停机]" + (" ✓" if self.accepted else "")
        lines.append("-" * 50)
        
        for tape in self.tapes:
            t, h = tape.display()
            lines.append(f"{tape.name}: {t}")
            lines.append(f"{'':>{len(tape.name)+2}}{h}")
        
        if self.display_extra:
            extra = self.display_extra()
            if extra:
                lines.append("-" * 50)
                lines.append(extra)
        
        out = "\n".join(lines)
        print(out)
        return out
    
    def run_interactive(self) -> bool:
        self.show(True)
        while not self.halted:
            input("按Enter继续...")
            self.step()
            self.show(True)
        return self.accepted
    
    def run_auto(self, delay: float = 0.5, max_steps: int = 10000) -> bool:
        self.show(True)
        while not self.halted and self.steps < max_steps:
            time.sleep(delay)
            self.step()
            self.show(True)
        return self.accepted


if __name__ == '__main__':
    tm = MultiTapeTM(1, "写101")
    tm.set_init_state("q0")
    tm.add_accept("q3")
    tm.add_transition("q0", (BLANK,), ("1",), ("R",), "q1")
    tm.add_transition("q1", (BLANK,), ("0",), ("R",), "q2")
    tm.add_transition("q2", (BLANK,), ("1",), ("S",), "q3")
    tm.run_auto(0.3)
