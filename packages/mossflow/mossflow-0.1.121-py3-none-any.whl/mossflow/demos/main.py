from mossflow.TkinterWidgets import FlowPlane as  plane
from mossflow.TkinterWidgets import load_icon
from PIL import Image, ImageTk
import tkinter as tk

def on_toplevel_close():
    print("Closing Toplevel window...")
    toplevel.destroy()  # 销毁Toplevel窗口
    root.destroy()      # 销毁root窗口，这将结束mainloop()
def disable_shortcuts(event):
    # 禁用 Alt+F4 快捷键
    if event.keysym == 'F4' and (event.state & 0x0008):  # 0x0008 是 Alt 键的状态掩码
        return "break"  # 阻止默认行为
    # 禁用 Ctrl+W 快捷键
    if event.keysym == 'w' and (event.state & 0x0004):  # 0x0004 是 Ctrl 键的状态掩码
        return "break"  # 阻止默认行为
    # 禁止 win 按键
    if event.keysym in ['Super_L', 'Super_R','Win_L','Win_R']:
        return "break"  # 阻止默认行为    
root = tk.Tk()
root.withdraw()  # Hide the root window
toplevel = tk.Toplevel(root,width=800, height=600)
toplevel.iconphoto(True,ImageTk.PhotoImage(Image.open(load_icon())))  # Set the icon for the window
toplevel.title("CvFlow")

toplevel.attributes("-fullscreen", True)  # Make the root window fullscreen
toplevel.overrideredirect(True)  # Remove window decorations

toplevel.pack_propagate(False)  # Prevent the window from resizing to fit its contents
graphics_frame = plane(toplevel)
graphics_frame.pack(fill=tk.BOTH, expand=True) 
toplevel.protocol("WM_DELETE_WINDOW", on_toplevel_close)
toplevel.bind_all("<Alt-F4>", disable_shortcuts)
toplevel.bind_all("<KeyPress>", disable_shortcuts)

root.mainloop() 
print("Tkinter demo finished.")