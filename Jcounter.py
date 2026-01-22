import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageDraw
import json
import os

class ColonyCounter:
    def __init__(self, root):
        self.root = root
        self.root.title("菌落计数工具")
        self.root.geometry("1200x800")
        
        # 初始化变量
        self.image = None
        self.tk_image = None
        self.zoom_level = 1.0
        self.original_image = None
        self.clicks = []
        self.current_count = 0
        
        # 创建界面
        self.create_widgets()
        
        # 绑定键盘事件
        self.root.bind('<z>', self.zoom_in)
        self.root.bind('<x>', self.zoom_out)
        self.root.bind('<d>', self.delete_last)
        self.root.bind('<c>', self.clear_all)
        self.root.bind('<s>', self.save_counts)
        self.root.bind('<l>', self.load_counts)
        
    def create_widgets(self):
        # 控制面板
        control_frame = tk.Frame(self.root, bg='lightgray', width=200)
        control_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        # 按钮
        tk.Button(control_frame, text="打开图像", command=self.open_image, 
                 bg='#4CAF50', fg='white', font=('Arial', 12), padx=20, pady=10).pack(pady=10)
        tk.Button(control_frame, text="保存计数", command=self.save_counts_btn, 
                 bg='#2196F3', fg='white', font=('Arial', 12), padx=20, pady=10).pack(pady=5)
        tk.Button(control_frame, text="加载计数", command=self.load_counts_btn, 
                 bg='#FF9800', fg='white', font=('Arial', 12), padx=20, pady=10).pack(pady=5)
        tk.Button(control_frame, text="删除上一个", command=self.delete_last_btn, 
                 bg='#f44336', fg='white', font=('Arial', 12), padx=20, pady=10).pack(pady=5)
        tk.Button(control_frame, text="清空所有", command=self.clear_all_btn, 
                 bg='#9E9E9E', fg='white', font=('Arial', 12), padx=20, pady=10).pack(pady=5)
        
        # 计数显示
        self.count_label = tk.Label(control_frame, text="计数: 0", 
                                   font=('Arial', 20, 'bold'), bg='lightgray')
        self.count_label.pack(pady=20)
        
        # 缩放控制
        zoom_frame = tk.Frame(control_frame, bg='lightgray')
        zoom_frame.pack(pady=10)
        tk.Label(zoom_frame, text="缩放控制:", bg='lightgray').pack()
        tk.Button(zoom_frame, text="放大 (Z)", command=self.zoom_in_btn, width=15).pack(pady=2)
        tk.Button(zoom_frame, text="缩小 (X)", command=self.zoom_out_btn, width=15).pack(pady=2)
        tk.Button(zoom_frame, text="重置缩放", command=self.reset_zoom, width=15).pack(pady=2)
        
        # 帮助文本
        help_text = """
        使用说明：
        1. 点击"打开图像"加载菌落图片
        2. 在菌落上点击进行计数
        3. 快捷键：
           Z - 放大图像
           X - 缩小图像
           D - 删除上一个标记
           C - 清空所有计数
           S - 保存计数结果
           L - 加载计数结果
        4. 右键点击可以拖动图像
        """
        help_label = tk.Label(control_frame, text=help_text, justify=tk.LEFT, 
                             bg='lightgray', font=('Arial', 10))
        help_label.pack(pady=20, padx=10)
        
        # 图像显示区域
        self.canvas_frame = tk.Frame(self.root)
        self.canvas_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 创建带滚动条的画布
        self.canvas = tk.Canvas(self.canvas_frame, bg='gray')
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, 
                             xscrollcommand=self.h_scrollbar.set)
        
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Button-3>", self.start_drag)
        self.canvas.bind("<B3-Motion>", self.on_drag)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        
    def open_image(self):
        file_path = filedialog.askopenfilename(
            title="选择菌落图像",
            filetypes=[
                ("图像文件", "*.jpg *.jpeg *.png *.bmp *.tiff"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            try:
                self.image = Image.open(file_path)
                self.original_image = self.image.copy()
                self.zoom_level = 1.0
                self.clicks = []
                self.current_count = 0
                self.update_count_display()
                self.display_image()
                self.root.title(f"菌落计数工具 - {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("错误", f"无法打开图像: {str(e)}")
    
    def display_image(self):
        if not self.image:
            return
            
        # 调整图像大小
        width = int(self.image.width * self.zoom_level)
        height = int(self.image.height * self.zoom_level)
        resized_image = self.image.resize((width, height), Image.Resampling.LANCZOS)
        
        # 转换为tkinter格式
        self.tk_image = ImageTk.PhotoImage(resized_image)
        
        # 更新画布
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
        
        # 重新绘制标记点
        self.redraw_marks()
    
    def on_click(self, event):
        if not self.image:
            return
            
        # 获取画布上的坐标
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # 计算在原始图像上的坐标
        original_x = int(canvas_x / self.zoom_level)
        original_y = int(canvas_y / self.zoom_level)
        
        # 确保点击在图像范围内
        if 0 <= original_x < self.original_image.width and 0 <= original_y < self.original_image.height:
            self.clicks.append((original_x, original_y))
            self.current_count += 1
            self.update_count_display()
            self.draw_mark(canvas_x, canvas_y)
    
    def draw_mark(self, x, y, index=None):
        if index is None:
            index = len(self.clicks)
        
        # 绘制红色圆圈
        radius = 10
        self.canvas.create_oval(
            x - radius, y - radius, x + radius, y + radius,
            outline='red', width=1, tags=f"mark_{index}"
        )
        
        # 绘制数字标签
        self.canvas.create_text(
            x, y, text=str(index + 1),
            fill='red', font=('Arial', 10, 'bold'), tags=f"label_{index}"
        )
    
    def redraw_marks(self):
        for i, (orig_x, orig_y) in enumerate(self.clicks):
            canvas_x = orig_x * self.zoom_level
            canvas_y = orig_y * self.zoom_level
            self.draw_mark(canvas_x, canvas_y, i)
    
    def update_count_display(self):
        self.count_label.config(text=f"计数: {self.current_count}")
    
    def zoom_in(self, event=None):
        if self.image:
            self.zoom_level *= 1.2
            self.display_image()
    
    def zoom_in_btn(self):
        self.zoom_in()
    
    def zoom_out(self, event=None):
        if self.image and self.zoom_level > 0.1:
            self.zoom_level /= 1.2
            self.display_image()
    
    def zoom_out_btn(self):
        self.zoom_out()
    
    def reset_zoom(self):
        if self.image:
            self.zoom_level = 1.0
            self.display_image()
    
    def delete_last(self, event=None):
        if self.clicks:
            self.clicks.pop()
            self.current_count -= 1
            self.update_count_display()
            self.display_image()
    
    def delete_last_btn(self):
        self.delete_last()
    
    def clear_all(self, event=None):
        if messagebox.askyesno("确认", "确定要清空所有计数吗？"):
            self.clicks = []
            self.current_count = 0
            self.update_count_display()
            self.display_image()
    
    def clear_all_btn(self):
        self.clear_all()
    
    def save_counts(self, event=None):
        self.save_counts_btn()
    
    def save_counts_btn(self):
        if not self.clicks:
            messagebox.showwarning("警告", "没有可保存的计数数据")
            return
            
        file_path = filedialog.asksaveasfilename(
            title="保存计数结果",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                data = {
                    "total_count": len(self.clicks),
                    "clicks": self.clicks,
                    "image_size": self.original_image.size if self.original_image else None
                }
                
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
                
                messagebox.showinfo("成功", f"计数结果已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def load_counts(self, event=None):
        self.load_counts_btn()
    
    def load_counts_btn(self):
        if not self.image:
            messagebox.showwarning("警告", "请先打开图像")
            return
            
        file_path = filedialog.askopenfilename(
            title="加载计数结果",
            filetypes=[("JSON文件", "*.json"), ("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                
                self.clicks = data.get("clicks", [])
                self.current_count = len(self.clicks)
                self.update_count_display()
                self.display_image()
                
                messagebox.showinfo("成功", f"已加载 {self.current_count} 个计数点")
            except Exception as e:
                messagebox.showerror("错误", f"加载失败: {str(e)}")
    
    def start_drag(self, event):
        self.canvas.scan_mark(event.x, event.y)
    
    def on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)
    
    def on_mousewheel(self, event):
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

def main():
    root = tk.Tk()
    app = ColonyCounter(root)
    root.mainloop()

if __name__ == "__main__":
    main()