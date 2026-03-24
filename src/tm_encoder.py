"""
图灵机编码模块
将JSON格式的图灵机定义转换为二进制编码
"""

import json
from typing import Dict, List, Tuple, Any


class TuringMachineEncoder:
    """图灵机编码器"""
    
    def __init__(self):
        self.state_map: Dict[str, int] = {}
        self.symbol_map: Dict[str, int] = {}
        self.transitions: List[Tuple] = []
        self.input_strings: List[str] = []
        
    def load_from_json(self, json_path: str) -> Dict[str, Any]:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def parse_tm_definition(self, tm_def: Dict[str, Any]) -> None:
        self.state_map = {}
        self.symbol_map = {}
        self.transitions = []
        self.input_strings = tm_def.get('input', [])
        
        states = set()
        symbols = {' '}  # 空符号总是第一个
        
        for state_name, actions in tm_def.items():
            if state_name == 'input':
                continue
            states.add(state_name)
            for char, action in actions.items():
                symbols.add(char)
                symbols.add(action['write'])
                states.add(action['nextState'])
        
        # 状态排序：q1, q2, q3...
        sorted_states = sorted(states, key=lambda x: (
            not x.startswith('q'),
            int(x[1:]) if x.startswith('q') and x[1:].isdigit() else float('inf'),
            x
        ))
        for i, state in enumerate(sorted_states, 1):
            self.state_map[state] = i
            
        # 符号排序：空符号为1
        symbol_list = [' '] + sorted(symbols - {' '})
        for i, symbol in enumerate(symbol_list, 1):
            self.symbol_map[symbol] = i
            
        # 解析转移
        for state_name, actions in tm_def.items():
            if state_name == 'input':
                continue
            for char, action in actions.items():
                self.transitions.append((
                    state_name, char,
                    action['write'], action['move'], action['nextState']
                ))
    
    def _unary(self, n: int) -> str:
        return '1' * n
    
    def _encode_direction(self, direction: str) -> str:
        return '1' if direction.lower() in ('left', 'l') else '11'
    
    def _encode_transition(self, t: Tuple) -> str:
        state, read_sym, write_sym, direction, next_state = t
        parts = [
            self._unary(self.state_map[state]),
            self._unary(self.symbol_map[read_sym]),
            self._unary(self.symbol_map[write_sym]),
            self._encode_direction(direction),
            self._unary(self.state_map[next_state])
        ]
        return '0'.join(parts)
    
    def encode(self, tm_def: Dict[str, Any] = None, json_path: str = None) -> str:
        if json_path:
            tm_def = self.load_from_json(json_path)
        if tm_def:
            self.parse_tm_definition(tm_def)
        if not self.transitions:
            raise ValueError("没有转移函数")
        return '00'.join(self._encode_transition(t) for t in self.transitions)
    
    def get_state_map(self) -> Dict[str, int]:
        return self.state_map.copy()
    
    def get_symbol_map(self) -> Dict[str, int]:
        return self.symbol_map.copy()
    
    def get_input_string(self) -> str:
        return '_'.join(self.input_strings) if self.input_strings else ''
    
    def decode_for_display(self, encoded: str) -> str:
        inv_state = {v: k for k, v in self.state_map.items()}
        inv_symbol = {v: k for k, v in self.symbol_map.items()}
        
        result = []
        for t in encoded.split('00'):
            parts = t.split('0')
            if len(parts) == 5:
                state = inv_state.get(len(parts[0]), '?')
                read_sym = inv_symbol.get(len(parts[1]), '?')
                write_sym = inv_symbol.get(len(parts[2]), '?')
                direction = 'L' if len(parts[3]) == 1 else 'R'
                next_state = inv_state.get(len(parts[4]), '?')
                result.append(f"δ({state}, '{read_sym}') = ({next_state}, '{write_sym}', {direction})")
        return '\n'.join(result)
    
    def print_info(self) -> None:
        print("状态映射:")
        for state, num in sorted(self.state_map.items(), key=lambda x: x[1]):
            print(f"  {state} -> {'1' * num}")
            
        print("\n符号映射:")
        for sym, num in sorted(self.symbol_map.items(), key=lambda x: x[1]):
            print(f"  '{sym if sym != ' ' else '_'}' -> {'1' * num}")
            
        print("\n转移函数:")
        for t in self.transitions:
            state, read_sym, write_sym, direction, next_state = t
            d = 'L' if direction.lower() in ('left', 'l') else 'R'
            r = '_' if read_sym == ' ' else read_sym
            w = '_' if write_sym == ' ' else write_sym
            print(f"  δ({state}, '{r}') = ({next_state}, '{w}', {d})")


if __name__ == '__main__':
    sample = {
        "q1": {" ": {"write": "1", "move": "right", "nextState": "q2"}},
        "q2": {
            " ": {"write": "0", "move": "left", "nextState": "q2"},
            "1": {"write": "0", "move": "left", "nextState": "q3"}
        },
        "input": ["0", "1", "11"]
    }
    
    encoder = TuringMachineEncoder()
    encoded = encoder.encode(sample)
    encoder.print_info()
    print(f"\n编码: {encoded}")
    print(f"长度: {len(encoded)}")
