import customtkinter as ctk
from tkinter import messagebox
from app.ui.ui_topic import TopicWindow
from app.ui.ui_grammar import GrammarWindow
from app.ui.ui_vocabulary import VocabularyWindow
from app.ui.ui_exercise import ExerciseWindow
from app.ui.ui_exercise_answer import ExerciseAnswerWindow
from app.ui.ui_users import UsersWindow
from app.ui.ui_definition import DefinitionWindow


import os
import sys
import customtkinter as ctk
from tkinter import messagebox


def resource_path(relative_path):
    
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

    


class MainWindow:
    def __init__(self, user):
        self.user = user

        # Настройка окна
        self.root = ctk.CTk()
        self.root.title("EasyEng — Главное меню")
        self.root.geometry("1000x1000")
        self.root.resizable(False, False)
        self.root.iconbitmap(resource_path("app.ico"))

        # Заголовок
        title = ctk.CTkLabel(
            self.root,
            text=f"Добро пожаловать, {user['name']}!",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=("gray10", "gray90")
        )
        title.pack(pady=(30, 10))

        subtitle = ctk.CTkLabel(
            self.root,
            text=f"Роль: {self._role_rus()} | Уровень: {user.get('current_level', '—')}",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        subtitle.pack(pady=(0, 30))

        # Фрейм для кнопок
        frame = ctk.CTkFrame(self.root, corner_radius=15, fg_color=("gray90", "gray15"))
        frame.pack(pady=10, padx=60, fill="both", expand=True)

        # Определяем кнопки в зависимости от роли
        buttons = self._get_buttons()

        # Создаём кнопки
        for text, cmd in buttons:
            btn = ctk.CTkButton(
                frame,
                text=text,
                height=50,
                font=ctk.CTkFont(size=15, weight="bold"),
                corner_radius=10,
                command=cmd
            )
            btn.pack(pady=10, padx=25, fill="x")

        # Кнопка выхода
        logout_btn = ctk.CTkButton(
            self.root,
            text="🚪 Выйти",
            height=40,
            fg_color="gray",
            hover_color="red",
            font=ctk.CTkFont(size=13),
            command=self.logout
        )
        logout_btn.pack(pady=20)

        self.root.focus_force()
        self.root.mainloop()

    def _role_rus(self) -> str:
        """Перевод роли на русский"""
        roles = {"admin": "Администратор", "teacher": "Преподаватель", "student": "Студент"}
        return roles.get(self.user["role"], self.user["role"])

    def _get_buttons(self):
        """Возвращает кнопки в зависимости от роли"""
        buttons = [
            ("📘 Темы", self.open_topics),
            ("📖 Правила грамматики", self.open_grammar),
            ("📚 Словарь", self.open_vocabulary),
            ("🔍 Определения", self.open_definition),
            ("✍️ Упражнения", self.open_exercises),
        ]

        if self.user["role"] == "student":
            buttons.append(("📝 Мои ответы", self.open_my_answers))

        if self.user["role"] in ("admin", "teacher"):
            buttons.append(("✅ Ответы на упражнения", self.open_exercise_answers))
            buttons.append(("👥 Пользователи", self.open_users))

        return buttons

    # === Методы открытия окон ===
    def open_topics(self): TopicWindow(self.user)
    def open_grammar(self): GrammarWindow(self.user)
    def open_vocabulary(self): VocabularyWindow(self.user)
    def open_definition(self): DefinitionWindow(self.user)
    def open_exercises(self): ExerciseWindow(self.user)

    def open_my_answers(self):
        from app.ui.ui_exercise_answer import ExerciseAnswerWindow
        ExerciseAnswerWindow(self.user)

    def open_exercise_answers(self):
        from app.ui.ui_exercise_answer import ExerciseAnswerWindow
        ExerciseAnswerWindow(self.user)

    def open_users(self): UsersWindow(self.user)

    def logout(self):
        self.root.destroy()
        from app.ui.ui_login import LoginWindow
        LoginWindow()
