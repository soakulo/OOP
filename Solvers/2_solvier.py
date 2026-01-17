import tkinter as tk
from tkinter import ttk, messagebox
from itertools import permutations
import re


class TruthTableAnalyzer:
    """Класс для анализа таблиц истинности"""
    
    def __init__(self):
        self.variables = ['a', 'b', 'c', 'd']
    
    def safe_eval(self, expr, values):
        """Безопасное вычисление логического выражения"""
        # Функции для логических операций
        def imp(x, y):
            """Импликация: x -> y = (not x) or y"""
            return (not x) or y
        
        def eq(x, y):
            """Эквивалентность: x <-> y"""
            return x == y
        
        # Локальное пространство имен
        local_vars = {
            'a': values.get('a', False),
            'b': values.get('b', False),
            'c': values.get('c', False),
            'd': values.get('d', False),
            'True': True,
            'False': False,
            'imp': imp,
            'eq': eq,
        }
        
        # Предобработка выражения
        processed = expr.strip()
        
        # Заменяем символы на Python-совместимые
        replacements = [
            ('→', ' imp '), ('⇒', ' imp '), ('⊃', ' imp '), ('->', ' imp '),
            ('≡', ' eq '), ('↔', ' eq '), ('<->', ' eq '),
            ('∧', ' and '), ('&&', ' and '), ('&', ' and '), 
            ('·', ' and '), ('*', ' and '),
            ('∨', ' or '), ('||', ' or '), ('|', ' or '), ('+', ' or '),
            ('¬', ' not '), ('!', ' not '), ('~', ' not '),
        ]
        
        for old, new in replacements:
            processed = processed.replace(old, new)
        
        # Обработка импликации в формате (a) <= (b)
        # Заменяем на imp(a, b)
        max_iterations = 50
        iteration = 0
        while '<=' in processed and iteration < max_iterations:
            # Паттерн для простых выражений
            new_expr = re.sub(
                r'(\([^()]+\)|[a-d])\s*<=\s*(\([^()]+\)|[a-d])',
                r'imp(\1, \2)',
                processed
            )
            if new_expr == processed:
                break
            processed = new_expr
            iteration += 1
        
        # Обработка оставшихся <= внутри скобок
        while '<=' in processed and iteration < max_iterations:
            processed = re.sub(r'(\w+)\s*<=\s*(\w+)', r'imp(\1, \2)', processed)
            iteration += 1
        
        try:
            result = eval(processed, {"__builtins__": {}}, local_vars)
            return bool(result)
        except Exception as e:
            print(f"Ошибка вычисления: {e}")
            print(f"Исходное выражение: {expr}")
            print(f"Обработанное: {processed}")
            return False
    
    def generate_full_truth_table(self, expr):
        """Генерирует полную таблицу истинности для 4 переменных"""
        truth_table = [['a', 'b', 'c', 'd', 'F']]
        
        # Генерируем все 16 комбинаций
        for i in range(16):
            a = (i >> 3) & 1
            b = (i >> 2) & 1
            c = (i >> 1) & 1
            d = i & 1
            
            values = {
                'a': bool(a),
                'b': bool(b),
                'c': bool(c),
                'd': bool(d)
            }
            
            result = self.safe_eval(expr, values)
            row = [str(a), str(b), str(c), str(d), '1' if result else '0']
            truth_table.append(row)
        
        return truth_table
    
    def find_all_mappings(self, full_table, fragment):
        """Находит все возможные соответствия столбцов переменным"""
        mappings = []
        
        for var_order in permutations(['a', 'b', 'c', 'd']):
            if self._check_mapping(full_table, fragment, var_order):
                mappings.append(var_order)
        
        return mappings
    
    def _check_mapping(self, full_table, fragment, var_order):
        """Проверяет конкретное соответствие переменных столбцам"""
        for frag_row in fragment:
            # Пропускаем полностью пустые строки
            if all(cell == '' for cell in frag_row):
                continue
            
            found = False
            
            for full_row in full_table[1:]:  # Пропускаем заголовок
                match = True
                
                # Проверяем первые 4 столбца (переменные)
                for col in range(4):
                    frag_value = frag_row[col]
                    if frag_value in ['0', '1']:
                        var_name = var_order[col]
                        var_idx = ord(var_name) - ord('a')
                        
                        if full_row[var_idx] != frag_value:
                            match = False
                            break
                
                # Проверяем столбец функции
                if match and len(frag_row) > 4:
                    frag_func = frag_row[4]
                    if frag_func in ['0', '1']:
                        if full_row[4] != frag_func:
                            match = False
                
                if match:
                    found = True
                    break
            
            if not found:
                return False
        
        return True
    
    def complete_fragment(self, full_table, fragment, var_order):
        """Достраивает фрагмент таблицы на основе найденного соответствия"""
        completed = []
        
        for frag_row in fragment:
            # Пропускаем полностью пустые строки
            if all(cell == '' for cell in frag_row):
                completed.append(['', '', '', '', ''])
                continue
            
            # Ищем соответствующую строку в полной таблице
            found_row = None
            for full_row in full_table[1:]:
                match = True
                
                for col in range(4):
                    frag_value = frag_row[col]
                    if frag_value in ['0', '1']:
                        var_name = var_order[col]
                        var_idx = ord(var_name) - ord('a')
                        
                        if full_row[var_idx] != frag_value:
                            match = False
                            break
                
                if match and len(frag_row) > 4:
                    frag_func = frag_row[4]
                    if frag_func in ['0', '1']:
                        if full_row[4] != frag_func:
                            match = False
                
                if match:
                    found_row = full_row
                    break
            
            if found_row:
                # Достраиваем строку
                new_row = []
                for col in range(4):
                    var_name = var_order[col]
                    var_idx = ord(var_name) - ord('a')
                    new_row.append(found_row[var_idx])
                new_row.append(found_row[4])
                completed.append(new_row)
            else:
                # Не нашли - оставляем как есть
                completed.append(frag_row[:])
        
        return completed


class LogicTableApp:
    """Главное приложение"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Анализатор таблиц истинности")
        self.root.geometry("750x700")
        self.root.resizable(True, True)
        
        self.analyzer = TruthTableAnalyzer()
        self.num_rows = 3
        self.entries = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Создает интерфейс"""
        # Основной контейнер с прокруткой
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Заголовок
        title = tk.Label(main_frame, 
                        text="Определение соответствия переменных столбцам", 
                        font=("Arial", 14, "bold"))
        title.pack(pady=5)
        
        # === Блок ввода выражения ===
        expr_frame = tk.LabelFrame(main_frame, text="Логическое выражение", 
                                   padx=10, pady=10)
        expr_frame.pack(fill="x", pady=5)
        
        help_text = """Используйте переменные a, b, c, d и операторы:
• AND: and, &, ∧, ·, *
• OR: or, |, ∨, +  
• NOT: not, !, ¬, ~
• Импликация: ->, →, <=
• Эквивалентность: ==, ↔, ≡"""
        
        tk.Label(expr_frame, text=help_text, font=("Arial", 9), 
                justify="left", fg="gray").pack(anchor="w")
        
        self.expr_var = tk.StringVar()
        self.expr_entry = tk.Entry(expr_frame, textvariable=self.expr_var, 
                                   width=60, font=("Consolas", 11))
        self.expr_entry.pack(fill="x", pady=5)
        
        # Примеры выражений
        examples_frame = tk.Frame(expr_frame)
        examples_frame.pack(fill="x")
        tk.Label(examples_frame, text="Примеры:", font=("Arial", 9)).pack(side="left")
        
        examples = [
            ("a and b", "a and b"),
            ("a -> b", "(a) <= (b)"),
            ("(a→b)∧c", "((a) <= (b)) and c"),
        ]
        for text, expr in examples:
            btn = tk.Button(examples_frame, text=text, font=("Arial", 8),
                           command=lambda e=expr: self.expr_var.set(e))
            btn.pack(side="left", padx=2)
        
        # === Настройка количества строк ===
        rows_frame = tk.Frame(main_frame)
        rows_frame.pack(fill="x", pady=5)
        
        tk.Label(rows_frame, text="Количество строк:").pack(side="left")
        self.rows_spinbox = tk.Spinbox(rows_frame, from_=1, to=16, width=5,
                                       command=self._update_table_rows)
        self.rows_spinbox.delete(0, tk.END)
        self.rows_spinbox.insert(0, "3")
        self.rows_spinbox.pack(side="left", padx=5)
        
        tk.Button(rows_frame, text="Применить", 
                 command=self._update_table_rows).pack(side="left")
        
        # === Таблица ввода ===
        self.table_frame = tk.LabelFrame(main_frame, 
                                         text="Фрагмент таблицы истинности", 
                                         padx=10, pady=10)
        self.table_frame.pack(fill="x", pady=5)
        
        self._create_input_table()
        
        # === Кнопки управления ===
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        self.solve_btn = tk.Button(btn_frame, text="🔍 Найти соответствие", 
                                   command=self.solve, bg="#4CAF50", fg="white",
                                   font=("Arial", 11, "bold"), width=20, height=2)
        self.solve_btn.pack(side="left", padx=5)
        
        self.show_full_btn = tk.Button(btn_frame, text="📋 Показать полную таблицу",
                                       command=self.show_full_table,
                                       font=("Arial", 10))
        self.show_full_btn.pack(side="left", padx=5)
        
        self.clear_btn = tk.Button(btn_frame, text="🗑 Очистить", 
                                   command=self.clear, font=("Arial", 10))
        self.clear_btn.pack(side="left", padx=5)
        
        # === Результат ===
        result_frame = tk.LabelFrame(main_frame, text="Результат", padx=10, pady=10)
        result_frame.pack(fill="x", pady=5)
        
        self.result_text = tk.StringVar()
        self.result_label = tk.Label(result_frame, textvariable=self.result_text,
                                     font=("Arial", 28, "bold"), fg="#2196F3")
        self.result_label.pack()
        
        self.info_label = tk.Label(result_frame, text="", font=("Arial", 10), fg="gray")
        self.info_label.pack()
        
        # === Достроенная таблица ===
        self.completed_frame = tk.LabelFrame(main_frame, 
                                             text="Достроенная таблица", 
                                             padx=10, pady=10)
        self.completed_frame.pack(fill="both", expand=True, pady=5)
    
    def _create_input_table(self):
        """Создает таблицу ввода"""
        # Очищаем старую таблицу
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        self.entries = []
        
        # Заголовки столбцов
        headers = ["Столбец 1", "Столбец 2", "Столбец 3", "Столбец 4", "F"]
        for col, header in enumerate(headers):
            label = tk.Label(self.table_frame, text=header, width=10, 
                            relief="ridge", bg="#e0e0e0", 
                            font=("Arial", 9, "bold"))
            label.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
        
        # Номера строк и поля ввода
        for row in range(self.num_rows):
            # Номер строки
            row_label = tk.Label(self.table_frame, text=f"{row+1}", width=3,
                                relief="ridge", bg="#f0f0f0")
            row_label.grid(row=row+1, column=5, sticky="nsew", padx=1, pady=1)
            
            row_entries = []
            for col in range(5):
                entry = tk.Entry(self.table_frame, width=10, justify='center', 
                               font=("Arial", 11))
                entry.grid(row=row+1, column=col, sticky="nsew", padx=1, pady=1)
                
                # Валидация ввода (только 0, 1 или пусто)
                entry.bind('<KeyRelease>', self._validate_entry)
                row_entries.append(entry)
            self.entries.append(row_entries)
        
        # Настройка размеров
        for i in range(6):
            self.table_frame.grid_columnconfigure(i, weight=1)
    
    def _validate_entry(self, event):
        """Валидация ввода в ячейку"""
        entry = event.widget
        value = entry.get()
        if value and value not in ['0', '1']:
            entry.delete(0, tk.END)
            if value[0] in ['0', '1']:
                entry.insert(0, value[0])
    
    def _update_table_rows(self):
        """Обновляет количество строк в таблице"""
        try:
            new_rows = int(self.rows_spinbox.get())
            if 1 <= new_rows <= 16:
                self.num_rows = new_rows
                self._create_input_table()
        except ValueError:
            pass
    
    def get_fragment_data(self):
        """Получает данные из таблицы"""
        fragment = []
        for row_entries in self.entries:
            row = []
            for entry in row_entries:
                value = entry.get().strip()
                row.append(value if value in ['0', '1'] else '')
            fragment.append(row)
        return fragment
    
    def solve(self):
        """Решает задачу"""
        expr = self.expr_var.get().strip()
        fragment = self.get_fragment_data()
        
        if not expr:
            self.result_text.set("⚠ Введите выражение!")
            self.info_label.config(text="")
            return
        
        # Проверяем, есть ли данные в таблице
        has_data = any(cell in ['0', '1'] 
                       for row in fragment for cell in row)
        
        if not has_data:
            self.result_text.set("⚠ Заполните таблицу!")
            self.info_label.config(text="")
            return
        
        try:
            # Генерируем полную таблицу истинности
            full_table = self.analyzer.generate_full_truth_table(expr)
            
            # Ищем соответствия
            mappings = self.analyzer.find_all_mappings(full_table, fragment)
            
            if not mappings:
                self.result_text.set("❌ Нет решения!")
                self.info_label.config(text="Фрагмент не соответствует выражению")
                self._clear_completed_table()
                return
            
            # Берем первое найденное соответствие
            var_order = mappings[0]
            answer = ''.join(var_order)
            self.result_text.set(answer)
            
            # Информация о найденных решениях
            if len(mappings) > 1:
                all_answers = [' '.join(m) for m in mappings]
                self.info_label.config(
                    text=f"Найдено решений: {len(mappings)} | Все: {', '.join(all_answers)}"
                )
            else:
                self.info_label.config(text="Единственное решение ✓")
            
            # Достраиваем и показываем таблицу
            completed = self.analyzer.complete_fragment(full_table, fragment, var_order)
            self._display_completed_table(completed, var_order)
            
            # Отладочная информация
            print(f"Выражение: {expr}")
            print(f"Найдено соответствий: {len(mappings)}")
            print(f"Ответ: {answer}")
            
        except Exception as e:
            self.result_text.set(f"⚠ Ошибка!")
            self.info_label.config(text=str(e))
            print(f"Ошибка: {e}")
            import traceback
            traceback.print_exc()
    
    def _display_completed_table(self, completed, var_order):
        """Отображает достроенную таблицу"""
        # Очищаем предыдущую таблицу
        self._clear_completed_table()
        
        # Заголовки с именами переменных
        headers = list(var_order) + ['F']
        for col, h in enumerate(headers):
            lbl = tk.Label(self.completed_frame, text=h, width=10, 
                          relief="ridge", bg="#d0e0f0", 
                          font=("Arial", 10, "bold"))
            lbl.grid(row=0, column=col, sticky="nsew", padx=1, pady=1)
        
        # Данные
        original_fragment = self.get_fragment_data()
        
        for row_idx, row in enumerate(completed):
            for col_idx, val in enumerate(row):
                # Определяем, была ли ячейка заполнена пользователем
                original_val = original_fragment[row_idx][col_idx] if row_idx < len(original_fragment) else ''
                
                if original_val in ['0', '1']:
                    bg_color = "#ffffff"  # Белый для введенных данных
                else:
                    bg_color = "#e8f5e9"  # Светло-зеленый для достроенных
                
                lbl = tk.Label(self.completed_frame, text=val, width=10,
                              relief="ridge", font=("Arial", 11), bg=bg_color)
                lbl.grid(row=row_idx+1, column=col_idx, sticky="nsew", padx=1, pady=1)
        
        # Легенда
        legend_frame = tk.Frame(self.completed_frame)
        legend_frame.grid(row=len(completed)+1, column=0, columnspan=5, pady=5)
        
        tk.Label(legend_frame, text="█", fg="#e8f5e9", bg="#e8f5e9").pack(side="left")
        tk.Label(legend_frame, text=" - достроенные значения", 
                font=("Arial", 8)).pack(side="left")
    
    def _clear_completed_table(self):
        """Очищает достроенную таблицу"""
        for widget in self.completed_frame.winfo_children():
            widget.destroy()
    
    def show_full_table(self):
        """Показывает полную таблицу истинности в новом окне"""
        expr = self.expr_var.get().strip()
        if not expr:
            messagebox.showwarning("Внимание", "Введите логическое выражение!")
            return
        
        try:
            full_table = self.analyzer.generate_full_truth_table(expr)
            
            # Создаем новое окно
            window = tk.Toplevel(self.root)
            window.title("Полная таблица истинности")
            window.geometry("400x500")
            
            # Заголовок
            tk.Label(window, text=f"F = {expr}", font=("Arial", 10, "bold"),
                    wraplength=380).pack(pady=5)
            
            # Таблица
            table_frame = tk.Frame(window)
            table_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            for row_idx, row in enumerate(full_table):
                for col_idx, val in enumerate(row):
                    if row_idx == 0:
                        lbl = tk.Label(table_frame, text=val, width=6,
                                      relief="ridge", bg="#e0e0e0",
                                      font=("Arial", 10, "bold"))
                    else:
                        bg = "#e8f5e9" if val == '1' and col_idx == 4 else "#ffffff"
                        lbl = tk.Label(table_frame, text=val, width=6,
                                      relief="ridge", font=("Arial", 10), bg=bg)
                    lbl.grid(row=row_idx, column=col_idx, sticky="nsew")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось построить таблицу: {e}")
    
    def clear(self):
        """Очищает все поля"""
        self.expr_var.set("")
        for row in self.entries:
            for entry in row:
                entry.delete(0, tk.END)
        self.result_text.set("")
        self.info_label.config(text="")
        self._clear_completed_table()


# Запуск приложения
if __name__ == "__main__":
    root = tk.Tk()
    app = LogicTableApp(root)
    root.mainloop()