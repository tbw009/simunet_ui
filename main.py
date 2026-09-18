import tkinter as tk
from tkinter import ttk

class IDE(ttk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.pack(fill="both", expand=True)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        self.text=tk.Text(self, wrap='none', undo=True, font=('Consolas',11))
        self.text.grid(row=0,column=1,sticky='nsew')

        peer=f"{self.text._w}_gutter"
        self.text.tk.call(self.text._w,'peer','create',peer)
        self.gutter=tk.Text(self,name=peer.split('.')[-1])
        self.gutter.grid(row=0,column=0,sticky='ns')
        self.gutter.configure(width=6,state='disabled',bg='#f0f0f0')

        vs=ttk.Scrollbar(self,orient='vertical',command=self.text.yview)
        vs.grid(row=0,column=2,sticky='ns')
        self.text.configure(yscrollcommand=lambda a,b:(vs.set(a,b),self.gutter.yview_moveto(a)))

        self.text.bind('<KeyRelease>', self.update_gutter)
        self.update_gutter()

    def update_gutter(self,event=None):
        n=int(self.text.index('end-1c').split('.')[0])
        txt='
'.join(str(i) for i in range(1,n+1))
        self.gutter.config(state='normal')
        self.gutter.delete('1.0','end')
        self.gutter.insert('1.0',txt)
        self.gutter.config(state='disabled')

    def fold(self,start,end):
        tag=f'fold_{start}'
        self.text.tag_add(tag,f'{start+1}.0',f'{end+1}.0')
        self.text.tag_configure(tag,elide=True)

if __name__=='__main__':
    root=tk.Tk()
    root.title('Production IDE Skeleton')
    root.geometry('1200x800')
    IDE(root)
    root.mainloop()
