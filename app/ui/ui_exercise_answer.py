# app/ui/ui_exercise_answer.py
import customtkinter as ctk
from tkinter import messagebox
from app.db import get_connection


class ExerciseAnswerWindow:
    def __init__(self, user):
        self.user = user
        self.win = ctk.CTkToplevel()
        self.win.title("📝 Ответы на упражнения")
        self.win.geometry("1000x700")
        self.win.transient()
        self.win.grab_set()
        self.win.focus_force()

        ctk.CTkLabel(
            self.win,
            text="Ответы на упражнения",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 5))

        subtitle = f"Роль: {self._role_rus()} | Пользователь: {user['name']}"
        ctk.CTkLabel(self.win, text=subtitle, text_color="gray").pack(pady=(0, 20))

        # === Фильтры (для всех) ===
        filter_frame = ctk.CTkFrame(self.win)
        filter_frame.pack(pady=(0, 10), padx=40, fill="x")

        ctk.CTkLabel(filter_frame, text="🔍 Поиск по заданию", anchor="w").pack(pady=(0, 5), anchor="w")
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Введите текст упражнения...")
        self.search_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        ctk.CTkLabel(filter_frame, text="Статус", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
        self.status_var = ctk.StringVar(value="Все")
        self.status_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Все", "Решённые", "Нерешённые"],
            variable=self.status_var,
            width=120
        )
        self.status_combo.pack(side="left", padx=(5, 10))

        # Только для админа: фильтр по пользователю
        if self.user["role"] == "admin":
            ctk.CTkLabel(filter_frame, text="Пользователь", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
            self.user_var = ctk.StringVar(value="Все пользователи")
            self.user_combo = ctk.CTkComboBox(filter_frame, variable=self.user_var, width=180)
            self.user_combo.pack(side="left", padx=(5, 10))
            self.load_users()

        ctk.CTkButton(filter_frame, text="🎯 Применить", width=100, command=self.load_answers).pack(side="left", padx=(10, 5))
        ctk.CTkButton(filter_frame, text="🔄 Сброс", width=80, command=self.reset_filters).pack(side="right")

        # === Список ответов ===
        main_frame = ctk.CTkFrame(self.win)
        main_frame.pack(pady=10, padx=40, fill="both", expand=True)

        self.scrollable_frame = ctk.CTkScrollableFrame(main_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # === Кнопки ===
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=(10, 20), padx=40, fill="x")

        if self.user["role"] == "student":
            ctk.CTkButton(
                btn_frame,
                text="📤 Отправить ответ",
                command=self.open_submit_form
            ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="⬅️ Назад",
            fg_color="gray",
            command=self.win.destroy
        ).pack(side="left", expand=True, fill="x")

        self.load_answers()

    def _role_rus(self):
        roles = {"admin": "Администратор", "student": "Студент"}
        return roles.get(self.user["role"], self.user["role"])

    def reset_filters(self):
        self.search_entry.delete(0, "end")
        self.status_var.set("Все")
        if hasattr(self, 'user_var'):
            self.user_var.set("Все пользователи")
        self.load_answers()

    def load_users(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name FROM users ORDER BY name")
        users = [row["name"] for row in cur.fetchall()]
        conn.close()
        self.user_combo.configure(values=["Все пользователи"] + users)
        self.user_combo.set("Все пользователи")

    def load_answers(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        query = self.search_entry.get().strip().lower()
        user_filter = self.user_var.get() if hasattr(self, 'user_var') else None
        status_filter = self.status_var.get()

        conn = get_connection()
        cur = conn.cursor()

        sql = """
            SELECT 
                ea.answer_id, ea.exercise_id, ea.user_id, ea.is_complete, ea.created_at,
                e.problem,
                u.name AS user_name
            FROM exercise_answer ea
            JOIN exercise e ON ea.exercise_id = e.exercise_id
            JOIN users u ON ea.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        # Роль
        if self.user["role"] == "student":
            sql += " AND ea.user_id = ?"
            params.append(self.user["user_id"])
        elif user_filter and user_filter != "Все пользователи":
            sql += " AND u.name = ?"
            params.append(user_filter)

        # Поиск
        if query:
            sql += " AND e.problem LIKE ?"
            params.append(f"%{query}%")

        # Статус
        if status_filter == "Решённые":
            sql += " AND ea.is_complete = 1"
        elif status_filter == "Нерешённые":
            sql += " AND ea.is_complete = 0"

        sql += " ORDER BY ea.created_at DESC"

        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=("gray90", "gray20"))
            frame.pack(fill="x", pady=5, padx=10)

            content = ctk.CTkFrame(frame, fg_color="transparent")
            content.pack(fill="x", side="left", padx=10, pady=10)

            # Задание
            ctk.CTkLabel(
                content,
                text=f"Задание: {row['problem'][:80]}{'...' if len(row['problem']) > 80 else ''}",
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
                wraplength=600
            ).pack(anchor="w")

            # Мета
            meta = f"Пользователь: {row['user_name']} | Дата: {row['created_at']}"
            ctk.CTkLabel(content, text=meta, text_color="blue", font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(3, 0))

            # Статус
            status_text = "✅ Решено" if row["is_complete"] else "❌ Не решено"
            status_color = "green" if row["is_complete"] else "red"
            ctk.CTkLabel(
                content,
                text=status_text,
                text_color=status_color,
                font=ctk.CTkFont(size=13, weight="bold"),
                anchor="w"
            ).pack(anchor="w", pady=(2, 0))

            # Ответы
            parts = self.load_answer_parts(row["answer_id"])
            self.display_answer_parts(parts, content)

            # Кнопки действий
            btns = ctk.CTkFrame(frame, fg_color="transparent")
            btns.pack(side="right", padx=10, pady=10)

            can_edit = not row["is_complete"]

            if (self.user["role"] == "admin" or row["user_id"] == self.user["user_id"]) and can_edit:
                ctk.CTkButton(
                    btns,
                    text="✏️",
                    width=60,
                    height=30,
                    command=lambda r=row: self.open_edit_form(r)
                ).pack(pady=2)

            if self.user["role"] == "admin" or (row["user_id"] == self.user["user_id"] and can_edit):
                ctk.CTkButton(
                    btns,
                    text="🗑️",
                    width=60,
                    height=30,
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda aid=row["answer_id"]: self.delete_answer(aid)
                ).pack(pady=2)

            # Админ: управление статусом
            if self.user["role"] == "admin":
                var = ctk.BooleanVar(value=row["is_complete"])
                chk = ctk.CTkCheckBox(btns, text="Решено", variable=var, onvalue=True, offvalue=False)
                chk.pack(pady=5)
                chk.configure(command=lambda aid=row["answer_id"], v=var: self.toggle_complete(aid, v.get()))

    def load_answer_parts(self, answer_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT part_number, answer_text 
            FROM exercise_answer_part 
            WHERE answer_id = ? 
            ORDER BY part_number
        """, (answer_id,))
        rows = cur.fetchall()
        conn.close()
        return {row["part_number"]: row["answer_text"] for row in rows}

    def display_answer_parts(self, parts, parent):
        for i in sorted(parts.keys()):
            text = parts[i] or "—"
            ctk.CTkLabel(
                parent,
                text=f"Часть {i}: {text}",
                text_color="green",
                anchor="w",
                wraplength=500
            ).pack(anchor="w", pady=1)

    def toggle_complete(self, answer_id, is_complete):
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("UPDATE exercise_answer SET is_complete = ? WHERE answer_id = ?", (is_complete, answer_id))
            conn.commit()
            self.load_answers()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить статус: {e}")
        finally:
            conn.close()

    def open_edit_form(self, row):
        form = ctk.CTkToplevel(self.win)
        form.title("✏️ Редактировать ответ")
        form.geometry("700x600")
        form.transient(self.win)
        form.grab_set()
        form.focus_force()

        ctk.CTkLabel(form, text="Редактирование ответа", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkLabel(form, text="Упражнение", anchor="w").pack(pady=(10, 5), padx=40, anchor="w")
        ctk.CTkLabel(form, text=f"#{row['exercise_id']}: {row['problem'][:60]}...", wraplength=500).pack(pady=5, padx=40, fill="x")

        current_parts = self.load_answer_parts(row["answer_id"])
        max_part = max(current_parts.keys()) if current_parts else 1

        ctk.CTkLabel(form, text="Количество частей", anchor="w").pack(pady=(10, 5), padx=40, anchor="w")
        parts_entry = ctk.CTkEntry(form, placeholder_text="Число")
        parts_entry.insert(0, str(max_part))
        parts_entry.pack(pady=5, padx=40, fill="x")

        input_frame = ctk.CTkFrame(form, fg_color="transparent")
        input_frame.pack(pady=10, padx=40, fill="both", expand=True)

        def refresh_inputs():
            for widget in input_frame.winfo_children():
                widget.destroy()
            try:
                n = int(parts_entry.get())
                for i in range(1, n + 1):
                    ctk.CTkLabel(input_frame, text=f"Ответ {i}:", anchor="w").pack(anchor="w", pady=(5, 0))
                    entry = ctk.CTkTextbox(input_frame, height=40, wrap="word")
                    entry.pack(fill="x", pady=(0, 10))
                    if i in current_parts:
                        entry.insert("0.0", current_parts[i] or "")
            except:
                ctk.CTkLabel(input_frame, text="Введите число", text_color="red").pack(anchor="w")

        parts_entry.bind("<FocusOut>", lambda e: refresh_inputs())
        refresh_inputs()

        def save():
            try:
                n = int(parts_entry.get())
                if n < 1 or n > 10:
                    messagebox.showerror("Ошибка", "Число частей: 1–10")
                    return
            except:
                messagebox.showerror("Ошибка", "Введите число")
                return

            answers = []
            for widget in input_frame.winfo_children():
                if isinstance(widget, ctk.CTkTextbox):
                    text = widget.get("0.0", "end").strip()
                    answers.append(text)

            if len(answers) != n:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return

            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM exercise_answer_part WHERE answer_id = ?", (row["answer_id"],))
                for i, ans in enumerate(answers):
                    cur.execute("""
                        INSERT INTO exercise_answer_part (answer_id, part_number, answer_text)
                        VALUES (?, ?, ?)
                    """, (row["answer_id"], i + 1, ans or None))
                conn.commit()
                messagebox.showinfo("Успех", "Ответ обновлён!")
                form.destroy()
                self.load_answers()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось обновить: {e}")
            finally:
                conn.close()

        ctk.CTkButton(form, text="💾 Сохранить", command=save).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(form, text="Отмена", fg_color="gray", command=form.destroy).pack(pady=(0, 20), padx=40, fill="x")

    def delete_answer(self, answer_id):
        if not messagebox.askyesno("Подтверждение", "Удалить ответ? Это нельзя отменить."):
            return
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM exercise_answer WHERE answer_id = ?", (answer_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Ответ удалён")
            self.load_answers()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()

    def open_submit_form(self):
        form = ctk.CTkToplevel(self.win)
        form.title("📤 Отправить ответ")
        form.geometry("700x600")
        form.transient(self.win)
        form.grab_set()
        form.focus_force()

        ctk.CTkLabel(form, text="Отправка ответа", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkLabel(form, text="Выберите упражнение", anchor="w").pack(pady=(10, 5), padx=40, anchor="w")
        exercise_combo = ctk.CTkComboBox(form, width=400)
        exercise_combo.pack(pady=5, padx=40, fill="x")
        exercises = self.load_exercises_for_combo()
        exercise_combo.configure(values=[f"{ex[0]}: {ex[1][:50]}..." for ex in exercises])
        exercise_combo.set("")

        ctk.CTkLabel(form, text="Количество частей", anchor="w").pack(pady=(10, 5), padx=40, anchor="w")
        parts_entry = ctk.CTkEntry(form, placeholder_text="Например: 2")
        parts_entry.pack(pady=5, padx=40, fill="x")

        input_frame = ctk.CTkFrame(form, fg_color="transparent")
        input_frame.pack(pady=10, padx=40, fill="both", expand=True)

        def on_parts_change(*args):
            for widget in input_frame.winfo_children():
                widget.destroy()
            try:
                n = int(parts_entry.get())
                if n < 1 or n > 10:
                    ctk.CTkLabel(input_frame, text="1–10 частей", text_color="red").pack(anchor="w")
                    return
                for i in range(n):
                    ctk.CTkLabel(input_frame, text=f"Ответ {i+1}:", anchor="w").pack(anchor="w", pady=(5, 0))
                    entry = ctk.CTkTextbox(input_frame, height=40, wrap="word")
                    entry.pack(fill="x", pady=(0, 10))
            except:
                ctk.CTkLabel(input_frame, text="Введите число", text_color="red").pack(anchor="w")

        parts_entry.bind("<KeyRelease>", on_parts_change)

        def submit():
            sel = exercise_combo.get()
            if not sel or ":" not in sel:
                messagebox.showerror("Ошибка", "Выберите упражнение")
                return
            try:
                ex_id = int(sel.split(":")[0])
            except:
                messagebox.showerror("Ошибка", "Неверный формат упражнения")
                return

            try:
                n = int(parts_entry.get())
                if n < 1 or n > 10:
                    messagebox.showerror("Ошибка", "1–10 частей")
                    return
            except:
                messagebox.showerror("Ошибка", "Введите число")
                return

            answers = []
            for widget in input_frame.winfo_children():
                if isinstance(widget, ctk.CTkTextbox):
                    text = widget.get("0.0", "end").strip()
                    answers.append(text)

            if len(answers) != n:
                messagebox.showerror("Ошибка", "Заполните все поля")
                return

            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO exercise_answer (exercise_id, user_id, is_complete)
                    VALUES (?, ?, 0)
                """, (ex_id, self.user["user_id"]))
                answer_id = cur.lastrowid

                for i, ans in enumerate(answers):
                    cur.execute("""
                        INSERT INTO exercise_answer_part (answer_id, part_number, answer_text)
                        VALUES (?, ?, ?)
                    """, (answer_id, i + 1, ans or None))

                conn.commit()
                messagebox.showinfo("Успех", "Ответ отправлен!")
                form.destroy()
                self.load_answers()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось отправить: {e}")
            finally:
                conn.close()

        ctk.CTkButton(form, text="📤 Отправить", command=submit).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(form, text="Отмена", fg_color="gray", command=form.destroy).pack(pady=(0, 20), padx=40, fill="x")

    def load_exercises_for_combo(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT exercise_id, problem FROM exercise ORDER BY exercise_id")
        rows = cur.fetchall()
        conn.close()
        return [(r["exercise_id"], r["problem"]) for r in rows]
