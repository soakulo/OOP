import tkinter as tk
from tkinter import messagebox


class TableApp:
    def __init__(self, root):
            self.root = root
            
    def show_table():
          pass
    

class LogicTable(TableApp):
    def __init__(self, root):
        super().__init__(root)

        self.label = tk.Label(root, text="Введите выражение (a, b, and, or, not, ==, <=):")
        self.label.pack(pady=10)
        
        self.entry = tk.Entry(root, width=30)
        self.entry.pack(pady=10)
        
        self.button = tk.Button(root, text="Показать таблицу", command=self.show_table)
        self.button.pack(pady=10)
        
        self.result = tk.Text(root, height=8, width=40)
        self.result.pack(pady=10)

    def show_table(self):
        self.result.delete(1.0, tk.END)
        expr = self.entry.get().strip()
        
        if not expr:
            messagebox.showerror("Ошибка", "Введите выражение!")
            return
        

        has_b = 'b' in expr
        
        try:
                if has_b:
                    self.result.insert(tk.END, "a | b | Результат\n")
                    self.result.insert(tk.END, "-------------\n")
                    for a in [True, False]:
                        for b in [True, False]:
                            result = eval(expr, {}, {'a': a, 'b': b})
                            self.result.insert(tk.END, f"{int(a)} | {int(b)} | {int(result)}\n")
                else:
                    self.result.insert(tk.END, "a | Результат\n")
                    self.result.insert(tk.END, "---------\n")
                    for a in [True, False]:
                        result = eval(expr, {}, {'a': a})
                        self.result.insert(tk.END, f"{int(a)} | {int(result)}\n")
        except:
                messagebox.showerror("Ошибка", "Неправильное выражение!")


if __name__ == "__main__":
      root = tk.Tk()
      app = LogicTable(root)
      root.mainloop()