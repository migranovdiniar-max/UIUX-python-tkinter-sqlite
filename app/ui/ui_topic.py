# app/ui/ui_topic.py
import customtkinter as ctk
from tkinter import messagebox
from app.db import get_connection
import sqlite3


class TopicWindow:
    def __init__(self, user):
        self.user = user
        self.win = ctk.CTkToplevel()
        self.win.title("📚 Темы курса")
        self.win.geometry("800x650")
        self.win.transient()
        self.win.grab_set()
        self.win.focus_force()

        # Заголовок
        ctk.CTkLabel(
            self.win,
            text="Темы английского",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 10))

        subtitle = f"Роль: {self._role_rus()}"
        ctk.CTkLabel(self.win, text=subtitle, text_color="gray").pack(pady=(0, 20))

        # === Фильтры: поиск + выбор сортировки + кнопка применения ===
        filter_frame = ctk.CTkFrame(self.win)
        filter_frame.pack(pady=(0, 10), padx=40, fill="x")

        # Поиск
        ctk.CTkLabel(filter_frame, text="🔍 Поиск по названию", anchor="w").pack(pady=(0, 5), anchor="w")
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Введите слово...")
        self.search_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

        # Выбор типа сортировки
        ctk.CTkLabel(filter_frame, text="Сортировать по ID", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
        self.sort_var = ctk.StringVar(value="По возрастанию")
        self.sort_combo = ctk.CTkComboBox(
            filter_frame,
            values=["По возрастанию", "По убыванию"],
            variable=self.sort_var,
            width=150
        )
        self.sort_combo.pack(side="left", padx=(5, 10))

        # Кнопка "Применить фильтр" с иконкой
        self.apply_filter_btn = ctk.CTkButton(
            filter_frame,
            text="🎯 Применить фильтр",
            width=140,
            command=self.load_topics
        )
        self.apply_filter_btn.pack(side="left", padx=(10, 0), pady=2)

        # Сброс
        ctk.CTkButton(filter_frame, text="🔄 Сброс", width=80, command=self.reset_filters).pack(side="right")

        # === Список тем ===
        table_frame = ctk.CTkFrame(self.win)
        table_frame.pack(pady=10, padx=40, fill="both", expand=True)

        self.scrollable_frame = ctk.CTkScrollableFrame(table_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Для массового удаления (только админ)
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
                command=self.bulk_delete_topics
            )
            self.bulk_delete_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

            ctk.CTkButton(
                btn_frame,
                text="➕ Добавить тему",
                command=self.open_add_topic
            ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="⬅️ Назад",
            fg_color="gray",
            command=self.win.destroy
        ).pack(side="left", expand=True, fill="x")

        # Загружаем темы сразу (с начальными фильтрами)
        self.load_topics()

    def _role_rus(self):
        roles = {"admin": "Администратор", "student": "Студент"}
        return roles.get(self.user["role"], self.user["role"])

    def reset_filters(self):
        """Сброс всех фильтров"""
        self.search_entry.delete(0, "end")
        self.sort_var.set("По возрастанию")
        self.load_topics()

    def load_topics(self, event=None):
        """Загружает темы с учётом поиска и выбранной сортировки (только при ручном применении)"""
        # Очистка списка
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_ids.clear()

        # Параметры фильтрации
        query = self.search_entry.get().strip().lower()
        sort_choice = self.sort_var.get()
        order_sql = "ORDER BY topic_id ASC" if sort_choice == "По возрастанию" else "ORDER BY topic_id DESC"

        # Загрузка из БД
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"SELECT topic_id, name, description FROM topic {order_sql}")
        rows = cur.fetchall()
        conn.close()

        # Фильтрация по поиску
        for row in rows:
            if query and query not in row["name"].lower():
                continue

            frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=("gray90", "gray20"))
            frame.pack(fill="x", pady=5, padx=10)

            # Чекбокс — только для админа
            if self.user["role"] == "admin":
                var = ctk.BooleanVar(value=False)
                checkbox = ctk.CTkCheckBox(frame, text="", width=30, variable=var)
                checkbox.pack(side="left", padx=(10, 5), pady=10)
                self.selected_ids[row["topic_id"]] = var
            else:
                # Пустая метка для выравнивания
                ctk.CTkLabel(frame, text="", width=40).pack(side="left")

            # Контент темы
            content = ctk.CTkFrame(frame, fg_color="transparent")
            content.pack(fill="x", side="left", padx=10, pady=10)

            ctk.CTkLabel(
                content,
                text=f"#{row['topic_id']} {row['name']}",
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            ).pack(anchor="w")

            if row["description"]:
                ctk.CTkLabel(
                    content,
                    text=row["description"],
                    wraplength=500,
                    justify="left",
                    text_color="gray",
                    anchor="w"
                ).pack(anchor="w", pady=(5, 0))

            # Кнопки действий — только для админа
            if self.user["role"] == "admin":
                btns = ctk.CTkFrame(frame, fg_color="transparent")
                btns.pack(side="right", padx=10, pady=10)

                ctk.CTkButton(
                    btns,
                    text="✏️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    command=lambda r=row: self.open_edit_topic(r)
                ).pack(pady=2)

                ctk.CTkButton(
                    btns,
                    text="🗑️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda tid=row["topic_id"]: self.delete_topic(tid)
                ).pack(pady=2)

    def bulk_delete_topics(self):
        selected = [tid for tid, var in self.selected_ids.items() if var.get()]
        if not selected:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return

        if not messagebox.askyesno("Подтверждение", f"Удалить {len(selected)} тем(ы)? Это нельзя отменить."):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            placeholders = ",".join("?" * len(selected))
            cur.execute(f"DELETE FROM topic WHERE topic_id IN ({placeholders})", selected)
            conn.commit()
            messagebox.showinfo("Успех", f"Удалено {len(selected)} тем(ы)")
            self.load_topics()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()

    def open_add_topic(self):
        self.open_topic_form("Добавить тему")

    def open_edit_topic(self, topic):
        self.open_topic_form("Редактировать тему", topic)

    def open_topic_form(self, title, topic=None):
        form = ctk.CTkToplevel(self.win)
        form.title(title)
        form.geometry("500x400")
        form.transient(self.win)
        form.grab_set()
        form.focus_force()

        ctk.CTkLabel(form, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        ctk.CTkLabel(form, text="Название темы*", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        name_entry = ctk.CTkEntry(form, placeholder_text="Например: Present Simple", height=40)
        name_entry.pack(pady=(5, 15), padx=40, fill="x")

        ctk.CTkLabel(form, text="Описание (опционально)", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        desc_entry = ctk.CTkTextbox(form, height=120, wrap="word")
        desc_entry.pack(pady=(5, 20), padx=40, fill="x")

        if topic:
            name_entry.insert(0, topic["name"])
            if topic["description"]:
                desc_entry.insert("0.0", topic["description"])

        def save():
            name = name_entry.get().strip()
            desc = desc_entry.get("0.0", "end").strip()

            if not name:
                messagebox.showwarning("Ошибка", "Введите название темы")
                return

            conn = get_connection()
            cur = conn.cursor()
            try:
                if topic:
                    cur.execute("""
                        UPDATE topic SET name = ?, description = ? WHERE topic_id = ?
                    """, (name, desc or None, topic["topic_id"]))
                else:
                    cur.execute("""
                        INSERT INTO topic (name, description) VALUES (?, ?)
                    """, (name, desc or None))
                conn.commit()
                messagebox.showinfo("Успех", f"Тема '{name}' сохранена!")
                form.destroy()
                self.load_topics()
            except sqlite3.IntegrityError:
                messagebox.showerror("Ошибка", "Тема с таким названием уже существует")
            finally:
                conn.close()

        ctk.CTkButton(form, text="💾 Сохранить", height=40, command=save).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(form, text="Отмена", height=35, fg_color="gray", command=form.destroy).pack(pady=(0, 20), padx=40, fill="x")

    def delete_topic(self, topic_id):
        if not messagebox.askyesno("Подтверждение", "Удалить тему? Это нельзя отменить."):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM topic WHERE topic_id = ?", (topic_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Тема удалена")
            self.load_topics()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()
