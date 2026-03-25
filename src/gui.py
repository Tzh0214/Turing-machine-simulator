import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, font

# 确保可以导入 src 下的模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.universal_tm import UniversalTM

class UTMGui:
    def __init__(self, root):
        self.root = root
        self.root.title("图灵机模拟器 - 可视化界面")
        self.root.geometry("800x600")
        
        self.utm = UniversalTM()
        self.is_auto_playing = False
        
        self._setup_ui()
        
    def _setup_ui(self):
        # 顶部控制面板
        control_frame = tk.Frame(self.root, pady=10)
        control_frame.pack(fill=tk.X)
        
        tk.Button(control_frame, text="加载 JSON", command=self.load_json).pack(side=tk.LEFT, padx=10)
        self.btn_step = tk.Button(control_frame, text="单步执行", command=self.step, state=tk.DISABLED)
        self.btn_step.pack(side=tk.LEFT, padx=10)
        
        self.btn_auto = tk.Button(control_frame, text="自动播放", command=self.toggle_auto, state=tk.DISABLED)
        self.btn_auto.pack(side=tk.LEFT, padx=10)
        
        self.lbl_status = tk.Label(control_frame, text="请先加载一个 JSON 图灵机定义文件", fg="blue")
        self.lbl_status.pack(side=tk.LEFT, padx=20)
        
        # 中间：阶段说明面板
        phase_frame = tk.LabelFrame(self.root, text="当前运行阶段说明", padx=10, pady=10)
        phase_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_phase = tk.Label(phase_frame, text="等待开始...", font=("Microsoft YaHei", 12, "bold"), fg="#D35400")
        self.lbl_phase.pack(anchor=tk.W)
        
        self.lbl_detail = tk.Label(phase_frame, text="", font=("Microsoft YaHei", 10), fg="#34495E")
        self.lbl_detail.pack(anchor=tk.W)
        
        # 底部：磁带视图 (使用等宽字体)
        tape_frame = tk.LabelFrame(self.root, text="纸带视图", padx=10, pady=10)
        tape_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        custom_font = font.Font(family="Consolas", size=14)
        self.text_display = tk.Text(tape_frame, font=custom_font, bg="#282C34", fg="#00FF00", wrap=tk.NONE)
        
        # 滚动条
        scroll_y = tk.Scrollbar(tape_frame, command=self.text_display.yview)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x = tk.Scrollbar(tape_frame, command=self.text_display.xview, orient=tk.HORIZONTAL)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.text_display.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        self.text_display.pack(fill=tk.BOTH, expand=True)

    def load_json(self):
        # 默认打开 test 目录
        init_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'test')
        if not os.path.exists(init_dir):
            init_dir = os.getcwd()
            
        filepath = filedialog.askopenfilename(
            initialdir=init_dir,
            title="选择图灵机 JSON 文件",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if filepath:
            try:
                self.utm.load(json_path=filepath)
                self.utm.init()
                self.lbl_status.config(text=f"已加载: {os.path.basename(filepath)}", fg="green")
                self.btn_step.config(state=tk.NORMAL)
                self.btn_auto.config(state=tk.NORMAL)
                self.update_display()
            except Exception as e:
                messagebox.showerror("加载失败", f"无法加载该文件: {str(e)}")

    def step(self):
        if not self.utm.halted:
            self.utm.step()
            self.update_display()
            if self.utm.halted:
                self.lbl_status.config(text="执行完毕 (停机)!", fg="red")
                self.btn_step.config(state=tk.DISABLED)
                self.is_auto_playing = False
                self.btn_auto.config(text="自动播放")
                messagebox.showinfo("结束", f"图灵机已停机。\n步数: {self.utm.steps}\n结果: {'接受' if self.utm.accepted else '拒绝/无匹配转移'}")

    def toggle_auto(self):
        if self.utm.halted:
            return
            
        self.is_auto_playing = not self.is_auto_playing
        if self.is_auto_playing:
            self.btn_auto.config(text="停止播放")
            self.btn_step.config(state=tk.DISABLED)
            self._auto_step()
        else:
            self.btn_auto.config(text="自动播放")
            self.btn_step.config(state=tk.NORMAL)

    def _auto_step(self):
        if self.is_auto_playing and not self.utm.halted:
            self.step()
            # 设置下一次执行的时间间隙，目前是 500 毫秒 (0.5秒)
            self.root.after(500, self._auto_step)

    def update_display(self):
        # 1. 更新阶段说明
        self.lbl_phase.config(text=f"步骤 {self.utm.steps} | {self.utm.phase}")
        self.lbl_detail.config(text=self.utm.phase_detail if self.utm.phase_detail else "...")
        
        if self.utm.sim_state > 0:
            state_name = self.utm.inv_state.get(self.utm.sim_state, f"q{self.utm.sim_state}")
            self.lbl_detail.config(text=self.lbl_detail.cget("text") + f"  [当前被模拟状态: {state_name}]")

        # 2. 更新纸带显示
        lines = []
        for tape in self.utm.mtm.tapes:
            t_str, h_str = tape.display(padding=5)
            lines.append(f"{tape.name}:")
            lines.append(t_str)
            lines.append(h_str)
            lines.append("-" * 50)
            
        self.text_display.delete('1.0', tk.END)
        self.text_display.insert(tk.END, "\n".join(lines))

if __name__ == "__main__":
    root = tk.Tk()
    app = UTMGui(root)
    root.mainloop()