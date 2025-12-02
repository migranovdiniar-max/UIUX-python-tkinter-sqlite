# app/ui/ui_exercise.py
import customtkinter as ctk
from tkinter import messagebox
from app.db import get_connection


class ExerciseWindow:
    def __init__(self, user):
        self.user = user
        self.win = ctk.CTkToplevel()
        self.win.title("💪 Упражнения")
        self.win.geometry("1000x700")
        self.win.transient()
        self.win.grab_set()
        self.win.focus_force()

        # --- Заголовок ---
        ctk.CTkLabel(
            self.win,
            text="Управление упражнениями",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 5))

        subtitle = f"Роль: {self._role_rus()}"
        ctk.CTkLabel(self.win, text=subtitle, text_color="gray").pack(pady=(0, 20))

        # === Фильтры ===
        filter_frame = ctk.CTkFrame(self.win)
        filter_frame.pack(pady=(0, 10), padx=40, fill="x")

        # Поиск по заданию
        ctk.CTkLabel(filter_frame, text="🔍 Поиск по тексту", anchor="w").pack(pady=(0, 5), anchor="w")
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Введите слово...")
        self.search_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Фильтр по типу
        ctk.CTkLabel(filter_frame, text="Тип", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
        self.type_var = ctk.StringVar(value="Все типы")
        self.type_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Все типы", "grammar", "vocabulary", "listening", "reading", "writing", "speaking"],
            variable=self.type_var,
            width=120
        )
        self.type_combo.pack(side="left", padx=(5, 10))

        # Фильтр по уровню
        ctk.CTkLabel(filter_frame, text="Уровень", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
        self.level_var = ctk.StringVar(value="Все уровни")
        self.level_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Все уровни", "A1", "A1.1", "A1.2", "A2", "A2.1", "A2.2",
                    "B1", "B1.1", "B1.2", "B2", "B2.1", "B2.2",
                    "C1", "C1.1", "C1.2", "C2"],
            variable=self.level_var,
            width=120
        )
        self.level_combo.pack(side="left", padx=(5, 10))

        # Кнопки фильтрации
        ctk.CTkButton(filter_frame, text="🎯 Применить", width=100, command=self.load_exercises).pack(side="left", padx=(10, 5))
        ctk.CTkButton(filter_frame, text="🔄 Сброс", width=80, command=self.reset_filters).pack(side="right")

        # === Список упражнений (с прокруткой) ===
        table_frame = ctk.CTkFrame(self.win)
        table_frame.pack(pady=10, padx=40, fill="both", expand=True)

        self.scrollable_frame = ctk.CTkScrollableFrame(table_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Для массового удаления
        self.selected_ids = {}

        # === Кнопки действий ===
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=(10, 20), padx=40, fill="x")

        if self.user["role"] == "admin":
            self.bulk_delete_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️ Удалить выбранные",
                fg_color="red",
                hover_color="darkred",
                command=self.bulk_delete_exercises
            )
            self.bulk_delete_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

            ctk.CTkButton(
                btn_frame,
                text="➕ Добавить упражнение",
                command=self.add_exercise
            ).pack(side="left", padx=(0, 10), expand=True, fill="x")

            ctk.CTkButton(
                btn_frame,
                text="✏️ Редактировать",
                command=self.edit_exercise
            ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="⬅️ Назад",
            fg_color="gray",
            command=self.win.destroy
        ).pack(side="left", expand=True, fill="x")

        # Загружаем данные
        self.load_exercises()

    def _role_rus(self):
        roles = {"admin": "Администратор", "student": "Студент", "teacher": "Преподаватель"}
        return roles.get(self.user["role"], self.user["role"])

    def reset_filters(self):
        self.search_entry.delete(0, "end")
        self.type_var.set("Все типы")
        self.level_var.set("Все уровни")
        self.load_exercises()

    def load_exercises(self):
        # Очистка
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_ids.clear()

        # Параметры фильтров
        query = self.search_entry.get().strip().lower()
        ex_type = self.type_var.get()
        level_filter = self.level_var.get()

        # Загрузка данных с JOIN'ами
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                e.exercise_id, e.problem, e.type, e.exercise_level, 
                t.name AS topic_name, gr.title AS rule_title
            FROM exercise e
            LEFT JOIN topic t ON e.topic_id = t.topic_id
            LEFT JOIN grammar_rule gr ON e.rule_id = gr.rule_id
            ORDER BY e.exercise_id DESC
        """)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            # Фильтры
            if query and query not in row["problem"].lower():
                continue
            if ex_type != "Все типы" and row["type"] != ex_type:
                continue
            if level_filter != "Все уровни" and row["exercise_level"] != level_filter:
                continue

            # --- Карточка упражнения ---
            frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=("gray90", "gray20"))
            frame.pack(fill="x", pady=5, padx=10)

            # Чекбокс (только для админа)
            if self.user["role"] == "admin":
                var = ctk.BooleanVar(value=False)
                checkbox = ctk.CTkCheckBox(frame, text="", width=30, variable=var)
                checkbox.pack(side="left", padx=(10, 5), pady=10)
                self.selected_ids[row["exercise_id"]] = var
            else:
                ctk.CTkLabel(frame, text="", width=40).pack(side="left")

            # Контент
            content = ctk.CTkFrame(frame, fg_color="transparent")
            content.pack(fill="x", side="left", padx=10, pady=10)

            # ID + Задание (обрезано)
            ctk.CTkLabel(
                content,
                text=f"#{row['exercise_id']} {row['problem'][:80]}{'...' if len(row['problem']) > 80 else ''}",
                font=ctk.CTkFont(weight="bold"),
                anchor="w",
                wraplength=600
            ).pack(anchor="w")

            # Мета-информация
            meta_parts = [f"Тип: {row['type']}", f"Уровень: {row['exercise_level']}"]
            if row["topic_name"]:
                meta_parts.append(f"Тема: {row['topic_name']}")
            if row["rule_title"]:
                meta_parts.append(f"Правило: {row['rule_title']}")

            ctk.CTkLabel(
                content,
                text=" | ".join(meta_parts),
                text_color="blue",
                font=ctk.CTkFont(size=12),
                anchor="w",
                wraplength=600
            ).pack(anchor="w", pady=(3, 0))

            # Кнопки действий (только админ)
            if self.user["role"] == "admin":
                btns = ctk.CTkFrame(frame, fg_color="transparent")
                btns.pack(side="right", padx=10, pady=10)

                ctk.CTkButton(
                    btns,
                    text="✏️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    command=lambda r=row: self.edit_exercise_by_row(r)
                ).pack(pady=2)

                ctk.CTkButton(
                    btns,
                    text="🗑️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda eid=row["exercise_id"]: self.delete_exercise(eid)
                ).pack(pady=2)

    def edit_exercise_by_row(self, row):
        # Просто передаём строку в редактирование
        self.edit_exercise(row)

    def bulk_delete_exercises(self):
        selected = [eid for eid, var in self.selected_ids.items() if var.get()]
        if not selected:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить {len(selected)} упражнений?"):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            placeholders = ",".join("?" * len(selected))
            cur.execute(f"DELETE FROM exercise WHERE exercise_id IN ({placeholders})", selected)
            conn.commit()
            messagebox.showinfo("Успех", f"Удалено {len(selected)} упражнений")
            self.load_exercises()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()

    def add_exercise(self):
        dlg = ExerciseDialog(self.win, "Добавить упражнение", topics=self.load_topics(), load_rules=self.load_rules_for_topic)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO exercise (problem, media_url, type, exercise_level, topic_id, rule_id)
                VALUES (?,?,?,?,?,?)
            """, (
                dlg.result["problem"],
                dlg.result["media_url"],
                dlg.result["type"],
                dlg.result["level"],
                dlg.result["topic_id"],
                dlg.result["rule_id"]
            ))
            conn.commit()
            conn.close()
            self.load_exercises()

    def edit_exercise(self, row=None):
        if row is None:
            sel = self.scrollable_frame.winfo_children()
            if not sel or len(sel) == 0:
                messagebox.showinfo("Информация", "Нет упражнений для редактирования")
                return
            # Если вызвано без параметра — ищем выбранную чекбоксами запись
            selected = [eid for eid, var in self.selected_ids.items() if var.get()]
            if len(selected) != 1:
                messagebox.showinfo("Информация", "Выберите ровно одно упражнение")
                return
            ex_id = selected[0]
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT e.*, t.name AS topic_name, gr.title AS rule_title
                FROM exercise e
                LEFT JOIN topic t ON e.topic_id = t.topic_id
                LEFT JOIN grammar_rule gr ON e.rule_id = gr.rule_id
                WHERE e.exercise_id = ?
            """, (ex_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                messagebox.showerror("Ошибка", "Упражнение не найдено")
                return
        else:
            # Уже передана строка
            ex_id = row["exercise_id"]

        dlg = ExerciseDialog(
            self.win,
            "Редактировать упражнение",
            data=row,
            topics=self.load_topics(),
            load_rules=self.load_rules_for_topic
        )
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE exercise
                SET problem=?, media_url=?, type=?, exercise_level=?, topic_id=?, rule_id=?
                WHERE exercise_id=?
            """, (
                dlg.result["problem"],
                dlg.result["media_url"],
                dlg.result["type"],
                dlg.result["level"],
                dlg.result["topic_id"],
                dlg.result["rule_id"],
                ex_id
            ))
            conn.commit()
            conn.close()
            self.load_exercises()

    def delete_exercise(self, ex_id):
        if not messagebox.askyesno("Подтверждение", "Удалить упражнение? Это также удалит связанные ответы."):
            return
        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM exercise WHERE exercise_id = ?", (ex_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Упражнение удалено")
            self.load_exercises()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()

    def load_topics(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT topic_id, name FROM topic ORDER BY name")
        rows = cur.fetchall()
        conn.close()
        return [(r["topic_id"], r["name"]) for r in rows]

    def load_rules_for_topic(self, topic_id):
        conn = get_connection()
        cur = conn.cursor()
        if topic_id is None:
            cur.execute("SELECT rule_id, title FROM grammar_rule ORDER BY title")
        else:
            cur.execute("SELECT rule_id, title FROM grammar_rule WHERE topic_id = ? ORDER BY title", (topic_id,))
        rows = cur.fetchall()
        conn.close()
        return [(r["rule_id"], r["title"]) for r in rows]


# --- Диалог добавления/редактирования — без изменений (но стилизован) ---
class ExerciseDialog:
    def __init__(self, parent, title, data=None, topics=None, load_rules=None):
        self.result = None
        self.load_rules = load_rules

        self.top = ctk.CTkToplevel(parent)
        self.top.title(title)
        self.top.geometry("700x800")
        self.top.transient(parent)
        self.top.grab_set()
        self.top.focus_force()

        scroll = ctk.CTkScrollableFrame(self.top)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Поля ---
        ctk.CTkLabel(scroll, text="Текст задания *", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(10, 5))
        self.t_problem = ctk.CTkTextbox(scroll, height=120, wrap="word")
        self.t_problem.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(scroll, text="Ссылка на медиа (опц.)", anchor="w").pack(anchor="w", padx=20, pady=(10, 5))
        self.e_media = ctk.CTkEntry(scroll, placeholder_text="https://...")
        self.e_media.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(scroll, text="Тип *", anchor="w").pack(anchor="w", padx=20, pady=(10, 5))
        self.e_type = ctk.CTkEntry(scroll, placeholder_text="grammar, vocabulary и т.п.")
        self.e_type.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(scroll, text="Уровень (A1-C2)", anchor="w").pack(anchor="w", padx=20, pady=(10, 5))
        self.e_level = ctk.CTkEntry(scroll, placeholder_text="B1")
        self.e_level.pack(fill="x", padx=20, pady=5)

        # Тема
        ctk.CTkLabel(scroll, text="Тема", anchor="w").pack(anchor="w", padx=20, pady=(10, 5))
        topics = topics or []
        self.topic_map = {f"{t[0]}: {t[1]}": t[0] for t in topics}
        values = list(self.topic_map.keys()) if topics else ["Нет тем"]
        self.topic_combo = ctk.CTkComboBox(scroll, values=values, state="readonly")
        self.topic_combo.pack(fill="x", padx=20, pady=5)
        self.topic_combo.bind("<<ComboboxSelected>>", self.on_topic_change)

        # Правило
        ctk.CTkLabel(scroll, text="Грамматическое правило (опц.)", anchor="w").pack(anchor="w", padx=20, pady=(10, 5))
        self.rule_map = {}
        self.rule_combo = ctk.CTkComboBox(scroll, values=[], state="readonly")
        self.rule_combo.pack(fill="x", padx=20, pady=5)
        self.rule_combo.set("")

        # --- Кнопки ---
        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20)
        ctk.CTkButton(btn_frame, text="✅ Сохранить", command=self.on_save).pack(side="left", padx=20, expand=True)
        ctk.CTkButton(btn_frame, text="Отмена", fg_color="gray", command=self.top.destroy).pack(side="right", padx=20, expand=True)

        # Заполнение при редактировании
        if data:
            self.t_problem.insert("0.0", data["problem"] or "")
            self.e_media.insert(0, data["media_url"] or "")
            self.e_type.insert(0, data["type"] or "")
            self.e_level.insert(0, data["exercise_level"] or "")

            # Тема
            topic_name = data.get("topic_name")
            if topic_name:
                for key, tid in self.topic_map.items():
                    if str(tid) == str(data["topic_id"]):
                        self.topic_combo.set(key)
                        break
            self.on_topic_change()

            # Правило
            rule_title = data.get("rule_title")
            if rule_title and data["rule_id"]:
                rules = self.load_rules(data["topic_id"] if data["topic_id"] else None)
                self.rule_map = {f"{r[0]}: {r[1]}": r[0] for r in rules}
                self.rule_combo.configure(values=list(self.rule_map.keys()))
                for k, rid in self.rule_map.items():
                    if rid == data["rule_id"]:
                        self.rule_combo.set(k)
                        break

    def on_topic_change(self, event=None):
        sel = self.topic_combo.get().strip()
        if not sel or sel == "Нет тем":
            self.rule_combo.configure(values=[], state="disabled")
            self.rule_combo.set("")
            self.rule_map = {}
            return
        try:
            tid = int(sel.split(":")[0])
        except:
            return
        rules = self.load_rules(tid)
        if rules:
            self.rule_map = {f"{r[0]}: {r[1]}": r[0] for r in rules}
            self.rule_combo.configure(values=list(self.rule_map.keys()), state="readonly")
            self.rule_combo.set("")
        else:
            self.rule_combo.configure(values=["Нет правил"], state="disabled")
            self.rule_combo.set("")

    def on_save(self):
        problem = self.t_problem.get("0.0", "end").strip()
        typ = self.e_type.get().strip()
        if not problem or not typ:
            messagebox.showerror("Ошибка", "Поля 'Задание' и 'Тип' обязательны!")
            return

        self.result = {
            "problem": problem,
            "media_url": self.e_media.get().strip() or None,
            "type": typ,
            "level": self.e_level.get().strip() or None,
            "topic_id": self._get_id_from_combo(self.topic_combo, self.topic_map),
            "rule_id": self._get_id_from_combo(self.rule_combo, self.rule_map),
        }
        self.top.destroy()

    def _get_id_from_combo(self, combo, id_map):
        sel = combo.get().strip()
        if sel in id_map and ":" in sel:
            try:
                return int(sel.split(":")[0])
            except:
                pass
        return None
