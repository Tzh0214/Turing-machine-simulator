#!/usr/bin/env python3
"""
图灵机模拟器主程序

使用:
    python -m src.main --json test/add_tm.json --mode auto
    python -m src.main --json test/add_tm.json --mode interactive
    python -m src.main --encode-only --json test/add_tm.json
    python -m src.main --demo
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tm_encoder import TuringMachineEncoder
from src.multi_tape_tm import MultiTapeTM, BLANK
from src.universal_tm import UniversalTM


def run_encoder(json_path: str) -> str:
    print("\n=== 图灵机编码 ===\n")
    encoder = TuringMachineEncoder()
    encoded = encoder.encode(json_path=json_path)
    encoder.print_info()
    print(f"\n编码: {encoded}")
    print(f"长度: {len(encoded)}")
    print("\n解码验证:")
    print(encoder.decode_for_display(encoded))
    return encoded


def run_utm(json_path: str, mode: str, delay: float, max_steps: int):
    print("\n=== 通用图灵机 ===\n")
    utm = UniversalTM()
    utm.load(json_path=json_path)
    utm.init()
    
    print("\n开始运行...\n")
    
    if mode == 'interactive':
        result = utm.run_interactive(max_steps)
    elif mode == 'auto':
        result = utm.run_auto(delay, max_steps)
    else:
        result = utm.run_silent(max_steps)
        utm.show()
    
    print(f"\n结果: {'接受' if result else '停机'}, 步数: {utm.steps}")
    utm.save_history("utm_execution_log.txt")
    return result


def demo():
    print("\n=== 多带TM演示 ===")
    print("将 '101' 复制到第二条磁带\n")
    
    tm = MultiTapeTM(2, "复制机")
    tm.set_init_state("q1")
    tm.add_accept("qf")
    tm.init_tape(0, "101")
    
    tm.add_transition("q1", ("0", BLANK), ("0", "0"), ("R", "R"), "q1")
    tm.add_transition("q1", ("1", BLANK), ("1", "1"), ("R", "R"), "q1")
    tm.add_transition("q1", (BLANK, BLANK), (BLANK, BLANK), ("S", "S"), "qf")
    
    input("按Enter开始...")
    tm.run_auto(0.4)


def main():
    parser = argparse.ArgumentParser(description='图灵机模拟器')
    parser.add_argument('--json', '-j', type=str, help='JSON文件路径')
    parser.add_argument('--mode', '-m', default='auto',
                        choices=['interactive', 'auto', 'silent'])
    parser.add_argument('--delay', '-d', type=float, default=0.5)
    parser.add_argument('--max-steps', '-s', type=int, default=1000)
    parser.add_argument('--encode-only', '-e', action='store_true')
    parser.add_argument('--demo', action='store_true')
    
    args = parser.parse_args()
    
    print("\n图灵机模拟器")
    print("=" * 30)
    
    if args.demo:
        demo()
        return
    
    if not args.json:
        default = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), 'test', 'add_tm.json')
        if os.path.exists(default):
            args.json = default
            print(f"使用默认: {args.json}")
        else:
            print("错误: 请用 --json 指定文件")
            sys.exit(1)
    
    if not os.path.exists(args.json):
        print(f"文件不存在: {args.json}")
        sys.exit(1)
    
    run_encoder(args.json)
    
    if args.encode_only:
        return
    
    input("\n按Enter运行UTM...")
    run_utm(args.json, args.mode, args.delay, args.max_steps)


if __name__ == '__main__':
    main()
