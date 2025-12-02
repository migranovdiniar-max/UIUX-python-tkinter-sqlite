# app/ui/ui_vocabulary.py
import customtkinter as ctk
from tkinter import messagebox
from app.db import get_connection


class VocabularyWindow:
    def __init__(self, user):
        self.user = user
        self.win = ctk.CTkToplevel()
        self.win.title("📖 Словарь")
        self.win.geometry("900x700")
        self.win.transient()
        self.win.grab_set()
        self.win.focus_force()

        ctk.CTkLabel(
            self.win,
            text="Управление словарём",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 10))

        subtitle = f"Роль: {self._role_rus()}"
        ctk.CTkLabel(self.win, text=subtitle, text_color="gray").pack(pady=(0, 20))

        # === Фильтры ===
        filter_frame = ctk.CTkFrame(self.win)
        filter_frame.pack(pady=(0, 10), padx=40, fill="x")

        # Поиск по слову
        ctk.CTkLabel(filter_frame, text="🔍 Поиск по слову", anchor="w").pack(pady=(0, 5), anchor="w")
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Введите слово...")
        self.search_entry.pack(side="left", padx=(0, 10), fill="x", expand=True)

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

        # Фильтр по части речи
        ctk.CTkLabel(filter_frame, text="Часть речи", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
        self.pos_var = ctk.StringVar(value="Все части")
        self.pos_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Все части", "noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "interjection"],
            variable=self.pos_var,
            width=130
        )
        self.pos_combo.pack(side="left", padx=(5, 10))

        # Только для админа: фильтр по пользователю
        self.user_filter_frame = None
        self.user_var = None
        if self.user["role"] == "admin":
            ctk.CTkLabel(filter_frame, text="Пользователь", anchor="w").pack(pady=(0, 5), padx=(10, 0), anchor="w")
            self.user_var = ctk.StringVar(value="Все пользователи")
            self.user_combo = ctk.CTkComboBox(filter_frame, variable=self.user_var, width=150)
            self.user_combo.pack(side="left", padx=(5, 10))
            self.load_users_into_combobox()

        # Кнопки
        ctk.CTkButton(filter_frame, text="🎯 Применить", width=100, command=self.load_words).pack(side="left", padx=(10, 5))
        ctk.CTkButton(filter_frame, text="🔄 Сброс", width=80, command=self.reset_filters).pack(side="right")

        # === Таблица слов ===
        table_frame = ctk.CTkFrame(self.win)
        table_frame.pack(pady=10, padx=40, fill="both", expand=True)

        self.scrollable_frame = ctk.CTkScrollableFrame(table_frame)
        self.scrollable_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Для массового удаления
        self.selected_ids = {}

        # === Кнопки внизу ===
        btn_frame = ctk.CTkFrame(self.win, fg_color="transparent")
        btn_frame.pack(pady=(10, 20), padx=40, fill="x")

        # Кнопка "Удалить выбранные" — только для админа
        if self.user["role"] == "admin":
            self.bulk_delete_btn = ctk.CTkButton(
                btn_frame,
                text="🗑️ Удалить выбранные",
                fg_color="red",
                hover_color="darkred",
                command=self.bulk_delete_words
            )
            self.bulk_delete_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

        # Кнопка "Добавить слово" — доступна и студенту, и админу
        ctk.CTkButton(
            btn_frame,
            text="➕ Добавить слово",
            command=self.open_add_word
        ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        # Кнопка "Назад"
        ctk.CTkButton(
            btn_frame,
            text="⬅️ Назад",
            fg_color="gray",
            command=self.win.destroy
        ).pack(side="left", expand=True, fill="x")

        self.load_words()

    def _role_rus(self):
        roles = {"admin": "Администратор", "student": "Студент"}
        return roles.get(self.user["role"], self.user["role"])

    def reset_filters(self):
        self.search_entry.delete(0, "end")
        self.level_var.set("Все уровни")
        self.pos_var.set("Все части")
        if self.user["role"] == "admin":
            self.user_var.set("Все пользователи")
        self.load_words()

    def load_users_into_combobox(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name FROM users ORDER BY name")
        users = [row["name"] for row in cur.fetchall()]
        conn.close()
        self.user_combo.configure(values=["Все пользователи"] + users)
        self.user_combo.set("Все пользователи")

    def load_words(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_ids.clear()

        query = self.search_entry.get().strip().lower()
        level_filter = self.level_var.get()
        pos_filter = self.pos_var.get()
        user_filter = self.user_var.get() if self.user["role"] == "admin" else None

        conn = get_connection()
        cur = conn.cursor()

        # 🔐 SQL-запрос: студент видит только свои + системные (от админа)
        sql = """
            SELECT v.*, u.name as user_name
            FROM vocabulary v
            JOIN users u ON v.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        if self.user["role"] == "student":
            sql += " AND (v.user_id = ? OR v.is_admin_preset = 1)"
            params.append(self.user["user_id"])

        # Админ может фильтровать по пользователю
        if self.user["role"] == "admin" and user_filter and user_filter != "Все пользователи":
            sql += " AND u.name = ?"
            params.append(user_filter)

        sql += " ORDER BY v.word_id DESC"

        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            # Локальные фильтры по поиску, уровню, части речи
            if query and query not in row["word"].lower():
                continue
            if level_filter != "Все уровни" and row["word_level"] != level_filter:
                continue
            if pos_filter != "Все части" and row["part_of_speech"] != pos_filter:
                continue

            # Защита: студент не видит чужие не-системные слова
            if self.user["role"] == "student":
                if row["user_id"] != self.user["user_id"] and not row["is_admin_preset"]:
                    continue

            # === Отображение слова ===
            frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=("gray90", "gray20"))
            frame.pack(fill="x", pady=5, padx=10)

            # Право на редактирование: только если это НЕ системное слово
            can_edit = (
                self.user["role"] == "admin"
                or (self.user["role"] == "student" and row["user_id"] == self.user["user_id"] and not row["is_admin_preset"])
            )

            # Чекбокс для удаления (только у админа или если можно редактировать)
            if self.user["role"] == "admin" or can_edit:
                var = ctk.BooleanVar(value=False)
                checkbox = ctk.CTkCheckBox(frame, text="", width=30, variable=var)
                checkbox.pack(side="left", padx=(10, 5), pady=10)
                self.selected_ids[row["word_id"]] = var
            else:
                ctk.CTkLabel(frame, text="", width=40).pack(side="left")

            # Контент
            content = ctk.CTkFrame(frame, fg_color="transparent")
            content.pack(fill="x", side="left", padx=10, pady=10)

            bold_text = f"#{row['word_id']} {row['word']}"
            if row["is_admin_preset"]:
                bold_text += " (системное)"
            ctk.CTkLabel(content, text=bold_text, font=ctk.CTkFont(weight="bold"), anchor="w").pack(anchor="w")

            meta = f"Уровень: {row['word_level']} | Часть речи: {row['part_of_speech'] or '—'}"
            if self.user["role"] == "admin":
                meta += f" | Автор: {row['user_name']}"
            ctk.CTkLabel(content, text=meta, text_color="blue", font=ctk.CTkFont(size=12), anchor="w").pack(anchor="w", pady=(2, 2))

            if row["synonym"]:
                ctk.CTkLabel(content, text=f"Синоним: {row['synonym']}", text_color="gray", anchor="w").pack(anchor="w", pady=1)
            if row["antonym"]:
                ctk.CTkLabel(content, text=f"Антоним: {row['antonym']}", text_color="gray", anchor="w").pack(anchor="w", pady=1)
            if row["topic_id"]:
                topic_name = self.get_topic_name(row["topic_id"])
                ctk.CTkLabel(content, text=f"Тема: {topic_name}", text_color="purple", anchor="w").pack(anchor="w", pady=1)

            # Кнопки редактирования и удаления
            if can_edit:
                btns = ctk.CTkFrame(frame, fg_color="transparent")
                btns.pack(side="right", padx=10, pady=10)

                ctk.CTkButton(
                    btns,
                    text="✏️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    command=lambda r=row: self.open_edit_word(r)
                ).pack(pady=2)

                ctk.CTkButton(
                    btns,
                    text="🗑️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda wid=row["word_id"]: self.delete_word(wid)
                ).pack(pady=2)

    def get_topic_name(self, topic_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM topic WHERE topic_id = ?", (topic_id,))
        row = cur.fetchone()
        conn.close()
        return row["name"] if row else "—"

    def bulk_delete_words(self):
        selected = [wid for wid, var in self.selected_ids.items() if var.get()]
        if not selected:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить {len(selected)} слов(а)?"):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            placeholders = ",".join("?" * len(selected))
            cur.execute(f"DELETE FROM vocabulary WHERE word_id IN ({placeholders})", selected)
            conn.commit()
            messagebox.showinfo("Успех", f"Удалено {len(selected)} слов")
            self.load_words()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}")
        finally:
            conn.close()

    def open_add_word(self):
        self.open_word_form("Добавить слово")

    def open_edit_word(self, word):
        self.open_word_form("Редактировать слово", word)

    def open_word_form(self, title, word=None):
        form = ctk.CTkToplevel(self.win)
        form.title(title)
        form.geometry("700x700")
        form.transient(self.win)
        form.grab_set()
        form.focus_force()

        ctk.CTkLabel(form, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        # Слово
        ctk.CTkLabel(form, text="Слово*", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        word_entry = ctk.CTkEntry(form, placeholder_text="Например: run", height=40)
        word_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Синоним
        ctk.CTkLabel(form, text="Синоним", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        synonym_entry = ctk.CTkEntry(form, placeholder_text="Например: sprint")
        synonym_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Антоним
        ctk.CTkLabel(form, text="Антоним", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        antonym_entry = ctk.CTkEntry(form, placeholder_text="Например: walk")
        antonym_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Часть речи
        ctk.CTkLabel(form, text="Часть речи", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        pos_var = ctk.StringVar(value="noun")
        pos_combo = ctk.CTkComboBox(form, values=["noun", "verb", "adjective", "adverb", "pronoun", "preposition", "conjunction", "interjection"], variable=pos_var)
        pos_combo.pack(pady=(5, 15), padx=40, fill="x")

        # Уровень
        ctk.CTkLabel(form, text="Уровень", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        level_var = ctk.StringVar(value="B1")
        level_combo = ctk.CTkComboBox(form, values=["A1", "A1.1", "A1.2", "A2", "A2.1", "A2.2",
                                                    "B1", "B1.1", "B1.2", "B2", "B2.1", "B2.2",
                                                    "C1", "C1.1", "C1.2", "C2"], variable=level_var)
        level_combo.pack(pady=(5, 15), padx=40, fill="x")

        # Тема
        ctk.CTkLabel(form, text="Тема (опционально)", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        topic_var = ctk.StringVar()
        topic_combo = ctk.CTkComboBox(form, variable=topic_var)
        topic_combo.pack(pady=(5, 15), padx=40, fill="x")
        self.load_topics_into_combobox(topic_combo, topic_var)

        # Заполнение формы при редактировании
        if word:
            word_entry.insert(0, word["word"])
            synonym_entry.insert(0, word["synonym"] or "")
            antonym_entry.insert(0, word["antonym"] or "")
            pos_var.set(word["part_of_speech"] or "noun")
            level_var.set(word["word_level"] or "B1")
            topic_var.set(self.get_topic_name(word["topic_id"]) or "")

        def save():
            word_val = word_entry.get().strip()
            if not word_val:
                messagebox.showwarning("Ошибка", "Введите слово")
                return

            # Слова от админа — системные
            is_preset = self.user["role"] == "admin"

            conn = get_connection()
            cur = conn.cursor()
            try:
                topic_id = self.get_topic_id_by_name(topic_var.get()) if topic_var.get() else None
                user_id = self.user["user_id"]

                if word:  # Редактирование
                    # Защита: нельзя редактировать системные слова, если ты не админ
                    if word["is_admin_preset"] and self.user["role"] != "admin":
                        messagebox.showerror("Ошибка", "Нельзя редактировать системные слова")
                        return
                    cur.execute("""
                        UPDATE vocabulary SET word=?, synonym=?, antonym=?, part_of_speech=?, word_level=?, topic_id=?
                        WHERE word_id=?
                    """, (
                        word_val,
                        synonym_entry.get().strip(),
                        antonym_entry.get().strip(),
                        pos_var.get(),
                        level_var.get(),
                        topic_id,
                        word["word_id"]
                    ))
                else:  # Добавление
                    cur.execute("""
                        INSERT INTO vocabulary (word, synonym, antonym, part_of_speech, word_level, topic_id, user_id, is_admin_preset)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        word_val,
                        synonym_entry.get().strip(),
                        antonym_entry.get().strip(),
                        pos_var.get(),
                        level_var.get(),
                        topic_id,
                        user_id,
                        is_preset
                    ))
                conn.commit()
                messagebox.showinfo("Успех", "Слово сохранено!")
                form.destroy()
                self.load_words()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
            finally:
                conn.close()

        ctk.CTkButton(form, text="💾 Сохранить", height=40, command=save).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(form, text="Отмена", height=35, fg_color="gray", command=form.destroy).pack(pady=(0, 20), padx=40, fill="x")

    def load_topics_into_combobox(self, combobox, var):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM topic ORDER BY name")
        topics = [row["name"] for row in cur.fetchall()]
        conn.close()
        combobox.configure(values=topics)
        if topics:
            var.set(topics[0])

    def get_topic_id_by_name(self, name):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT topic_id FROM topic WHERE name = ?", (name,))
        row = cur.fetchone()
        conn.close()
        return row["topic_id"] if row else None

    def delete_word(self, word_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT is_admin_preset FROM vocabulary WHERE word_id = ?", (word_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Ошибка", "Слово не найдено")
            return

        # Студент не может удалять системные слова
        if row["is_admin_preset"] and self.user["role"] != "admin":
            messagebox.showerror("Ошибка", "Нельзя удалить системное слово")
            return

        if not messagebox.askyesno("Подтверждение", "Удалить слово?"):
            return

        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM vocabulary WHERE word_id = ?", (word_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Слово удалено")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()
            self.load_words()
