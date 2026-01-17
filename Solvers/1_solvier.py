import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Tuple, Optional, Set
import heapq


class GraphMatcher:
    """Класс для сопоставления двух графов и поиска соответствия вершин"""
    
    VERTEX_LETTERS = ['А', 'Б', 'В', 'Г', 'Д', 'Е', 'К']
    
    def __init__(self):
        self.weighted_matrix: List[List[float]] = []
        self.structure_matrix: List[List[int]] = []
        self.num_vertices: int = 0
        
        self.letter_to_digit: Dict[str, int] = {}
        self.digit_to_letter: Dict[int, str] = {}
    
    def set_matrices(self, weighted: List[List[float]], structure: List[List[int]]) -> bool:
        """Установка обеих матриц и автоматическое сопоставление"""
        if len(weighted) != len(structure):
            return False
        
        if len(weighted) > len(self.VERTEX_LETTERS):
            return False
        
        self.weighted_matrix = weighted
        self.structure_matrix = structure
        self.num_vertices = len(weighted)
        
        return self._find_mapping()
    
    def _get_adjacency_structure(self, matrix: List[List[float]]) -> List[Set[int]]:
        """Получение структуры смежности"""
        n = len(matrix)
        adjacency = []
        for i in range(n):
            neighbors = set()
            for j in range(n):
                if matrix[i][j] > 0 and i != j:
                    neighbors.add(j)
            adjacency.append(neighbors)
        return adjacency
    
    def _find_mapping(self) -> bool:
        """Поиск соответствия между вершинами"""
        n = self.num_vertices
        
        weighted_adj = self._get_adjacency_structure(self.weighted_matrix)
        structure_adj = self._get_adjacency_structure(self.structure_matrix)
        
        # Группировка по степеням
        weighted_by_degree: Dict[int, List[int]] = {}
        for i in range(n):
            degree = len(weighted_adj[i])
            weighted_by_degree.setdefault(degree, []).append(i)
        
        structure_by_degree: Dict[int, List[int]] = {}
        for i in range(n):
            degree = len(structure_adj[i])
            structure_by_degree.setdefault(degree, []).append(i)
        
        # Проверка совпадения степеней
        if set(weighted_by_degree.keys()) != set(structure_by_degree.keys()):
            return False
        
        for degree in weighted_by_degree:
            if len(weighted_by_degree[degree]) != len(structure_by_degree[degree]):
                return False
        
        # Поиск изоморфизма
        mapping = self._backtrack_mapping(weighted_adj, structure_adj, weighted_by_degree)
        
        if mapping:
            self.letter_to_digit.clear()
            self.digit_to_letter.clear()
            
            for struct_idx, weight_idx in enumerate(mapping):
                letter = self.VERTEX_LETTERS[struct_idx]
                self.letter_to_digit[letter] = weight_idx
                self.digit_to_letter[weight_idx] = letter
            
            return True
        
        return False
    
    def _backtrack_mapping(
        self,
        weighted_adj: List[Set[int]],
        structure_adj: List[Set[int]],
        weighted_by_degree: Dict[int, List[int]]
    ) -> Optional[List[int]]:
        """Поиск изоморфизма перебором с возвратом"""
        n = self.num_vertices
        mapping = [-1] * n
        used_weighted = [False] * n
        
        def is_consistent(struct_idx: int, weighted_idx: int) -> bool:
            for neighbor in structure_adj[struct_idx]:
                if mapping[neighbor] != -1:
                    if mapping[neighbor] not in weighted_adj[weighted_idx]:
                        return False
            
            for neighbor in weighted_adj[weighted_idx]:
                mapped_structs = [i for i in range(n) if mapping[i] == neighbor]
                if mapped_structs:
                    if mapped_structs[0] not in structure_adj[struct_idx]:
                        return False
            
            return True
        
        def backtrack(struct_idx: int) -> bool:
            if struct_idx == n:
                return True
            
            degree = len(structure_adj[struct_idx])
            candidates = weighted_by_degree.get(degree, [])
            
            for weighted_idx in candidates:
                if not used_weighted[weighted_idx] and is_consistent(struct_idx, weighted_idx):
                    mapping[struct_idx] = weighted_idx
                    used_weighted[weighted_idx] = True
                    
                    if backtrack(struct_idx + 1):
                        return True
                    
                    mapping[struct_idx] = -1
                    used_weighted[weighted_idx] = False
            
            return False
        
        return mapping if backtrack(0) else None
    
    def get_distance(self, letter1: str, letter2: str) -> Optional[float]:
        """Получение расстояния между вершинами"""
        letter1, letter2 = letter1.upper(), letter2.upper()
        
        if letter1 not in self.letter_to_digit or letter2 not in self.letter_to_digit:
            return None
        
        idx1 = self.letter_to_digit[letter1]
        idx2 = self.letter_to_digit[letter2]
        
        if idx1 == idx2:
            return 0
        
        weight = self.weighted_matrix[idx1][idx2]
        return weight if weight > 0 else None
    
    def dijkstra(self, letter1: str, letter2: str) -> Tuple[Optional[float], List[str]]:
        """Кратчайший путь"""
        letter1, letter2 = letter1.upper(), letter2.upper()
        
        if letter1 not in self.letter_to_digit or letter2 not in self.letter_to_digit:
            return None, []
        
        start = self.letter_to_digit[letter1]
        end = self.letter_to_digit[letter2]
        
        if start == end:
            return 0, [letter1]
        
        n = self.num_vertices
        distances = [float('inf')] * n
        distances[start] = 0
        previous = [-1] * n
        visited = [False] * n
        
        pq = [(0, start)]
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if visited[current]:
                continue
            visited[current] = True
            
            if current == end:
                break
            
            for neighbor in range(n):
                weight = self.weighted_matrix[current][neighbor]
                if weight > 0 and not visited[neighbor]:
                    new_dist = current_dist + weight
                    if new_dist < distances[neighbor]:
                        distances[neighbor] = new_dist
                        previous[neighbor] = current
                        heapq.heappush(pq, (new_dist, neighbor))
        
        if distances[end] == float('inf'):
            return None, []
        
        path = []
        current = end
        while current != -1:
            path.append(self.digit_to_letter[current])
            current = previous[current]
        path.reverse()
        
        return distances[end], path
    
    def get_mapping_info(self) -> str:
        """Информация о сопоставлении"""
        if not self.letter_to_digit:
            return "Сопоставление не найдено"
        
        lines = ["Найденное соответствие:"]
        lines.append("─" * 25)
        
        for letter in self.VERTEX_LETTERS[:self.num_vertices]:
            digit = self.letter_to_digit[letter]
            lines.append(f"  {letter} (буква) ↔ {digit} (цифра)")
        
        return '\n'.join(lines)
    
    def get_edges_info(self) -> str:
        """Информация о рёбрах"""
        if not self.letter_to_digit:
            return "Сначала загрузите матрицы"
        
        edges = []
        for i in range(self.num_vertices):
            for j in range(i + 1, self.num_vertices):
                weight = self.weighted_matrix[i][j]
                if weight > 0:
                    letter_i = self.digit_to_letter[i]
                    letter_j = self.digit_to_letter[j]
                    edges.append((letter_i, letter_j, weight))
        
        if not edges:
            return "Нет рёбер"
        
        lines = [f"Рёбра графа ({len(edges)} шт.):"]
        lines.append("─" * 25)
        for l1, l2, w in sorted(edges):
            w_str = int(w) if w == int(w) else w
            lines.append(f"  {l1} ↔ {l2} : вес {w_str}")
        
        return '\n'.join(lines)
    
    def get_available_letters(self) -> List[str]:
        """Доступные буквы"""
        return self.VERTEX_LETTERS[:self.num_vertices]


class GraphApp:
    """Основной класс приложения"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Сопоставление графов (А, Б, В, Г, Д, Е, К)")
        self.root.geometry("1100x800")
        self.root.configure(bg='#f0f0f0')
        
        self.matcher = GraphMatcher()
        
        self._create_widgets()
        self._load_default_example()
    
    def _create_widgets(self) -> None:
        """Создание интерфейса"""
        # Заголовок
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(
            header_frame,
            text="🔍 Сопоставление графов и поиск расстояния",
            font=('Arial', 14, 'bold')
        ).pack()
        
        ttk.Label(
            header_frame,
            text="Поддерживаемые вершины: А, Б, В, Г, Д, Е, К (до 7 вершин)",
            font=('Arial', 10),
            foreground='gray'
        ).pack()
        
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя часть - ввод матриц
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        
        self._create_matrix_inputs(top_frame)
        
        # Нижняя часть - результаты
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill=tk.BOTH, expand=True)
        
        self._create_results_section(bottom_frame)
    
    def _create_matrix_inputs(self, parent: ttk.Frame) -> None:
        """Поля ввода матриц"""
        # Матрица с весами
        weighted_frame = ttk.LabelFrame(
            parent,
            text="📊 Матрица с весами (вершины: 0, 1, 2, ...)",
            padding="10"
        )
        weighted_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        ttk.Label(
            weighted_frame,
            text="Матрица смежности с весами рёбер\n"
                 "(строки через ';' или Enter, элементы через ',')",
            foreground='gray'
        ).pack(anchor='w')
        
        self.weighted_text = tk.Text(
            weighted_frame,
            height=10,
            width=40,
            font=('Consolas', 10)
        )
        self.weighted_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Матрица структуры
        structure_frame = ttk.LabelFrame(
            parent,
            text="📋 Матрица структуры (вершины: А, Б, В, Г, Д, Е, К)",
            padding="10"
        )
        structure_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        ttk.Label(
            structure_frame,
            text="Матрица связности (0/1)\n"
                 "1 = есть ребро, 0 = нет ребра",
            foreground='gray'
        ).pack(anchor='w')
        
        self.structure_text = tk.Text(
            structure_frame,
            height=10,
            width=40,
            font=('Consolas', 10)
        )
        self.structure_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Кнопки
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        ttk.Button(
            btn_frame,
            text="🔄 Сопоставить\nграфы",
            command=self._match_graphs,
            width=15
        ).pack(pady=5)
        
        ttk.Button(
            btn_frame,
            text="📝 Пример\n(5 вершин)",
            command=self._load_default_example,
            width=15
        ).pack(pady=5)
        
        ttk.Button(
            btn_frame,
            text="📝 Пример\n(7 вершин)",
            command=self._load_7vertex_example,
            width=15
        ).pack(pady=5)
        
        ttk.Button(
            btn_frame,
            text="🗑️ Очистить",
            command=self._clear_all,
            width=15
        ).pack(pady=5)
    
    def _create_results_section(self, parent: ttk.Frame) -> None:
        """Секция результатов"""
        # Левая часть
        left_frame = ttk.Frame(parent)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Сопоставление
        mapping_frame = ttk.LabelFrame(left_frame, text="🔗 Сопоставление вершин", padding="10")
        mapping_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mapping_text = tk.Text(
            mapping_frame,
            height=9,
            width=30,
            font=('Consolas', 11),
            state='disabled',
            bg='#e8f4e8'
        )
        self.mapping_text.pack(fill=tk.X)
        
        # Рёбра
        edges_frame = ttk.LabelFrame(left_frame, text="📐 Рёбра графа", padding="10")
        edges_frame.pack(fill=tk.BOTH, expand=True)
        
        self.edges_text = tk.Text(
            edges_frame,
            height=10,
            width=30,
            font=('Consolas', 10),
            state='disabled',
            bg='#e8e8f4'
        )
        self.edges_text.pack(fill=tk.BOTH, expand=True)
        
        # Правая часть
        right_frame = ttk.Frame(parent)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        
        # Поиск
        search_frame = ttk.LabelFrame(right_frame, text="🎯 Поиск расстояния", padding="15")
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.hint_label = ttk.Label(
            search_frame,
            text="Сначала сопоставьте графы",
            foreground='gray',
            font=('Arial', 10)
        )
        self.hint_label.pack(pady=5)
        
        # Ввод
        input_grid = ttk.Frame(search_frame)
        input_grid.pack(pady=10)
        
        ttk.Label(input_grid, text="Начальная вершина:", font=('Arial', 11)).grid(
            row=0, column=0, sticky='e', padx=5, pady=5
        )
        self.vertex1_entry = ttk.Entry(input_grid, width=8, font=('Arial', 14))
        self.vertex1_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(input_grid, text="Конечная вершина:", font=('Arial', 11)).grid(
            row=1, column=0, sticky='e', padx=5, pady=5
        )
        self.vertex2_entry = ttk.Entry(input_grid, width=8, font=('Arial', 14))
        self.vertex2_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Кнопки поиска
        btn_frame = ttk.Frame(search_frame)
        btn_frame.pack(pady=10)
        
        ttk.Button(
            btn_frame,
            text="📏 Прямое расстояние",
            command=self._find_direct
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            btn_frame,
            text="🛤️ Кратчайший путь",
            command=self._find_shortest
        ).pack(side=tk.LEFT, padx=5)
        
        # Результат
        result_frame = ttk.LabelFrame(right_frame, text="📊 Результат", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True)
        
        self.result_text = tk.Text(
            result_frame,
            height=15,
            width=40,
            font=('Arial', 11),
            state='disabled',
            bg='#fffef0'
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def _load_default_example(self) -> None:
        """Пример с 5 вершинами"""
        weighted = """0, 4, 2, 0, 0
4, 0, 1, 5, 0
2, 1, 0, 8, 10
0, 5, 8, 0, 2
0, 0, 10, 2, 0"""
        
        structure = """0, 1, 1, 1, 1
1, 0, 1, 0, 0
1, 1, 0, 0, 1
1, 0, 0, 0, 1
1, 0, 1, 1, 0"""
        
        self.weighted_text.delete('1.0', tk.END)
        self.weighted_text.insert('1.0', weighted)
        
        self.structure_text.delete('1.0', tk.END)
        self.structure_text.insert('1.0', structure)
        
        self._show_result("Загружен пример (5 вершин: А, Б, В, Г, Д).\n\nНажмите 'Сопоставить графы'.")
    
    def _load_7vertex_example(self) -> None:
        """Пример с 7 вершинами"""
        weighted = """0, 3, 0, 7, 0, 0, 0
3, 0, 4, 2, 0, 0, 0
0, 4, 0, 5, 6, 0, 0
7, 2, 5, 0, 0, 1, 0
0, 0, 6, 0, 0, 8, 2
0, 0, 0, 1, 8, 0, 9
0, 0, 0, 0, 2, 9, 0"""
        
        structure = """0, 1, 1, 1, 1, 0, 0
1, 0, 1, 1, 0, 0, 0
1, 1, 0, 0, 0, 0, 0
1, 1, 0, 0, 0, 1, 0
1, 0, 0, 0, 0, 1, 1
0, 0, 0, 1, 1, 0, 1
0, 0, 0, 0, 1, 1, 0"""
        
        self.weighted_text.delete('1.0', tk.END)
        self.weighted_text.insert('1.0', weighted)
        
        self.structure_text.delete('1.0', tk.END)
        self.structure_text.insert('1.0', structure)
        
        self._show_result("Загружен пример (7 вершин: А, Б, В, Г, Д, Е, К).\n\nНажмите 'Сопоставить графы'.")
    
    def _clear_all(self) -> None:
        """Очистка"""
        self.weighted_text.delete('1.0', tk.END)
        self.structure_text.delete('1.0', tk.END)
        self.vertex1_entry.delete(0, tk.END)
        self.vertex2_entry.delete(0, tk.END)
        
        self._update_text(self.mapping_text, "")
        self._update_text(self.edges_text, "")
        self._show_result("")
        self.hint_label.config(text="Введите матрицы и сопоставьте графы")
    
    def _parse_matrix(self, text: str) -> List[List[float]]:
        """Парсинг матрицы из текста"""
        text = text.strip()
        
        # Заменяем переносы строк на точку с запятой для унификации
        text = text.replace('\n', ';')
        
        # Разбиваем по точке с запятой
        rows = text.split(';')
        
        matrix = []
        for row in rows:
            row = row.strip()
            # Пропускаем пустые строки
            if not row:
                continue
            # Парсим значения
            values = []
            for x in row.split(','):
                x = x.strip()
                if x:  # Пропускаем пустые значения
                    values.append(float(x))
            if values:  # Добавляем только непустые строки
                matrix.append(values)
        
        # Проверки
        n = len(matrix)
        if n == 0:
            raise ValueError("Матрица пуста")
        if n > 7:
            raise ValueError(f"Максимум 7 вершин, получено {n}")
        
        for i, row in enumerate(matrix):
            if len(row) != n:
                raise ValueError(f"Строка {i+1}: получено {len(row)} элементов, ожидается {n}")
        
        return matrix
    
    def _match_graphs(self) -> None:
        """Сопоставление графов"""
        try:
            weighted = self._parse_matrix(self.weighted_text.get('1.0', tk.END))
            structure = self._parse_matrix(self.structure_text.get('1.0', tk.END))
            
            if len(weighted) != len(structure):
                messagebox.showerror(
                    "Ошибка",
                    f"Размеры матриц не совпадают!\n"
                    f"Матрица с весами: {len(weighted)}×{len(weighted)}\n"
                    f"Матрица структуры: {len(structure)}×{len(structure)}"
                )
                return
            
            # Бинаризация структурной матрицы
            structure_binary = [[1 if x > 0 else 0 for x in row] for row in structure]
            
            success = self.matcher.set_matrices(weighted, structure_binary)
            
            if success:
                self._update_text(self.mapping_text, self.matcher.get_mapping_info())
                self._update_text(self.edges_text, self.matcher.get_edges_info())
                
                available = ', '.join(self.matcher.get_available_letters())
                self.hint_label.config(text=f"Доступные вершины: {available}")
                
                self._show_result(
                    "✅ ГРАФЫ УСПЕШНО СОПОСТАВЛЕНЫ!\n\n"
                    f"Найдено соответствие для {self.matcher.num_vertices} вершин.\n\n"
                    f"Используйте буквы: {available}\n\n"
                    "Теперь можно искать расстояние."
                )
            else:
                self._update_text(self.mapping_text, "❌ Соответствие не найдено")
                self._update_text(self.edges_text, "")
                self._show_result(
                    "❌ НЕ УДАЛОСЬ СОПОСТАВИТЬ ГРАФЫ!\n\n"
                    "Возможные причины:\n"
                    "• Графы имеют разную структуру\n"
                    "• Разное количество рёбер\n"
                    "• Разные степени вершин\n\n"
                    "Проверьте правильность матриц."
                )
                
        except ValueError as e:
            messagebox.showerror("Ошибка", str(e))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверный формат: {e}")
    
    def _validate_input(self) -> Tuple[Optional[str], Optional[str]]:
        """Валидация ввода"""
        if not self.matcher.letter_to_digit:
            messagebox.showwarning("Внимание", "Сначала сопоставьте графы!")
            return None, None
        
        letter1 = self.vertex1_entry.get().strip().upper()
        letter2 = self.vertex2_entry.get().strip().upper()
        
        if not letter1 or not letter2:
            messagebox.showwarning("Внимание", "Введите обе вершины!")
            return None, None
        
        letter1, letter2 = letter1[0], letter2[0]
        available = self.matcher.get_available_letters()
        
        if letter1 not in available:
            messagebox.showwarning("Внимание", f"Вершина '{letter1}' не существует!\nДоступные: {', '.join(available)}")
            return None, None
        
        if letter2 not in available:
            messagebox.showwarning("Внимание", f"Вершина '{letter2}' не существует!\nДоступные: {', '.join(available)}")
            return None, None
        
        return letter1, letter2
    
    def _find_direct(self) -> None:
        """Прямое расстояние"""
        letter1, letter2 = self._validate_input()
        if not letter1:
            return
        
        distance = self.matcher.get_distance(letter1, letter2)
        digit1 = self.matcher.letter_to_digit[letter1]
        digit2 = self.matcher.letter_to_digit[letter2]
        
        result = "═" * 35 + "\n"
        result += "  ПРЯМОЕ РАССТОЯНИЕ (ВЕС РЕБРА)\n"
        result += "═" * 35 + "\n\n"
        result += f"Вершина {letter1} (соответствует {digit1})\n"
        result += f"        ↓\n"
        result += f"Вершина {letter2} (соответствует {digit2})\n\n"
        
        if letter1 == letter2:
            result += "📍 Это одна и та же вершина\n\n"
            result += "➤ Расстояние: 0"
        elif distance is None:
            result += "❌ Прямого ребра НЕТ!\n\n"
            result += "Эти вершины не соединены напрямую.\n\n"
            result += "Попробуйте 'Кратчайший путь'."
        else:
            dist_str = int(distance) if distance == int(distance) else distance
            result += f"✅ Ребро существует!\n\n"
            result += f"➤ Вес ребра: {dist_str}"
        
        self._show_result(result)
    
    def _find_shortest(self) -> None:
        """Кратчайший путь"""
        letter1, letter2 = self._validate_input()
        if not letter1:
            return
        
        distance, path = self.matcher.dijkstra(letter1, letter2)
        digit1 = self.matcher.letter_to_digit[letter1]
        digit2 = self.matcher.letter_to_digit[letter2]
        
        result = "═" * 35 + "\n"
        result += "     КРАТЧАЙШИЙ ПУТЬ\n"
        result += "═" * 35 + "\n\n"
        result += f"Из: {letter1} (соответствует {digit1})\n"
        result += f"В:  {letter2} (соответствует {digit2})\n\n"
        
        if distance is None:
            result += "❌ ПУТЬ НЕ СУЩЕСТВУЕТ!\n\n"
            result += "Вершины в разных компонентах."
        elif distance == 0:
            result += "📍 Одна и та же вершина\n\n"
            result += "➤ Расстояние: 0"
        else:
            path_str = " → ".join(path)
            result += f"✅ Путь найден!\n\n"
            result += f"🛤️ Маршрут:\n{path_str}\n\n"
            result += "📐 Детализация:\n"
            
            for i in range(len(path) - 1):
                w = self.matcher.get_distance(path[i], path[i+1])
                w_str = int(w) if w == int(w) else w
                d1 = self.matcher.letter_to_digit[path[i]]
                d2 = self.matcher.letter_to_digit[path[i+1]]
                result += f"   {path[i]}({d1}) → {path[i+1]}({d2}): {w_str}\n"
            
            total_str = int(distance) if distance == int(distance) else distance
            result += f"\n{'─' * 35}\n"
            result += f"➤ ИТОГО: {total_str}"
        
        self._show_result(result)
    
    def _update_text(self, widget: tk.Text, text: str) -> None:
        """Обновление текстового виджета"""
        widget.config(state='normal')
        widget.delete('1.0', tk.END)
        widget.insert('1.0', text)
        widget.config(state='disabled')
    
    def _show_result(self, text: str) -> None:
        """Показ результата"""
        self._update_text(self.result_text, text)


def main():
    root = tk.Tk()
    
    root.update_idletasks()
    w, h = 1100, 800
    x = (root.winfo_screenwidth() - w) // 2
    y = (root.winfo_screenheight() - h) // 2
    root.geometry(f'{w}x{h}+{x}+{y}')
    
    app = GraphApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()