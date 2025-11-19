import tkinter as tk
from tkinter import ttk

# подключаем все UI-модули
from app.ui.ui_topic import TopicWindow
from app.ui.ui_grammar import GrammarWindow
from app.ui.ui_vocabulary import VocabularyWindow
from app.ui.ui_exercise import ExerciseWindow
from app.ui.ui_exercise_answer import ExerciseAnswerWindow
from app.ui.ui_user_answers import UserExerciseWindow
from app.ui.ui_users import UsersWindow
from app.ui.ui_definition import DefinitionWindow


class MainWindow:
    def __init__(self, user):
        self.user = user
        self.win = tk.Tk()
        self.win.title(f"Main Menu - {user['role']}")
        self.win.geometry("500x500")

        title = tk.Label(self.win, text="Main Menu", font=("Arial", 18, "bold"))
        title.pack(pady=15)

        frame = tk.Frame(self.win)
        frame.pack(expand=True)

        buttons = []

        # Доступно всем
        buttons.append(("Topics", self.open_topics))
        buttons.append(("Grammar Rules", self.open_grammar))
        buttons.append(("Vocabulary", self.open_vocabulary))
        buttons.append(("Definition", self.open_definition))
        buttons.append(("Exercises", self.open_exercises))
        buttons.append(("User Answers", self.open_user_answers))

        # Студенты НЕ должны видеть эти меню
        if self.user["role"] in ("admin", "teacher"):
            buttons.append(("Exercise Answers (ETALON)", self.open_exercise_answers))
            buttons.append(("Users", self.open_users))

        for text, cmd in buttons:
            tk.Button(frame, text=text, width=25, height=2, command=cmd)\
                .pack(pady=6)

        self.win.mainloop()

    def open_topics(self):
        TopicWindow(self.user)

    def open_grammar(self):
        GrammarWindow(self.user)

    def open_vocabulary(self):
        VocabularyWindow(self.user)

    def open_definition(self):
        DefinitionWindow(self.user)

    def open_exercises(self):
        ExerciseWindow(self.user)

    def open_exercise_answers(self):
        ExerciseAnswerWindow(self.user)

    def open_user_answers(self):
        UserExerciseWindow(self.user)

    def open_users(self):
        UsersWindow(self.user)
