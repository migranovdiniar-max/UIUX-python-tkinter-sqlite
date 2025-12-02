import customtkinter as ctk
from tkinter import messagebox
from app.auth import authenticate, register_user
from app.ui.ui_main import MainWindow


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


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class LoginWindow:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("EasyEng — Вход")
        self.root.geometry("450x580")
        self.root.resizable(False, False)
        self.root.iconbitmap(resource_path("app.ico"))

        main_frame = ctk.CTkFrame(self.root, corner_radius=15)
        main_frame.pack(pady=40, padx=30, fill="both", expand=True)

        ctk.CTkLabel(main_frame, text="Добро пожаловать!", font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(30, 10))
        ctk.CTkLabel(main_frame, text="Войдите в свой аккаунт", text_color="gray").pack(pady=(0, 30))

        # Email
        ctk.CTkLabel(main_frame, text="Email", anchor="w").pack(pady=(10, 0), padx=25, anchor="w")
        self.email = ctk.CTkEntry(main_frame, placeholder_text="ваш@email.com", height=40)
        self.email.pack(pady=(5, 15), padx=25, fill="x")

        # Пароль
        ctk.CTkLabel(main_frame, text="Пароль", anchor="w").pack(pady=(10, 0), padx=25, anchor="w")
        self.password = ctk.CTkEntry(main_frame, placeholder_text="••••••••", show="*", height=40)
        self.password.pack(pady=(5, 15), padx=25, fill="x")

        # Вход
        ctk.CTkButton(main_frame, text="Войти", height=45, command=self.login).pack(pady=20, padx=25, fill="x")

        # Регистрация
        ctk.CTkButton(
            main_frame,
            text="Создать аккаунт",
            height=40,
            fg_color="transparent",
            border_width=1,
            text_color=("gray10", "gray90"),
            hover_color=("gray70", "gray30"),
            command=self.open_register_choice
        ).pack(pady=(0, 20), padx=25, fill="x")

        ctk.CTkLabel(self.root, text="© 2025 English Learning App", text_color="gray", font=ctk.CTkFont(size=11)).pack(pady=(0, 15))

        self.root.focus_force()
        self.root.mainloop()

    def login(self):
        email = self.email.get().strip()
        password = self.password.get().strip()
        if not email or not password:
            messagebox.showwarning("Ошибка", "Введите email и пароль")
            return
        user = authenticate(email, password)
        if user:
            self.root.destroy()
            MainWindow(user)
        else:
            messagebox.showerror("Ошибка", "Неверный email или пароль")

    def open_register_choice(self):
        choice_window = ctk.CTkToplevel(self.root)
        choice_window.title("Кто вы?")
        choice_window.geometry("350x200")
        choice_window.resizable(False, False)
        choice_window.transient(self.root)
        choice_window.grab_set()
        self.center_window(choice_window, 350, 200)

        ctk.CTkLabel(choice_window, text="Регистрация", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)
        ctk.CTkButton(choice_window, text="🎓 Студент", height=45, command=lambda: [choice_window.destroy(), self.open_student_register()]).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(choice_window, text="🔑 Администратор", height=45, command=lambda: [choice_window.destroy(), self.open_admin_register()]).pack(pady=10, padx=40, fill="x")

    def center_window(self, window, w, h):
        self.root.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        window.geometry(f"{w}x{h}+{x}+{y}")

    def open_student_register(self):
        reg_window = ctk.CTkToplevel(self.root)
        reg_window.title("Регистрация студента")
        reg_window.geometry("400x600")
        reg_window.resizable(False, False)
        reg_window.transient(self.root)
        reg_window.grab_set()
        reg_window.iconbitmap("app.ico")
        self.center_window(reg_window, 400, 600)

        ctk.CTkLabel(reg_window, text="Регистрация студента", font=ctk.CTkFont(size=20, weight="bold")).pack(pady=20)

        name_entry = self.create_entry(reg_window, "Имя", "Анна")
        email_entry = self.create_entry(reg_window, "Email", "ваш@email.com")
        password_entry = self.create_entry(reg_window, "Пароль", "••••••••", show="*")

        ctk.CTkLabel(reg_window, text="Текущий уровень", anchor="w").pack(pady=(10, 0), padx=30, anchor="w")
        current_level = ctk.CTkComboBox(reg_window, values=["A1", "A1.1", "A1.2", "A2", "A2.1", "A2.2", "B1", "B1.1", "B1.2", "B2", "B2.1", "B2.2", "C1", "C1.1", "C1.2", "C2"], state="readonly")
        current_level.set("A1")
        current_level.pack(pady=(5, 15), padx=30, fill="x")

        ctk.CTkLabel(reg_window, text="Цель", anchor="w").pack(pady=(10, 0), padx=30, anchor="w")
        target_level = ctk.CTkComboBox(reg_window, values=["A2", "A2.1", "A2.2", "B1", "B1.1", "B1.2", "B2", "B2.1", "B2.2", "C1", "C1.1", "C1.2", "C2"], state="readonly")
        target_level.set("B1")
        target_level.pack(pady=(5, 15), padx=30, fill="x")

        def submit():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            cl = current_level.get().strip()
            tl = target_level.get().strip()
            if not all([name, email, password, cl, tl]):
                messagebox.showwarning("Ошибка", "Заполните все поля")
                return
            if "@" not in email: return messagebox.showerror("Ошибка", "Некорректный email")
            if len(password) < 6: return messagebox.showerror("Ошибка", "Пароль < 6 симв.")
            if register_user(name, email, password, "student", cl, tl):
                messagebox.showinfo("Успех", "Аккаунт студента создан!")
                reg_window.destroy()
            else:
                messagebox.showerror("Ошибка", "Email уже существует")

        ctk.CTkButton(reg_window, text="Зарегистрироваться", height=45, command=submit).pack(pady=20, padx=30, fill="x")
        ctk.CTkButton(reg_window, text="Отмена", fg_color="gray", hover_color="red", command=reg_window.destroy).pack(pady=5, padx=30, fill="x")

    def create_entry(self, parent, label, placeholder, show=None):
        """
        Утилита: создаёт подпись и поле ввода.
        """
        ctk.CTkLabel(parent, text=label, anchor="w").pack(pady=(10, 0), padx=30, anchor="w")
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, show=show, height=40)
        entry.pack(pady=(5, 15), padx=30, fill="x")
        return entry

    def open_admin_register(self):
        reg_window = ctk.CTkToplevel(self.root)
        reg_window.title("🔑 Регистрация администратора")
        reg_window.geometry("400x550")  # Увеличили высоту
        reg_window.resizable(False, False)
        reg_window.transient(self.root)
        reg_window.grab_set()
        reg_window.focus_force()
        reg_window.iconbitmap("app.ico")
        self.center_window(reg_window, 400, 550)

        # Заголовок
        ctk.CTkLabel(
            reg_window,
            text="Регистрация администратора",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Поля
        name_entry = self.create_entry(reg_window, "Имя", "Иван")
        email_entry = self.create_entry(reg_window, "Email", "admin@example.com")
        password_entry = self.create_entry(reg_window, "Пароль", "••••••••", show="*")

        ctk.CTkLabel(reg_window, text="Админ-токен", anchor="w").pack(pady=(10, 0), padx=30, anchor="w")
        token_entry = ctk.CTkEntry(
            reg_window,
            placeholder_text="Введите секретный токен",
            show="*",
            height=40
        )
        token_entry.pack(pady=(5, 15), padx=30, fill="x")

        # === КНОПКА "ЗАРЕГИСТРИРОВАТЬСЯ" (гарантированно видна) ===
        def submit():
            name = name_entry.get().strip()
            email = email_entry.get().strip()
            password = password_entry.get().strip()
            token = token_entry.get().strip()

            if not all([name, email, password, token]):
                messagebox.showwarning("Ошибка", "Все поля обязательны")
                return
            if "@" not in email:
                messagebox.showerror("Ошибка", "Некорректный email")
                return
            if len(password) < 6:
                messagebox.showerror("Ошибка", "Пароль должен быть не короче 6 символов")
                return

            from app.auth import register_user
            success = register_user(
                name=name,
                email=email,
                password=password,
                role="admin",
                admin_token=token
            )

            if success:
                messagebox.showinfo("Успех", "Администратор успешно создан!")
                reg_window.destroy()
            else:
                messagebox.showerror("Ошибка", "Неверный токен или email уже занят")

        # Кнопка — с padding и внизу
        ctk.CTkButton(
            reg_window,
            text="Зарегистрироваться",
            height=45,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=submit
        ).pack(pady=(30, 15), padx=30, fill="x")

        ctk.CTkButton(
            reg_window,
            text="Отмена",
            height=40,
            fg_color="gray",
            hover_color="red",
            command=reg_window.destroy
        ).pack(pady=(0, 20), padx=30, fill="x")

        # Фокус на окно
        reg_window.focus_force()

