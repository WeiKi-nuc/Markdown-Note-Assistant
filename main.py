import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.ui.ui_manager import UIManager


def main():
    root = tk.Tk()
    app = UIManager(root)
    
    try:
        root.iconbitmap(default='')
    except:
        pass
    
    root.mainloop()


if __name__ == "__main__":
    main()
