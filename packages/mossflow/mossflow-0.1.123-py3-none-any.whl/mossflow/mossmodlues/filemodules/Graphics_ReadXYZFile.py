from OpenGL.GL import *
import cv2 as cv
import tkinter as tk
import time
from tkinter import messagebox
import numpy as np
from mossflow.TkinterWidgets import Graphics_ValueModule,gstr
from tkhtmlview import HTMLLabel
from tkinter import ttk,colorchooser,filedialog

class Graphics_ReadXYZFile(Graphics_ValueModule):
    rawname = 'readxyzfile'
    zhname = '读取XYZ文件'
    enname = 'Read XYZ File'
    def __init__(self,x:int=0,y:int=0,name:str='ReadXYZ',message=None):
        super().__init__(x,y,name,message)
        self.linemodule = False
        self.parameters={'filename':None,'pointscloud':None,'lastrunstatus':self.lastrunstatus}

    def run(self):
        starttime = time.perf_counter()
        self.statuscolor = [1.0, 1.0, 0.0]
        """Read XYZ file and output point cloud data."""
        try:
            with open(self.parameters['filename'], 'r') as file:
                points = []
                for line in file:
                    parts = line.strip().split(',')
                    if len(parts) >= 3:
                        try:
                            x, y, z = map(float, parts[:3])
                            points.append([x, y, z,1.0])  # 添加齐次坐标
                        except ValueError:
                            continue
                self.parameters['pointscloud'] = np.array(points,dtype=np.float32)
            self.lastrunstatus = True
            self.statuscolor = [0.0, 1.0, 0.0]      
        except Exception as e:
            self.lastrunstatus = False
            self.statuscolor = [1.0, 0.0, 0.0]
            messagebox.showerror("Error", f"Failed to load xyz file: {e}")
        self.spantime= time.perf_counter() - starttime
        self.moudlestatus = f'Name: {self.text} \n Status: {self.status} \n Time: {self.spantime:.4f}s \n LastRunStatus: {self.lastrunstatus}'
        self.parameters['lastrunstatus']=self.lastrunstatus
