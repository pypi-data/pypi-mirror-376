from OpenGL.GL import *
import cv2 as cv
import tkinter as tk
import time
from tkinter import messagebox
import numpy as np
from mossflow.TkinterWidgets import Graphics_ValueModule,gstr
from tkhtmlview import HTMLLabel
from tkinter import ttk,colorchooser,filedialog
from mossflow.libs.pcl.pointscloud import getminmax3d
class Graphics_GetMinMax3DModule(Graphics_ValueModule):
    rawname = 'getminmax3d'
    zhname = '获取点云最小最大值'
    enname = 'Get Min Max 3D'
    def __init__(self,x:int=0,y:int=0,name:str='GetMinMax3D',message=None):
        super().__init__(x,y,name,message)
        self.linemodule = False
        self.parameters={'pointscloud':None,'xmin':None,'xmax':None,'ymin':None,'ymax':None,'zmin':None,'zmax':None,'lastrunstatus':self.lastrunstatus}

    def run(self):
        starttime = time.perf_counter()
        self.statuscolor = [1.0, 1.0, 0.0]
        """Read get min max 3d from point cloud data."""
        try:
            minx,miny,minz,maxx,maxy,maxz = getminmax3d(self.parameters['pointscloud'])
            self.parameters['xmin']=minx
            self.parameters['ymin']=miny
            self.parameters['zmin']=minz
            self.parameters['xmax']=maxx
            self.parameters['ymax']=maxy
            self.parameters['zmax']=maxz
            self.lastrunstatus = True
            self.statuscolor = [0.0, 1.0, 0.0]      
        except Exception as e:
            self.lastrunstatus = False
            self.statuscolor = [1.0, 0.0, 0.0]
            messagebox.showerror("Error", f"Failed to getminmax3d file: {e}")
        self.spantime= time.perf_counter() - starttime
        self.moudlestatus = f'Name: {self.text} \n Status: {self.status} \n Time: {self.spantime:.4f}s \n LastRunStatus: {self.lastrunstatus}'
        self.parameters['lastrunstatus']=self.lastrunstatus    