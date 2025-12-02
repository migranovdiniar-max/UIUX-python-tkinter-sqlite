# app/ui/ui_grammar.py
import customtkinter as ctk
from tkinter import messagebox
from app.db import get_connection


class GrammarWindow:
    def __init__(self, user):
        self.user = user
        self.win = ctk.CTkToplevel()
        self.win.title("📘 Грамматика")
        self.win.geometry("900x700")
        self.win.transient()
        self.win.grab_set()
        self.win.focus_force()

        # Заголовок
        ctk.CTkLabel(
            self.win,
            text="Грамматические правила",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 10))

        subtitle = f"Роль: {self._role_rus()}"
        ctk.CTkLabel(self.win, text=subtitle, text_color="gray").pack(pady=(0, 20))

        # === Фильтры ===
        filter_frame = ctk.CTkFrame(self.win)
        filter_frame.pack(pady=(0, 10), padx=40, fill="x")

        # Поиск по названию
        ctk.CTkLabel(filter_frame, text="🔍 Поиск по названию", anchor="w").pack(pady=(0, 5), anchor="w")
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Введите слово...")
        self.search_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Сортировка по ID
        ctk.CTkLabel(filter_frame, text="Сортировать по ID", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
        self.sort_id_var = ctk.StringVar(value="По возрастанию")
        self.sort_id_combo = ctk.CTkComboBox(
            filter_frame,
            values=["По возрастанию", "По убыванию"],
            variable=self.sort_id_var,
            width=150
        )
        self.sort_id_combo.pack(side="left", padx=(5, 10))

        # Фильтр по уровню
        ctk.CTkLabel(filter_frame, text="Уровень", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
        self.level_var = ctk.StringVar(value="Все уровни")
        self.level_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Все уровни"] + [
                "A1", "A1.1", "A1.2",
                "A2", "A2.1", "A2.2",
                "B1", "B1.1", "B1.2",
                "B2", "B2.1", "B2.2",
                "C1", "C1.1", "C1.2",
                "C2"
            ],
            variable=self.level_var,
            width=120
        )
        self.level_combo.pack(side="left", padx=(5, 10))

        # Кнопка "Применить фильтр"
        self.apply_filter_btn = ctk.CTkButton(
            filter_frame,
            text="🎯 Применить",
            width=120,
            command=self.load_grammar
        )
        self.apply_filter_btn.pack(side="left", padx=(10, 0), pady=2)

        # Сброс
        ctk.CTkButton(filter_frame, text="🔄 Сброс", width=80, command=self.reset_filters).pack(side="right")

        # === Таблица с прокруткой ===
        table_frame = ctk.CTkFrame(self.win)
        table_frame.pack(pady=10, padx=40, fill="both", expand=True)

        self.scrollable_frame = ctk.CTkScrollableFrame(table_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Для массового удаления
        self.selected_ids = {}

        # === Кнопки внизу ===
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=(10, 20), padx=40, fill="x")

        if self.user["role"] == "admin":
            self.bulk_delete_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️ Удалить выбранные",
                fg_color="red",
                hover_color="darkred",
                command=self.bulk_delete_rules
            )
            self.bulk_delete_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

            ctk.CTkButton(
                btn_frame,
                text="➕ Добавить правило",
                command=self.open_add_rule
            ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="⬅️ Назад",
            fg_color="gray",
            command=self.win.destroy
        ).pack(side="left", expand=True, fill="x")

        self.load_grammar()

    def _role_rus(self):
        roles = {"admin": "Администратор", "student": "Студент"}
        return roles.get(self.user["role"], self.user["role"])

    def reset_filters(self):
        """Сброс всех фильтров"""
        self.search_entry.delete(0, "end")
        self.sort_id_var.set("По возрастанию")
        self.level_var.set("Все уровни")
        self.load_grammar()

    def load_grammar(self, event=None):
        """Загружает правила с фильтрами"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_ids.clear()

        # Параметры
        query = self.search_entry.get().strip().lower()
        sort_order = self.sort_id_var.get()
        selected_level = self.level_var.get()

        order_sql = "ORDER BY rule_id ASC" if sort_order == "По возрастанию" else "ORDER BY rule_id DESC"

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT gr.rule_id, gr.title, gr.description, gr.example, gr.grammar_level, t.name AS topic_name
            FROM grammar_rule gr
            LEFT JOIN topic t ON gr.topic_id = t.topic_id
            {order_sql}
        """)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            level_match = (selected_level == "Все уровни" or row["grammar_level"] == selected_level)
            search_match = not query or query in row["title"].lower()

            if not level_match or not search_match:
                continue

            frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=("gray90", "gray20"))
            frame.pack(fill="x", pady=5, padx=10)

            # Чекбокс (только для админа)
            if self.user["role"] == "admin":
                var = ctk.BooleanVar(value=False)
                checkbox = ctk.CTkCheckBox(frame, text="", width=30, variable=var)
                checkbox.pack(side="left", padx=(10, 5), pady=10)
                self.selected_ids[row["rule_id"]] = var
            else:
                ctk.CTkLabel(frame, text="", width=40).pack(side="left")  # выравнивание

            # Контент
            content = ctk.CTkFrame(frame, fg_color="transparent")
            content.pack(fill="x", side="left", padx=10, pady=10)

            # Заголовок + ID
            ctk.CTkLabel(
                content,
                text=f"#{row['rule_id']} {row['title']}",
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            ).pack(anchor="w")

            # Уровень и тема
            meta_text = f"Уровень: {row['grammar_level']}"
            if row["topic_name"]:
                meta_text += f" | Тема: {row['topic_name']}"
            ctk.CTkLabel(
                content,
                text=meta_text,
                text_color="blue" if row["topic_name"] else "gray",
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(anchor="w", pady=(2, 2))

            # Описание и пример
            if row["description"]:
                ctk.CTkLabel(
                    content,
                    text=row["description"],
                    wraplength=500,
                    justify="left",
                    text_color="gray",
                    anchor="w"
                ).pack(anchor="w", pady=(2, 2))

            if row["example"]:
                ctk.CTkLabel(
                    content,
                    text=f"Пример: {row['example']}",
                    wraplength=500,
                    justify="left",
                    text_color="green",
                    anchor="w"
                ).pack(anchor="w", pady=(2, 2))

            # Кнопки (только для админа)
            if self.user["role"] == "admin":
                btns = ctk.CTkFrame(frame, fg_color="transparent")
                btns.pack(side="right", padx=10, pady=10)

                ctk.CTkButton(
                    btns,
                    text="✏️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    command=lambda r=row: self.open_edit_rule(r)
                ).pack(pady=2)

                ctk.CTkButton(
                    btns,
                    text="🗑️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda rid=row["rule_id"]: self.delete_rule(rid)
                ).pack(pady=2)

    def bulk_delete_rules(self):
        selected = [rid for rid, var in self.selected_ids.items() if var.get()]
        if not selected:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return

        if not messagebox.askyesno("Подтверждение", f"Удалить {len(selected)} правил(а)? Это нельзя отменить."):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            placeholders = ",".join("?" * len(selected))
            cur.execute(f"DELETE FROM grammar_rule WHERE rule_id IN ({placeholders})", selected)
            conn.commit()
            messagebox.showinfo("Успех", f"Удалено {len(selected)} правил(а)")
            self.load_grammar()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()

    def open_add_rule(self):
        self.open_rule_form("Добавить правило")

    def open_edit_rule(self, rule):
        self.open_rule_form("Редактировать правило", rule)

    def open_rule_form(self, title, rule=None):
        form = ctk.CTkToplevel(self.win)
        form.title(title)
        form.geometry("800x800")
        form.transient(self.win)
        form.grab_set()
        form.focus_force()

        ctk.CTkLabel(form, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        # Название
        ctk.CTkLabel(form, text="Название правила*", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        title_entry = ctk.CTkEntry(form, placeholder_text="Present Simple", height=40)
        title_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Уровень
        ctk.CTkLabel(form, text="Уровень", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        level_var = ctk.StringVar(value="B1")
        level_combo = ctk.CTkComboBox(
            form,
            values=[
                "A1", "A1.1", "A1.2",
                "A2", "A2.1", "A2.2",
                "B1", "B1.1", "B1.2",
                "B2", "B2.1", "B2.2",
                "C1", "C1.1", "C1.2",
                "C2"
            ],
            variable=level_var
        )
        level_combo.pack(pady=(5, 15), padx=40, fill="x")

        # Тема
        ctk.CTkLabel(form, text="Тема (опционально)", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        topic_var = ctk.StringVar()
        topic_combo = ctk.CTkComboBox(form, variable=topic_var)
        topic_combo.pack(pady=(5, 15), padx=40, fill="x")
        self.load_topics_into_combobox(topic_combo, topic_var)

        # Описание
        ctk.CTkLabel(form, text="Описание", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        desc_entry = ctk.CTkTextbox(form, height=80, wrap="word")
        desc_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Пример
        ctk.CTkLabel(form, text="Пример", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        example_entry = ctk.CTkTextbox(form, height=80, wrap="word")
        example_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Заполнение при редактировании
        if rule:
            title_entry.insert(0, rule["title"])
            level_var.set(rule["grammar_level"])
            topic_var.set(rule["topic_name"] or "")
            if rule["description"]:
                desc_entry.insert("0.0", rule["description"])
            if rule["example"]:
                example_entry.insert("0.0", rule["example"])

        def save():
            title_val = title_entry.get().strip()
            level_val = level_var.get()
            topic_val = topic_var.get()
            desc_val = desc_entry.get("0.0", "end").strip()
            example_val = example_entry.get("0.0", "end").strip()

            if not title_val:
                messagebox.showwarning("Ошибка", "Введите название правила")
                return

            # Получаем topic_id
            topic_id = self.get_topic_id_by_name(topic_val) if topic_val else None

            conn = get_connection()
            cur = conn.cursor()
            try:
                if rule:
                    cur.execute("""
                        UPDATE grammar_rule
                        SET title = ?, grammar_level = ?, topic_id = ?, description = ?, example = ?
                        WHERE rule_id = ?
                    """, (title_val, level_val, topic_id, desc_val or None, example_val or None, rule["rule_id"]))
                else:
                    cur.execute("""
                        INSERT INTO grammar_rule (title, grammar_level, topic_id, description, example)
                        VALUES (?, ?, ?, ?, ?)
                    """, (title_val, level_val, topic_id, desc_val or None, example_val or None))
                conn.commit()
                messagebox.showinfo("Успех", f"Правило '{title_val}' сохранено!")
                form.destroy()
                self.load_grammar()
            except sqlite3.IntegrityError as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
            finally:
                conn.close()

        ctk.CTkButton(form, text="💾 Сохранить", height=40, command=save).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(form, text="Отмена", height=35, fg_color="gray", command=form.destroy).pack(pady=(0, 20), padx=40, fill="x")

    def load_topics_into_combobox(self, combobox, var):
        """Загружает темы в выпадающий список"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM topic ORDER BY name")
        topics = [row["name"] for row in cur.fetchall()]
        conn.close()
        combobox.configure(values=topics)
        if topics:
            var.set(topics[0])

    def get_topic_id_by_name(self, name):
        """Получает topic_id по имени"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT topic_id FROM topic WHERE name = ?", (name,))
        row = cur.fetchone()
        conn.close()
        return row["topic_id"] if row else None

    def delete_rule(self, rule_id):
        if not messagebox.askyesno("Подтверждение", "Удалить правило? Это нельзя отменить."):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM grammar_rule WHERE rule_id = ?", (rule_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Правило удалено")
            self.load_grammar()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()
