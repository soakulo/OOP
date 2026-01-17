import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import sys

sys.setrecursionlimit(10000)


class GameSolverApp:
    """Solver для задач теории игр с кучами камней (ЕГЭ задания 19, 21)"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Solver - Задачи теории игр (кучи камней)")
        self.root.geometry("850x750")
        self.root.minsize(750, 650)
        
        self.create_widgets()
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill='both', expand=True)
        
        ops_frame = ttk.LabelFrame(main_frame, text="1. Варианты ходов (применяются к сумме s)", padding="10")
        ops_frame.pack(fill='x', pady=5)
        
        ttk.Label(ops_frame, text="Введите операции через запятую:").pack(anchor='w')
        ttk.Label(ops_frame, 
                 text="Примеры: (s - 1), (s + 2), (s // 2), (s * 3), (s - 5)", 
                 foreground='gray').pack(anchor='w')
        
        self.ops_entry = ttk.Entry(ops_frame, width=60, font=('Consolas', 11))
        self.ops_entry.insert(0, "(s - 1), (s // 2)")
        self.ops_entry.pack(fill='x', pady=5)
        
        init_frame = ttk.LabelFrame(main_frame, text="2. Начальные условия", padding="10")
        init_frame.pack(fill='x', pady=5)
        
        pile_row = ttk.Frame(init_frame)
        pile_row.pack(fill='x', pady=3)
        ttk.Label(pile_row, text="Первая куча:", width=15).pack(side='left')
        self.pile1_entry = ttk.Entry(pile_row, width=10)
        self.pile1_entry.insert(0, "10")
        self.pile1_entry.pack(side='left', padx=5)
        ttk.Label(pile_row, text="(фиксированное значение)", foreground='gray').pack(side='left')
        
        s_row = ttk.Frame(init_frame)
        s_row.pack(fill='x', pady=3)
        ttk.Label(s_row, text="Вторая куча S:", width=15).pack(side='left')
        ttk.Label(s_row, text="от").pack(side='left')
        self.s_min_entry = ttk.Entry(s_row, width=8)
        self.s_min_entry.insert(0, "11")
        self.s_min_entry.pack(side='left', padx=3)
        ttk.Label(s_row, text="до").pack(side='left')
        self.s_max_entry = ttk.Entry(s_row, width=8)
        self.s_max_entry.insert(0, "100")
        self.s_max_entry.pack(side='left', padx=3)
        ttk.Label(s_row, text="(диапазон поиска)", foreground='gray').pack(side='left')
        
        win_frame = ttk.LabelFrame(main_frame, text="3. Условие окончания игры", padding="10")
        win_frame.pack(fill='x', pady=5)
        
        win_row = ttk.Frame(win_frame)
        win_row.pack(fill='x')
        ttk.Label(win_row, text="Игра заканчивается, когда сумма камней").pack(side='left')
        
        self.condition_var = tk.StringVar(value="<=")
        condition_combo = ttk.Combobox(win_row, textvariable=self.condition_var, 
                                       values=["<=", ">="], width=5, state="readonly")
        condition_combo.pack(side='left', padx=5)
        
        self.threshold_entry = ttk.Entry(win_row, width=10)
        self.threshold_entry.insert(0, "20")
        self.threshold_entry.pack(side='left', padx=5)
        
        task_frame = ttk.LabelFrame(main_frame, text="4. Условие задачи", padding="10")
        task_frame.pack(fill='x', pady=5)
        
        moves_row = ttk.Frame(task_frame)
        moves_row.pack(fill='x', pady=3)
        ttk.Label(moves_row, text="Номер хода победы (m):").pack(side='left')
        self.moves_entry = ttk.Entry(moves_row, width=8)
        self.moves_entry.insert(0, "2")
        self.moves_entry.pack(side='left', padx=5)
        
        explain_frame = ttk.Frame(task_frame)
        explain_frame.pack(fill='x', pady=5)
        explain_text = """  m=1: Петя выигрывает своим 1-м ходом
  m=2: Ваня выигрывает своим 1-м ходом (2-й ход в игре)
  m=3: Петя выигрывает своим 2-м ходом
  m=4: Ваня выигрывает своим 2-м ходом"""
        ttk.Label(explain_frame, text=explain_text, foreground='#555555', 
                 font=('Consolas', 9)).pack(anchor='w')
        
        check_frame = ttk.Frame(task_frame)
        check_frame.pack(fill='x', pady=8)
        
        self.is_task19_var = tk.BooleanVar(value=False)
        check19 = ttk.Checkbutton(
            check_frame, 
            text="19 — заменить all на any (неудачный ход противника)", 
            variable=self.is_task19_var
        )
        check19.pack(anchor='w')
        
        ttk.Label(check_frame, 
                 text="    (используется когда нужно найти ситуацию после 'неудачного' хода)", 
                 foreground='gray', font=('', 9)).pack(anchor='w')
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=15)
        
        solve_btn = ttk.Button(btn_frame, text="🔍 РЕШИТЬ", command=self.solve, width=15)
        solve_btn.pack(side='left', padx=5)
        
        example_btn = ttk.Button(btn_frame, text="📋 Пример из условия", 
                                command=self.load_example, width=18)
        example_btn.pack(side='left', padx=5)
        
        clear_btn = ttk.Button(btn_frame, text="🗑 Очистить", command=self.clear_output, width=12)
        clear_btn.pack(side='left', padx=5)
        
        result_frame = ttk.LabelFrame(main_frame, text="Результаты", padding="10")
        result_frame.pack(fill='both', expand=True, pady=5)
        
        self.output = ScrolledText(result_frame, height=12, wrap='word', 
                                   font=('Consolas', 10))
        self.output.pack(fill='both', expand=True)
    
    def load_example(self):
        self.ops_entry.delete(0, tk.END)
        self.ops_entry.insert(0, "(s - 1), (s // 2)")
        
        self.pile1_entry.delete(0, tk.END)
        self.pile1_entry.insert(0, "10")
        
        self.s_min_entry.delete(0, tk.END)
        self.s_min_entry.insert(0, "11")
        
        self.s_max_entry.delete(0, tk.END)
        self.s_max_entry.insert(0, "100")
        
        self.threshold_entry.delete(0, tk.END)
        self.threshold_entry.insert(0, "20")
        
        self.condition_var.set("<=")
        
        self.moves_entry.delete(0, tk.END)
        self.moves_entry.insert(0, "2")
        
        self.is_task19_var.set(True)
        
        self.output.delete(1.0, tk.END)
        self.output.insert(tk.END, "✅ Загружен пример из условия задачи:\n")
        self.output.insert(tk.END, "   • Ходы: убрать 1 камень (s-1) ИЛИ разделить на 2 (s//2)\n")
        self.output.insert(tk.END, "   • Кучи: (10, S), где S в диапазоне [11, 100]\n")
        self.output.insert(tk.END, "   • Выигрыш: сумма ≤ 20\n")
        self.output.insert(tk.END, "   • m=2: Ваня выигрывает первым ходом\n")
        self.output.insert(tk.END, "   • Режим 19: ВКЛ (после неудачного хода Пети)\n\n")
        self.output.insert(tk.END, "Нажмите '🔍 РЕШИТЬ' для поиска подходящих S\n")
    
    def clear_output(self):
        self.output.delete(1.0, tk.END)
    
    def parse_operations(self, ops_str):
        operations = []
        parts = ops_str.split(',')
        for part in parts:
            part = part.strip()
            if part.startswith('(') and part.endswith(')'):
                part = part[1:-1]
            part = part.strip()
            if part:
                operations.append(part)
        return operations
    
    def solve(self):
        try:
            pile1 = int(self.pile1_entry.get())
            s_min = int(self.s_min_entry.get())
            s_max = int(self.s_max_entry.get())
            threshold = int(self.threshold_entry.get())
            condition = self.condition_var.get()
            m = int(self.moves_entry.get())
            is_task19 = self.is_task19_var.get()
            
            operations = self.parse_operations(self.ops_entry.get())
            
            if not operations:
                raise ValueError("Укажите хотя бы одну операцию!")
            
            if s_min > s_max:
                raise ValueError("Минимум S должен быть меньше или равен максимуму!")
            
            if m < 1:
                raise ValueError("Номер хода должен быть >= 1!")
            
            def check_end(s):
                if condition == "<=":
                    return s <= threshold
                else:
                    return s >= threshold
            
            def f(s, moves, cache):
                if check_end(s):
                    return moves % 2 == 0
                
                if moves == 0:
                    return False
                
                key = (s, moves)
                if key in cache:
                    return cache[key]
                
                h = []
                for op in operations:
                    try:
                        new_s = eval(op)
                        if new_s >= 0:
                            h.append(f(new_s, moves - 1, cache))
                    except:
                        pass
                
                if not h:
                    result = False
                elif is_task19:
                    result = any(h)
                else:
                    result = any(h) if moves % 2 else all(h)
                
                cache[key] = result
                return result
            
            valid_s = []
            for s_val in range(s_min, s_max + 1):
                cache = {}
                total = pile1 + s_val
                if f(total, m, cache):
                    valid_s.append(s_val)
            
            self.output.delete(1.0, tk.END)
            
            self.output.insert(tk.END, "═" * 58 + "\n")
            self.output.insert(tk.END, "                      ПАРАМЕТРЫ ПОИСКА\n")
            self.output.insert(tk.END, "═" * 58 + "\n")
            self.output.insert(tk.END, f"  Операции:         {operations}\n")
            self.output.insert(tk.END, f"  Первая куча:      {pile1}\n")
            self.output.insert(tk.END, f"  Диапазон S:       [{s_min}, {s_max}]\n")
            self.output.insert(tk.END, f"  Условие выигрыша: сумма {condition} {threshold}\n")
            self.output.insert(tk.END, f"  Ход победы:       m = {m}")
            
            if m == 1:
                self.output.insert(tk.END, " (Петя, 1-й ход)\n")
            elif m == 2:
                self.output.insert(tk.END, " (Ваня, 1-й ход)\n")
            elif m == 3:
                self.output.insert(tk.END, " (Петя, 2-й ход)\n")
            elif m == 4:
                self.output.insert(tk.END, " (Ваня, 2-й ход)\n")
            else:
                self.output.insert(tk.END, "\n")
            
            self.output.insert(tk.END, f"  Режим 19:         {'ДА (all→any)' if is_task19 else 'НЕТ'}\n\n")
            
            self.output.insert(tk.END, "═" * 58 + "\n")
            self.output.insert(tk.END, "                        РЕЗУЛЬТАТЫ\n")
            self.output.insert(tk.END, "═" * 58 + "\n")
            
            if valid_s:
                self.output.insert(tk.END, f"  Найдено значений S: {len(valid_s)}\n\n")
                self.output.insert(tk.END, f"  Список подходящих S:\n  {valid_s}\n\n")
                self.output.insert(tk.END, "─" * 58 + "\n")
                self.output.insert(tk.END, f"  ✅ МАКСИМАЛЬНОЕ S: {max(valid_s)}\n")
                self.output.insert(tk.END, f"  ✅ МИНИМАЛЬНОЕ S:  {min(valid_s)}\n")
                self.output.insert(tk.END, "─" * 58 + "\n")
            else:
                self.output.insert(tk.END, "\n  ❌ Подходящих значений S не найдено в указанном диапазоне\n")
                
        except ValueError as e:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, f"⚠️ Ошибка ввода:\n   {e}\n")
        except RecursionError:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, "⚠️ Превышена глубина рекурсии!\n")
            self.output.insert(tk.END, "   Попробуйте уменьшить диапазон или изменить параметры.\n")
        except Exception as e:
            self.output.delete(1.0, tk.END)
            self.output.insert(tk.END, f"❌ Ошибка: {e}\n")


class Application:
    
    def __init__(self):
        self.root = tk.Tk()
        self.app = GameSolverApp(self.root)
    
    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    application = Application()
    application.run()