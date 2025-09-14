import tkinter as tk
from tkhtmlview import HTMLLabel
from tkinter import ttk,colorchooser,messagebox
from tkinter import font as tkfont
from pyopengltk import OpenGLFrame
from OpenGL.GL import *
import numpy as np
from math import pi, cos, sin
from PIL import Image, ImageDraw, ImageFont,ImageTk
import cv2
import time
import json
from tkinter import filedialog, messagebox
import os,sys
import importlib.util
from importlib.resources import files, as_file
import re
import platform as sysplatform
from OpenGL.GL.shaders import compileShader, compileProgram
import glm
import copy
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor

class TextureFormat(Enum):
    Color = 0
    Luminance = 1
    DepthColor = 2
def load_icon(iconpath='main.png'):
    try:
        # 使用files() API (Python 3.9+)
        ref = files("mossflow.resources") / f"{iconpath}"
        with as_file(ref) as icon_path:
            return str(icon_path)  # 返回绝对路径
    except Exception as e:
        print(f"加载图标失败: {e}")
        return None
iconp=load_icon()
class ImgViewer(tk.Toplevel):
    def __init__(self, parent, module, importannos2flowplane =None):
        """
        图像查看器窗口
        :param parent: 父窗口
        :param image: 要显示的图像（numpy数组）
        """
        super().__init__(parent)    
        self.texts = {
            'zh':{
                'save_image_success': "图像保存成功！",
                'save_image_error': "图像保存失败：",
                'image_viewer': "图像查看器",
                'save': "保存",
                'info': "信息",
                'depthcolor': "深度颜色",
                'graphicstree': "图形树",
                'select_image': "选择图像",
                "shapetools": "形状工具",
            },
            'en':{
                'save_image_success': "Image saved successfully!",
                'save_image_error': "Failed to save image: ",
                'image_viewer': "Image Viewer",
                'save': "Save",
                'info': "Info",
                'depthcolor': "Depth Color",
                'graphicstree': "Graphics Tree",
                'select_image': "Select Image",
                "shapetools": "Shape Tools",
            }
        }
        self.module = module
        self.language = module.language if hasattr(module, 'language') else 'zh'
        self.enable_iv_lableinfo= tk.BooleanVar(value=False)  # 是否显示标签信息
        self.enable_iv_depthcolor = tk.BooleanVar(value=False)  # 是否启用深度颜色
        self.enable_iv_graphicstree = tk.BooleanVar(value=False)  # 是否显示图形树
        self.enable_iv_shapetools = tk.BooleanVar(value=False)  # 是否显示形状工具
        self.title(self.texts[self.language]['image_viewer'])
        self.iconphoto(True,ImageTk.PhotoImage(Image.open(load_icon())))  # 设置窗口图标
        self.geometry(f"600x600+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")
        toolmenu_frame = tk.Frame(self)
        toolmenu_frame.grid(row=0, column=0, sticky='ew')
        
        self.image = None
        self.format = format
        self.pixelformat = None
        self.insideformat = None
        
        image_frame = tk.Frame(self)        
        image_frame.grid(row=1, column=0, sticky='nsew')
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, minsize=30)
        
        if 'CoordSys' in module.parameters:
            self.iv = ImgGLFrame(image_frame,module.parameters['CoordSys'])
        else:
            self.iv = ImgGLFrame(image_frame)
        self.iv.pack(fill=tk.BOTH, expand=True)
        self.iv.setlangeuage(self.language)
        imgscommbox = ttk.Combobox(toolmenu_frame, state="readonly",values=[key for key, value in module.parameters.items() if isinstance(value, np.ndarray)],width=6)
        imgscommbox.grid(row=0, column=0, padx=2, pady=1,sticky='w')
        imgscommbox.bind("<<ComboboxSelected>>", lambda event: self.changecurrentimage(module.parameters[imgscommbox.get()]))
        tk.Button(toolmenu_frame, text=self.texts[self.language]['save'],command=lambda: importannos2flowplane(self.module,'CoordSys',copy.deepcopy(self.iv.imagecoord))).grid(row=0, column=1, padx=0, pady=1,sticky='w')
        tk.Checkbutton(toolmenu_frame,text=self.texts[self.language]['info'],variable=self.enable_iv_lableinfo,command= self.update_iv_tools).grid(row=0, column=2, padx=0, pady=1,sticky='w')
        tk.Checkbutton(toolmenu_frame,text=self.texts[self.language]['depthcolor'],variable=self.enable_iv_depthcolor,command= self.update_iv_tools).grid(row=0, column=3, padx=0, pady=1,sticky='w')
        tk.Checkbutton(toolmenu_frame,text=self.texts[self.language]['graphicstree'],variable=self.enable_iv_graphicstree,command= self.update_iv_tools).grid(row=0, column=4, padx=0, pady=1,sticky='w')
        tk.Checkbutton(toolmenu_frame,text=self.texts[self.language]['shapetools'],variable=self.enable_iv_shapetools,command= self.update_iv_tools).grid(row=0, column=5, padx=0, pady=1,sticky='w')
        
        self.protocol("WM_DELETE_WINDOW", self.on_window_close)        
        if len(imgscommbox['values'])!=0:
            imgscommbox.current(0)  # 设置默认选中第一个图像
            image_frame.after(1000, lambda : self.changecurrentimage(module.parameters[imgscommbox.get()]))  # 延时调用以确保窗口已完全加载
    def changecurrentimage(self,img:np.ndarray):
        if img is not None:
            if img.ndim == 2 or (img.ndim == 3 and img.shape[2] == 1) :
                if img.dtype == np.float32:
                    self.format = GL_R32F
                    self.insideformat = GL_RED
                    self.pixelformat = GL_FLOAT
                else:
                    self.format = GL_LUMINANCE
                    self.insideformat = GL_LUMINANCE
                    self.pixelformat =GL_UNSIGNED_BYTE
            elif img.ndim == 3 and img.shape[2] == 3 and img.dtype == np.uint8:
                self.format = GL_BGRA
                self.insideformat = GL_BGRA
                self.pixelformat =GL_UNSIGNED_BYTE
            elif img.ndim == 3 and img.shape[2] == 4 and img.dtype == np.uint8:
                self.format = GL_BGRA
                self.insideformat = GL_BGRA
                self.pixelformat =GL_UNSIGNED_BYTE
            else:
                self.lastrunstatus = False
                self.breifimage = None
                self.statuscolor = [1.0, 0.0, 0.0]
            self.image = img
            self.iv.load_texture(self.image.shape[1], self.image.shape[0], self.image, self.format ,self.insideformat,self.pixelformat)
    def on_window_close(self):
        self.destroy()
        del self
    def update_iv_tools(self):
        self.iv.updatetools(self.enable_iv_lableinfo.get(),self.enable_iv_depthcolor.get(),self.enable_iv_graphicstree.get(),self.enable_iv_shapetools.get())
    def save_image(self):
        """保存图像到文件"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")]
        )
        if file_path:
            try:
                self.iv.tkMakeCurrent()  # 确保OpenGL上下文正确
                screenshotpixels= glReadPixels(0, 0, self.iv.width, self.iv.height, GL_BGR, GL_UNSIGNED_BYTE)
                cv2.imwrite(file_path, np.flipud(np.frombuffer(screenshotpixels, dtype=np.uint8).reshape(self.iv.height, self.iv.width, 3)))
                messagebox.showinfo("Success", self.texts[self.language]['save_image_success'])
            except Exception as e:
                messagebox.showerror("Error", f"{self.texts[self.language]['save_image_error']}: {e}")
        
class NumericInputPad:
    def __init__(self, parent, message=None):
        
        window = tk.Toplevel(parent)
        windowx = parent.winfo_rootx()+parent.winfo_width() - 370
        windowy = parent.winfo_rooty()+parent.winfo_height() - 500
        window.geometry(f"360x480+{windowx}+{windowy}")      

        self.root = window
        self.root.title("NumericInputPad")
        self.root.resizable(False, False)
        self.root.configure(bg="#f5f5f5")
        
        self.message = message
        
        # 自定义字体
        self.display_font = tkfont.Font(family="Arial", size=28, weight="bold")
        self.button_font = tkfont.Font(family="Arial", size=18)
        self.special_button_font = tkfont.Font(family="Arial", size=14)
        
        # 显示区域
        self.display_var = tk.StringVar()
        self.display_var.set("0")
        self.display = tk.Entry(
            self.root,
            textvariable=self.display_var,
            font=self.display_font,
            bd=2,
            relief=tk.FLAT,
            bg="#ffffff",
            fg="#333333",
            justify="right",
            insertwidth=0,
            readonlybackground="#ffffff",
        )
        self.display.grid(row=0, column=0, columnspan=4, padx=15, pady=(20, 15), ipady=12, sticky="ew")
        
        # 按钮样式配置
        self.button_config = {
            "font": self.button_font,
            "bd": 0,
            "relief": tk.RAISED,
            "height": 1,
            "width": 4,
            "activebackground": "#e0e0e0",
            "highlightthickness": 0,
            "highlightbackground": "#cccccc"
        }
        
        # 数字按钮布局
        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2),
            ('0', 4, 1), ('.', 4, 2), ('-', 4, 0),
            ('⌫', 1, 3), ('C', 2, 3), ('确定', 3, 3, 2)
        ]
        
        # 创建按钮
        for button_info in buttons:
            text = button_info[0]
            row = button_info[1]
            col = button_info[2]
            rowspan = button_info[3] if len(button_info) > 3 else 1
            
            btn_style = self.button_config.copy()
            
            if text.isdigit():
                btn_style.update({"bg": "#ffffff", "fg": "#333333"})
            elif text in ['.', '-']:
                btn_style.update({"bg": "#f0f0f0", "fg": "#666666"})
            else:
                if text == '确定':
                    btn_style.update({
                        "bg": "#4CAF50", 
                        "fg": "white", 
                        "font": self.special_button_font,
                        "height": 3
                    })
                else:
                    btn_style.update({
                        "bg": "#e0e0e0", 
                        "fg": "#333333",
                        "font": self.special_button_font
                    })
            
            button = tk.Button(self.root, text=text, **btn_style)
            
            if rowspan > 1:
                button.grid(row=row, column=col, rowspan=rowspan, padx=5, pady=5, sticky="nswe")
            else:
                button.grid(row=row, column=col, padx=5, pady=5)
            
            button.bind("<Button-1>", lambda e, t=text: self.on_button_click(t))
        
        # 配置网格布局权重
        for i in range(5):
            self.root.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.root.grid_columnconfigure(i, weight=1)
        
        # 初始化输入状态
        self.current_input = "0"
        self.has_decimal = False
    
    def on_button_click(self, button_text):
        if button_text.isdigit():
            self.process_digit(button_text)
        elif button_text == '.':
            self.process_decimal()
        elif button_text == '-':
            self.process_sign()
        elif button_text == '⌫':
            self.process_backspace()
        elif button_text == 'C':
            self.process_clear()
        elif button_text == '确定':
            self.process_confirm()
    
    def process_digit(self, digit):
        if self.current_input == "0":
            self.current_input = digit
        elif self.current_input == "-0":
            self.current_input = "-" + digit
        else:
            self.current_input += digit
        self.update_display()
    
    def process_decimal(self):
        if not self.has_decimal:
            # 如果当前是"0"或"-0"，在添加小数点前不需要保留0
            if self.current_input == "0":
                self.current_input = "0."
            elif self.current_input == "-0":
                self.current_input = "-0."
            else:
                self.current_input += '.'
            self.has_decimal = True
            self.update_display()
    
    def process_sign(self):
        if self.current_input.startswith('-'):
            self.current_input = self.current_input[1:]
        else:
            if self.current_input != "0":
                self.current_input = '-' + self.current_input
        self.update_display()
    
    def process_backspace(self):
        if len(self.current_input) > 1:
            # 检查是否删除了小数点
            if self.current_input[-1] == '.':
                self.has_decimal = False
            self.current_input = self.current_input[:-1]
            
            # 处理删除负号后的情况
            if self.current_input == "-":
                self.current_input = "0"
        else:
            self.current_input = "0"
            self.has_decimal = False
        
        self.update_display()
    
    def process_clear(self):
        self.current_input = "0"
        self.has_decimal = False
        self.update_display()
    
    def process_confirm(self):
        if self.message is None:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.current_input)
            messagebox.showinfo("Copy!", "Copied to clipboard!")
            self.root.destroy()  # 关闭数字键盘窗口   
            return
        else:
            self.message(self.current_input)
        self.root.destroy()  # 关闭数字键盘窗口
    def update_display(self):
        # 确保显示格式正确
        display_text = self.current_input
        
        # 处理".x"显示为"0.x"的情况
        if display_text.startswith('.') or (display_text.startswith('-') and display_text[1] == '.'):
            if display_text.startswith('-'):
                display_text = "-0" + display_text[1:]
            else:
                display_text = "0" + display_text
        
        # 处理只有负号的情况
        if display_text == "-":
            display_text = "-0"
        
        # 处理"-0"后面跟着数字的情况
        if display_text.startswith("-0") and len(display_text) > 2 and display_text[2] != '.':
            display_text = "-" + display_text[2:]
        
        # 更新显示和内部状态
        self.display_var.set(display_text)
        self.current_input = display_text
class LangCombo:
    def __init__(self,parent,defultlange,callback = None):
        self.langselector = ttk.Combobox(parent, state="readonly",values=['zh','en'], width=6)
        self.langselector.set(defultlange)
        self.langselector.pack(side='right', anchor='ne', padx=0, pady=0)
        self.langselector.bind("<<ComboboxSelected>>", callback)
    @classmethod
    def show(cls, parent, defultlange, callback=None):
        """显示语言选择窗口"""
        cls.instance = cls(parent, defultlange, callback)
        return cls.instance.langselector
class InputStrDialog(tk.Toplevel):
    def __init__(self, parent, title, input):
        super().__init__(parent)
        self.input = input  # 保存输入内容
        self.title(title)
        self.geometry(f"200x100+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")
        self.resizable(False, False)
        self.grab_set()
        self.iconphoto(True,ImageTk.PhotoImage(Image.open(load_icon())))  # 设置窗口图标
        
        inputbox = PlaceholderEntry(self,placeholder=self.input,width=60)
             
        def on_submit():
            self.input=inputbox.get()  # 保存输入内容
            self.destroy()  # 关闭窗口

        submit_btn = ttk.Button(self, text="确定", command=on_submit)
        inputbox.pack(pady=10, padx=10, side= 'top', expand=True)
        submit_btn.pack(pady=10, padx=10, side= 'top',fill= 'both', expand=True)
        self.bind("<Return>", lambda event: on_submit())  # 按回车键提交
        
        # 阻塞等待窗口关闭
        submit_btn.focus_set()  # 设置按钮为默认焦点
        self.wait_window()

        # 窗口关闭后，检查用户是否输入了内容
        self.input = self.input if self.input!=input else ""
        
class PlaceholderEntry(ttk.Frame):
    """
    一个带提示文字的输入框组件（基于Frame封装）
    - 支持 placeholder 提示
    - 支持 ttk 样式
    - 提供 get()/set() 方法操作文本
    """
    def __init__(self, master, placeholder="", **kwargs):
        super().__init__(master)
        
        # 默认配置
        self.placeholder = placeholder
        self.entry_var = tk.StringVar()
        
        # 创建 ttk 样式
        self.style = ttk.Style()
        self.style.configure("Placeholder.TEntry", foreground="grey")
        self.style.configure("Normal.TEntry", foreground="black")
        
        # 创建输入框
        self.entry = ttk.Entry(
            self,
            textvariable=self.entry_var,
            style="Placeholder.TEntry",
            **kwargs
        )
        self.entry.pack(fill="both", expand=True)
        
        # 初始化提示文字
        self._show_placeholder()
        
        # 绑定事件
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
    
    def _show_placeholder(self):
        """显示提示文字"""
        self.entry_var.set(self.placeholder)
        self.entry.config(style="Placeholder.TEntry")
    
    def _hide_placeholder(self):
        """隐藏提示文字"""
        if self.entry_var.get() == self.placeholder:
            self.entry_var.set("")
        self.entry.config(style="Normal.TEntry")
    
    def _on_focus_in(self, event):
        """获得焦点时隐藏提示"""
        if self.entry_var.get() == self.placeholder:
            self._hide_placeholder()
    
    def _on_focus_out(self, event):
        """失去焦点时显示提示（如果内容为空）"""
        if not self.entry_var.get():
            self._show_placeholder()
    
    def get(self):
        """获取输入内容（自动过滤提示文字）"""
        text = self.entry_var.get()
        return text
    
    def set(self, text):
        """设置输入内容"""
        self.entry_var.set(text)
        self.entry.config(style="Normal.TEntry")
class FlowPlane(OpenGLFrame):
    def __init__(self, *args, **kwargs):
        print("FlowPlane init")
        super().__init__(*args, **kwargs)
        # 语言设置
        self.language = 'zh'
        # 外观设置
        self.background_color = [0.11, 0.13, 0.22, 1.0]
        self.drawobjects = {}
        self.selectobjects = []
        # 部件初始化
        self.infolabel = tk.Label(self, text="Information", bg="black", fg="white")
        self.infolabel.pack(side='left',anchor='nw', padx=0, pady=0)
        self.infolabel.bind("<Double-Button-1>", self.copy_to_clipboard)
        # 动画使能
        self.animate = True
        # 窗口大小
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        # 缩放和位置变量
        self.scale = 1.0
        self.min_scale = 0.01
        self.max_scale = 100.0
        self.offset_x = 0#self.width / 2
        self.offset_y = 0#self.height / 2
        self.rotation_angle = 0  # 旋转角度（弧度）       
        # 鼠标跟踪
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.current_mouse_x = 0
        self.current_mouse_y = 0
        self.curent_img_x = 0
        self.curent_img_y = 0
        self.dragging = False     
        # 绑定事件
        self.bind("<Motion>", self.on_mouse_move)  # 鼠标移动事件
        self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>", self.on_mouse_wheel)    # Linux上滚
        self.bind("<Button-5>", self.on_mouse_wheel)    # Linux下滚
        self.bind("<ButtonPress-3>", self.on_button3_press) # 右键按下事件
        self.bind("<ButtonPress-2>", self.on_button2_press) # 中键按下事件
        self.bind("<B3-Motion>", self.on_mouseright_drag) # 右键拖动事件
        self.bind("<ButtonRelease-3>", self.on_button3_release) # 右键释放事件
        self.bind("<Button-1>", self.on_mouseleft_click)  # 左键单击事件
        self.bind("<Double-Button-1>", self.on_mouseleftdouble_click) # 左键双击事件
        self.bind("<Double-Button-3>", self.on_mouselrightdouble_click) # 右键双击事件

        self.bind("<Configure>", self.on_resize) # 窗口大小变化事件
        self.bind("<F5>", self.on_f5)  # F5键事件
        self.bind("<F11>", self.on_f11)
        self.bind("<Delete>", self.on_delete)  # Delete键事件
        # 上下文菜单字典
        self.texts = {
            'zh':{
                'update_drawobjects_msg_title': "更新模块",
                'update_drawobjects_msg_content': "模块已存在，是否覆盖？",
                'update_drawobjects_msg_error': "模块名称不能为空。",
                'on_confirmbuttonclick_errormsg_title': "错误",
                'on_confirmbuttonclick_errormsg_content': "设置输入失败，请检查参数。",
                'on_f11_error': "请选择一个模块",
                'module': "模块",
                'langeuage': "语言",
                'setting': "设置",
                'link': "链接",
                'basicline': "链接",
                'ifline': "条件分支",
                'script': "脚本",
                'tool': '工具',
                'calculator': "计算器",
                'numberkeyboard': "数字键盘",
                'imageviewer': "图像查看器",
                'defaulttask': "默认任务",
                'save': "保存任务",
                'fileprocess': "文件处理",
            },
            'en':{
                'update_drawobjects_msg_title': "Update Module",
                'update_drawobjects_msg_content': "Module already exists. Overwrite?",
                'update_drawobjects_msg_error': "Module name cannot be empty.",
                'on_confirmbuttonclick_errormsg_title': "Error",
                'on_confirmbuttonclick_errormsg_content': "Failed to set input, please check parameters.",
                'on_f11_error': "Please select a module",
                'module': "Module",
                'langeuage': "Language",
                'setting': "Settings",
                'link': "Link",
                'basicline': "Basic Line",
                'ifline': "If Line",
                'script': "Script",
                'tool': 'Tool',
                'calculator': "Calculator",
                'numberkeyboard': "Numeric Pad",
                'imageviewer': "Image Viewer",
                'defaulttask': "Default Task",
                'save': "Save Task",
                'fileprocess': "File Process",
            }
        }
        # 上下文菜单
        self.context_menu = tk.Menu(self,tearoff=0)
        
        self.setting_menu = tk.Menu(self.context_menu, tearoff=0)
        self.module_menu = tk.Menu(self.context_menu, tearoff=0)
        self.tool_menu = tk.Menu(self.context_menu, tearoff=0)
                
        self.setting_menu.add_cascade(label=self.texts[self.language]['langeuage'],command=lambda: LangCombo.show(self,defultlange=self.language,callback=self.on_language_change))  
        self.setting_menu.add_cascade(label=self.texts[self.language]['defaulttask'],command=lambda :self.load_task())  # 添加默认任务加载
        self.setting_menu.add_cascade(label=self.texts[self.language]['save'], command=lambda :self.save_task())  # 添加保存任务
        
        self.tool_menu.add_cascade(label=self.texts[self.language]['numberkeyboard'], command=lambda : NumericInputPad(self))  # 添加计算器工具
        self.tool_menu.add_cascade(label=self.texts[self.language]['imageviewer'],accelerator="F11", command=lambda : self.on_f11(None))  # 添加图像查看器工具
                    
        self.module_menu.add_cascade(label=self.texts[self.language]['script'], command=lambda :self.on_addscript())
        
        
        self.context_menu.add_cascade(label=self.texts[self.language]['setting'], menu=self.setting_menu)
        self.context_menu.add_cascade(label=self.texts[self.language]['module'], menu=self.module_menu)        
        self.context_menu.add_cascade(label=self.texts[self.language]['tool'], menu=self.tool_menu)
        self.menulist = []
        self.ini_module()  # 初始化模块
    def save_task(self):
        """保存当前任务到文件"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".flp",
            filetypes=[("FlowTask files", "*.flp"), ("All files", "*.*")]
        )
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    data={
                        'language': self.language,
                        'background_color': self.background_color,
                        'scale': self.scale,
                        'offset_x': self.offset_x,
                        'offset_y': self.offset_y,
                        'rotation_angle': self.rotation_angle,
                        'modlues': {key: obj.get_json_data() for key, obj in self.drawobjects.items() if not obj.linemodule},
                        'linemodules': {key: obj.get_json_data() for key, obj in self.drawobjects.items() if obj.linemodule},
                        'texts': self.texts                 
                    }
                    json.dump(data, f, ensure_ascii=False, indent=4, cls=CustomEncoder)                    
            except Exception as e:
                self.drawobjects.clear()  # 清空现有模块
                messagebox.showerror("Error", f"Failed to save task: {e}")
    def load_task(self,defult_path=None):
        """从文件加载任务"""
        if defult_path is None:
            file_path = filedialog.askopenfilename(
                title="Open Task File",
                filetypes=[("FlowTask files", "*.flp"), ("All files", "*.*")]
            )
        file_path = defult_path
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.language = data.get('language', 'zh')
                self.background_color = data.get('background_color', [0.11, 0.13, 0.22, 1.0])
                self.scale = data.get('scale', 1.0)
                self.offset_x = data.get('offset_x', 0)
                self.offset_y = data.get('offset_y', 0)
                self.rotation_angle = data.get('rotation_angle', 0)
                #self.texts = data.get('texts', self.texts)
                
                # 清空现有模块
                self.drawobjects.clear()
                
                # 加载模块
                for key, module_data in data.get('modlues', {}).items():
                    module_class = getattr(sys.modules[module_data['class']], module_data['class'])
                    module_instance = module_class.from_json(module_data)
                    module_instance.message = self.on_message   
                    module_instance.get_image()
                    self.update_drawobjects(module_instance)
                
                # 加载连线模块
                for key, module_data in data.get('linemodules', {}).items():
                    module_class = getattr(sys.modules[module_data['class']], module_data['class'])
                    module_instance = module_class.from_json(module_data,self.drawobjects)
                    module_instance.message = self.on_message   
                    self.update_drawobjects(module_instance)             
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load task: {e}")
    def on_addscript(self):
        file_path = filedialog.askopenfilename(
            title="Open Python File",
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if file_path:
            module_name = os.path.splitext(os.path.basename(file_path))[0]
            spec = importlib.util.spec_from_file_location(f'{module_name}', file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            my_class = getattr(module, module_name)()
            rawname = getattr(my_class, 'rawname')
            zhname = getattr(my_class,'zhname')
            enname = getattr(my_class,'enname')
            self.texts['zh'][rawname] = zhname
            self.texts['en'][rawname] = enname
            self.update_drawobjects(my_class.from_userdefined(self,self.curent_img_x,self.curent_img_y,name=self.texts[self.language][rawname],message=self.on_message))
            # 这里可以添加后续处理代码，比如显示内容或进一步操作
    def on_importannos2flowplane(self,imgmodule,moudluename,coords):
        annosmodule = Graphics_ValueModule(imgmodule.x+50,imgmodule.y+50,name=moudluename,message=self.on_message)
        annosmodule.parameters['CoordSys'] = coords
        annosmodule.parameters['image'] = imgmodule.parameters['image']
        self.update_drawobjects(annosmodule)
        
    def load_module(self,directory):
        def get_directory_tree_with_depth(directory, target_depth=None):
            """
            获取目录树，并记录每个节点的深度
            :param directory: 目标目录路径
            :param target_depth: 可选，指定要返回的层级深度（从0开始）
            :return: 
                - 如果未指定 target_depth: 返回完整树形结构 + 各节点深度字典
                - 如果指定 target_depth: 返回该层级的所有目录和文件
            """
            tree = {}
            depth_info = {}  # 记录各层级的深度信息

            for root, dirs, files in os.walk(directory):
                # 计算当前深度（根目录为0）
                rel_path = os.path.relpath(root, directory)
                current_depth = 0 if rel_path == "." else len(rel_path.split(os.sep))

                # 如果指定了 target_depth，只收集目标层级的数据
                if target_depth is not None and current_depth != target_depth:
                    continue
                
                # 构建当前层级的树结构
                current_level = tree
                if rel_path != ".":
                    for part in rel_path.split(os.sep):
                        current_level = current_level.setdefault(part, {})

                # 添加文件和子目录
                current_level["_files"] = files
                current_level["_depth"] = current_depth  # 记录深度
                for dir_name in dirs:
                    current_level[dir_name] = {}

                # 记录深度信息（用于按深度索引）
                if current_depth not in depth_info:
                    depth_info[current_depth] = []
                depth_info[current_depth].append({
                    "path": root,
                    "dirs": dirs,
                    "files": files
                })

            # 返回结果
            if target_depth is not None:
                return depth_info.get(target_depth, [])
            else:
                return {
                    "tree": tree,          # 完整树形结构
                    "depth_info": depth_info  # 按深度分组的节点信息
                }
        trees = get_directory_tree_with_depth(directory)   
        menus=[]
        for key,items in trees['depth_info'].items():
            for index,item in enumerate(items):
                files = item['files']
                depth=int(key)
                if '__init__.py' in files:
                    with open(os.path.join(item['path'], '__init__.py'), 'r', encoding='utf-8') as f:
                        content = f.read()
                        name = None
                        try:
                            match = re.search(r'name\s*=\s*({.*?})', content, re.DOTALL)
                            if match:
                                name_dict = eval(match.group(1))
                                name = name_dict
                        except Exception as e:
                                name = None
                        if name :
                            self.texts['zh'][name['rawname']] = name['zh']
                            self.texts['en'][name['rawname']] = name['en']

                            if depth==0:
                                rootmenu = tk.Menu(self.module_menu, tearoff=0)
                                menus.append([name['rawname'],rootmenu,[],self.module_menu,1+len(self.menulist)])
                                self.module_menu.add_cascade(label=self.texts[self.language][name['rawname']], menu=rootmenu)
                            else:
                                cacademenu = tk.Menu(menus[depth-1][1], tearoff=0)
                                menus.append([name['rawname'],cacademenu,[],menus[depth-1][1],index])
                                menus[depth-1][1].add_cascade(label=self.texts[self.language][name['rawname']], menu=cacademenu)
                    pys=[]
                    for file in files:
                        try:
                            if file.endswith('.py') and file != '__init__.py':
                                file_path = os.path.join(item['path'], file)
                                module_name = os.path.splitext(os.path.basename(file_path))[0]
                                spec = importlib.util.spec_from_file_location(f'{module_name}', file_path)
                                module = importlib.util.module_from_spec(spec)
                                sys.modules[module_name] = module  # 将模块添加到系统模块中
                                spec.loader.exec_module(module)
                                my_class = getattr(module, module_name)
                                rawname = getattr(my_class, 'rawname')
                                zhname = getattr(my_class,'zhname')
                                enname = getattr(my_class,'enname')
                                self.texts['zh'][rawname] = zhname
                                self.texts['en'][rawname] = enname

                                menus[-1][1].add_cascade(label=self.texts[self.language][rawname],command=lambda cls=my_class: self.update_drawobjects(cls.from_userdefined(self, self.curent_img_x, self.curent_img_y,name=cls.rawname,message=self.on_message)))

                                pys.append(rawname)
                        except Exception as e:
                            print(f"Error loading module {file}: {e}")
                    menus[-1][2] = pys 
        self.menulist.append(menus)
    def ini_module(self):
        basedirectory = os.path.dirname(os.path.abspath(__file__))  # 获取当前文件所在目录
        modulesdirectory = os.path.join(basedirectory,'mossmodlues') # os.path.join(os.getcwd(), 'mossflow','mossmodlues')  # 拼接模块目录路径        
        if modulesdirectory:
            for path in os.listdir(modulesdirectory):
                self.load_module(os.path.join(modulesdirectory, path))
            self.load_task(os.path.join(modulesdirectory, 'default.flp'))  # 加载默认任务文件
    def on_language_change(self,event):
        """语言切换"""
        after_lang=event.widget.get()
        self.language = after_lang  # 获取当前选择的语言

        for obj in self.drawobjects.values():
            if hasattr(obj, "language"):
                obj.language=after_lang
        event.widget.destroy()  # 销毁语言选择组件
        
        self.context_menu.entryconfig(0, label=self.texts[self.language]['setting'])
        self.context_menu.entryconfig(1, label=self.texts[self.language]['module'])
        self.context_menu.entryconfig(2, label=self.texts[self.language]['tool'])
        
        self.tool_menu.entryconfig(0, label=self.texts[self.language]['numberkeyboard'])
        self.tool_menu.entryconfig(1, label=self.texts[self.language]['imageviewer'])
        
        self.setting_menu.entryconfig(0, label=self.texts[self.language]['langeuage'])
        self.setting_menu.entryconfig(1, label=self.texts[self.language]['defaulttask'])
        self.setting_menu.entryconfig(2, label=self.texts[self.language]['save'])
        
        self.module_menu.entryconfig(0, label=self.texts[self.language]['script'])

        for menus in self.menulist:
            for menu in menus:
                for i in range(len(menu[2])):
                    if menu[2][i] in self.texts[self.language]:
                        menu[1].entryconfig(i, label=self.texts[self.language][menu[2][i]])
                menu[3].entryconfig(menu[4], label=self.texts[self.language][menu[0]])    
    def update_drawobjects(self,module):
        """更新绘图对象"""
        keys = list(self.drawobjects.keys())
        if module.text in keys:
            if not messagebox.askyesno(self.texts[self.language]['update_drawobjects_msg_title'], self.texts[self.language]['update_drawobjects_msg_content']):
                return
            # If user selects Yes, allow overwrite (do nothing here, will overwrite below)
        else:
            if module.text == "":
                messagebox.showerror(self.texts[self.language]['update_drawobjects_msg_title'], self.texts[self.language]['update_drawobjects_msg_error'])
                return
        self.drawobjects[module.text] = module   
        #module.show_parameter_page(module.x,module.y,self)  
    # region Gobal Functions
    def on_message(self,module,operationcode:int,**kwargs):
        def on_objectselection(event):
            selected_index = modulecombo.current()
            if selected_index != -1:
                paramcombo['values'] = list(self.drawobjects[modulecombo.get()].parameters.keys())  # 更新输出选项
        def on_outputselection(event):
            pass
        def on_confirmbuttonclick(event):
            try:           
                selected_index = modulecombo.current()
                if selected_index != -1 and operationcode == 1:
                    paramname= kwargs['paramname']
                    keyname = kwargs['keyname']
                    setattr(module, paramname,self.drawobjects[modulecombo.get()]) # 赋值模块
                    setattr(module, keyname,paramcombo.get()) # 赋值模块
                    
                    kwargs['button'].config(text=f"{paramname}:   {getattr(module,paramname).text}\n    {gstr(getattr(module,keyname))}")  # 更新按钮文本
                    
                    window.destroy()
            except Exception as e:
                messagebox.showerror(self.texts['on_confirmbuttonclick_errormsg_title'], self.texts['on_confirmbuttonclick_errormsg_content'] + f"\n{e}")
        # 删除模块
        if operationcode == -1:
            del self.drawobjects[module.text]
            del module
            return
        # 修改模块名称
        if operationcode == -2:
            first_key = next((k for k, v in self.drawobjects.items() if v == module), None)
            self.drawobjects[module.text] = self.drawobjects.pop(first_key)  # 取出旧键值并赋给新键
            return
        if operationcode == 3:
            module.load(self.drawobjects)
            return
        elif operationcode == 1:
            pass
        window= tk.Toplevel(self)
        window.iconphoto(True,ImageTk.PhotoImage(Image.open(load_icon())))  # 设置窗口图标
        l1=getattr(sys.modules['Grpahics_WrapIfLineModule'],'Grpahics_WrapIfLineModule')
        l2=getattr(sys.modules['Grpahics_WrapLineModule'],'Grpahics_WrapLineModule')
        modulecombo = ttk.Combobox(window, values=[key for key in self.drawobjects.keys() if not isinstance(self.drawobjects[key], (l1,l2))], state="readonly")
        modulecombo.bind("<<ComboboxSelected>>", on_objectselection)  # 绑定选择事件
        modulecombo.grid(column=0,row=0,pady=1)
        paramcombo = ttk.Combobox(window)
        paramcombo.bind("<<ComboboxSelected>>", on_outputselection)  # 绑定选择事件
        paramcombo.grid(column=0,row=1,pady=1)        
        confirmbutton = tk.Button(window, text="Confirm")
        confirmbutton.bind("<Button-1>", on_confirmbuttonclick)  # 绑定单击事件
        confirmbutton.grid(column=0,row=2,pady=1)
        window.geometry(f"+{self.winfo_rootx()+100}+{self.winfo_rooty()+100}")
    def copy_to_clipboard(self,evetn):
        # 清空剪切板并复制标签内容
        self.clipboard_clear()
        self.clipboard_append(self.infolabel.cget("text"))
        messagebox.showinfo("Copy!", "Copied to clipboard!")
    # endregion
    # region GL functions
    def on_resize(self, event):
        if event.widget != self:
            return
        try:
            self.tkMakeCurrent()
            self.width = event.width
            self.height = event.height

            # 防止初始化为0大小
            if self.width < 1 or self.height < 1:
                self.width, self.height = 800, 800
            glViewport(0, 0, self.width, self.height)
        except Exception as e:
            pass
    def initgl(self):
        """初始化OpenGL和加载纹理"""
        self.tkMakeCurrent()
        glClearColor(self.background_color[0], self.background_color[1], self.background_color[2], self.background_color[3])
    def redraw(self):
        """渲染纹理四边形"""
        glViewport(0, 0, self.width, self.height)
        self.tkMakeCurrent()
        glUseProgram(0)  # 禁用着色器程序
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(self.background_color[0], self.background_color[1], self.background_color[2], self.background_color[3])

        if True:            
            # 设置投影矩阵
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            glOrtho(-self.width/2, self.width/2, self.height/2, -self.height/2,-1,1)
            
            # 设置模型视图矩阵
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            
            # 应用缩放和平移
            glTranslatef(self.offset_x,self.offset_y, 0)
            glScalef(self.scale, self.scale, 1)
            glRotatef(self.rotation_angle*(180/pi), 0, 0, 1)
            keys = list(self.drawobjects.keys())
            for i,key in enumerate(keys):
                self.drawobjects[key].GLDraw()
            glColor3f(1.0, 1.0, 1.0)

    # endregion
    # region Mouse Event
    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        self.current_mouse_x = event.x
        self.current_mouse_y = event.y
        imgpos= self.WindowPos2GLPos(self.current_mouse_x, self.current_mouse_y)
        self.curent_img_x = imgpos[0]
        self.curent_img_y = imgpos[1]
        #self.infolabel.config(text= f"GLPosition {self.curent_img_x:.2f}, {self.curent_img_y:.2f},\nScale: {self.scale:.2f}, \nOffset: ({self.offset_x:.2f}, {self.offset_y:.2f})")
    def on_mouse_wheel(self, event):
        """处理鼠标滚轮事件"""
        # 确定缩放方向
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):  # 上滚/放大
            zoom_factor = 1.1
        else:  # 下滚/缩小
            zoom_factor = 0.9
        
        # 应用缩放限制
        new_scale = self.scale * zoom_factor
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        
        
        self.scale = new_scale
        self.redraw() 
    def on_button3_press(self, event):
        """开始拖动"""
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.dragging = True
    def on_button2_press(self, event):
        self.tkMakeCurrent()
        glViewport(0, 0, self.width, self.height)
        self.reset_view()
        self.redraw()
    def on_mouseright_drag(self, event):
        """处理拖动"""
        if self.dragging and len(self.selectobjects)== 0:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            
            self.offset_x += dx
            self.offset_y += dy

            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.redraw()
        if self.dragging and len(self.selectobjects) > 0:
            lastglx,lastgly= self.WindowPos2GLPos(self.last_mouse_x, self.last_mouse_y)
            curglx,curgly= self.WindowPos2GLPos(event.x, event.y)
            for i in range(len(self.selectobjects)):
                self.selectobjects[i].x += curglx - lastglx
                self.selectobjects[i].y += curgly - lastgly
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.redraw()
    def on_mouseleft_click(self,event):
        """处理左键单击事件"""
        self.focus_force()
        # 获取鼠标在窗口中的位置
        mouse_x = event.x
        mouse_y = event.y
        keys = list(self.drawobjects.keys())
        for i,key in enumerate(keys):
            self.drawobjects[key].status = 'Normal'
        self.selectobjects.clear()
        # 计算鼠标在图片坐标系中的位置
        mouse_x_imgsystem,mouse_y_imgsystem= self.WindowPos2GLPos(mouse_x, mouse_y)
        for i,key in enumerate(keys):
            tryselectobjs= self.drawobjects[key].contains(mouse_x_imgsystem, mouse_y_imgsystem)
            if tryselectobjs is not None: 
                if isinstance(tryselectobjs, list):
                    self.selectobjects.extend(tryselectobjs)
                else:
                    self.selectobjects.append(tryselectobjs)
                self.infolabel.config(text= tryselectobjs.moudlestatus)
                break
            else:
                self.drawobjects[key].status = 'Normal'
        self.redraw()       
    def on_button3_release(self, event):
        """结束拖动"""
        self.dragging = False
    def on_mouseleftdouble_click(self,event):
        """处理左键双击事件"""
        # 打开上下文菜单
        # 获取鼠标在窗口中的位置
        mouse_x = event.x
        mouse_y = event.y
        keys = list(self.drawobjects.keys())
        for i,key in enumerate(keys):
            self.drawobjects[key].status = 'Normal'
        self.selectobjects.clear()
        # 计算鼠标在图片坐标系中的位置
        mouse_x_imgsystem,mouse_y_imgsystem= self.WindowPos2GLPos(mouse_x, mouse_y)
        for i,key in enumerate(keys):
            self.drawobjects[key].show_parameter_page(mouse_x_imgsystem, mouse_y_imgsystem,self)    
    def on_mouselrightdouble_click(self,event):
        """处理右键双击事件"""
        # 打开上下文菜单
        
        self.context_menu.post(event.x_root, event.y_root)    
    # endregion
    # region Keyboard Event
    def on_f5(self,event):
        """处理F5键事件"""
        if len(self.selectobjects)>0:
            for i in range(len(self.selectobjects)):
                self.selectobjects[i].run()
                self.infolabel.config(text= self.selectobjects[i].moudlestatus)
    def on_f11(self,event):
        if self.selectobjects is None or len(self.selectobjects) ==0:
            messagebox.showinfo("Error", self.texts[self.language]['on_f11_error'])
            return
        iv=ImgViewer(self,self.selectobjects[0],self.on_importannos2flowplane)
    def on_delete(self,event):
        """处理Delete键事件"""
        if len(self.selectobjects)>0:
            if tk.messagebox.askokcancel("Delete", "Are you sure you want to delete these modules?"):
                for i in range(len(self.selectobjects)):
                    del self.drawobjects[self.selectobjects[i].text]
                    del self.selectobjects[i]
                self.redraw()
    # endregion
    # region View Functions
    def reset_view(self):
        self.scale = 1.0
        self.offset_x = 0#self.width / 2
        self.offset_y = 0#self.height / 2
        self.curent_img_x =0
        self.curent_img_y =0
        self.current_mouse_x =0
        self.current_mouse_y =0
        self.redraw()
    def GLPos2WindowPos(self, x, y):
        """将图片坐标转换为窗口坐标，考虑旋转"""
        affine_matrix = np.array([
        [self.scale * cos(self.rotation_angle), -self.scale * sin(self.rotation_angle), self.offset_x],
        [self.scale * sin(self.rotation_angle), self.scale * cos(self.rotation_angle), self.offset_y],
        [0, 0, 1]])
        point = np.array([x, y, 1])
        transformed_point = np.dot(affine_matrix, point)
        return transformed_point[0]+self.width/2, transformed_point[1]+self.height/2
    def WindowPos2GLPos(self, x, y):
        """将窗口坐标转换为图片坐标，考虑旋转"""
        # 减去偏移
        x = x - self.width/2
        y = y - self.height/2
        affine_matrix = np.array([
        [self.scale * cos(self.rotation_angle), -self.scale * sin(self.rotation_angle), self.offset_x],
        [self.scale * sin(self.rotation_angle), self.scale * cos(self.rotation_angle), self.offset_y],
        [0, 0, 1]])
        point = np.array([x, y, 1])
        affine_matrix_inv=np.linalg.inv(affine_matrix)
        # 反向旋转
        transformed_point = np.dot(affine_matrix_inv, point)
        return transformed_point[0], transformed_point[1]
    # endregion
class ImgGLFrame(OpenGLFrame):
    #顶点着色器
    vertex_shader = """
        #version 460
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec2 texCoord;
        uniform mat4 projection;
        uniform mat4 model;
        uniform mat4 view;
        out vec2 vTexCoord;

        void main()
        {
            gl_Position = projection*view*model*vec4(position, 1.0);
            vTexCoord = texCoord;
        }
        """
    rect_vertex_shader = """
        #version 460
        layout(location = 0) in vec3 position;
        layout(location = 1) in vec4 shapecolor;
        uniform mat4 projection;
        uniform mat4 model;
        uniform mat4 view;
        out vec4 shapecolor_out;

        void main()
        {
            gl_Position = projection*view*model*vec4(position, 1.0);
            shapecolor_out = shapecolor;  
        }
        """
    vertex_shader_es = """
        attribute vec3 position;
        attribute vec2 texCoord;
        uniform mat4 projection;
        uniform mat4 model;
        uniform mat4 view;
        varying vec2 vTexCoord;

        void main()
        {
            gl_Position = projection * view * model * vec4(position, 1.0);
            vTexCoord = texCoord;
        }"""
    #片段着色器
    fragment_shader_es = """
        precision mediump float;
        varying vec2 vTexCoord;
        uniform sampler2D textureSampler;
        uniform int texturetype;  // 0: RGB, 1: Luminance
        uniform float minv;  // 最小亮度
        uniform float maxv;  // 最大亮度

        vec3 hsv2rgb(vec3 c) {
            vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
            vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
            return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
        }

        vec3 luminanceToColor(float luminance, float minLuminance, float maxLuminance) {
            
            float normalizedLuminance = (luminance - minLuminance) / (maxLuminance - minLuminance);
            normalizedLuminance = clamp(1.0 - normalizedLuminance, 0.0, 1.0);

            // 调整Hue范围：0.0（红）→ ~0.8（紫）
            float hue = normalizedLuminance * 0.8; // 限制在红→紫之间
            vec3 hsvColor = vec3(hue, 1.0, 1.0); // 饱和度和亮度设为1
            return hsv2rgb(hsvColor);
        }

        void main() {
            vec4 texColor;

            if (texturetype == 0) {
                texColor = texture2D(textureSampler, vTexCoord);  // 直接使用纹理
                gl_FragColor = texColor; // 使用纹理颜色
            } 
            else if (texturetype == 1) {
                float luminance = texture2D(textureSampler, vTexCoord).r;  // 获取纹理的红色通道作为亮度
                float normalizeluminance = clamp((luminance - minv) / (maxv - minv), 0.0, 1.0);
                if (luminance < minv || luminance > maxv) {
                    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);  // 如果亮度不在范围内，设置为黑色
                } 
                else {
                    gl_FragColor = vec4(normalizeluminance, normalizeluminance, normalizeluminance, 1.0);  // 将亮度值应用到RGB通道
                }
            } 
            else if (texturetype == 2) {
                float luminance = texture2D(textureSampler, vTexCoord).r;  // 获取纹理的红色通道作为亮度
                vec3 color = luminanceToColor(luminance, minv, maxv);  // 将亮度值转换为颜色
                if (luminance < minv || luminance > maxv || isnan(luminance)) {
                    gl_FragColor = vec4(0.0, 0.0, 0.0, 1.0);  // 如果亮度不在范围内，设置为黑色
                } 
                else {
                    gl_FragColor = vec4(color, 1.0);  // 将颜色应用到输出
                }
            }
        }"""
    fragment_shader = """
        #version 460
        in vec2 vTexCoord;
        out vec4 fragColor;

        uniform sampler2D textureSampler;
        uniform int texturetype;  // 0: RGB, 1: Luminance
        uniform float minv;  // 最小亮度
        uniform float maxv;  // 最大亮度
        vec3 hsv2rgb(vec3 c) {
            vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
            vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
            return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
        }

        vec3 luminanceToColor(float luminance, float minLuminance, float maxLuminance) 
        {
            float normalizedLuminance = (luminance - minLuminance) / (maxLuminance - minLuminance);
            normalizedLuminance = clamp(1-normalizedLuminance, 0.0, 1.0);

            // 调整Hue范围：0.0（红）→ ~0.8（紫）
            float hue = normalizedLuminance * 0.8; // 限制在红→紫之间
            vec3 hsvColor = vec3(hue, 1.0, 1.0); // 饱和度和亮度设为1
            return hsv2rgb(hsvColor);
        }
        
        void main()
        {
            if (texturetype == 0) 
            {
                fragColor = texture(textureSampler, vTexCoord);  // 直接使用纹理
            } 
            else if (texturetype == 1) 
            {
                float luminance = texture(textureSampler, vTexCoord).r;  // 获取纹理的红色通道作为亮度
                float normalizeluminance = clamp((luminance - minv) / (maxv-minv), 0.0, 1.0);
                if(luminance < minv || luminance > maxv) 
                {
                    fragColor = vec4(0.0, 0.0, 0.0, 1.0);  // 如果亮度不在范围内，设置为黑色
                }
                else 
                {
                    fragColor = vec4(normalizeluminance, normalizeluminance, normalizeluminance, 1.0);  // 将亮度值应用到RGB通道
                }
            }
            else if (texturetype == 2) 
            {
                float luminance = texture(textureSampler, vTexCoord).r;  // 获取纹理的红色通道作为亮度
                vec3 color = luminanceToColor(luminance,minv,maxv);  // 将亮度值转换为颜色
                if(luminance < minv || luminance > maxv || isnan(luminance)) 
                {
                    fragColor = vec4(0.0, 0.0, 0.0, 1.0);  // 如果亮度不在范围内，设置为黑色
                } 
                else 
                {
                    fragColor = vec4(color, 1.0);  // 将颜色应用到输出
                }
            }
        }
        """
    rect_fragment_shader = """
        #version 460
        in vec4 shapecolor_out;
        out vec4 fragColor;
        void main()
        {
            fragColor = shapecolor_out;  // 使用传入的颜色
        }
        """
    def __init__(self,master,coordsys=None,**kwargs):
        super().__init__(master,**kwargs)
        self.language = 'en'
        self.texts = {
            'en':{
            'info': 'Information',
            'minmax': 'Min-Max:',   
            'auto': 'Auto',
            },
            'zh':{
            'info': '信息',
            'minmax': '最小-最大:',
            'auto': '自动',
            }
        }
        self.imagecoord = coordsys if coordsys is not None else ImgGL_Coordinate('BaseCoordSys',0,0,100,100,0,[1,1,1,0.5])
        self.drag_interval = 0.015  # 设置拖动延迟为100毫秒
        self.last_drag_time = 0
        self.isDrawingSelectionRect = False
        self.selectrect = ImgGL_Rectangle('selectroi',0,0,10,10,0,[1,1,1,0.75])
        
        self.animate =False
        self.shader= None
        self.maxvalue=tk.DoubleVar(value=1.0)
        self.minvalue=tk.DoubleVar(value=-1.0)
        self.img_texture_data=None
        
        self.infolabel = tk.Label(self, text=self.texts[self.language]['info'], bg="black", fg="white")
        self.infolabel.bind("<Double-Button-1>", self.copy_to_clipboard)

        self.minmax_frame = tk.Frame(self)
        self.label = tk.Label(self.minmax_frame, text=self.texts[self.language]['minmax'])
        self.minscale = tk.Scale(self.minmax_frame,state='disabled',from_=-10,to=10,variable=self.minvalue,orient=tk.HORIZONTAL,resolution=0.01,troughcolor="gray", sliderrelief=tk.RAISED, activebackground="blue", font=("Arial", 10))
        self.maxscale = tk.Scale(self.minmax_frame,state='disabled',from_=-10,to=10,variable=self.maxvalue,orient=tk.HORIZONTAL,resolution=0.01,troughcolor="gray", sliderrelief=tk.RAISED, activebackground="red", font=("Arial", 10))
        self.autocolorbn = tk.Button(self.minmax_frame,state='disabled', text="Auto")
        self.label.grid(row=0, column=0, padx=5, pady=5)
        self.minscale.grid(row=0, column=1, padx=5, pady=5)
        self.maxscale.grid(row=0, column=2, padx=5, pady=5)
        self.autocolorbn.grid(row=0, column=3, padx=5, pady=5)
        self.minvalue.trace_add("write", lambda *args: self.set_minv(self.minvalue.get()))  # 绑定变量变化事件
        self.maxvalue.trace_add("write", lambda *args: self.set_maxv(self.maxvalue.get()))  # 绑定变量变化事件
        self.autocolorbn.bind("<Button-1>", lambda event: self.update_window_depthcolor())

        # 创建Treeview
        self.graphicstreeframe = Graphics_Tree(self)
        self.tree = self.graphicstreeframe.tree
        def update(root,ashape):
            self.tree.insert(root, "end",str(id(ashape)), text=ashape.name)
            if isinstance(ashape, ImgGL_Coordinate) and len(ashape.shapes) > 0:
                for subshape in ashape.shapes:
                    update(id(ashape),subshape)
        update("",self.imagecoord)
        
        
#        self.tree.insert("", "end",id(self.imagecoord), text=self.imagecoord.name)
        # 创建形状工具
        self.shapetoolsframe= tk.Frame(self)
        self.addrectbn = tk.Button(self.shapetoolsframe, text="Rect")
        self.addrectbn.grid(row=0, column=0, padx=0, pady=0)
        self.addrectbn.bind("<Button-1>", lambda event: self.on_addrect())
        self.addcoordbn = tk.Button(self.shapetoolsframe, text="Coord")
        self.addcoordbn.grid(row=0, column=1, padx=0, pady=0)
        self.addcoordbn.bind("<Button-1>", lambda event: self.on_addcoord())
        self.addseglinebn = tk.Button(self.shapetoolsframe, text="Line")
        self.addseglinebn.grid(row=0, column=2, padx=0, pady=0)
        self.addseglinebn.bind("<Button-1>", lambda event: self.on_addsegline())
        
        self.texture_id = None
        self.selectobjects = []  # 存储选中的对象
        self.selectobject= None
        self.copybuffer = None
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        # 缩放和位置变量
        self.scale = 1.0
        self.min_scale = 0.01
        self.max_scale = 100.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.rotation_angle = 0.0  
        # 鼠标跟踪
        self.last_mouse_x = 0
        self.last_mouse_y = 0
        self.current_mouse_x = 0
        self.current_mouse_y = 0
        self.curent_img_x = 0
        self.curent_img_y = 0
        self.leftdragging = False
        self.rightdragging =False
        # 键盘状态
        self.ctrl = False
        self.shift = False
        # 绑定事件
        self.bind("<Enter>", self.on_enter)  # 鼠标进入事件
        self.bind("<Motion>", self.on_mouse_move)  # 鼠标移动事件
        self.bind("<MouseWheel>", self.on_mouse_wheel)  # Windows
        self.bind("<Button-4>", self.on_mouse_wheel)    # Linux上滚
        self.bind("<Button-5>", self.on_mouse_wheel)    # Linux下滚
        self.bind("<ButtonPress-1>", self.on_button1_press)
        self.bind("<ButtonPress-2>", self.on_button2_press)
        self.bind("<ButtonPress-3>", self.on_button3_press)
        self.bind("<B1-Motion>", self.on_leftmouse_drag)
        self.bind("<B3-Motion>", self.on_rightmouse_drag)
        self.bind("<ButtonRelease-1>", self.on_leftbutton_release)
        self.bind("<ButtonRelease-3>", self.on_rightbutton_release)
        self.bind("<Configure>", self.on_resize)
        self.bind("<Destroy>", self.close)  # 窗口销毁时清除OpenGL资源    
        self.bind("<KeyPress>", self.on_key_press)  # 键盘按下事件
        self.bind("<KeyRelease>", self.on_key_release)  # 键盘释放事件
        self.bind("<Double-Button-1>", self.on_mouseleftdouble_click)  # 左键双击事件
    def on_addrect(self):
        inputdialog= InputStrDialog(self,"Add Rectangle","Rectangle Name:")
        rectname = inputdialog.input
        if rectname :
            newrectx,newrecty = self.WindowPos2ImagePos(self.width/2,self.height/2)
            newwidth = self.width/self.scale*0.33
            newheight = self.height/self.scale*0.33
            newrect= ImgGL_Rectangle(rectname,newrectx-self.img_width/2,newrecty-self.img_height/2,newwidth,newheight,0,[1,0,0,1])
            newrect.parent = self.imagecoord
            self.tree.insert(id(self.imagecoord), "end",id(newrect), text=newrect.name)
            self.imagecoord.shapes.append(newrect)         
            self.redraw()
        else:
            messagebox.showerror("Error", "Invalid or duplicate name!")
    def on_addsegline(self):
        inputdialog= InputStrDialog(self,"Add Line","Line Name:")
        linename = inputdialog.input
        if linename:
            newcoordx,newcoordy = self.WindowPos2ImagePos(self.width/2,self.height/2)
            newcoordy -= self.img_height/2
            newcoordx -= self.img_width/2
            newwidth = self.width/self.scale*0.1
            newline= ImgGL_SegmentLine(linename,[newcoordx+newwidth,newcoordy],[newcoordx-newwidth,newcoordy],0,[1,0,0,1])
            newline.parent = self.imagecoord
            self.imagecoord.shapes.append(newline)
            self.tree.insert(id(self.imagecoord), "end",id(newline), text=newline.name)
            self.redraw()
    def on_addcoord(self):
        inputdialog= InputStrDialog(self,"Add Coordinate System","Coordinate Name:")
        coordname = inputdialog.input
        if coordname:
            newcoordx,newcoordy = self.WindowPos2ImagePos(self.width/2,self.height/2)
            newwidth = self.width/self.scale*0.33
            newheight = self.height/self.scale*0.33
            newcoord= ImgGL_Coordinate(coordname,newcoordx-self.img_width/2,newcoordy-self.img_height/2,newwidth,newheight,0,[1,0,0,1])
            newcoord.parent = self.imagecoord
            self.imagecoord.shapes.append(newcoord)
            self.tree.insert(id(self.imagecoord), "end",id(newcoord), text=newcoord.name)
            self.redraw()
    def setlangeuage(self,language):
        if language in self.texts:
            self.language = language
            self.infolabel.config(text=self.texts[self.language]['info'])
            self.label.config(text=self.texts[self.language]['minmax'])
            self.autocolorbn.config(text=self.texts[self.language]['auto'])
    def updatetools(self,labeinfo:False,minmax:False,graphics:False,shapetools:False):
        if labeinfo:
            self.infolabel.pack(anchor='nw', padx=10, pady=10)
            self.bind("")
        else:
            self.infolabel.pack_forget()  # 隐藏标签
        if minmax:
            self.minmax_frame.pack(anchor='nw', padx=10, pady=10)
        else:
            self.minmax_frame.pack_forget() 
        if graphics:
            self.graphicstreeframe.pack(anchor='nw', padx=10, pady=10, expand=True)
        else:
            self.graphicstreeframe.pack_forget()
        if shapetools:
            self.shapetoolsframe.pack(anchor='nw', padx=10, pady=10)
        else:
            self.shapetoolsframe.pack_forget()
    def initgl(self):
        self.tkMakeCurrent()
        glClearColor(0.2, 0.2, 0.2, 1.0)  
        self.shader =self.create_shader_program()
        self.rect_shader = self.create_rectshapeshader_program()
        self.indices = np.array([
                0, 1, 2,
                2, 3, 0
            ], dtype=np.uint32)
            # 创建VAO, VBO和EBO
        self.vao = glGenVertexArrays(1)  # 创建顶点数组对象
        self.vbo = glGenBuffers(1)
        self.ebo = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_STATIC_DRAW)
        self.texture_id = None
        self.img_height = 8
        self.img_width = 8   
    def close(self,event):
        """清除OpenGL选项"""
        self.tkMakeCurrent()
        if self.texture_id is not None:
            glDeleteTextures([self.texture_id])
            self.texture_id = None
        if self.vao is not None:
            glDeleteVertexArrays(1, [self.vao])
            self.vao = None
        if self.vbo is not None:
            glDeleteBuffers(1, [self.vbo])
            self.vbo = None
        if self.ebo is not None:
            glDeleteBuffers(1, [self.ebo])
            self.ebo = None
        if self.shader is not None:
            glDeleteProgram(self.shader)
            self.shader = None
    def clipWindowRoi(self):
        """裁剪窗口到当前视图"""
        if self.img_texture_data is None:
            return
        x1,y1= self.WindowPos2ImagePos(0,0)
        x2,y2= self.WindowPos2ImagePos(self.width,self.height)
        x1 = 0 if x1 <0 or x1 > self.img_width else x1
        y1 = 0 if y1 <0 or y1 > self.img_height else y1
        x2 = self.img_width if x2 <0 or x2 > self.img_width else x2
        y2 = self.img_height if y2 <0 or y2 > self.img_height else y2
        if x1 >= x2 or y1 >= y2:
            messagebox.showerror("Error", "Invalid clipping region")
            return
        return self.img_texture_data[int(y1):int(y2), int(x1):int(x2)]       
    def copy_to_clipboard(self,evetn):
        # 清空剪切板并复制标签内容
        self.clipboard_clear()
        self.clipboard_append(self.infolabel.cget("text"))
        messagebox.showinfo("Copy!", "Copied to clipboard!")
    def on_resize(self, event):
        """处理窗口大小变化"""
        if event.widget != self:
            return
        self.tkMakeCurrent()
        self.width = self.winfo_width()
        self.height = self.winfo_height()
        
        # 防止初始化为0大小
        if self.width < 1 or self.height < 1:
            self.width, self.height = 800, 800
        version = glGetString(GL_VERSION)
        if version and hasattr(self, 'shader'):
            try:
                glViewport(0, 0, self.width, self.height)
            except Exception as e:
                messagebox.askquestion('Error',f"Error updating viewport: {e}", icon='error')
    def ortho_matrix(self,left, right, bottom, top, near, far):
        return glm.ortho(left, right, bottom, top, near, far)
    def view_matrix(self):       
        return glm.lookAt(glm.vec3(0, 0, 1),  # 相机位置
                          glm.vec3(0, 0, 0),  # 目标位置
                          glm.vec3(0, 1, 0))
    def model_matrix(self,offset_x, offset_y,angle, scale):
        modelm= glm.mat4(1.0)  # 单位矩阵
        translation = glm.translate(modelm, glm.vec3( offset_x, offset_y, 0))
        scaling = glm.scale(modelm, glm.vec3(scale, scale, 1))
        roation = glm.rotate(modelm, glm.radians(angle), glm.vec3(0, 0, 1))
        return translation*scaling*roation  # 返回平移+缩放后的模型矩阵
    def update_window_depthcolor(self):
        """更新窗口深度图"""
        if self.img_texture_data is None:
            return
        self.tkMakeCurrent()
        glUseProgram(self.shader)
        window_texture_data = self.clipWindowRoi()
        if window_texture_data is None:
            return
        else:
                vaild_values = window_texture_data[window_texture_data > -10000]
                self.maxvalue.set(np.max(vaild_values))
                self.minvalue.set(np.min(vaild_values))
                self.redraw()
    def load_texture(self,width:int,height:int,texture_data:np.ndarray,format,insideformat,pixel_format):
        """加载图片并创建OpenGL纹理"""
        try:
            self.tkMakeCurrent()
            self.texture_id = glGenTextures(1)

            if self.shader is None:
                messagebox.askquestion('Error',f"Error creating shader program: {glGetError()}", icon='error')
                return            
            if self.texture_id is not None:
                glDeleteTextures([self.texture_id])
                self.texture_id = None      
            glUseProgram(self.shader)  # 使用着色器程序
  
            glBindVertexArray(self.vao)  # 绑定VAO
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)  # 绑定VBO
            self.vertices = np.array([
                # 位置    纹理坐标
                 -width/2, -height/2,   0.0,  0.0,   0.0,  # 左下
                 width/2,  -height/2,   0.0,  1.0,   0.0,  # 右下
                 width/2,  height/2,    0.0,  1.0,   1.0,  # 右上
                 -width/2,  height/2,   0.0,  0.0,   1.0   # 左上
            ], dtype=np.float32)          
            glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
    
            # 绑定并设置元素缓冲
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_DYNAMIC_DRAW)
    
            # 位置属性
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
    
            # 纹理坐标属性
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
            glEnableVertexAttribArray(1)
    
            # 解绑VAO
            glBindVertexArray(0)
            if format == GL_R32F:
                textureType = TextureFormat.DepthColor
                vaild_values = texture_data[texture_data > -10000]
                v1 = np.min(vaild_values)
                v2 = np.max(vaild_values)
                
                self.minscale.configure(state='normal',from_=v1, to=v2)
                self.maxscale.configure(state='normal',from_=v1, to=v2)

                self.maxvalue.set(v2)
                self.minvalue.set(v1)
                glUniform1f(glGetUniformLocation(self.shader, "maxv"), v2)  # 设置纹理类型
                glUniform1f(glGetUniformLocation(self.shader, "minv"), v1)  # 设置纹理类型
                
                self.autocolorbn.configure(state='normal')
            else:
                textureType = TextureFormat.Color
                self.minscale.configure(state='disabled',from_=self.minvalue.get(), to=self.maxvalue.get())
                self.maxscale.configure(state='disabled',from_=self.minvalue.get(), to=self.maxvalue.get())
                self.autocolorbn.configure(state='disabled')
                
            glUniform1i(glGetUniformLocation(self.shader, "texturetype"), textureType.value)  # 设置纹理类型
                  
            self.texture_id = glGenTextures(1)  # 创建纹理ID   
            self.img_width = width
            self.img_height = height

            self.img_texture_data = texture_data
            self.format=format
            self.insideformat = insideformat
            self.pixel_format=pixel_format
            glBindTexture(GL_TEXTURE_2D, self.texture_id)   
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)  # 边缘处理
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
            glTexImage2D(GL_TEXTURE_2D, 0, self.format, self.img_width, self.img_height,0, self.insideformat, self.pixel_format, self.img_texture_data)
            glBindTexture(GL_TEXTURE_2D, 0)  # 禁用纹理

            self.on_button2_press(None)

        except Exception as e:
            messagebox.askquestion('Error',f"Error updating viewport: {e},\n,{glGetError()}", icon='error')

            self.texture_id = None      
    def set_maxv(self, maxv:float):
        """设置最大亮度值"""
        self.tkMakeCurrent()
        if self.shader is not None:
            glUseProgram(self.shader)  # 使用着色器程序
            glUniform1f(glGetUniformLocation(self.shader, "maxv"), maxv)
            self.redraw()
    def set_minv(self, minv:float):
        """设置最小亮度值"""
        self.tkMakeCurrent()
        if self.shader is not None:
            glUseProgram(self.shader)  # 使用着色器程序
            glUniform1f(glGetUniformLocation(self.shader, "minv"), minv)
            self.redraw()
    def create_shader_program(self):
        """创建并编译着色器程序"""
        # 编译着色器
        if sysplatform.system() == 'Windows':
            vertex = compileShader(self.vertex_shader, GL_VERTEX_SHADER)
            fragment = compileShader(self.fragment_shader, GL_FRAGMENT_SHADER)
        else:
            vertex = compileShader(self.vertex_shader_es, GL_VERTEX_SHADER)
            fragment = compileShader(self.fragment_shader_es, GL_FRAGMENT_SHADER)
        # 链接着色器程序
        program = compileProgram(vertex, fragment)

        # 检查链接状态
        if not glGetProgramiv(program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(program).decode()
            print(f"程序链接错误: {error}")
            glDeleteProgram(program)
            return None

        return program        
    def create_rectshapeshader_program(self):
        """创建并编译着色器程序"""
        # 编译着色器
        if sysplatform.system() == 'Windows':
            vertex = compileShader(self.rect_vertex_shader, GL_VERTEX_SHADER)
            fragment = compileShader(self.rect_fragment_shader, GL_FRAGMENT_SHADER)
        else:
            vertex = compileShader(self.vertex_shader_es, GL_VERTEX_SHADER)
            fragment = compileShader(self.fragment_shader_es, GL_FRAGMENT_SHADER)
        # 链接着色器程序
        program = compileProgram(vertex, fragment)

        # 检查链接状态
        if not glGetProgramiv(program, GL_LINK_STATUS):
            error = glGetProgramInfoLog(program).decode()
            print(f"程序链接错误: {error}")
            glDeleteProgram(program)
            return None
        return program
    def redraw(self):
        """渲染纹理四边形"""
        # wglMakeCurrent(self.winfo_id(), wglCreateContext(self.winfo_id))  # 设置当前上下文
        self.tkMakeCurrent()
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glClearColor(0.11, 0.13, 0.09, 1.0)
        glEnable(GL_BLEND)  # 启用混合
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        if self.texture_id:
            glUseProgram(self.shader)  # 使用着色器程序
            glBindVertexArray(self.vao)
            if self.format == GL_R32F:
                textureType = TextureFormat.DepthColor
                glUniform1f(glGetUniformLocation(self.shader, "maxv"), self.maxvalue.get())  # 设置纹理类型
                glUniform1f(glGetUniformLocation(self.shader, "minv"), self.minvalue.get())  # 设置纹理类型
            else:
                textureType = TextureFormat.Color          
            glUniform1i(glGetUniformLocation(self.shader, "texturetype"), textureType.value)  # 设置纹理类型
            glUniformMatrix4fv(glGetUniformLocation(self.shader, "projection"),
                               1, GL_TRUE, np.array((self.ortho_matrix(-self.width/2, self.width/2,self.height/2, -self.height/2, -1, 1))))
            glUniformMatrix4fv(glGetUniformLocation(self.shader, "model"),
                               1, GL_TRUE, np.array(self.model_matrix(self.offset_x,self.offset_y,self.rotation_angle,self.scale)))  # 单位矩阵
            glUniformMatrix4fv(glGetUniformLocation(self.shader, "view"),
                               1, GL_TRUE, np.array(self.view_matrix()))
            glBindBuffer(GL_ARRAY_BUFFER, self.vbo)  # 绑定VBO
            glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
            glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ebo)  # 绑定EBO
            glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_DYNAMIC_DRAW)
            glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(0))
            glEnableVertexAttribArray(0)
            glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
            glEnableVertexAttribArray(1)
            glActiveTexture(GL_TEXTURE0)
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glUniform1i(glGetUniformLocation(self.shader, "textureSampler"), 0)
            glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
            glBindTexture(GL_TEXTURE_2D, 0)  # 禁用纹理
            glBindVertexArray(0)  # 解绑VAO
       #绘制图像
        self.imagecoord.draw(self)
        if self.isDrawingSelectionRect:
            self.selectrect.draw(self)
        self.tkSwapBuffers()  # 交换前后缓冲区
        self.updating = False
    def on_enter(self, event):
        """处理鼠标进入事件"""
        self.focus_force()
    def on_mouse_move(self, event):
        """处理鼠标移动事件"""
        self.current_mouse_x = event.x
        self.current_mouse_y = event.y

        imgpos= self.WindowPos2ImagePos(self.current_mouse_x, self.current_mouse_y)
        self.curent_img_x = imgpos[0]
        self.curent_img_y = imgpos[1]
        if self.img_texture_data is not None:
            self.curent_img_x = 0  if self.curent_img_x> self.img_width-1 or self.curent_img_x<0 else self.curent_img_x
            self.curent_img_y = 0  if self.curent_img_y> self.img_height-1 or self.curent_img_y<0 else self.curent_img_y
            currentvalue= self.img_texture_data[int(self.curent_img_y), int(self.curent_img_x)]
            if self.language == 'zh':
                self.infolabel.config(text= f"当前坐标 {self.curent_img_x:.2f}, {self.curent_img_y:.2f},\n像素值 {currentvalue}\n缩放: {self.scale:.2f}, \n偏移: ({self.offset_x:.2f}, {self.offset_y:.2f})\n尺寸: ({self.img_width}, {self.img_height})")
            else:
                self.infolabel.config(text= f"CurrentPosition {self.curent_img_x:.2f}, {self.curent_img_y:.2f},\nImageValue {currentvalue}\nScale: {self.scale:.2f}, \nOffset: ({self.offset_x:.2f}, {self.offset_y:.2f})\nSize: ({self.img_width}, {self.img_height})")
    def on_mouse_wheel(self, event):
        """处理鼠标滚轮事件"""
        # 获取鼠标在窗口中的位置
        mouse_x = event.x
        mouse_y = event.y
        
        # 计算鼠标在图片坐标系中的位置
        mouse_x_imgsystem,mouse_y_imgsystem= self.WindowPos2ImagePos(mouse_x, mouse_y)
                
        
        # 确定缩放方向
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):  # 上滚/放大
            zoom_factor = 1.1
        else:  # 下滚/缩小
            zoom_factor = 0.9
        
        # 应用缩放限制
        new_scale = self.scale * zoom_factor
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        
        self.scale = new_scale
        x,y= self.ImagePos2WindowPos(mouse_x_imgsystem, mouse_y_imgsystem)
        self.offset_x = mouse_x-x + self.offset_x
        self.offset_y = mouse_y-y + self.offset_y
        self.redraw() 
    def on_button1_press(self, event):
        """开始拖动"""
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.leftdragging = True
    def on_button2_press(self, event):
        self.reset_view()
        self.redraw()
    def on_button3_press(self, event):
        """右键点击事件"""
             

        self.tree.selection_clear()
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y      
        self.rightdragging = True
        img_x, img_y = self.WindowPos2ImagePos(event.x, event.y)
        if not self.ctrl:
            if self.selectobject is not None:
                self.selectobject.isselected = False
                self.selectobject.isfilled = False
                self.selectobject.update_vertices()
                self.selectobject = None
                self.tree.selection_remove(self.tree.selection())
            res = False
            for rect in self.imagecoord.list_shapes():
                rect.operationcode=0
                rect.check(img_x-self.img_width/2, img_y-self.img_height/2)
                if rect.operationcode !=0:
                    self.selectobject = rect
                    self.selectobject.update_vertices()
                    self.tree.selection_set(id(self.selectobject))  # 选中树形视图中的对象
                    res = True
                else:
                    rect.isselected = False
                    rect.isfilled = False
                    rect.update_vertices()
            if not res:
                self.selectrect.width=0
                self.selectrect.height=0
                newx,newy = self.WindowPos2ImagePos(event.x,event.y)
                self.selectrect.x = newx - self.img_width/2
                self.selectrect.y = newy - self.img_height/2
                self.selectrect.update_vertices()
                self.isDrawingSelectionRect = True         
        else:
            for rect in self.imagecoord.list_shapes():
                rect.check(img_x-self.img_width/2, img_y-self.img_height/2)
                index =id(rect)
                selections = self.tree.selection()
                if rect.operationcode !=0:                  
                    if  str(index) not in selections:
                        self.tree.selection_add(index)
                    else:
                        self.tree.selection_remove(id(rect))
                        rect.isselected = False
                        rect.isfilled = False
                else:
                    if  str(index) in selections:
                        rect.isselected = True
                        rect.isfilled = True
                rect.update_vertices()
        self.redraw()
    def on_leftmouse_drag(self, event):
        """处理拖动"""
        if self.leftdragging:
            dx = event.x - self.last_mouse_x
            dy = event.y - self.last_mouse_y
            self.offset_x += dx
            self.offset_y += dy
            self.last_mouse_x = event.x
            self.last_mouse_y = event.y
            self.redraw()
    def on_mouseleftdouble_click(self, event):
        if  self.selectobject is not None:
            if isinstance(self.selectobject,ImgGL_Shape):
                self.selectobject.show_settings( event.x_root,event.y_root,self.redraw,self.update_tree_names)
    def on_rightmouse_drag(self,event):
        realdelay=  time.time() - self.last_drag_time
        if realdelay > self.drag_interval:
            self.on_delayrightmouse_drag(event)
            self.last_drag_time = time.time()
    def on_delayrightmouse_drag(self, event):
        """处理右键拖动"""
        # 画选择框
        if self.rightdragging and self.isDrawingSelectionRect:
            ax,ay = self.WindowPos2ImagePos(self.last_mouse_x, self.last_mouse_y)
            bx,by = self.WindowPos2ImagePos(event.x, event.y)
            x1 = ax - self.img_width / 2
            y1 = ay - self.img_height / 2
            x2 = bx - self.img_width / 2
            y2 = by - self.img_height / 2
            
            
            self.selectrect.width = abs(x2 - x1)
            self.selectrect.height = abs(y2 - y1)
            self.selectrect.x = (x1 + x2) / 2
            self.selectrect.y = (y1 + y2) / 2
            for rect in self.imagecoord.list_shapes():
                if (rect.x <= x2 and rect.x >= x1 and rect.y <= y2 and rect.y >= y1) or (rect.x <=x2 and rect.x >= x1 and rect.y >=y2 and rect.y <= y1) or (rect.x >= x2 and rect.x <= x1 and rect.y <= y2 and rect.y >= y1) or (rect.x >= x2 and rect.x <= x1 and rect.y >= y2 and rect.y <= y1):
                    rect.isselected = True
                    rect.isfilled = True
                    rect.update_vertices()
                    if id(rect) not in self.tree.selection():
                        self.tree.selection_add(id(rect))
                else:
                    for item in self.tree.selection():
                        if item == str(id(rect)):
                            rect.isfilled = False
                            rect.isselected = False
                            rect.update_vertices()
                            self.tree.selection_remove(item)
            self.selectrect.update_vertices()
            self.redraw()       
            return 
        img_x, img_y = self.WindowPos2ImagePos(event.x, event.y)    
        x = img_x - self.img_width / 2
        y = img_y - self.img_height / 2            
        lastimg_x = self.WindowPos2ImagePos(self.last_mouse_x, self.last_mouse_y)[0] - self.img_width / 2
        lastimg_y = self.WindowPos2ImagePos(self.last_mouse_x, self.last_mouse_y)[1] - self.img_height / 2
        offsetx = (event.x - self.last_mouse_x) / self.scale
        offsety = (event.y - self.last_mouse_y) / self.scale
        if self.selectobject is None or isinstance(self.selectobject, ImgGL_SegmentLine):
            angleossfet = 0
        else:
            angleossfet = self.selectobject.get_anglevector(self.selectobject.x, self.selectobject.y, lastimg_x, lastimg_y) - self.selectobject.get_anglevector(self.selectobject.x, self.selectobject.y, x, y)
        # 移动多个选中对象
        if self.rightdragging and len(self.selectobjects) > 1 and self.ctrl:
            for rect in self.selectobjects:
                rect.operationcode = 1
                rect.when_drag_transform(x,y,offsetx,offsety,0)
                rect.operationcode = 0
            self.redraw()
            return
        # 移动或变换选中对象
        if self.rightdragging and self.selectobject is not None and not self.ctrl:
            self.selectobject.when_drag_transform(x,y,offsetx,offsety,angleossfet)
            self.redraw()      
    def update_tree_names(self,ids):
        """同步rects中的name到treeview的text"""
        rectids = [str(id(rect)) for rect in self.imagecoord.list_shapes()]
        allitems = self.graphicstreeframe.list_all_items()
        for item in allitems:
            if item == str(ids) or (self.extract_number(item) is not None and self.extract_number(item) == str(ids)):
                if item.isdigit():
                    rect = self.imagecoord.list_shapes()[rectids.index(item)]
                    self.tree.item(item, text=rect.name)
                else:
                    number = self.extract_number(item)
                    rect = self.imagecoord.list_shapes()[rectids.index(number)]
                    self.tree.item(item, text=rect.name)
    def on_key_press(self, event):
        """处理键盘按下事件"""
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self.ctrl = True
        if event.keysym == 'Shift_L' or event.keysym == 'Shift_R':
            self.shift = True
        if event.state & 0x0004 and event.keysym == 'c':
            """Ctrl+C 复制当前标签内容到剪切板"""
            if self.selectobject is not None:
                self.copybuffer = self.selectobject
        if event.state & 0x0004 and event.keysym == 'v':
            """Ctrl+V 粘贴剪切板内容"""
            if self.copybuffer is not None:
                new_shape = copy.deepcopy(self.copybuffer)
                new_shape.x = self.curent_img_x - self.img_width / 2
                new_shape.y = self.curent_img_y - self.img_height / 2
                xoffset = self.copybuffer.x - new_shape.x
                yoffset = self.copybuffer.y - new_shape.y
                if len(new_shape.points) > 0:
                    for point in new_shape.points:
                        point[0] -= xoffset
                        point[1] -= yoffset
                new_shape.update_vertices()
                new_shape.name += "_copy"
                new_shape.parent = self.imagecoord
                self.imagecoord.shapes.append(new_shape)
                self.tree.insert(id(self.imagecoord), 'end',id(new_shape), text=new_shape.name)
                self.redraw()
        if event.keysym == 'Delete':
            """删除选中对象"""
            if self.selectobject is self.imagecoord:
                return
            if self.selectobjects is not None and len(self.selectobjects) > 0:
                allitems = self.graphicstreeframe.list_all_items()
                for rect in self.selectobjects:
                    if rect is self.imagecoord:
                        continue
                    rect.parent.shapes.remove(rect)
                    [self.tree.delete(item) for item in allitems if item == str(id(rect)) or (self.extract_number(item) is not None and self.extract_number(item) == str(id(rect)))]
                
                self.selectobjects.clear()
                self.redraw()
    def on_key_release(self, event):
        """处理键盘释放事件"""
        if event.keysym == 'Control_L' or event.keysym == 'Control_R':
            self.ctrl = False
        if event.keysym == 'Shift_L' or event.keysym == 'Shift_R':
            self.shift = False
    def reset_view(self):
        if self.width / self.height > 1:
            self.scale = self.height / self.img_height
            self.offset_x = 0
            self.offset_y = 0
            self.curent_img_x =0
            self.curent_img_y =0
            self.current_mouse_x =0
            self.current_mouse_y =0
        else:
            self.scale = self.width / self.img_width
            self.offset_x = 0
            self.offset_y = 0
            self.curent_img_x =0
            self.curent_img_y =0
            self.current_mouse_x =0
            self.current_mouse_y =0
        self.redraw()
    def on_leftbutton_release(self, event):
        """结束左键拖动"""
        self.leftdragging = False
    def on_rightbutton_release(self, event):
        """结束右键点击"""
        self.rightdragging = False
        self.isDrawingSelectionRect = False
        self.last_mouse_x = event.x
        self.last_mouse_y = event.y
        self.redraw()
    def extract_number(self,s):
        # 判断字符串是否包含 '_Link'
        if '_Link' in s:
            # 找到 '_Link' 的位置
            index = s.index('_Link')
            # 提取 '_Link' 前的部分
            number_part = s[:index]
            if number_part.isdigit():
                return number_part
            else:
                return None
        else:
            if s.isdigit():
                return s
        return None
    def ImagePos2WindowPos(self, x, y):
        """将图片坐标转换为窗口坐标"""
        window_x = (x - self.img_width/2)*self.scale + self.offset_x + self.width/2
        window_y = (y - self.img_height/2)*self.scale + self.offset_y + self.height/2
        return window_x, window_y
    def WindowPos2ImagePos(self, x, y):
        """将窗口坐标转换为图片坐标"""
        image_x = (x-self.width/2 - self.offset_x) / self.scale+self.img_width/2
        image_y = (y-self.height/2 - self.offset_y) / self.scale+self.img_height/2
        return image_x, image_y
    def WindowPos2GLPos(self, x, y):
        """将窗口坐标转换为OpenGL坐标"""
        gl_x = (x - self.width / 2 - self.offset_x) / self.scale
        gl_y = (y - self.height / 2 - self.offset_y) / self.scale
        return gl_x, gl_y
class Graphics_Tree(tk.Frame):
    def __init__(self, master:ImgGLFrame, **kwargs):
        super().__init__(master, **kwargs)        
        self.master = master
        self.tree = ttk.Treeview(self,height=10,show='tree headings',selectmode='browse')
        self.tree.heading('#0', text='GraphicsTree', anchor='w')
        self.tree.pack(expand=True, fill='both')
        self.tree.bind("<<TreeviewSelect>>",lambda event: self.on_tree_select(event))  # 绑定单击事件
        self.tree.bind("<KeyPress>", lambda event: self.on_key_press(event))  # 绑定键盘事件
    def on_key_press(self, event):
        """处理键盘按下事件"""
        if event.state & 0x0004 and event.keysym == 'c':
            """Ctrl+C 复制当前标签内容到剪切板"""
            if self.tree.selection() is not None:
                self.copybuffer = self.tree.selection()
        if event.state & 0x0004 and event.keysym == 'v':
            """Ctrl+V 粘贴剪切板内容"""
            if self.copybuffer is not None:
                nowitems =  self.tree.selection()
                shape_id = self.master.extract_number(nowitems[0])
                shapes = self.master.imagecoord.list_shapes()
                shape = next((item for item in shapes if str(id(item)) == shape_id), None)
                if shape is None or not isinstance(shape,ImgGL_Coordinate):
                    return
                else:
                    for item in self.copybuffer:
                        try:
                            copyshape_id = self.master.extract_number(item)
                            copyshape = next((item for item in shapes if str(id(item)) == copyshape_id), None)
                            if copyshape is None:
                                continue
                            else:
                                self.tree.delete(item)
                                copyshape.parent.shapes.remove(copyshape)
                                copyshape.parent = shape
                                shape.shapes.append(copyshape)
                                #self.tree.insert(nowitems[0], "end", copy_item, text=copyshape.name)
                                def update(root,ashape):
                                    self.tree.insert(root, "end",str(id(ashape)), text=ashape.name)
                                    if isinstance(ashape, ImgGL_Coordinate) and len(ashape.shapes) > 0:
                                        for subshape in ashape.shapes:
                                            subshape.parent = ashape
                                            update(id(ashape),subshape)
                                update(nowitems[0],copyshape)
                            
                        except Exception as e:
                            messagebox.showerror("Error", f"Failed to paste: {e}")
        if event.keysym == 'Delete':
            """删除选中对象"""
            self.on_delete()
        pass
    def on_delete(self):
        items = self.tree.selection()
        shapes = self.master.imagecoord.list_shapes()
        for item in items:
            item_parent = self.tree.parent(item)
            parent_shape_id = self.master.extract_number(item_parent)
            if parent_shape_id is None:
                continue
            parent_shape = next((s for s in shapes if str(id(s)) == parent_shape_id), None)        
            shape_id = self.master.extract_number(item)
            shape = next((s for s in shapes if str(id(s)) == shape_id), None)
            if shape is not None and shape is not self.master.imagecoord:
                parent_shape.shapes.remove(shape)
                self.tree.delete(item)
    def on_tree_select(self, event):
        """处理树形视图选择事件"""
        selected_items=self.tree.selection()
        self.master.selectobjects.clear()
        if selected_items is None or len(selected_items) == 0:
            return
        shapes = self.master.imagecoord.list_shapes()
        for rect in shapes:
            rect.isselected = False
            rect.isfilled = False
            rect.update_vertices()
        for item in selected_items:
            rectids =[str(id(rect)) for rect in shapes]
            if item in rectids or self.master.extract_number(item) is not None:
                if item.isdigit():
                    rect = shapes[rectids.index(item)]
                else:
                    number = self.master.extract_number(item)
                    rect = shapes[rectids.index(number)]
                rect.isselected = True
                rect.isfilled = True
                rect.update_vertices()
                self.master.selectobjects.append(rect)
        self.master.redraw()
    def list_all_items(self,parent=""):
        # 获取指定父节点下的所有子项
        children = self.tree.get_children(parent)
        items = []
        for child in children:
            # 获取项的文本
            items.append(child)
            # 递归获取子项
            items.extend(self.list_all_items(child))
        return items            
class ImgGL_Shape():
    def __init__(self,name,x,y,angle,color=[0.7, 0.7, 0.7, 1.0]):
        self.parent = None
        self.x = x
        self.y = y
        self.points = []  # 顶点列表
        self.beforepoints = []  # 变换前的顶点列表
        self.optpoint= -1  # 当前操作的顶点索引
        self.angle = angle
        self.beforeangle = angle
        self.beforex = x
        self.beforey = y
        self.width = 0
        self.height = 0
        self.name = name
        self.color = color
        self.selectcolor = [0.7, 0.7, 0.7, 0.5]  # 选中时的颜色
        self.isselected = False
        self.isfilled = False
        self.isupdating =False
        self.linewidth = 1.0
        self.selectdistance = 10
        self.indices = None
        self.operationcode = 0 # 0: none, 1: move
        self.font_size=10
        self.font= self.get_cross_platform_font(self.font_size,path="C:\\Windows\\Fonts\\msyh.ttc")
        self.isdrawtext = True
    def to_dict(self):
        """将形状转换为字典格式"""
        return {
            'name': self.name,
            'x': self.x,
            'y': self.y,
            'color': self.color,
            'selectcolor': self.selectcolor,
            'isselected': self.isselected,
            'isfilled': self.isfilled,
            'linewidth': self.linewidth,
            'selectdistance': self.selectdistance,
            'operationcode': self.operationcode,
            'font_size': self.font_size,
            'font_path': self.font.path if hasattr(self.font, 'path') else None
        }
    def __json__(self):
        return self.to_dict()
    def __deepcopy__(self, memo):
        raise NotImplementedError("Subclasses should implement this method")
    def show_settings(self):
        """显示形状参数设置窗口"""
        raise NotImplementedError("Subclasses should implement this method")
    def bind(self,method):
        """绑定相关形状更新方法,通过方法更新这个图形"""
        raise NotImplementedError("Subclasses should implement this method")
    def get_cross_platform_font(self,font_size,path=None):
        try:
            # 优先尝试系统指定字体
            return ImageFont.truetype(path, font_size)
        except Exception:
            # 失败时回退到Pillow的默认字体
            return ImageFont.load_default(font_size)
    def when_drag_transform(self):
        raise NotImplementedError("Subclasses should implement this method")
    def when_drag_rotating(self):
        raise NotImplementedError("Subclasses should implement this method")
    def draw(self):
        """绘制形状"""
        raise NotImplementedError("Subclasses should implement this method")
    def check(self,x,y):
        """选择判断"""
        raise NotImplementedError("Subclasses should implement this method")
    def extract_img(self,oriimg:np.ndarray):
        """从原图像中提取形状区域"""
        raise NotImplementedError("Subclasses should implement this method")
    def extract_pixel(self,extract_methold:int,oriimg:np.ndarray):
        """从原图像中提取形状像素"""
        raise NotImplementedError("Subclasses should implement this method")
    def update_vertices(self):
        """更新顶点数据"""
        raise NotImplementedError("Subclasses should implement this method")
    def rotate_point(self, x, y, x1, y1, theta_degrees):
        """
        计算点 (x, y) 绕中心点 (x1, y1) 旋转后的新坐标

        参数:
            x, y: 待旋转的点坐标
            x1, y1: 旋转中心
            theta_degrees: 旋转角度（度）

        返回:
            (x_new, y_new): 旋转后的坐标
        """
        theta = np.radians(theta_degrees)  # 角度转弧度
        cos_theta = np.cos(theta)
        sin_theta = np.sin(theta)

        # 平移至原点
        x_translated = x - x1
        y_translated = y - y1

        # 旋转矩阵乘法
        x_rotated = x_translated * cos_theta - y_translated * sin_theta
        y_rotated = x_translated * sin_theta + y_translated * cos_theta

        # 平移回原坐标系
        x_new = x_rotated + x1
        y_new = y_rotated + y1
        return x_new, y_new
    def get_anglevectors(self, v1,v2):
        """
        计算两个向量 v1 和 v2 的夹角
        返回值为角度，范围在 [0, 360)
        """
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        else:
            cos_angle = dot_product / (norm_v1 * norm_v2)
            return np.degrees(np.arccos(np.clip(cos_angle, -1.0, 1.0)))
    def get_anglevector(self, x1, y1, x2, y2):
        """
        计算从点 (x1, y1) 到点 (x2, y2) 的向量的角度
        返回值为角度，范围在 [0, 360)
        """
        dx = x2 - x1
        dy = y2 - y1
        return np.degrees(np.arctan2(dy, dx))
    def get_distancepoints(self,x1, y1, x2, y2):
        """
        计算两点之间的距离
        """
        return np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 )
    def get_distancepoint2lineABC(self,x0, y0, A, B, C):
        """
        计算点 (x0, y0) 到直线 Ax + By + C
        """
        numerator = abs(A * x0 + B * y0 + C)
        denominator = np.sqrt(A**2 + B**2)
        distance = numerator / denominator
        return distance
    def get_distancepoint2lineP1(self,x0, y0, x1, y1, angle):
        """
        计算点 (x0, y0) 到通过点 (x1, y1) 且与水平线成 angle 角的直线的距离
        """
        A = np.sin(np.radians(angle))
        B = -np.cos(np.radians(angle))
        C = -(A * x1 + B * y1)
        return ImgGL_Shape.get_distancepoint2lineABC(self,x0, y0, A, B, C)   
    def get_distancepoint2lineP1P2(self,x0, y0, x1, y1, x2, y2):
        """
        计算点 (x0, y0) 到线段 (x1, y1)-(x2, y2) 的距离
        """
        A = y2 - y1
        B = x1 - x2
        C = x2 * y1 - x1 * y2
        distance = ImgGL_Shape.get_distancepoint2lineABC(self,x0, y0, A, B, C)
        
        # 检查垂足是否在线段上
        dot_product1 = (x0 - x1) * (x2 - x1) + (y0 - y1) * (y2 - y1)
        dot_product2 = (x0 - x2) * (x1 - x2) + (y0 - y2) * (y1 - y2)
        
        if dot_product1 < 0:
            return np.sqrt((x0 - x1) ** 2 + (y0 - y1) ** 2)
        elif dot_product2 < 0:
            return np.sqrt((x0 - x2) ** 2 + (y0 - y2) ** 2)
        else:
            return distance
class ImgGL_Rectangle(ImgGL_Shape):
    def __init__(self, name, x, y, width, height,angle, color=[0.0, 0.0, 0.0, 1.0]):
        super().__init__(name,x, y, color)
        self.name = name
        self.width = width
        self.height = height
        self.angle = angle  # 旋转角度
        self.beforeangle = angle
        self.beforex = x
        self.beforey = y
        self.update_vertices()
    def when_drag_transform(self,x,y,dx,dy,angle):
        if self.operationcode == 1:  # 移动操作
            self.x = self.beforex + dx
            self.y = self.beforey + dy
            self.update_vertices() 
        elif self.operationcode == 2:
            self.height= self.get_distancepoint2lineP1(self.x, self.y, x, y, self.angle)*2
            self.update_vertices()
        elif self.operationcode == 3:
            self.width= self.get_distancepoint2lineP1(self.x, self.y, x, y, self.angle+90)*2
            self.update_vertices()
        elif self.operationcode == 4:
            self.angle = self.beforeangle - angle
            self.update_vertices()

    @classmethod
    def from_dict(cls, data):
        """从字典数据创建 ImgGL_Rectangle 实例"""
        name = data.get('name', 'Rectangle')
        x = data.get('x', 0.0)
        y = data.get('y', 0.0)
        width = data.get('width', 100.0)
        height = data.get('height', 100.0)
        angle = data.get('angle', 0.0)
        color = data.get('color', [0.0, 0.0, 0.0, 1.0])
        return cls(name, x, y, width, height, angle, color)
    def to_dict(self):
        return {
            'name': self.name,
            'class': 'ImgGL_Rectangle',
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'angle': self.angle,
            'color': self.color,
            'font_size': self.font_size
        }
    def extract_img(self, oriimg):
        """从原图像中提取形状区域"""
        x1,y1 = self.rotate_point(self.x - self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x + self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x + self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x - self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x1 = x1 + oriimg.shape[1] // 2
        y1 = y1 + oriimg.shape[0] // 2
        x2 = x2 + oriimg.shape[1] // 2
        y2 = y2 + oriimg.shape[0] // 2
        x3 = x3 + oriimg.shape[1] // 2
        y3 = y3 + oriimg.shape[0] // 2
        x4 = x4 + oriimg.shape[1] // 2
        y4 = y4 + oriimg.shape[0] // 2
        
        
        xmin = int(min(x1, x2, x3, x4))
        xmax = int(max(x1, x2, x3, x4))
        ymin = int(min(y1, y2, y3, y4))
        ymax = int(max(y1, y2, y3, y4))
        xmin = max(0, xmin)
        xmax = min(oriimg.shape[1], xmax)
        ymin = max(0, ymin)
        ymax = min(oriimg.shape[0], ymax)
        roi=copy.deepcopy(oriimg[ymin:ymax, xmin:xmax])  
        roi_mask = np.zeros_like(roi, dtype=np.uint8)     
        cv2.fillConvexPoly(roi_mask, np.array([[x1-xmin, y1-ymin], [x2-xmin, y2-ymin], [x3-xmin, y3-ymin], [x4-xmin, y4-ymin]], dtype=np.int32),255)
        if oriimg.ndim == 3 and oriimg.shape[2] == 3 and oriimg.dtype == np.uint8:
            roi[roi_mask==0] = 0
        elif oriimg.ndim == 3 and oriimg.shape[2] == 1 and oriimg.dtype == np.float32:
            roi[roi_mask==0] = np.nan
        elif oriimg.ndim == 2 and oriimg.dtype == np.uint8:
            roi[roi_mask==0] = 0
        elif oriimg.ndim == 2 and oriimg.dtype == np.float32:
            roi[roi_mask==0] = np.nan
        return roi
    def show_settings(self,x,y,glredraw,treeviewupdate):
        def choose_color():
            color = colorchooser.askcolor(color=(int(self.color[0]*255),int(self.color[1]*255),int(self.color[2]*255)), title='ColorChooser')[0]
            if color:
                self.color = [color[0]/255, color[1]/255, color[2]/255, 1.0]
                glredraw()  # 重绘图形以应用新颜色
        def save_settings():
            self.name = name_entry.get()
            self.font_size = int(font_size_entry.get())
            self.font = self.get_cross_platform_font(self.font_size,path="C:\\Windows\\Fonts\\msyh.ttc")
            self.angle = float(angle_entry.get())
            self.width = float(width_entry.get())
            self.height = float(height_entry.get())
            self.update_vertices()
            settings_window.destroy()
            glredraw()
            treeviewupdate(id(self))
        def on_xchanged():
            self.x = float(x_entry.get())
            self.update_vertices()
            glredraw()
        def on_ychanged():
            self.y = float(y_entry.get())
            self.update_vertices()
            glredraw()
        def on_anglechanged():
            self.angle = float(angle_entry.get())
            self.update_vertices()
            glredraw()
        def on_widthchanged():
            self.width = float(width_entry.get())
            self.update_vertices()
            glredraw()
        def on_heightchanged():
            self.height = float(height_entry.get())
            self.update_vertices()
            glredraw()
        """显示形状设置对话框"""
        settings_window = tk.Toplevel()
        settings_window.title(f"Settings for {self.name}")
        
        notebook = ttk.Notebook(settings_window)
        viewsettings_frame = tk.Frame(notebook)
        viewsettings_frame.pack(padx=10, pady=10)
        notebook.pack(fill='both', expand=True)
        notebook.add(viewsettings_frame, text='View')
        
        tk.Label(viewsettings_frame, text="Name:").grid(row=0, column=0)
        name_entry = tk.Entry(viewsettings_frame)
        name_entry.insert(0, self.name)
        name_entry.grid(row=0, column=1)
        
        tk.Label(viewsettings_frame, text="Color:").grid(row=1, column=0)
        color_button = tk.Button(viewsettings_frame, text="Choose Color", command=choose_color)
        color_button.grid(row=1, column=1)
        
        tk.Label(viewsettings_frame, text="Font Size:").grid(row=2,column=0)
        font_size_entry = tk.Entry(viewsettings_frame)
        font_size_entry.insert(0, self.font_size)
        font_size_entry.grid(row=2, column=1)
                     
        tk.Label(viewsettings_frame, text="Angle:").grid(row=3, column=0)
        angle_entry = tk.Entry(viewsettings_frame)
        angle_entry.insert(0, self.angle)
        angle_entry.grid(row=3, column=1)
        angle_entry.bind("<Return>", lambda event: on_anglechanged())  
        tk.Label(viewsettings_frame, text="Width:").grid(row=4, column=0)
        width_entry = tk.Entry(viewsettings_frame)
        width_entry.insert(0, self.width)
        width_entry.grid(row=4, column=1)
        width_entry.bind("<Return>", lambda event: on_widthchanged())
        tk.Label(viewsettings_frame, text="Height:").grid(row=5, column=0)
        height_entry = tk.Entry(viewsettings_frame)
        height_entry.insert(0, self.height)
        height_entry.grid(row=5, column=1)
        height_entry.bind("<Return>", lambda event: on_heightchanged())
        tk.Label(viewsettings_frame, text="X:").grid(row=6, column=0)
        x_entry = tk.Entry(viewsettings_frame)
        x_entry.insert(0, self.x)
        x_entry.grid(row=6, column=1)
        x_entry.bind("<Return>", lambda event: on_xchanged()) 
        tk.Label(viewsettings_frame, text="Y:").grid(row=7, column=0)
        y_entry = tk.Entry(viewsettings_frame)
        y_entry.insert(0, self.y)
        y_entry.grid(row=7, column=1)
        y_entry.bind("<Return>", lambda event: on_ychanged()) 
        
        tk.Button(viewsettings_frame, text="Save", command=save_settings).grid(row=8, column=0, columnspan=2,sticky="nsew")
        settings_window.geometry(f"+{x}+{y}")  # 设置大小
        settings_window.update_idletasks()  # 更新窗口的内容
        settings_window.attributes('-topmost', True)  # 窗口置顶
    def __deepcopy__(self,memo):
        """深拷贝方法"""
        new_shape = ImgGL_Rectangle(self.name, self.x, self.y, self.width, self.height, self.angle, self.color)
        new_shape.isselected = False
        new_shape.isfilled = False
        new_shape.selectcolor = self.selectcolor
        new_shape.linewidth = self.linewidth
        new_shape.selectdistance = self.selectdistance
        new_shape.font_size = self.font_size
        new_shape.font = self.font
        return new_shape
    def get_bounding_box(self):
        xmin,ymin,xmax,ymax= self.font.getbbox(self.name)
        w = xmax - xmin
        h = ymax - ymin
        x1,y1 = self.rotate_point(self.x - self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x - self.width / 2 + w, self.y - self.height / 2, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x - self.width / 2 + w, self.y - self.height / 2 + h, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x - self.width / 2, self.y - self.height / 2 +h, self.x, self.y, self.angle)
        return np.array([
            x1,y1,0.0,0,0,
            x2,y2,0.0,1,0,
            x3,y3,0.0,1,1,
            x4,y4,0.0,0,1
        ], dtype=np.float32)
    def update_vertices(self):
        self.indices_boundingbox = np.array([0,1,2,2,3,0], dtype=np.uint32)

        if self.width < 20 or self.height < 20:
            self.selectdistance = 2
            self.font_size = 5
        else:
            self.selectdistance = 10
            self.font_size = 10
        self.isupdating = True
        x1,y1 = self.rotate_point(self.x - self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x + self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x + self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x - self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        

        self.boundingbox = self.get_bounding_box()

        if self.isfilled:
            x5 = (x2 +x1)*0.5
            y5 = (y2 +y1)*0.5
            x6 = (x3 +x2)*0.5
            y6 = (y3 +y2)*0.5

            ax1,ay1 = self.rotate_point(x5 - self.selectdistance / 2, y5 - self.selectdistance / 2, x5,y5, self.angle)
            ax2,ay2 = self.rotate_point(x5 + self.selectdistance / 2, y5 - self.selectdistance / 2, x5,y5, self.angle)
            ax3,ay3 = self.rotate_point(x5 + self.selectdistance / 2, y5 + self.selectdistance / 2, x5,y5, self.angle)
            ax4,ay4 = self.rotate_point(x5 - self.selectdistance / 2, y5 + self.selectdistance / 2, x5,y5, self.angle)

            bx1,by1 = self.rotate_point(x6 - self.selectdistance / 2, y6 - self.selectdistance / 2, x6,y6, self.angle)
            bx2,by2 = self.rotate_point(x6 + self.selectdistance / 2, y6 - self.selectdistance / 2, x6,y6, self.angle)
            bx3,by3 = self.rotate_point(x6 + self.selectdistance / 2, y6 + self.selectdistance / 2, x6,y6, self.angle)
            bx4,by4 = self.rotate_point(x6 - self.selectdistance / 2, y6 + self.selectdistance / 2, x6,y6, self.angle)

            cx1,cy1 = self.rotate_point(x2 - self.selectdistance / 2, y2 - self.selectdistance / 2, x2,y2, self.angle)
            cx2,cy2 = self.rotate_point(x2 + self.selectdistance / 2, y2 - self.selectdistance / 2, x2,y2, self.angle)
            cx3,cy3 = self.rotate_point(x2 + self.selectdistance / 2, y2 + self.selectdistance / 2, x2,y2, self.angle)
            cx4,cy4 = self.rotate_point(x2 - self.selectdistance / 2, y2 + self.selectdistance / 2, x2,y2, self.angle)

            self.vertices = np.array([
                self.x,self.y, 0.0, self.selectcolor[0],self.selectcolor[1],self.selectcolor[2],self.selectcolor[3], 
                x1, y1, 0.0, self.selectcolor[0],self.selectcolor[1],self.selectcolor[2],self.selectcolor[3],
                x2, y2, 0.0, self.selectcolor[0],self.selectcolor[1],self.selectcolor[2],self.selectcolor[3], 
                x3, y3, 0.0, self.selectcolor[0],self.selectcolor[1],self.selectcolor[2],self.selectcolor[3],  
                x4, y4, 0.0, self.selectcolor[0],self.selectcolor[1],self.selectcolor[2],self.selectcolor[3],          
                x5, y5,   0.0, 1, 0, 0, 1,
                ax1, ay1, 0.0, 1, 0, 0, 1, 
                ax2, ay2, 0.0, 1, 0, 0, 1,
                ax3, ay3, 0.0, 1, 0, 0, 1, 
                ax4, ay4, 0.0, 1, 0, 0, 1, 
                x6, y6,   0.0, 1, 0, 1, 1, 
                bx1, by1, 0.0, 1, 0, 1, 1, 
                bx2, by2, 0.0, 1, 0, 1, 1, 
                bx3, by3, 0.0, 1, 0, 1, 1, 
                bx4, by4, 0.0, 1, 0, 1, 1,  
                x2,y2,    0.0, 1, 1, 1, 1,
                cx1, cy1, 0.0, 1, 1, 1, 1,
                cx2, cy2, 0.0, 1, 1, 1, 1, 
                cx3, cy3, 0.0, 1, 1, 1, 1,
                cx4, cy4, 0.0, 1, 1, 1, 1,  
            ], dtype=np.float32)
            self.indices = np.array([0,1,2,3,4,1,5,6,7,8,9,6,10,11,12,13,14,11,15,16,17,18,19,16], dtype=np.uint32)
        else:
            self.vertices = np.array([
                x1, y1, 0.0, self.color[0],self.color[1],self.color[2],self.color[3], # 左下角
                x2, y2, 0.0, self.color[0],self.color[1],self.color[2],self.color[3],  # 右下角
                x3, y3, 0.0, self.color[0],self.color[1],self.color[2],self.color[3],  # 右上角
                x4, y4, 0.0, self.color[0],self.color[1],self.color[2],self.color[3],   # 左上角
            ], dtype=np.float32)
            self.indices = np.array([0,1,1,2,2,3,3,0], dtype=np.uint32)

        self.isupdating = False
    def draw(self,glframe):
        if self.isupdating:
            return
        glUseProgram(glframe.rect_shader)
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "projection"),
                       1, GL_TRUE, np.array((glframe.ortho_matrix(-glframe.width/2, glframe.width/2,glframe.height/2, -glframe.height/2, -1, 1))))
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "model"),
                       1, GL_TRUE, np.array(glframe.model_matrix(glframe.offset_x,glframe.offset_y,glframe.rotation_angle,glframe.scale)))  # 单位矩阵
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "view"),
                       1, GL_TRUE, np.array(glframe.view_matrix()))
        vao=glGenVertexArrays(1)
        vbo=glGenBuffers(1)
        ebo=glGenBuffers(1)
        texture_id=glGenBuffers(1)
        glBindVertexArray(vao)  # 创建新的VAO
        glBindBuffer(GL_ARRAY_BUFFER, vbo)  # 绑定VBO
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)  # 绑定EBO
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        """绘制矩形"""
        if self.isfilled:
            for i in range(0, len(self.indices), 6):
                glDrawElements(GL_TRIANGLE_FAN, 6, GL_UNSIGNED_INT, ctypes.c_void_p(i * sizeof(GLuint)))
        else:
            glDrawElements(GL_LINES, len(self.indices), GL_UNSIGNED_INT, None)        
        
        glUseProgram(glframe.shader)  # 使用着色器程序
        glBindVertexArray(vao)
        textureType = TextureFormat.Color          
        glUniform1i(glGetUniformLocation(glframe.shader, "texturetype"), textureType.value)  # 设置纹理类型
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "projection"),
                           1, GL_TRUE, np.array((glframe.ortho_matrix(-glframe.width/2, glframe.width/2,glframe.height/2, -glframe.height/2, -1, 1))))
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "model"),
                           1, GL_TRUE, np.array(glframe.model_matrix(glframe.offset_x,glframe.offset_y,glframe.rotation_angle,glframe.scale)))  # 单位矩阵
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "view"),
                           1, GL_TRUE, np.array(glframe.view_matrix()))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)  # 绑定VBO
        glBufferData(GL_ARRAY_BUFFER, self.boundingbox.nbytes, self.boundingbox, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)  # 绑定EBO
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices_boundingbox.nbytes, self.indices_boundingbox, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glUniform1i(glGetUniformLocation(glframe.shader, "textureSampler"), 0)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)  # 边缘处理
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        bbox = self.font.getbbox(self.name)
        pil_image = Image.new("RGBA", (int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])), (int(self.color[0])*255,int(self.color[1])*255,int(self.color[2])*255,int(self.color[3])*255))
        textdraw = ImageDraw.Draw(pil_image)
        textdraw.text((0,- bbox[1]), self.name, font=self.font, fill=(255,255,255,255))
        textimage = np.array(pil_image)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, textimage.shape[1], textimage.shape[0], 
             0, GL_RGBA, GL_UNSIGNED_BYTE, textimage)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindTexture(GL_TEXTURE_2D, 0)  # 禁用纹理
        glBindVertexArray(0)    
        glDeleteVertexArrays(1, [vao])  # 删除VAO以释放资源 
        glDeleteBuffers(1, [vbo])  # 删除VBO以释放资源
        glDeleteBuffers(1, [ebo])  # 删除EBO以释放资源      
        glDeleteBuffers(1, [texture_id])  # 删除纹理ID以释放资源      
    def check(self, x, y):
        """检查鼠标是否在矩形内"""
        x1,y1 = self.rotate_point(self.x - self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x + self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x + self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x - self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x5 = (x2 +x1)*0.5
        y5 = (y2 +y1)*0.5
        x6 = (x3 +x2)*0.5
        y6 = (y3 +y2)*0.5
        res =  cv2.pointPolygonTest(np.array([[x1,y1],[x2,y2],[x3,y3],[x4,y4]],dtype=np.float32),(x,y),False)
        if res >=0:
            self.operationcode = 1
            self.isselected = True
            self.isfilled = True
            self.beforex = self.x
            self.beforey = self.y
            self.beforeangle = self.angle
        else:
            self.beforex = self.x
            self.beforey = self.y
            self.beforeangle = self.angle
            if self.get_distancepoints(x, y, x5, y5)<self.selectdistance:
                self.operationcode = 2
                self.isselected = True
                self.isfilled = True
            elif self.get_distancepoints(x, y, x6, y6)<self.selectdistance:
                self.operationcode = 3
                self.isselected = True
                self.isfilled = True
            elif self.get_distancepoints(x, y, x2, y2)<self.selectdistance:
                self.operationcode = 4
                self.isselected = True
                self.isfilled = True
            else:
                self.operationcode = 0
                self.isselected = False
                self.isfilled = False
class ImgGL_Coordinate(ImgGL_Shape):
    def __init__(self, name, x, y, width, height, angle, color=[0.0, 0.0, 0.0, 1.0]):
        super().__init__(name, x, y, angle, color)
        self.name = name
        self.width = width
        self.height = height
        self.beforeangle = angle
        self.beforex = x
        self.beforey = y
        self.shapes = []
        xmin,ymin,xmax,ymax= self.font.getbbox(self.name)
        self.fw = xmax - xmin
        self.fh = ymax - ymin
        self.update_vertices()
    def list_shapes(self):
        """
        递归列出所有子形状（包括自身的所有嵌套 ImgGL_Coordinate）
        """
        def list_all_shapes(shape_list):
            shapes = []
            for shape in shape_list:
                shapes.append(shape)
                if isinstance(shape, ImgGL_Coordinate):
                    shapes.extend(list_all_shapes(shape.shapes))
            return shapes
        shapes = list_all_shapes(self.shapes)
        shapes.insert(0,self)
        return shapes
    def when_drag_transform(self,x,y,dx,dy,angle):
        if self.operationcode == 1:  # 移动操作
            self.x = self.beforex + dx
            self.y = self.beforey + dy
            self.update_vertices() 
            for shape in self.list_shapes()[1:]:  # 排除自身
                shape.operationcode = 1
                shape.when_drag_transform(x,y,dx,dy,0)
                shape.operationcode = 0
        elif self.operationcode == 4:
            self.angle = self.beforeangle - angle
            self.update_vertices()
            for shape in self.list_shapes()[1:]:  # 排除自身 
                newx,newy= self.rotate_point(shape.beforex, shape.beforey, self.x, self.y, -angle)
                shape.x = newx
                shape.y = newy
                for idx,point in enumerate(shape.beforepoints):
                    shape.points[idx][0],shape.points[idx][1]= self.rotate_point(point[0], point[1], self.x, self.y, -angle)
                shape.update_vertices()
    def show_settings(self,x,y,glredraw,treeviewupdate):
        def choose_color():
            color = colorchooser.askcolor(color=(int(self.color[0]*255),int(self.color[1]*255),int(self.color[2]*255)), title='ColorChooser')[0]
            if color:
                self.color = [color[0]/255, color[1]/255, color[2]/255, 1.0]
                glredraw()  # 重绘图形以应用新颜色
        def save_settings():
            self.name = name_entry.get()
            self.font_size = int(font_size_entry.get())
            self.font = self.get_cross_platform_font(self.font_size,path="C:\\Windows\\Fonts\\msyh.ttc")
            xmin,ymin,xmax,ymax= self.font.getbbox(self.name)
            self.fw = xmax - xmin
            self.fh = ymax - ymin
            self.angle = float(angle_entry.get())
            self.width = float(width_entry.get())
            self.height = float(height_entry.get())
            self.update_vertices()
            settings_window.destroy()
            glredraw()
            treeviewupdate(id(self))
        def on_xchanged():          
            nowx = float(x_entry.get())
            dx = nowx - self.x
            self.x = float(x_entry.get())
            self.update_vertices()
            for shape in self.list_shapes():
                shape.operationcode = 1
                shape.when_drag_transform(x,y,dx,0,0)
                shape.operationcode = 0
            glredraw()
        def on_ychanged():
            nowy = float(y_entry.get())
            dy = nowy - self.y
            self.y = float(y_entry.get())
            self.update_vertices()
            for shape in self.list_shapes():
                shape.operationcode = 1
                shape.when_drag_transform(x,y,0,dy,0)
                shape.operationcode = 0
            glredraw()
        def on_anglechanged():
            nowangle = float(angle_entry.get())
            angle = nowangle - self.angle
            self.angle = float(angle_entry.get())
            self.update_vertices()
            for shape in self.list_shapes():    
                newx,newy= self.rotate_point(shape.x, shape.y, self.x, self.y, angle)
                shape.x = newx
                shape.y = newy
                for idx,point in enumerate(shape.points):
                    shape.points[idx][0],shape.points[idx][1]= self.rotate_point(point[0], point[1], self.x, self.y, angle)
                shape.update_vertices()
            glredraw()
        def on_widthchanged():
            self.width = float(width_entry.get())
            self.update_vertices()
            glredraw()
        def on_heightchanged():
            self.height = float(height_entry.get())
            self.update_vertices()
            glredraw()
        """显示形状设置对话框"""
        settings_window = tk.Toplevel()
        settings_window.title(f"Settings for {self.name}")
        
        notebook = ttk.Notebook(settings_window)
        viewsettings_frame = tk.Frame(notebook)
        viewsettings_frame.pack(padx=10, pady=10)
        notebook.pack(fill='both', expand=True)
        notebook.add(viewsettings_frame, text='View')
        
        tk.Label(viewsettings_frame, text="Name:").grid(row=0, column=0)
        name_entry = tk.Entry(viewsettings_frame)
        name_entry.insert(0, self.name)
        name_entry.grid(row=0, column=1)
        
        tk.Label(viewsettings_frame, text="Color:").grid(row=1, column=0)
        color_button = tk.Button(viewsettings_frame, text="Choose Color", command=choose_color)
        color_button.grid(row=1, column=1)
        
        tk.Label(viewsettings_frame, text="Font Size:").grid(row=2,column=0)
        font_size_entry = tk.Entry(viewsettings_frame)
        font_size_entry.insert(0, self.font_size)
        font_size_entry.grid(row=2, column=1)
                     
        tk.Label(viewsettings_frame, text="Angle:").grid(row=3, column=0)
        angle_entry = tk.Entry(viewsettings_frame)
        angle_entry.insert(0, self.angle)
        angle_entry.grid(row=3, column=1)
        angle_entry.bind("<Return>", lambda event: on_anglechanged())  
        tk.Label(viewsettings_frame, text="Width:").grid(row=4, column=0)
        width_entry = tk.Entry(viewsettings_frame)
        width_entry.insert(0, self.width)
        width_entry.grid(row=4, column=1)
        width_entry.bind("<Return>", lambda event: on_widthchanged())
        tk.Label(viewsettings_frame, text="Height:").grid(row=5, column=0)
        height_entry = tk.Entry(viewsettings_frame)
        height_entry.insert(0, self.height)
        height_entry.grid(row=5, column=1)
        height_entry.bind("<Return>", lambda event: on_heightchanged())
        tk.Label(viewsettings_frame, text="X:").grid(row=6, column=0)
        x_entry = tk.Entry(viewsettings_frame)
        x_entry.insert(0, self.x)
        x_entry.grid(row=6, column=1)
        x_entry.bind("<Return>", lambda event: on_xchanged()) 
        tk.Label(viewsettings_frame, text="Y:").grid(row=7, column=0)
        y_entry = tk.Entry(viewsettings_frame)
        y_entry.insert(0, self.y)
        y_entry.grid(row=7, column=1)
        y_entry.bind("<Return>", lambda event: on_ychanged()) 
        
        tk.Button(viewsettings_frame, text="Save", command=save_settings).grid(row=8, column=0, columnspan=2,sticky="nsew")
        settings_window.geometry(f"+{x}+{y}")  # 设置大小
        settings_window.update_idletasks()  # 更新窗口的内容
        settings_window.attributes('-topmost', True)  # 窗口置顶
    @classmethod
    def from_dict(cls, data):
        """从字典数据创建 ImgGL_Coordinate 实例"""
        name = data.get('name', 'Coordinate')
        x = data.get('x', 0.0)
        y = data.get('y', 0.0)
        width = data.get('width', 100.0)
        height = data.get('height', 100.0)
        angle = data.get('angle', 0.0)
        color = data.get('color', [0.0, 0.0, 0.0, 1.0])
        return cls(name, x, y, width, height, angle, color)
    def to_dict(self):
        return {
            'name': self.name,
            'class': 'ImgGL_Coordinate',
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'angle': self.angle,
            'color': self.color,
            'font_size': self.font_size
        }
    def __deepcopy__(self, memo):
        newshape = ImgGL_Coordinate(self.name, self.x, self.y, self.width, self.height, self.angle, self.color)
        newshape.isselected = False
        newshape.isfilled = False
        newshape.selectcolor = self.selectcolor
        newshape.linewidth = self.linewidth
        newshape.selectdistance = self.selectdistance
        newshape.font_size = self.font_size
        newshape.font = self.font
        newshape.shapes = [copy.deepcopy(shape, memo) for shape in self.shapes]
        return newshape
    def update_vertices(self):
        self.indices_boundingbox = np.array([0,1,2,2,3,0], dtype=np.uint32)
        self.boundingbox = self.get_bounding_box()

        self.isupdating = True
        x1,y1 = self.rotate_point(self.x - self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x + self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x + self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x - self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)

        x5 = (x3 +x4)*0.5
        y5 = (y3 +y4)*0.5
        x6 = (x3 +x2)*0.5
        y6 = (y3 +y2)*0.5

        self.vertices = np.array([
            self.x,self.y,0.0,  0, 0, 1, 1, 
            x5, y5, 0.0,        0, 0, 1, 1,
            self.x,self.y,0.0,  1, 0, 0, 1,
            x6, y6, 0.0,        1, 0, 0, 1,
            ], dtype=np.float32)

        self.indices = np.array([0,1,2,3], dtype=np.uint32)
        self.isupdating = False
    def draw(self,glframe):
        if self.isupdating:
            return
        glLineWidth(self.selectdistance/2)
        if self.isfilled:
           glEnable(GL_LINE_STIPPLE)
           glLineStipple(1, 0x00FF)  # 1: 线条重复次数, 0x00FF: 虚线模式
        else:
            glDisable(GL_LINE_STIPPLE)
        glUseProgram(glframe.rect_shader)
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "projection"),
                       1, GL_TRUE, np.array((glframe.ortho_matrix(-glframe.width/2, glframe.width/2,glframe.height/2, -glframe.height/2, -1, 1))))
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "model"),
                       1, GL_TRUE, np.array(glframe.model_matrix(glframe.offset_x,glframe.offset_y,glframe.rotation_angle,glframe.scale)))  # 单位矩阵
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "view"),
                       1, GL_TRUE, np.array(glframe.view_matrix()))
        vao=glGenVertexArrays(1)
        vbo=glGenBuffers(1)
        ebo=glGenBuffers(1)
        texture_id=glGenBuffers(1)
        glBindVertexArray(vao)  # 创建新的VAO
        glBindBuffer(GL_ARRAY_BUFFER, vbo)  # 绑定VBO
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)  # 绑定EBO
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        """绘制线段"""
        glDrawElements(GL_LINES, len(self.indices), GL_UNSIGNED_INT, None)         
        glUseProgram(glframe.shader)  # 使用着色器程序
        glBindVertexArray(vao)
        textureType = TextureFormat.Color          
        glUniform1i(glGetUniformLocation(glframe.shader, "texturetype"), textureType.value)  # 设置纹理类型
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "projection"),
                           1, GL_TRUE, np.array((glframe.ortho_matrix(-glframe.width/2, glframe.width/2,glframe.height/2, -glframe.height/2, -1, 1))))
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "model"),
                           1, GL_TRUE, np.array(glframe.model_matrix(glframe.offset_x,glframe.offset_y,glframe.rotation_angle,glframe.scale)))  # 单位矩阵
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "view"),
                           1, GL_TRUE, np.array(glframe.view_matrix()))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)  # 绑定VBO
        glBufferData(GL_ARRAY_BUFFER, self.boundingbox.nbytes, self.boundingbox, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)  # 绑定EBO
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices_boundingbox.nbytes, self.indices_boundingbox, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glUniform1i(glGetUniformLocation(glframe.shader, "textureSampler"), 0)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)  # 边缘处理
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        bbox = self.font.getbbox(self.name)
        pil_image = Image.new("RGBA", (int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])), (int(self.color[0])*255,int(self.color[1])*255,int(self.color[2])*255,int(self.color[3])*255))
        textdraw = ImageDraw.Draw(pil_image)
        textdraw.text((0,- bbox[1]), self.name, font=self.font, fill=(255,255,255,255))
        textimage = np.array(pil_image)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, textimage.shape[1], textimage.shape[0], 
             0, GL_RGBA, GL_UNSIGNED_BYTE, textimage)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindTexture(GL_TEXTURE_2D, 0)  # 禁用纹理
        glBindVertexArray(0)    
        glDeleteVertexArrays(1, [vao])  # 删除VAO以释放资源 
        glDeleteBuffers(1, [vbo])  # 删除VBO以释放资源
        glDeleteBuffers(1, [ebo])  # 删除EBO以释放资源      
        glDeleteBuffers(1, [texture_id])  # 删除纹理ID以释放资源  
        glLineWidth(2.0)  
        glDisable(GL_LINE_STIPPLE)
        def drawchildren(shape):
            shape.draw(glframe)
            if isinstance(shape, ImgGL_Coordinate):
                for child in shape.shapes:
                    drawchildren(child)
        [drawchildren(shape) for shape in self.shapes]
    def get_bounding_box(self):
        x1,y1 = self.rotate_point(self.x,     self.y, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x + self.fw, self.y, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x + self.fw, self.y + self.fh, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x,     self.y + self.fh, self.x, self.y, self.angle)
        return np.array([
            x1,y1,0.0,0,0,
            x2,y2,0.0,1,0,
            x3,y3,0.0,1,1,
            x4,y4,0.0,0,1
        ], dtype=np.float32)  
    def check(self, x, y):
        """检查鼠标是否在矩形内"""
        x1,y1 = self.rotate_point(self.x - self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x + self.width / 2, self.y - self.height / 2, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x + self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x - self.width / 2, self.y + self.height / 2, self.x, self.y, self.angle)
        x5 = (x3 + x4)*0.5
        y5 = (y3 + y4)*0.5
        x6 = (x3 + x2)*0.5
        y6 = (y3 + y2)*0.5
        res =  cv2.pointPolygonTest(np.array([
            [self.x+self.selectdistance,self.y+self.selectdistance],
            [self.x+self.selectdistance,self.y-self.selectdistance],
            [self.x-self.selectdistance,self.y-self.selectdistance],
            [self.x-self.selectdistance,self.y+self.selectdistance],
            ],dtype=np.float32),(x,y),False)
        if res >=0:
            self.operationcode = 1
            self.isselected = True
            self.isfilled = True
            self.beforex = self.x
            self.beforey = self.y
            self.beforeangle = self.angle
        else:
            self.beforex = self.x
            self.beforey = self.y
            self.beforeangle = self.angle
            if self.get_distancepoints(x, y, x5, y5)<self.selectdistance:
                self.operationcode = 2
                self.isselected = True
                self.isfilled = True
            elif self.get_distancepoints(x, y, x6, y6)<self.selectdistance:
                self.operationcode = 4
                self.isselected = True
                self.isfilled = True
            else:
                self.operationcode = 0
                self.isselected = False
                self.isfilled = False
class ImgGL_SegmentLine(ImgGL_Shape):
    def __init__(self, name,pointa,pointb, angle, color=[0.0, 0.0, 0.0, 1.0]):
        super().__init__(name, (pointa[0]+pointb[0])/2, (pointa[1]+pointb[1])/2,angle, color)
        self.points= [pointa,pointb]
        self.name = name
        self.angle = angle  # 旋转角度
        self.beforeangle = angle
        self.beforepoints = copy.deepcopy(self.points)
        self.update_vertices()
    @classmethod
    def from_dict(cls, data):
        """从字典数据创建 ImgGL_Coordinate 实例"""
        name = data.get('name', 'Coordinate')
        x = data.get('x', 0.0)
        y = data.get('y', 0.0)
        angle = data.get('angle', 0.0)
        color = data.get('color', [0.0, 0.0, 0.0, 1.0])
        points = data.get('points', [[-50.0,0.0],[50.0,0.0]])
        return cls(name, x, y,points[0],points[1], angle, color)
    def to_dict(self):
        return {
            'name': self.name,
            'class': 'ImgGL_SegmentLine',
            'x': self.x,
            'y': self.y,
            'width': self.width,
            'height': self.height,
            'angle': self.angle,
            'color': self.color,
            'font_size': self.font_size,
            'points': self.points
        }
    def update_vertices(self):
        self.indices_boundingbox = np.array([0,1,2,2,3,0], dtype=np.uint32)
        self.boundingbox = self.get_bounding_box()

        self.isupdating = True
        verts = []
        for pt in self.points:
            verts.extend([pt[0], pt[1], 0.0, self.color[0], self.color[1], self.color[2], self.color[3]])
        self.vertices = np.array(verts, dtype=np.float32)
        # self.vertices = np.array([
        #     self.points[0][0],self.points[0][1],0.0, self.color[0], self.color[1], self.color[2], self.color[3], 
        #     self.points[1][0],self.points[1][1],0.0, self.color[0], self.color[1], self.color[2], self.color[3],
        #     ], dtype=np.float32)

        self.indices = np.array([0,1], dtype=np.uint32)
        self.isupdating = False
    def draw(self,glframe):
        if self.isupdating:
            return
        glLineWidth(self.selectdistance/2)
        if self.isfilled:
           glEnable(GL_LINE_STIPPLE)
           glLineStipple(1, 0x00FF)  # 1: 线条重复次数, 0x00FF: 虚线模式
        else:
            glDisable(GL_LINE_STIPPLE)
        glUseProgram(glframe.rect_shader)
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "projection"),
                       1, GL_TRUE, np.array((glframe.ortho_matrix(-glframe.width/2, glframe.width/2,glframe.height/2, -glframe.height/2, -1, 1))))
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "model"),
                       1, GL_TRUE, np.array(glframe.model_matrix(glframe.offset_x,glframe.offset_y,glframe.rotation_angle,glframe.scale)))  # 单位矩阵
        glUniformMatrix4fv(glGetUniformLocation(glframe.rect_shader, "view"),
                       1, GL_TRUE, np.array(glframe.view_matrix()))
        vao=glGenVertexArrays(1)
        vbo=glGenBuffers(1)
        ebo=glGenBuffers(1)
        texture_id=glGenBuffers(1)
        glBindVertexArray(vao)  # 创建新的VAO
        glBindBuffer(GL_ARRAY_BUFFER, vbo)  # 绑定VBO
        glBufferData(GL_ARRAY_BUFFER, self.vertices.nbytes, self.vertices, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)  # 绑定EBO
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices.nbytes, self.indices, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 7 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 4, GL_FLOAT, GL_FALSE, 7 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        """绘制线段"""
        glDrawElements(GL_LINES, len(self.indices), GL_UNSIGNED_INT, None)         
        glUseProgram(glframe.shader)  # 使用着色器程序
        glBindVertexArray(vao)
        textureType = TextureFormat.Color          
        glUniform1i(glGetUniformLocation(glframe.shader, "texturetype"), textureType.value)  # 设置纹理类型
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "projection"),
                           1, GL_TRUE, np.array((glframe.ortho_matrix(-glframe.width/2, glframe.width/2,glframe.height/2, -glframe.height/2, -1, 1))))
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "model"),
                           1, GL_TRUE, np.array(glframe.model_matrix(glframe.offset_x,glframe.offset_y,glframe.rotation_angle,glframe.scale)))  # 单位矩阵
        glUniformMatrix4fv(glGetUniformLocation(glframe.shader, "view"),
                           1, GL_TRUE, np.array(glframe.view_matrix()))
        glBindBuffer(GL_ARRAY_BUFFER, vbo)  # 绑定VBO
        glBufferData(GL_ARRAY_BUFFER, self.boundingbox.nbytes, self.boundingbox, GL_DYNAMIC_DRAW)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)  # 绑定EBO
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices_boundingbox.nbytes, self.indices_boundingbox, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 5 * sizeof(GLfloat), ctypes.c_void_p(3 * sizeof(GLfloat)))
        glEnableVertexAttribArray(1)
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glUniform1i(glGetUniformLocation(glframe.shader, "textureSampler"), 0)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)  # 边缘处理
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        bbox = self.font.getbbox(self.name)
        pil_image = Image.new("RGBA", (int(bbox[2]-bbox[0]), int(bbox[3]-bbox[1])), (int(self.color[0])*255,int(self.color[1])*255,int(self.color[2])*255,int(self.color[3])*255))
        textdraw = ImageDraw.Draw(pil_image)
        textdraw.text((0,- bbox[1]), self.name, font=self.font, fill=(255,255,255,255))
        textimage = np.array(pil_image)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, textimage.shape[1], textimage.shape[0], 
             0, GL_RGBA, GL_UNSIGNED_BYTE, textimage)
        glDrawElements(GL_TRIANGLES, 6, GL_UNSIGNED_INT, None)
        glBindTexture(GL_TEXTURE_2D, 0)  # 禁用纹理
        glBindVertexArray(0)    
        glDeleteVertexArrays(1, [vao])  # 删除VAO以释放资源 
        glDeleteBuffers(1, [vbo])  # 删除VBO以释放资源
        glDeleteBuffers(1, [ebo])  # 删除EBO以释放资源      
        glDeleteBuffers(1, [texture_id])  # 删除纹理ID以释放资源  
        glLineWidth(2.0)  
        glDisable(GL_LINE_STIPPLE)
    def get_bounding_box(self):
        xmin,ymin,xmax,ymax= self.font.getbbox(self.name)
        w = xmax - xmin
        h = ymax - ymin
        x1,y1 = self.rotate_point(self.x,     self.y, self.x, self.y, self.angle)
        x2,y2 = self.rotate_point(self.x + w, self.y, self.x, self.y, self.angle)
        x3,y3 = self.rotate_point(self.x + w, self.y + h, self.x, self.y, self.angle)
        x4,y4 = self.rotate_point(self.x,     self.y + h, self.x, self.y, self.angle)
        return np.array([
            x1,y1,0.0,0,0,
            x2,y2,0.0,1,0,
            x3,y3,0.0,1,1,
            x4,y4,0.0,0,1
        ], dtype=np.float32)  
    def check(self, x, y):
        """检查鼠标是否在矩形内"""
        res =  cv2.pointPolygonTest(np.array([
            [self.x+self.selectdistance,self.y+self.selectdistance],
            [self.x+self.selectdistance,self.y-self.selectdistance],
            [self.x-self.selectdistance,self.y-self.selectdistance],
            [self.x-self.selectdistance,self.y+self.selectdistance],
            ],dtype=np.float32),(x,y),False)
        self.beforex = self.x
        self.beforey = self.y
        self.beforepoints = copy.deepcopy(self.points)
        self.beforeangle = self.angle
        if res >=0:
            self.operationcode = 1
            self.isselected = True
            self.isfilled = True
        else:
            for idx,point in enumerate(self.points):
                if self.get_distancepoints(x, y, point[0], point[1])<self.selectdistance:
                    self.operationcode = 2
                    self.optpoint = idx
                    self.isselected = True
                    self.isfilled = True
                    return
    def show_settings(self,x,y,glredraw,treeviewupdate):
        def choose_color():
            color = colorchooser.askcolor(color=(int(self.color[0]*255),int(self.color[1]*255),int(self.color[2]*255)), title='ColorChooser')[0]
            if color:
                self.color = [color[0]/255, color[1]/255, color[2]/255, 1.0]
                glredraw()  # 重绘图形以应用新颜色
        def save_settings():
            self.name = name_entry.get()
            self.font_size = int(font_size_entry.get())
            self.font = self.get_cross_platform_font(self.font_size,path="C:\\Windows\\Fonts\\msyh.ttc")
            self.update_vertices()
            settings_window.destroy()
            glredraw()
            treeviewupdate(id(self))
        def on_poinaxchanged():
            poinax = float(pointax_entry.get())
            self.points[self.optpoint] = [poinax, self.points[self.optpoint][1]]
            self.x = np.mean([p[0] for p in self.points])
            self.update_vertices()
            glredraw()
        def on_poinaychanged():
            poinay = float(pointay_entry.get())
            self.points[self.optpoint] = [self.points[self.optpoint][0], poinay]
            self.y = np.mean([p[1] for p in self.points])
            self.update_vertices()
            glredraw()
        def on_pointsindexchanged():
            pointsindex = int(pointsindex_spinbox.get())
            if pointsindex>=0 and pointsindex<len(self.points):
                self.optpoint = pointsindex
                pointax_entry.delete(0, 'end')
                pointax_entry.insert(0, self.points[self.optpoint][0])
                pointay_entry.delete(0, 'end')
                pointay_entry.insert(0, self.points[self.optpoint][1])
        """显示形状设置对话框"""
        settings_window = tk.Toplevel()
        settings_window.title(f"Settings for {self.name}")
        
        notebook = ttk.Notebook(settings_window)
        viewsettings_frame = tk.Frame(notebook)
        viewsettings_frame.pack(padx=10, pady=10)
        notebook.pack(fill='both', expand=True)
        notebook.add(viewsettings_frame, text='View')
        
        tk.Label(viewsettings_frame, text="Name:").grid(row=0, column=0)
        name_entry = tk.Entry(viewsettings_frame)
        name_entry.insert(0, self.name)
        name_entry.grid(row=0, column=1)
        
        tk.Label(viewsettings_frame, text="Color:").grid(row=1, column=0)
        color_button = tk.Button(viewsettings_frame, text="Choose Color", command=choose_color)
        color_button.grid(row=1, column=1)
        
        tk.Label(viewsettings_frame, text="Font Size:").grid(row=2,column=0)
        font_size_entry = tk.Entry(viewsettings_frame)
        font_size_entry.insert(0, self.font_size)
        font_size_entry.grid(row=2, column=1)
                    
        tk.Label(viewsettings_frame, text="PointsIndex:").grid(row=3, column=0) 
        pointsindex_spinbox = tk.Spinbox(viewsettings_frame, from_=0, to=len(self.points)-1, increment=1)
        pointsindex_spinbox.delete(0, 'end')
        pointsindex_spinbox.insert(0, 0 if self.optpoint<0 or self.optpoint>=len(self.points) else self.optpoint)
        pointsindex_spinbox.grid(row=3, column=1)
        pointsindex_spinbox.bind("<Button-1>", lambda event: on_pointsindexchanged())
        
        
        tk.Label(viewsettings_frame, text="PointAX:").grid(row=3, column=2)
        pointax_entry = tk.Entry(viewsettings_frame)
        pointax_entry.insert(0, self.points[self.optpoint][0] if self.optpoint>=0 and self.optpoint<len(self.points) else 0)
        pointax_entry.grid(row=3, column=3)
        pointax_entry.bind("<Return>", lambda event: on_poinaxchanged())  
        tk.Label(viewsettings_frame, text="PointAY:").grid(row=3, column=4)
        pointay_entry = tk.Entry(viewsettings_frame)
        pointay_entry.insert(0, self.points[self.optpoint][1] if self.optpoint>=0 and self.optpoint<len(self.points) else 0)
        pointay_entry.grid(row=3, column=5)
        pointay_entry.bind("<Return>", lambda event: on_poinaychanged())
        
        tk.Button(viewsettings_frame, text="Save", command=save_settings).grid(row=4, column=0, columnspan=5,sticky="nsew")
        settings_window.geometry(f"+{x}+{y}")  # 设置大小
        settings_window.update_idletasks()  # 更新窗口的内容
        settings_window.attributes('-topmost', True)  # 窗口置顶
    def __deepcopy__(self, memo):
        newshape = ImgGL_SegmentLine(self.name,[self.points[0][0],self.points[0][1]],[self.points[1][0],self.points[1][1]], self.angle, self.color)
        newshape.isselected = False
        newshape.isfilled = False
        newshape.selectcolor = self.selectcolor
        newshape.linewidth = self.linewidth
        newshape.selectdistance = self.selectdistance
        newshape.font_size = self.font_size
        newshape.font = self.font
        return newshape
    def when_drag_transform(self,x,y,dx, dy,angle):
        if self.operationcode == 1:
            self.x = self.beforex + dx
            self.y = self.beforey + dy
            for i in range(len(self.points)):
                self.points[i][0] = self.beforepoints[i][0] + dx
                self.points[i][1] = self.beforepoints[i][1] + dy
        elif self.operationcode == 2 and self.optpoint>=0 and self.optpoint<len(self.points):
            self.points[self.optpoint] = [self.beforepoints[self.optpoint][0] + dx, self.beforepoints[self.optpoint][1] + dy]
            self.x = np.mean([p[0] for p in self.points])
            self.y = np.mean([p[1] for p in self.points])
        self.update_vertices()
        
class Graphics_ValueModule():
    def __init__(self,x:int=0,y:int=0,name:str='ValueModule',message=None):
        self.linemodule = False
        self.x = x
        self.y = y
        self.radius = 10
        self.text = name
        self.selectdistance = 10
        self.status = 'Normal'
        self.normalcolor = [0.0,0.5,0.5,1.0]
        self.selectedcolor = [1.0, 0.0, 0.0,1.0]
        self.statuscolor = [1.0, 0.0, 0.0,1.0]
        self.drawtext = True
        self.font_path = "C:\\Windows\\Fonts\\msyh.ttc"  # 微软雅黑字体
        self.font_size = 16
        self.font = self.get_cross_platform_font(self.font_path, self.font_size)
        self.textcolor = [1.0, 1.0, 1.0,1.0]
        self.enable = True
        self.lastrunstatus = False
        self.textimage = None
        self.breifimage = None
        self.breifimage_visible = tk.IntVar()
        self.language = 'zh'
        self.spantime=0
        self.padding = 12
        self.get_image()
        self.message=message
        self.parameters={'lastrunstatus':self.lastrunstatus,}
        self.breifimagewidth = self.textimage.shape[1]
        self.breifimageheight = self.textimage.shape[0]*(self.textimage.shape[1]//self.breifimagewidth+1)
        self.moudlestatus = f'Name: {self.text} \n Status: {self.status} \n Time: {self.spantime:.4f}s \n LastRunStatus: {self.lastrunstatus}'
        self.texts = {}
        self.set_language(self.language)
        self.description_html = {
            'zh': 
                """
                <div style="
                    font-family: Arial, sans-serif;
                    background-color: #f0f8ff;
                    text-align: left;
                    padding: 10px;
                ">
                    <div style="
                        display: inline-block;
                        text-align: left;
                        padding: 10px;
                        border: 2px solid #4a90e2;
                        border-radius: 10px;
                        background-color: #ffffff;
                    ">
                        <h3 style="color: #4a90e2;">欢迎来到CVFLOW应用</h3>
                        <p style="font-size: 15px; color: #333;">我们很高兴见到您！</p>
                        <img src="{path}" alt="Title Icon" style="width: 100%; height: auto; margin-top: 5px;">

                    </div>
                </div>
                """.format(path=iconp),
            'en': 
                """
                <div style="
                    font-family: Arial, sans-serif;
                    background-color: #f0f8ff;
                    text-align: left;
                    padding: 10px;
                ">
                    <div style="
                        display: inline-block;
                        text-align: left;
                        padding: 10px;
                        border: 2px solid #4a90e2;
                        border-radius: 10px;
                        background-color: #ffffff;
                    ">
                        <h3 style="color: #4a90e2;">Welcome to Cvflow App</h3>
                        <p style="font-size: 15px; color: #333;">It's nice to see you here!</p>
                        <img src="{path}" alt="Title Icon" style="width: 100%; height: auto; margin-top: 5px;">
                
                    </div>
                </div>
                """.format(path=iconp)
        }
    def get_cross_platform_font(self,font_path,font_size):
        try:
            # 优先尝试系统指定字体
            return ImageFont.truetype(font_path, font_size)
        except Exception:
            # 失败时回退到Pillow的默认字体
            return ImageFont.load_default(font_size)
    @classmethod
    def from_userdefined(cls,master,x:int=0,y:int=0,name:str='ValueModule',message=None):
        inputdialog= InputStrDialog(master,"User Defined Module",name)
        return cls(x=x, y=y,name = inputdialog.input, message=message)
    @classmethod
    def from_json(cls, json_data,message=None):
        """从JSON数据创建Graphics_ValueModule实例"""
        x = json_data.get('x', 0)
        y = json_data.get('y', 0)
        name = json_data.get('name', 'ValueModule')
        module = cls(x=x, y=y, name=name,message=message)
        
        # 设置其他属性
        module.linemodule = json_data.get('linemodule', False)
        module.text = json_data.get('text', name)
        module.normalcolor = json_data.get('normalcolor', [0.0, 0.5, 0.5, 1.0])
        module.selectedcolor = json_data.get('selectedcolor', [1.0, 0.0, 0.0, 1.0])
        module.statuscolor = json_data.get('statuscolor', [1.0, 0.0, 0.0, 1.0])
        module.drawtext = json_data.get('drawtext', True)
        module.font_path = json_data.get('font_path', "C:\\Windows\\Fonts\\msyh.ttc")
        module.font_size = json_data.get('font_size', 16)
        module.textcolor = json_data.get('textcolor', [1.0, 1.0, 1.0, 1.0])
        module.enable = json_data.get('enable', True)
        module.lastrunstatus = json_data.get('lastrunstatus', False)
        module.breifimage_visible.set(json_data.get('breifimage_visible', True))
        module.breifimagewidth = json_data.get('breifimagewidth', 200)
        module.breifimageheight = json_data.get('breifimageheight', 100)
        
        # 设置语言和描述
        language = json_data.get('language', 'zh')
        module.set_language(language)
        
        return module
    def set_language(self,language:str):
        if language == 'zh':
            self.texts['color_choose']='颜色选择'
            self.texts['del_button']= '删除'
            self.texts['del_button_tip_title']='删除模块'
            self.texts['del_button_tip_content']='确定删除该模块吗？'
            self.texts['run_button']= '运行'
            self.texts['save_button']= '保存'
            self.texts['load_button']= '加载'
            self.texts['info_label']= '信息'
            self.texts['tab1']='视图'
            self.texts['tab2']='参数'
            self.texts['tab3']='说明'
            self.texts['name_label']='名称'
            self.texts['labelcolor']='标签颜色'
            self.texts['fontsize']='字体大小'
            self.texts['fontpath']='字体路径'
            self.texts['brifeimage']='显示简略图'
            self.texts['brifeimagewidth']='简略图宽度'
            self.texts['brifeimageheight']='简略图高度'
            self.texts['language']='语言'
            self.texts['load_button_tip_title']='错误'
            self.texts['load_button_tip_content']='加载模块失败，请检查模块文件是否存在或格式是否正确。'
            pass
        else:
            self.texts['color_choose']='Choose Color'
            self.texts['del_button']= 'Delete'
            self.texts['del_button_tip_title']='Delete Module'
            self.texts['del_button_tip_content']='Are you sure you want to delete this module?'
            self.texts['run_button']= 'Run'
            self.texts['save_button']= 'Save'
            self.texts['load_button']= 'Load'
            self.texts['info_label']= 'Info'
            self.texts['tab1']='View'
            self.texts['tab2']='Parameter'
            self.texts['tab3']='Description'
            self.texts['name_label']='Name'
            self.texts['labelcolor']='Label Color'
            self.texts['fontsize']='Font Size'
            self.texts['fontpath']='Font Path'
            self.texts['brifeimage']='Show Brife Image'
            self.texts['brifeimagewidth']='Brife Image Width'
            self.texts['brifeimageheight']='Brife Image Height'
            self.texts['language']='Language'
            self.texts['load_button_tip_title']='Error'
            self.texts['load_button_tip_content']='Failed to load module, please check if the module file exists or if the format is correct.'
            pass
    def get_image(self):
        
        self.font= self.get_cross_platform_font(self.font_path, self.font_size)
        # 设置字体路径，使用 Windows 系统的字体

        #self.font = cv2.FONT_HERSHEY_SIMPLEX
        self.text=self.text.replace('\\n','\n')
        self.lines = self.text.split('\n')
        # 计算每行文本的大小并找到最大宽度
        
        text_widths = [self.font.getbbox(line)[2]-self.font.getbbox(line)[0] for line in self.lines]
        text_width = max(text_widths) if text_widths else 0        
                
        self.bbox= self.font.getbbox(self.text)
        self.width = text_width + 2 * self.padding
        self.height = (self.bbox[3]-self.bbox[1])*len(self.lines) + 2 * self.padding
        self.textimage = np.full((self.height, self.width, 4),(int(self.normalcolor[0]*255),int(self.normalcolor[1]*255),int(self.normalcolor[2]*255),int(self.normalcolor[3]*255)), dtype=np.uint8)
        
        self.pil_image = Image.new("RGBA", (self.width, self.height), (int(self.normalcolor[0]*255),int(self.normalcolor[1]*255),int(self.normalcolor[2]*255),int(self.normalcolor[3]*255)))
        self.textdraw = ImageDraw.Draw(self.pil_image)
    def get_inside_rect(self):
        x1 = self.x + self.padding
        y1 = self.y + self.padding
        x2 = self.x + self.width - self.padding
        y2 = self.y + self.height - self.padding
        return x1, y1, x2, y2
    def get_output_triangle(self):
        x1 = self.x + self.width/2
        y1 = self.y + self.height
        p1x = x1 + self.radius/2
        p1y = y1
        p2x = x1 - self.radius/2
        p2y = y1 
        p3x = x1
        p3y = y1 + self.radius/2
        return p1x, p1y, p2x, p2y, p3x, p3y
    def get_input_triangle(self):
        x1 = self.x + self.width/2
        y1 = self.y
        p1x = x1 + self.radius/2
        p1y = y1
        p2x = x1 - self.radius/2
        p2y = y1 
        p3x = x1
        p3y = y1 - self.radius/2
        return p1x, p1y, p2x, p2y, p3x, p3y
    def check_inside(self,x:int,y:int):
        """判断点是否在坐标系内"""
        if self.enable is not True:
            return None
        x1, y1, x2, y2 = self.get_inside_rect()
        if x1 <= x <= x2 and y1 <= y <= y2:
            self.status = 'Selected'
            return self
        else:
            self.status = 'Normal'
            return None
    def run(self):
        starttime = time.perf_counter()
        self.spantime= time.perf_counter() - starttime
        self.moudlestatus = f'Name: {self.text} \n Status: {self.status} \n Time: {self.spantime:.4f}s \n LastRunStatus: {self.lastrunstatus}'
        self.parameters['lastrunstatus']=self.lastrunstatus
    def show_parameter_page(self,x,y,parent):
        x1, y1, x2, y2 = self.get_inside_rect()
        if not (x1 <= x <= x2 and y1 <= y <= y2):
            return
        def update_io():
            tab2.children.clear()
            keys = list(self.parameters.keys())
            for i,key in enumerate(keys):
                tk.Label(tab2, text=f"{key}\n    {gstr(self.parameters[key])}",anchor='w',justify='left').grid(row=i, column=0,sticky='ew' ,pady=5)
            pass
        def change_language():
            self.language = languages_commbox.get()
            self.set_language(self.language)
            run_button.config(text=self.texts['run_button'])
            del_button.config(text=self.texts['del_button'])
            save_button.config(text=self.texts['save_button'])
            load_button.config(text=self.texts['load_button'])
            info_label.config(text=self.texts['info_label'])
            notebook.tab(tab1, text=self.texts['tab1'])
            notebook.tab(tab2, text=self.texts['tab2'])
            notebook.tab(tab3, text=self.texts['tab3'])
            namelabel.config(text=self.texts['name_label'])
            button.config(text=self.texts['color_choose'])
            labelcolor.config(text=self.texts['labelcolor'])
            fontsize_label.config(text=self.texts['fontsize'])
            fontpath_label.config(text=self.texts['fontpath'])
            brieifimage_width.config(text=self.texts['brifeimagewidth'])
            brieifimage_height.config(text=self.texts['brifeimageheight'])
            breifimage_enbale.config(text=self.texts['brifeimage'])
            languages_lable.config(text=self.texts['language'])
            html_label.set_html(self.description_html[self.language])
        def check_language():
            self.set_language(self.language)
            run_button.config(text=self.texts['run_button'])
            del_button.config(text=self.texts['del_button'])
            save_button.config(text=self.texts['save_button'])
            load_button.config(text=self.texts['load_button'])
            info_label.config(text=self.texts['info_label'])
            notebook.tab(tab1, text=self.texts['tab1'])
            notebook.tab(tab2, text=self.texts['tab2'])
            notebook.tab(tab3, text=self.texts['tab3'])
            namelabel.config(text=self.texts['name_label'])
            button.config(text=self.texts['color_choose'])
            labelcolor.config(text=self.texts['labelcolor'])
            fontsize_label.config(text=self.texts['fontsize'])
            fontpath_label.config(text=self.texts['fontpath'])
            brieifimage_width.config(text=self.texts['brifeimagewidth'])
            brieifimage_height.config(text=self.texts['brifeimageheight'])
            breifimage_enbale.config(text=self.texts['brifeimage'])
            languages_lable.config(text=self.texts['language'])
            html_label.set_html(self.description_html[self.language])
        def choose_color():
            color = colorchooser.askcolor(color=(int(self.normalcolor[0]*255),int(self.normalcolor[1]*255),int(self.normalcolor[2]*255)), title=self.texts['color_choose'])
            if color[0] is not None:
                self.normalcolor = [color[0][0]/255,color[0][1]/255,color[0][2]/255,1.0]
                button.config(bg=color[1])
        def run_button_click():
            self.run()
            info_label.config(text=f'Info: CT:{self.spantime:.4f}s')
            update_io()
        def del_button_click():
            if tk.messagebox.askokcancel(self.texts['del_button_tip_title'], self.texts['del_button_tip_content']):
                self.message(self,-1)
                window.destroy()
        window= tk.Toplevel(parent)
        window.title(self.text)
        window.iconphoto(True,ImageTk.PhotoImage(Image.open(load_icon()))) 
        window.geometry(f'300x432+{parent.winfo_rootx()}+{parent.winfo_rooty()}')
        button_frame = tk.Frame(window)
        button_frame.pack(side='top', anchor='nw', pady=5)

        run_button = tk.Button(button_frame, text=self.texts['run_button'], command=run_button_click)
        run_button.pack(side='left', padx=1)

        del_button = tk.Button(button_frame, text=self.texts['del_button'], command=del_button_click)
        del_button.pack(side='left', padx=1)
        
        save_button = tk.Button(button_frame, text=self.texts['save_button'], command=self.save)
        save_button.pack(side='left', padx=1)
        
        load_button = tk.Button(button_frame, text=self.texts['load_button'], command=self.load)
        load_button.bind('<Button-1>',lambda event: self.load(),add=True)
        load_button.bind('<Button-1>',lambda event: update_io(),add=True)
        load_button.pack(side='left', padx=1)

        info_label = tk.Label(window,text=self.texts['info_label'])
        info_label.pack(side='bottom',anchor='sw')

        notebook = ttk.Notebook(window)
        notebook.pack(fill='both', expand=True)
        tab1 = ttk.Frame(notebook)
        tab2 = ttk.Frame(notebook)
        tab3 = ttk.Frame(notebook)
        notebook.add(tab1,text='View')
        notebook.add(tab2,text='Parameter')
        notebook.add(tab3,text='Description')
        
        frame = tk.Frame(tab1)
        frame.pack(padx=10, pady=10)
        tk.Label(frame, text="X:").grid(row=0, column=0, pady=5)
        x_entry = tk.Entry(frame)
        x_entry.insert(0, self.x)
        x_entry.grid(row=0, column=1, pady=5)
        x_entry.bind('<Return>', lambda event: setattr(self, 'x', int(x_entry.get())))
        tk.Label(frame, text="Y:").grid(row=1, column=0, pady=5)
        y_entry = tk.Entry(frame)
        y_entry.insert(0, self.y)
        y_entry.grid(row=1, column=1, pady=5)
        y_entry.bind('<Return>', lambda event: setattr(self, 'y', int(y_entry.get())))
        namelabel= tk.Label(frame, text=self.texts['name_label'])
        namelabel.grid(row=2, column=0, pady=5)
        text_entry = tk.Entry(frame)
        text_entry.delete(0, 'end')
        text_entry.insert(0, self.text)
        text_entry.grid(row=2, column=1, pady=5)
        text_entry.bind('<Return>',lambda event: setattr(self,'text',text_entry.get()),add=True)
        text_entry.bind('<Return>',lambda event: self.get_image(),add=True)
        text_entry.bind('<Return>',lambda event: self.message(self,-2),add=True)

        labelcolor=tk.Label(frame, text=self.texts['labelcolor'])
        labelcolor.grid(row=4, column=0, pady=5)
        button = tk.Button(frame, text=self.texts['color_choose'], command=choose_color)
        button.grid(row=4,column=1,pady=5)
        
        fontsize_label=tk.Label(frame, text=self.texts['fontsize'])
        fontsize_label.grid(row=5, column=0, pady=5)
        spinbox= tk.Spinbox(frame,from_=1,to=48)
        spinbox.delete(0, 'end')
        spinbox.insert(0, self.font_size)
        spinbox.bind('<Button-1>',lambda evemt: setattr(self,'font_size',int(spinbox.get())),add=True)
        spinbox.bind('<Button-1>',lambda evemt: self.get_image(),add=True)
        

        spinbox.grid(row=5,column=1,pady=5)
        
        
        fontpath_label=tk.Label(frame, text=self.texts['fontpath'])
        fontpath_label.grid(row=6, column=0, pady=5)
        fontscale_spinbox= tk.Entry(frame)
        fontscale_spinbox.delete(0, 'end')
        fontscale_spinbox.insert(0, self.font_path)
        fontscale_spinbox.bind('<Return>',lambda event: setattr(self,'font_path',fontscale_spinbox.get()),add=True)
        fontscale_spinbox.bind('<Return>',lambda event: self.get_image(),add=True)
        fontscale_spinbox.grid(row=6,column=1,pady=5)
        
        brieifimage_width = tk.Label(frame, text=self.texts['brifeimagewidth'])
        brieifimage_width.grid(row=7, column=0, pady=5)
        brieifimage_width_entry = tk.Entry(frame)
        brieifimage_width_entry.delete(0, 'end')
        brieifimage_width_entry.insert(0, self.breifimagewidth)
        brieifimage_width_entry.grid(row=7, column=1, pady=5)
        brieifimage_width_entry.bind('<Return>',lambda event: setattr(self,'breifimagewidth',int(brieifimage_width_entry.get())))
        
        brieifimage_height = tk.Label(frame, text=self.texts['brifeimageheight'])
        brieifimage_height.grid(row=8, column=0, pady=5)
        brieifimage_height_entry = tk.Entry(frame)
        brieifimage_height_entry.delete(0, 'end')
        brieifimage_height_entry.insert(0, self.breifimageheight)
        brieifimage_height_entry.grid(row=8, column=1, pady=5)
        brieifimage_height_entry.bind('<Return>',lambda event: setattr(self,'breifimageheight',int(brieifimage_height_entry.get())))
        
        breifimage_enbale = tk.Label(frame, text=self.texts['brifeimage'])
        breifimage_enbale.grid(row=9, column=0, pady=5)
        breifimage_enbale_checkbox = tk.Checkbutton(frame, variable= self.breifimage_visible, onvalue=1, offvalue=0)
        breifimage_enbale_checkbox.grid(row=9, column=1, pady=5)
        
        languages_lable = tk.Label(frame, text=self.texts['language'])
        languages_lable.grid(row=10, column=0, pady=5)
        languages_commbox = ttk.Combobox(frame,values= ['en', 'zh'], state='readonly', width=5)
        languages_commbox.set(self.language)
        languages_commbox.grid(row=10, column=1, pady=5)
        languages_commbox.bind('<<ComboboxSelected>>', lambda event: change_language(), add=True)
                  
        html_label = HTMLLabel(tab3, html=self.description_html[self.language])
        html_label.pack(fill=tk.BOTH, expand=True)
        
        check_language()        
        update_io()
    def render_text(self, x, y):
        if self.drawtext is not True:
            return
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture)
        glColor3f(1.0, 1.0, 1.0)        
                
        self.pil_image = Image.new("RGBA", (self.width, self.height), (int(self.normalcolor[0]*255),int(self.normalcolor[1]*255),int(self.normalcolor[2]*255),int(self.normalcolor[3]*255)))
        self.textdraw = ImageDraw.Draw(self.pil_image)

        self.textdraw.text((self.padding, self.padding - self.bbox[1]), self.text, font=self.font, fill=(int(self.textcolor[0]*255),int(self.textcolor[1]*255),int(self.textcolor[2]*255),int(self.textcolor[3]*255)))

        self.textimage = np.array(self.pil_image)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.textimage.shape[1], self.textimage.shape[0], 
                     0, GL_RGBA, GL_UNSIGNED_BYTE, self.textimage)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # 绘制四边形
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x, y)
        glTexCoord2f(1, 0); glVertex2f(x + self.textimage.shape[1], y)
        glTexCoord2f(1, 1); glVertex2f(x + self.textimage.shape[1], y + self.textimage.shape[0])
        glTexCoord2f(0, 1); glVertex2f(x, y + self.textimage.shape[0])
        glEnd()

        glDeleteTextures(1,[texture])

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)   
    def render_breifimage(self, x, y):
        if self.breifimage is None or self.breifimage_visible.get() == 0:
            return
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        breifimage_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, breifimage_texture)
        glColor3f(1.0, 1.0, 1.0)

        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, self.breifimage.shape[1], self.breifimage.shape[0], 
                     0, GL_LUMINANCE, GL_FLOAT, self.breifimage)
        
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        # 绘制四边形
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(x + self.textimage.shape[1], y)
        glTexCoord2f(1, 0); glVertex2f(x + self.textimage.shape[1]+self.breifimagewidth, y)
        glTexCoord2f(1, 1); glVertex2f(x + self.textimage.shape[1]+self.breifimagewidth, y + self.breifimageheight)
        glTexCoord2f(0, 1); glVertex2f(x + self.textimage.shape[1], y + self.breifimageheight)
        glEnd()

        glDeleteTextures(1,[breifimage_texture])

        glDisable(GL_TEXTURE_2D)
        glDisable(GL_BLEND)  
    def GLDraw(self):
        if True:
            self.render_text(self.x, self.y)
            self.render_breifimage(self.x, self.y)
            if self.status == 'Normal':
                glColor3f(self.normalcolor[0], self.normalcolor[1], self.normalcolor[2])
            else:
                glColor3f(self.selectedcolor[0], self.selectedcolor[1], self.selectedcolor[2])
            glBegin(GL_LINE_LOOP)
            glVertex2f(self.x, self.y)
            glVertex2f(self.x + self.textimage.shape[1], self.y)
            glVertex2f(self.x + self.textimage.shape[1], self.y + self.textimage.shape[0])
            glVertex2f(self.x, self.y + self.textimage.shape[0])
            glEnd()
            
            glColor3f(self.statuscolor[0], self.statuscolor[1], self.statuscolor[2])
            
            glBegin(GL_QUADS)
            glVertex2f(self.x-self.radius/2, self.y+2*self.radius-self.radius/2)
            glVertex2f(self.x+self.radius/2, self.y+2*self.radius-self.radius/2)
            glVertex2f(self.x+self.radius/2, self.y+2*self.radius+self.radius/2)
            glVertex2f(self.x-self.radius/2, self.y+2*self.radius+self.radius/2)
            glEnd()      
            
            glColor3f(1.0, 1.0, 1.0)     
    def contains(self,x:int,y:int):
        """判断点是否在坐标系内"""
        if self.enable is not True:
            return None
        return self.check_inside(x,y)
    def get_distance(self,x:int,y:int):
        """获取坐标系到点的距离"""
        distance = ((x - self.x) ** 2 + (y - self.y) ** 2) ** 0.5
        return distance
    def save(self):
        """保存模块为JSON"""
        file_path = filedialog.asksaveasfilename(defaultextension=f"{self.text}.cvvm",
                                                 filetypes=[("JSON files", "*.cvvm"), ("All files", "*.*")])
        if file_path:
            try:
                # 只保存可序列化的属性
                data = self.get_json_data()
                with open(file_path, 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=4 ,cls=CustomEncoder)
                messagebox.showinfo("Success", "Module saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save module: {e}")
    def get_json_data(self):
        """获取模块的JSON数据"""
        return {
            "class": self.__class__.__name__,
            "x": self.x,
            "y": self.y,
            "radius": self.radius,
            "text": self.text,
            "normalcolor": self.normalcolor,
            "selectedcolor": self.selectedcolor,
            "font_path": self.font_path,
            "font_size": self.font_size,
            "textcolor": self.textcolor,
            "parameters": self.parameters, #{k: None if isinstance(v, np.ndarray) else v for k, v in self.parameters.items()},
            "breifimagewidth": self.breifimagewidth,
            "breifimageheight": self.breifimageheight,
            "status": self.status,
            "language": self.language,
            'breifimage_visible': self.breifimage_visible.get(),
            "lastrunstatus": self.lastrunstatus,
        }
    def load(self):
        """加载模块的JSON文件"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.cvvm"), ("All files", "*.*")])
        if not file_path:
            return
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                if data.get("class") != self.__class__.__name__:
                    messagebox.showerror(self.texts['load_button_tip_title'], self.texts['load_button_tip_content'])
                    return
                # 只加载可序列化的属性
                self.x = data.get("x", self.x)
                self.y = data.get("y", self.y)
                self.radius = data.get("radius", self.radius)
                self.text = data.get("text", self.text)
                self.normalcolor = data.get("normalcolor", self.normalcolor)
                self.selectedcolor = data.get("selectedcolor", self.selectedcolor)
                self.font_path = data.get("font_path", self.font_path)
                self.font_size = data.get("font_size", self.font_size)
                self.textcolor = data.get("textcolor", self.textcolor)
                self.parameters = data.get("parameters", {})
                self.breifimagewidth = data.get("breifimagewidth",self.breifimagewidth)
                self.breifimageheight = data.get("breifimageheight",self.breifimageheight)
                self.status = data.get("status",self.status)
                self.language = data.get("language",self.language)
            for k,v in self.parameters.items():
                if k == 'Annos':
                    if isinstance(v, list):
                        new_annos = []
                        for item in v:
                            cls_name = item.get('class', None)
                            if cls_name == 'ImgGL_Rectangle':
                                new_annos.append(ImgGL_Rectangle.from_dict(item))
                            elif cls_name == 'ImgGL_Coordinate':
                                new_annos.append(ImgGL_Coordinate.from_dict(item))
                            elif cls_name == 'ImgGL_SegmentLine':
                                new_annos.append(ImgGL_SegmentLine.from_dict(item))
                            # 可以继续添加其他类型
                        self.parameters[k] = new_annos
        except Exception as e:
            messagebox.showerror(self.texts['load_button_tip_title'], self.texts['load_button_content'] + str(e))
def gstr(object):
    if isinstance(object,np.ndarray):
        return str(object.shape)
    elif isinstance(object, ImgGL_Shape):
        return object.name
    elif isinstance(object, list):
        return str([gstr(item) for item in object])
    else:
        return str(object)
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return None # 或者返回 obj.tolist() 如果你想保存数组数据
        if hasattr(obj, '__json__'):
            return obj.__json__()
        return super().default(obj)        
