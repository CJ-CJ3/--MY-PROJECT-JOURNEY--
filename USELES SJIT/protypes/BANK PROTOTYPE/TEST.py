import tkinter as tk
import time

def say():
    text = tk.Label(root, text="hello", font=("Bauhaus 93", 16))
    text.pack(pady=100)
    print("f")


root = tk.Tk()
root.title("ANOTHER 1")


button = tk.Button(root,text="CLICK THIS",command=say())
button.pack()

root.mainloop()
