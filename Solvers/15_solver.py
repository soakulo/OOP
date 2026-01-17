import sys
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum, auto
from abc import ABC, abstractmethod

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QGroupBox, QFormLayout, QComboBox,
    QFrame, QScrollArea, QSpinBox, QRadioButton,
    QButtonGroup, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPainter, QColor, QPen


# ═══════════════════════════════════════════════════════════════════════════
#                              ЛЕКСИЧЕСКИЙ АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════════════════════

class TokenType(Enum):
    """Типы токенов"""
    LPAREN = auto()      # (
    RPAREN = auto()      # )
    NOT = auto()         # ¬ ! ~
    AND = auto()         # ∧ & /\
    OR = auto()          # ∨ | \/
    IMPLIES = auto()     # → ->
    EQUIV = auto()        # ≡ ↔ <-> <=>
    XOR = auto()         # ⊕ ^
    IN = auto()          # ∈
    VAR_X = auto()       # x
    SET_NAME = auto()    # A, B, P, Q и т.д.
    EOF = auto()


@dataclass
class Token:
    """Токен"""
    type: TokenType
    value: str = ""
    position: int = 0


class Lexer:
    """Лексический анализатор логических выражений"""
    
    # Словарь для распознавания операторов
    OPERATORS = {
        '¬': TokenType.NOT,
        '!': TokenType.NOT,
        '~': TokenType.NOT,
        'NOT': TokenType.NOT,
        
        '∧': TokenType.AND,
        '&': TokenType.AND,
        '/\\': TokenType.AND,
        'AND': TokenType.AND,
        
        '∨': TokenType.OR,
        '|': TokenType.OR,
        '\\/': TokenType.OR,
        'OR': TokenType.OR,
        
        '→': TokenType.IMPLIES,
        '->': TokenType.IMPLIES,
        '=>': TokenType.IMPLIES,
        'IMPLIES': TokenType.IMPLIES,
        
        '≡': TokenType.EQUIV,
        '↔': TokenType.EQUIV,
        '<->': TokenType.EQUIV,
        '<=>': TokenType.EQUIV,
        'EQUIV': TokenType.EQUIV,
        'IFF': TokenType.EQUIV,
        
        '⊕': TokenType.XOR,
        '^': TokenType.XOR,
        'XOR': TokenType.XOR,
        
        '∈': TokenType.IN,
        'IN': TokenType.IN,
    }
    
    def __init__(self, text: str):
        self.text = text.upper().replace('В', 'IN').replace('И', 'AND').replace('ИЛИ', 'OR')
        self.original_text = text
        self.pos = 0
        self.length = len(self.text)
    
    def peek(self, offset: int = 0) -> str:
        """Посмотреть символ без продвижения"""
        pos = self.pos + offset
        if pos < self.length:
            return self.text[pos]
        return ''
    
    def advance(self, count: int = 1) -> str:
        """Продвинуться на count символов"""
        result = self.text[self.pos:self.pos + count]
        self.pos += count
        return result
    
    def skip_whitespace(self):
        """Пропустить пробелы"""
        while self.pos < self.length and self.text[self.pos].isspace():
            self.pos += 1
    
    def try_match(self, patterns: List[str]) -> Optional[str]:
        """Попытаться сопоставить один из паттернов"""
        for pattern in sorted(patterns, key=len, reverse=True):
            if self.text[self.pos:self.pos + len(pattern)] == pattern:
                return pattern
        return None
    
    def tokenize(self) -> List[Token]:
        """Разбить текст на токены"""
        tokens = []
        
        while self.pos < self.length:
            self.skip_whitespace()
            if self.pos >= self.length:
                break
            
            start_pos = self.pos
            ch = self.text[self.pos]
            
            # Скобки
            if ch == '(':
                tokens.append(Token(TokenType.LPAREN, '(', start_pos))
                self.advance()
                continue
            
            if ch == ')':
                tokens.append(Token(TokenType.RPAREN, ')', start_pos))
                self.advance()
                continue
            
            # Пробуем найти оператор
            matched = self.try_match(list(self.OPERATORS.keys()))
            if matched:
                token_type = self.OPERATORS[matched]
                tokens.append(Token(token_type, matched, start_pos))
                self.advance(len(matched))
                continue
            
            # Переменная X
            if ch == 'X':
                tokens.append(Token(TokenType.VAR_X, 'x', start_pos))
                self.advance()
                continue
            
            # Имя множества (буква)
            if ch.isalpha():
                name = ""
                while self.pos < self.length and self.text[self.pos].isalnum():
                    name += self.text[self.pos]
                    self.pos += 1
                
                # Проверяем, не оператор ли это
                if name in self.OPERATORS:
                    tokens.append(Token(self.OPERATORS[name], name, start_pos))
                else:
                    tokens.append(Token(TokenType.SET_NAME, name, start_pos))
                continue
            
            # Неизвестный символ - пропускаем
            self.advance()
        
        tokens.append(Token(TokenType.EOF, '', self.pos))
        return tokens


# ═══════════════════════════════════════════════════════════════════════════
#                          АБСТРАКТНОЕ СИНТАКСИЧЕСКОЕ ДЕРЕВО
# ═══════════════════════════════════════════════════════════════════════════

class ASTNode(ABC):
    """Базовый класс узла AST"""
    
    @abstractmethod
    def evaluate(self, x: int, sets: Dict[str, 'Segment'], target_value: Optional[bool] = None) -> bool:
        """Вычислить значение узла"""
        pass
    
    @abstractmethod
    def get_set_names(self) -> Set[str]:
        """Получить все имена множеств в выражении"""
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass


class MembershipNode(ASTNode):
    """Узел принадлежности (x ∈ A)"""
    
    def __init__(self, set_name: str):
        self.set_name = set_name
    
    def evaluate(self, x: int, sets: Dict[str, 'Segment'], target_value: Optional[bool] = None) -> bool:
        if self.set_name == target_value:
            # Это целевое множество - вернём специальное значение
            return None  # Будет обработано выше
        
        segment = sets.get(self.set_name)
        if segment is None:
            raise ValueError(f"Множество '{self.set_name}' не определено")
        return segment.contains(x)
    
    def get_set_names(self) -> Set[str]:
        return {self.set_name}
    
    def __str__(self) -> str:
        return f"(x ∈ {self.set_name})"


class NotNode(ASTNode):
    """Узел отрицания ¬A"""
    
    def __init__(self, operand: ASTNode):
        self.operand = operand
    
    def evaluate(self, x: int, sets: Dict[str, 'Segment'], target_value: Optional[bool] = None) -> bool:
        result = self.operand.evaluate(x, sets, target_value)
        if result is None:
            return None
        return not result
    
    def get_set_names(self) -> Set[str]:
        return self.operand.get_set_names()
    
    def __str__(self) -> str:
        return f"¬{self.operand}"


class BinaryNode(ASTNode):
    """Узел бинарной операции"""
    
    def __init__(self, left: ASTNode, operator: str, right: ASTNode):
        self.left = left
        self.operator = operator
        self.right = right
    
    def evaluate(self, x: int, sets: Dict[str, 'Segment'], target_value: Optional[bool] = None) -> bool:
        left_val = self.left.evaluate(x, sets, target_value)
        right_val = self.right.evaluate(x, sets, target_value)
        
        if left_val is None or right_val is None:
            return None
        
        if self.operator == 'AND':
            return left_val and right_val
        elif self.operator == 'OR':
            return left_val or right_val
        elif self.operator == 'IMPLIES':
            return (not left_val) or right_val
        elif self.operator == 'EQUIV':
            return left_val == right_val
        elif self.operator == 'XOR':
            return left_val != right_val
        else:
            raise ValueError(f"Неизвестный оператор: {self.operator}")
    
    def get_set_names(self) -> Set[str]:
        return self.left.get_set_names() | self.right.get_set_names()
    
    def __str__(self) -> str:
        op_symbols = {
            'AND': '∧',
            'OR': '∨',
            'IMPLIES': '→',
            'EQUIV': '≡',
            'XOR': '⊕'
        }
        return f"({self.left} {op_symbols.get(self.operator, self.operator)} {self.right})"


# ═══════════════════════════════════════════════════════════════════════════
#                              СИНТАКСИЧЕСКИЙ АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════════════════════

class Parser:
    """
    Парсер логических выражений
    
    Грамматика (от низшего приоритета к высшему):
    expr       = equiv_expr
    equiv_expr = implies_expr (('≡' | '↔') implies_expr)*
    implies_expr = xor_expr ('→' xor_expr)*
    xor_expr   = or_expr ('⊕' or_expr)*
    or_expr    = and_expr ('∨' and_expr)*
    and_expr   = unary_expr ('∧' unary_expr)*
    unary_expr = '¬' unary_expr | primary
    primary    = '(' expr ')' | membership
    membership = 'x' '∈' SET_NAME | SET_NAME (подразумевается x ∈ SET_NAME)
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def current(self) -> Token:
        return self.tokens[self.pos]
    
    def peek(self, offset: int = 0) -> Token:
        pos = self.pos + offset
        if pos < len(self.tokens):
            return self.tokens[pos]
        return Token(TokenType.EOF)
    
    def advance(self) -> Token:
        token = self.current()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return token
    
    def expect(self, token_type: TokenType) -> Token:
        if self.current().type != token_type:
            raise SyntaxError(
                f"Ожидался {token_type.name}, получен {self.current().type.name} "
                f"в позиции {self.current().position}"
            )
        return self.advance()
    
    def parse(self) -> ASTNode:
        """Главный метод парсинга"""
        result = self.parse_equiv()
        if self.current().type != TokenType.EOF:
            raise SyntaxError(
                f"Неожиданный токен {self.current().value} в позиции {self.current().position}"
            )
        return result
    
    def parse_equiv(self) -> ASTNode:
        """Эквивалентность (самый низкий приоритет)"""
        left = self.parse_implies()
        
        while self.current().type == TokenType.EQUIV:
            self.advance()
            right = self.parse_implies()
            left = BinaryNode(left, 'EQUIV', right)
        
        return left
    
    def parse_implies(self) -> ASTNode:
        """Импликация (правоассоциативная)"""
        left = self.parse_xor()
        
        if self.current().type == TokenType.IMPLIES:
            self.advance()
            right = self.parse_implies()  # Правая ассоциативность
            return BinaryNode(left, 'IMPLIES', right)
        
        return left
    
    def parse_xor(self) -> ASTNode:
        """Исключающее ИЛИ"""
        left = self.parse_or()
        
        while self.current().type == TokenType.XOR:
            self.advance()
            right = self.parse_or()
            left = BinaryNode(left, 'XOR', right)
        
        return left
    
    def parse_or(self) -> ASTNode:
        """Дизъюнкция"""
        left = self.parse_and()
        
        while self.current().type == TokenType.OR:
            self.advance()
            right = self.parse_and()
            left = BinaryNode(left, 'OR', right)
        
        return left
    
    def parse_and(self) -> ASTNode:
        """Конъюнкция"""
        left = self.parse_unary()
        
        while self.current().type == TokenType.AND:
            self.advance()
            right = self.parse_unary()
            left = BinaryNode(left, 'AND', right)
        
        return left
    
    def parse_unary(self) -> ASTNode:
        """Унарные операции (отрицание)"""
        if self.current().type == TokenType.NOT:
            self.advance()
            operand = self.parse_unary()
            return NotNode(operand)
        
        return self.parse_primary()
    
    def parse_primary(self) -> ASTNode:
        """Первичные выражения"""
        # Скобки
        if self.current().type == TokenType.LPAREN:
            self.advance()
            expr = self.parse_equiv()
            self.expect(TokenType.RPAREN)
            return expr
        
        # x ∈ A
        if self.current().type == TokenType.VAR_X:
            self.advance()
            if self.current().type == TokenType.IN:
                self.advance()
            if self.current().type == TokenType.SET_NAME:
                set_name = self.advance().value
                return MembershipNode(set_name)
            raise SyntaxError("Ожидалось имя множества после 'x ∈'")
        
        # Просто имя множества (подразумевается x ∈ ...)
        if self.current().type == TokenType.SET_NAME:
            set_name = self.advance().value
            return MembershipNode(set_name)
        
        raise SyntaxError(
            f"Неожиданный токен: {self.current().type.name} "
            f"('{self.current().value}') в позиции {self.current().position}"
        )


# ═══════════════════════════════════════════════════════════════════════════
#                                   ОТРЕЗОК
# ═══════════════════════════════════════════════════════════════════════════

class Segment:
    """Класс для представления отрезка на числовой прямой"""
    
    def __init__(self, left: int, right: int):
        self.left = min(left, right)
        self.right = max(left, right)
    
    def __repr__(self):
        return f"[{self.left}, {self.right}]"
    
    def length(self) -> int:
        return self.right - self.left
    
    def contains(self, x: int) -> bool:
        return self.left <= x <= self.right


# ═══════════════════════════════════════════════════════════════════════════
#                                   РЕШАТЕЛЬ
# ═══════════════════════════════════════════════════════════════════════════

class PointRequirement(Enum):
    """Требование к точке для искомого отрезка"""
    MUST_BE_IN = auto()      # Точка ДОЛЖНА быть в A
    MUST_BE_OUT = auto()     # Точка НЕ ДОЛЖНА быть в A
    CAN_BE_EITHER = auto()   # Точка может быть или не быть в A
    IMPOSSIBLE = auto()       # Невозможно удовлетворить формулу


class UniversalSolver:
    """Универсальный решатель логических выражений на отрезках"""
    
    def __init__(self, formula: str, segments: Dict[str, Segment], target_set: str):
        self.formula = formula
        self.segments = segments
        self.target_set = target_set.upper()
        
        # Парсинг формулы
        lexer = Lexer(formula)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        self.ast = parser.parse()
        
        # Проверяем, что целевое множество есть в формуле
        all_sets = self.ast.get_set_names()
        if self.target_set not in all_sets:
            raise ValueError(f"Множество '{self.target_set}' не найдено в формуле")
        
        # Проверяем, что все остальные множества определены
        for s in all_sets:
            if s != self.target_set and s not in segments:
                raise ValueError(f"Множество '{s}' не определено")
    
    def evaluate_with_target(self, x: int, target_in_a: bool) -> bool:
        """Вычислить формулу с заданным значением для целевого множества"""
        # Создаём временное множество для целевого
        if target_in_a:
            # x принадлежит целевому множеству
            temp_segment = Segment(x, x)
        else:
            # x не принадлежит целевому множеству
            temp_segment = Segment(x + 1000000, x + 1000001)
        
        test_segments = {**self.segments, self.target_set: temp_segment}
        return self._evaluate_node(self.ast, x, test_segments)
    
    def _evaluate_node(self, node: ASTNode, x: int, segments: Dict[str, Segment]) -> bool:
        """Рекурсивное вычисление узла AST"""
        if isinstance(node, MembershipNode):
            segment = segments.get(node.set_name)
            if segment is None:
                raise ValueError(f"Множество '{node.set_name}' не определено")
            return segment.contains(x)
        
        elif isinstance(node, NotNode):
            return not self._evaluate_node(node.operand, x, segments)
        
        elif isinstance(node, BinaryNode):
            left = self._evaluate_node(node.left, x, segments)
            right = self._evaluate_node(node.right, x, segments)
            
            if node.operator == 'AND':
                return left and right
            elif node.operator == 'OR':
                return left or right
            elif node.operator == 'IMPLIES':
                return (not left) or right
            elif node.operator == 'EQUIV':
                return left == right
            elif node.operator == 'XOR':
                return left != right
        
        raise ValueError(f"Неизвестный тип узла: {type(node)}")
    
    def analyze_point(self, x: int) -> PointRequirement:
        """Анализ требований к точке x"""
        # Проверяем формулу при x ∈ A и x ∉ A
        true_if_in = self.evaluate_with_target(x, True)
        true_if_out = self.evaluate_with_target(x, False)
        
        if true_if_in and true_if_out:
            return PointRequirement.CAN_BE_EITHER
        elif true_if_in and not true_if_out:
            return PointRequirement.MUST_BE_IN
        elif not true_if_in and true_if_out:
            return PointRequirement.MUST_BE_OUT
        else:
            return PointRequirement.IMPOSSIBLE
    
    def solve(self, find_max: bool = True) -> Tuple[int, Segment, str]:
        """
        Найти оптимальный отрезок
        
        Args:
            find_max: True - искать максимальную длину, False - минимальную
        
        Returns:
            (длина, отрезок, объяснение)
        """
        # Определяем диапазон анализа
        all_points = []
        for seg in self.segments.values():
            all_points.extend([seg.left, seg.right])
        
        if not all_points:
            return 0, None, "Нет определённых отрезков"
        
        min_point = min(all_points) - 10
        max_point = max(all_points) + 10
        
        # Анализируем каждую точку
        must_in = []
        must_out = []
        can_either = []
        impossible = []
        
        for x in range(min_point, max_point + 1):
            req = self.analyze_point(x)
            if req == PointRequirement.MUST_BE_IN:
                must_in.append(x)
            elif req == PointRequirement.MUST_BE_OUT:
                must_out.append(x)
            elif req == PointRequirement.CAN_BE_EITHER:
                can_either.append(x)
            else:
                impossible.append(x)
        
        # Проверяем на невозможность
        if impossible:
            return -1, None, self._format_impossible(impossible)
        
        # Строим решение
        if find_max:
            result, segment = self._find_max_segment(must_in, must_out, can_either, min_point, max_point)
        else:
            result, segment = self._find_min_segment(must_in, must_out)
        
        explanation = self._format_explanation(must_in, must_out, can_either, result, segment, find_max)
        
        return result, segment, explanation
    
    def _find_max_segment(self, must_in: List[int], must_out: List[int], 
                          can_either: List[int], min_p: int, max_p: int) -> Tuple[int, Segment]:
        """Найти отрезок максимальной длины"""
        must_out_set = set(must_out)
        
        if not must_in and not can_either:
            return 0, None
        
        # Все допустимые точки
        available = set(must_in) | set(can_either)
        
        # Находим максимальный непрерывный отрезок без must_out точек
        best_length = 0
        best_segment = None
        
        # Перебираем все возможные левые границы
        points = sorted(available)
        if not points:
            return 0, None
        
        for left in points:
            # Ищем самую правую границу
            right = left
            while right + 1 in available and right + 1 not in must_out_set:
                right += 1
            
            # Проверяем, что отрезок содержит все must_in в своём диапазоне
            contained_must_in = [p for p in must_in if left <= p <= right]
            missing_must_in = [p for p in must_in if p < left or p > right]
            
            # Отрезок должен содержать все must_in точки, которые попадают в него
            length = right - left
            
            if length > best_length:
                # Проверяем, что нет must_out внутри отрезка
                has_must_out = any(left <= p <= right for p in must_out)
                if not has_must_out:
                    best_length = length
                    best_segment = Segment(left, right)
        
        # Альтернативный подход: ищем области между must_out точками
        sorted_must_out = sorted(must_out_set)
        
        # Добавляем границы
        barriers = [min_p - 1] + sorted_must_out + [max_p + 1]
        
        for i in range(len(barriers) - 1):
            left_barrier = barriers[i]
            right_barrier = barriers[i + 1]
            
            # Допустимый диапазон: (left_barrier, right_barrier)
            segment_left = left_barrier + 1
            segment_right = right_barrier - 1
            
            if segment_left > segment_right:
                continue
            
            # Пересекаем с available
            actual_left = segment_left
            actual_right = segment_right
            
            length = actual_right - actual_left
            
            if length > best_length:
                best_length = length
                best_segment = Segment(actual_left, actual_right)
        
        return best_length, best_segment
    
    def _find_min_segment(self, must_in: List[int], must_out: List[int]) -> Tuple[int, Segment]:
        """Найти отрезок минимальной длины, покрывающий все must_in"""
        if not must_in:
            return 0, None
        
        must_out_set = set(must_out)
        
        # Минимальный отрезок должен покрывать все must_in
        left = min(must_in)
        right = max(must_in)
        
        # Проверяем, что между ними нет must_out
        for x in range(left, right + 1):
            if x in must_out_set:
                return -1, None  # Невозможно
        
        return right - left, Segment(left, right)
    
    def _format_explanation(self, must_in: List[int], must_out: List[int],
                           can_either: List[int], result: int, 
                           segment: Segment, find_max: bool) -> str:
        """Форматирование объяснения решения"""
        lines = [
            "═" * 60,
            "  РЕШЕНИЕ ЗАДАЧИ",
            "═" * 60,
            "",
            f"  Формула: {self.formula}",
            f"  Искомое множество: {self.target_set}",
            f"  Задача: найти {'МАКСИМАЛЬНУЮ' if find_max else 'МИНИМАЛЬНУЮ'} длину",
            "",
            "─" * 60,
            "  Исходные данные:",
            "─" * 60,
        ]
        
        for name, seg in self.segments.items():
            lines.append(f"    {name} = {seg}")
        
        lines.extend([
            "",
            "─" * 60,
            "  Анализ точек (для каких x формула истинна):",
            "─" * 60,
            "",
        ])
        
        if must_in:
            lines.append(f"  ✓ Точки, которые ДОЛЖНЫ быть в {self.target_set}:")
            lines.append(f"    {self._format_points(must_in)}")
            lines.append("")
        
        if must_out:
            lines.append(f"  ✗ Точки, которые НЕ ДОЛЖНЫ быть в {self.target_set}:")
            lines.append(f"    {self._format_points(must_out)}")
            lines.append("")
        
        if can_either and find_max:
            lines.append(f"  ○ Точки, которые МОГУТ быть в {self.target_set}:")
            lines.append(f"    {self._format_points(can_either)}")
            lines.append("")
        
        lines.extend([
            "─" * 60,
            "  РЕЗУЛЬТАТ:",
            "─" * 60,
            "",
        ])
        
        if result < 0:
            lines.append("  ❌ Задача не имеет решения!")
        elif segment:
            lines.append(f"  Оптимальный отрезок {self.target_set} = {segment}")
            lines.append(f"  Длина = {result}")
        else:
            lines.append(f"  Длина = {result}")
        
        lines.extend(["", "═" * 60])
        
        return "\n".join(lines)
    
    def _format_points(self, points: List[int]) -> str:
        """Форматирование списка точек как интервалов"""
        if not points:
            return "∅"
        
        points = sorted(points)
        intervals = []
        start = points[0]
        end = points[0]
        
        for p in points[1:]:
            if p == end + 1:
                end = p
            else:
                if start == end:
                    intervals.append(str(start))
                else:
                    intervals.append(f"[{start}..{end}]")
                start = end = p
        
        if start == end:
            intervals.append(str(start))
        else:
            intervals.append(f"[{start}..{end}]")
        
        return ", ".join(intervals)
    
    def _format_impossible(self, points: List[int]) -> str:
        """Сообщение о невозможности решения"""
        return (
            f"ОШИБКА: Формула не может быть тождественно истинной!\n"
            f"В точках {self._format_points(points)} формула ложна "
            f"при любом значении (x ∈ {self.target_set})"
        )


# ═══════════════════════════════════════════════════════════════════════════
#                              ВИЗУАЛИЗАЦИЯ
# ═══════════════════════════════════════════════════════════════════════════

class SegmentVisualizer(QFrame):
    """Виджет для визуализации отрезков"""
    
    COLORS = [
        QColor(41, 128, 185),   # Синий
        QColor(39, 174, 96),    # Зелёный
        QColor(142, 68, 173),   # Фиолетовый
        QColor(243, 156, 18),   # Оранжевый
        QColor(26, 188, 156),   # Бирюзовый
    ]
    
    def __init__(self):
        super().__init__()
        self.setMinimumHeight(150)
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.segments: Dict[str, Segment] = {}
        self.result_segment: Optional[Segment] = None
        self.result_name: str = "A"
    
    def set_data(self, segments: Dict[str, Segment], 
                 result: Optional[Segment] = None, result_name: str = "A"):
        self.segments = segments
        self.result_segment = result
        self.result_name = result_name
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if not self.segments:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Определяем границы
        all_points = []
        for seg in self.segments.values():
            all_points.extend([seg.left, seg.right])
        if self.result_segment:
            all_points.extend([self.result_segment.left, self.result_segment.right])
        
        min_val = min(all_points) - 3
        max_val = max(all_points) + 3
        
        width = self.width() - 60
        height = self.height()
        
        def to_x(val):
            if max_val == min_val:
                return 30 + width // 2
            return 30 + (val - min_val) / (max_val - min_val) * width
        
        # Рисуем числовую прямую
        y_base = height - 30
        painter.setPen(QPen(QColor(100, 100, 100), 2))
        painter.drawLine(20, y_base, self.width() - 20, y_base)
        
        # Рисуем метки
        painter.setFont(QFont("Arial", 8))
        for val in range(int(min_val), int(max_val) + 1):
            x = int(to_x(val))
            painter.drawLine(x, y_base - 3, x, y_base + 3)
            painter.drawText(x - 10, y_base + 15, str(val))
        
        # Рисуем отрезки
        y_offset = 25
        for i, (name, seg) in enumerate(self.segments.items()):
            color = self.COLORS[i % len(self.COLORS)]
            y = y_offset + i * 25
            
            painter.setPen(QPen(color, 5))
            painter.drawLine(int(to_x(seg.left)), y, int(to_x(seg.right)), y)
            
            # Точки на концах
            painter.setBrush(color)
            painter.drawEllipse(int(to_x(seg.left)) - 4, y - 4, 8, 8)
            painter.drawEllipse(int(to_x(seg.right)) - 4, y - 4, 8, 8)
            
            # Подпись
            painter.setPen(QPen(color.darker(120), 1))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(int(to_x(seg.left)) - 20, y + 4, f"{name}")
        
        # Рисуем результат
        if self.result_segment:
            y = y_offset + len(self.segments) * 25
            painter.setPen(QPen(QColor(220, 50, 50), 6))
            painter.drawLine(
                int(to_x(self.result_segment.left)), y,
                int(to_x(self.result_segment.right)), y
            )
            
            painter.setBrush(QColor(220, 50, 50))
            painter.drawEllipse(int(to_x(self.result_segment.left)) - 4, y - 4, 8, 8)
            painter.drawEllipse(int(to_x(self.result_segment.right)) - 4, y - 4, 8, 8)
            
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            painter.drawText(
                int(to_x(self.result_segment.left)) - 25, y + 4, 
                f"{self.result_name}*"
            )


# ═══════════════════════════════════════════════════════════════════════════
#                              ВВОД ОТРЕЗКОВ
# ═══════════════════════════════════════════════════════════════════════════

class SegmentInputWidget(QWidget):
    """Виджет для ввода одного отрезка"""
    
    def __init__(self, name: str = "P", left: int = 0, right: int = 10):
        super().__init__()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.name_input = QLineEdit(name)
        self.name_input.setMaximumWidth(50)
        self.name_input.setPlaceholderText("Имя")
        
        self.left_input = QSpinBox()
        self.left_input.setRange(-1000, 1000)
        self.left_input.setValue(left)
        
        self.right_input = QSpinBox()
        self.right_input.setRange(-1000, 1000)
        self.right_input.setValue(right)
        
        self.remove_btn = QPushButton("✕")
        self.remove_btn.setMaximumWidth(30)
        self.remove_btn.setStyleSheet("color: red;")
        
        layout.addWidget(self.name_input)
        layout.addWidget(QLabel("= ["))
        layout.addWidget(self.left_input)
        layout.addWidget(QLabel(","))
        layout.addWidget(self.right_input)
        layout.addWidget(QLabel("]"))
        layout.addWidget(self.remove_btn)
    
    def get_data(self) -> Tuple[str, Segment]:
        """Получить данные отрезка"""
        name = self.name_input.text().strip().upper()
        if not name:
            name = "X"
        return name, Segment(self.left_input.value(), self.right_input.value())


class SegmentListWidget(QWidget):
    """Виджет для списка отрезков"""
    
    def __init__(self):
        super().__init__()
        
        layout = QVBoxLayout(self)
        
        # Контейнер для отрезков
        self.segments_layout = QVBoxLayout()
        layout.addLayout(self.segments_layout)
        
        # Кнопка добавления
        add_btn = QPushButton("+ Добавить отрезок")
        add_btn.clicked.connect(self.add_segment)
        layout.addWidget(add_btn)
        
        # Добавляем начальные отрезки
        self.add_segment("P", 5, 30)
        self.add_segment("Q", 14, 23)
    
    def add_segment(self, name: str = "", left: int = 0, right: int = 10):
        """Добавить новый отрезок"""
        if not name:
            # Генерируем имя
            existing = set(self.get_segments().keys())
            for c in "PQRSTUVWXYZABCDEFGHIJKLMNO":
                if c not in existing:
                    name = c
                    break
            else:
                name = f"S{len(existing)}"
        
        widget = SegmentInputWidget(name, left, right)
        widget.remove_btn.clicked.connect(lambda: self.remove_segment(widget))
        self.segments_layout.addWidget(widget)
    
    def remove_segment(self, widget: SegmentInputWidget):
        """Удалить отрезок"""
        self.segments_layout.removeWidget(widget)
        widget.deleteLater()
    
    def get_segments(self) -> Dict[str, Segment]:
        """Получить все отрезки"""
        result = {}
        for i in range(self.segments_layout.count()):
            widget = self.segments_layout.itemAt(i).widget()
            if isinstance(widget, SegmentInputWidget):
                name, segment = widget.get_data()
                result[name] = segment
        return result


# ═══════════════════════════════════════════════════════════════════════════
#                              ГЛАВНОЕ ОКНО
# ═══════════════════════════════════════════════════════════════════════════

class MainWindow(QMainWindow):
    """Главное окно приложения"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Универсальный решатель задания 15 ЕГЭ (логические выражения)")
        self.setMinimumSize(850, 750)
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка интерфейса"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        # Заголовок
        title = QLabel("🎓 Решатель задания 15 ЕГЭ по информатике")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        subtitle = QLabel("Поддерживает произвольные логические выражения")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        main_layout.addWidget(subtitle)
        
        # Разделитель
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Левая панель - ввод
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Ввод формулы
        formula_group = QGroupBox("Логическое выражение")
        formula_layout = QVBoxLayout()
        
        self.formula_input = QLineEdit()
        self.formula_input.setFont(QFont("Consolas", 12))
        self.formula_input.setPlaceholderText("Введите формулу...")
        self.formula_input.setText("((x ∈ P) ≡ (x ∈ Q)) → ¬(x ∈ A)")
        formula_layout.addWidget(self.formula_input)
        
        # Подсказка по синтаксису
        hint = QLabel(
            "Операторы: ¬ или ! (НЕ), ∧ или & (И), ∨ или | (ИЛИ), "
            "→ или -> (импликация), ≡ или <-> (эквив.), ⊕ или ^ (XOR)\n"
            "Принадлежность: (x ∈ P) или просто P"
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-size: 10px;")
        formula_layout.addWidget(hint)
        
        formula_group.setLayout(formula_layout)
        left_layout.addWidget(formula_group)
        
        # Искомое множество
        target_group = QGroupBox("Искомое множество")
        target_layout = QHBoxLayout()
        
        self.target_input = QLineEdit("A")
        self.target_input.setMaximumWidth(60)
        target_layout.addWidget(QLabel("Имя:"))
        target_layout.addWidget(self.target_input)
        
        target_layout.addSpacing(20)
        
        self.find_max_radio = QRadioButton("Макс. длину")
        self.find_min_radio = QRadioButton("Мин. длину")
        self.find_max_radio.setChecked(True)
        
        target_layout.addWidget(QLabel("Искать:"))
        target_layout.addWidget(self.find_max_radio)
        target_layout.addWidget(self.find_min_radio)
        target_layout.addStretch()
        
        target_group.setLayout(target_layout)
        left_layout.addWidget(target_group)
        
        # Известные отрезки
        segments_group = QGroupBox("Известные отрезки")
        segments_layout = QVBoxLayout()
        
        self.segments_widget = SegmentListWidget()
        segments_layout.addWidget(self.segments_widget)
        
        segments_group.setLayout(segments_layout)
        left_layout.addWidget(segments_group)
        
        # Кнопка решения
        self.solve_btn = QPushButton("🔍 РЕШИТЬ")
        self.solve_btn.setFont(QFont("Arial", 14, QFont.Bold))
        self.solve_btn.setMinimumHeight(50)
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        self.solve_btn.clicked.connect(self._solve)
        left_layout.addWidget(self.solve_btn)
        
        left_layout.addStretch()
        splitter.addWidget(left_panel)
        
        # Правая панель - результат
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Визуализация
        viz_group = QGroupBox("Визуализация")
        viz_layout = QVBoxLayout()
        self.visualizer = SegmentVisualizer()
        viz_layout.addWidget(self.visualizer)
        viz_group.setLayout(viz_layout)
        right_layout.addWidget(viz_group)
        
        # Результат
        result_group = QGroupBox("Подробное решение")
        result_layout = QVBoxLayout()
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Consolas", 10))
        result_layout.addWidget(self.result_text)
        result_group.setLayout(result_layout)
        right_layout.addWidget(result_group)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 500])
        
        # Примеры
        examples_group = QGroupBox("Примеры формул")
        examples_layout = QHBoxLayout()
        
        examples = [
            ("((x∈P)≡(x∈Q))→¬(x∈A)", "Пример 1"),
            ("(¬(x∈A)→(x∈P))→((x∈A)→(x∈Q))", "Пример 2"),
            ("((x∈P)∨(x∈Q))→(x∈A)", "Пример 3"),
            ("(x∈A)→((x∈P)∧(x∈Q))", "Пример 4"),
        ]
        
        for formula, name in examples:
            btn = QPushButton(name)
            btn.setToolTip(formula)
            btn.clicked.connect(lambda checked, f=formula: self.formula_input.setText(f))
            examples_layout.addWidget(btn)
        
        examples_group.setLayout(examples_layout)
        main_layout.addWidget(examples_group)
    
    def _solve(self):
        """Решить задачу"""
        try:
            formula = self.formula_input.text()
            target = self.target_input.text().strip().upper()
            segments = self.segments_widget.get_segments()
            find_max = self.find_max_radio.isChecked()
            
            if not formula:
                raise ValueError("Введите формулу")
            
            if not target:
                raise ValueError("Введите имя искомого множества")
            
            if not segments:
                raise ValueError("Добавьте хотя бы один отрезок")
            
            # Удаляем целевое множество из известных, если оно там есть
            if target in segments:
                del segments[target]
            
            # Решаем
            solver = UniversalSolver(formula, segments, target)
            result, segment, explanation = solver.solve(find_max)
            
            # Отображаем
            self.result_text.setText(explanation)
            self.visualizer.set_data(segments, segment, target)
            
        except Exception as e:
            self.result_text.setText(f"❌ ОШИБКА:\n\n{str(e)}")
            QMessageBox.warning(self, "Ошибка", str(e))


# ═══════════════════════════════════════════════════════════════════════════
#                              ТОЧКА ВХОДА
# ═══════════════════════════════════════════════════════════════════════════

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()