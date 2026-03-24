# 图灵机模拟器

计算复杂性课程编程作业。实现图灵机编码、多带图灵机、通用图灵机。

## 结构

```
├── src/
│   ├── tm_encoder.py      # 编码模块
│   ├── multi_tape_tm.py   # 多带TM
│   ├── universal_tm.py    # UTM
│   └── main.py            # 主程序
├── test/
│   ├── add_tm.json        # 加法TM (2+3=5)
│   └── simple_tm.json
└── docs/
    └── report.pdf         # 实验报告
```

## 运行

```bash
cd Turing-machine-simulator

# 运行ADD测试 (自动模式)
python3 -m src.main --json test/add_tm.json --mode auto --delay 0.3

# 交互模式
python3 -m src.main --json test/add_tm.json --mode interactive

# 只看编码
python3 -m src.main --json test/add_tm.json --encode-only

# 多带TM演示
python3 -m src.main --demo
```

## JSON格式

```json
{
    "状态名": {
        "读取符号": {
            "write": "写入符号",
            "move": "right/left",
            "nextState": "下一状态"
        }
    },
    "input": ["输入1", "输入2"]
}
```

## ADD示例

`test/add_tm.json` 实现一进制加法:
- 输入 `["00", "000"]` = 2+3
- 输出 `00000` = 5
