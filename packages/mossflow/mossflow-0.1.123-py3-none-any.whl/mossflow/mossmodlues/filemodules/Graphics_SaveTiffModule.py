from OpenGL.GL import *
import tkinter as tk
import time
from tkinter import messagebox
import numpy as np
from mossflow.TkinterWidgets import Graphics_ValueModule,gstr
from tkhtmlview import HTMLLabel
from tkinter import ttk,colorchooser,filedialog
import tifffile as tiff

class Graphics_SaveTiffModule(Graphics_ValueModule):
    rawname = 'savetiff'
    zhname = '保存为Tiff文件'
    enname = 'Save as Tiff File'
    def __init__(self,x:int=0,y:int=0,name:str='SaveTiff',message=None):
        super().__init__(x,y,name,message)
        self.linemodule = False
        self.parameters={'depthimage':None,'lastrunstatus':self.lastrunstatus}

    def run(self):
        starttime = time.perf_counter()
        self.statuscolor = [1.0, 1.0, 0.0]
        """Save depth image as Tiff file."""
        try:
            if self.parameters['depthimage'] is None:
                raise ValueError("No depth image data provided.")
            file_path = filedialog.asksaveasfilename(defaultextension=f"{self.text}.tiff", filetypes=[("tiff files", "*.tiff"), ("All files", "*.*")])
            if file_path:
                tiff.imwrite(file_path, self.parameters['depthimage'])
            else:
                raise ValueError("No filename provided.")
            self.lastrunstatus = True
            self.statuscolor = [0.0, 1.0, 0.0]      
        except Exception as e:
            self.lastrunstatus = False
            self.statuscolor = [1.0, 0.0, 0.0]
            messagebox.showerror("Error", f"{e}")
        self.spantime= time.perf_counter() - starttime
        self.moudlestatus = f'Name: {self.text} \n Status: {self.status} \n Time: {self.spantime:.4f}s \n LastRunStatus: {self.lastrunstatus}'
        self.parameters['lastrunstatus']=self.lastrunstatus
