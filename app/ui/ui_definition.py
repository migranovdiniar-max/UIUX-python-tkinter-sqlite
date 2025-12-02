# app/ui/ui_definition.py
import customtkinter as ctk
from tkinter import messagebox
from app.db import get_connection


class DefinitionWindow:
    def __init__(self, user):
        self.user = user
        self.win = ctk.CTkToplevel()
        self.win.title("📖 Определения")
        self.win.geometry("900x700")
        self.win.transient()
        self.win.grab_set()
        self.win.focus_force()

        # Заголовок
        ctk.CTkLabel(
            self.win,
            text="Управление определениями",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(20, 10))

        subtitle = f"Роль: {self._role_rus()}"
        ctk.CTkLabel(self.win, text=subtitle, text_color="gray").pack(pady=(0, 20))

        # === Фильтры ===
        filter_frame = ctk.CTkFrame(self.win)
        filter_frame.pack(pady=(0, 10), padx=40, fill="x")

        # Поиск по слову (только слово, без ID)
        ctk.CTkLabel(filter_frame, text="🔍 Поиск по слову", anchor="w").pack(pady=(0, 5), anchor="w")
        self.search_entry = ctk.CTkEntry(filter_frame, placeholder_text="Введите слово...")
        self.search_entry.pack(pady=(5, 10), fill="x")

        # Сортировка по ID
        ctk.CTkLabel(filter_frame, text="↕️ Сортировка по ID", anchor="w").pack(pady=(0, 5), anchor="w")
        self.sort_var = ctk.StringVar(value="По убыванию")
        self.sort_combo = ctk.CTkComboBox(
            filter_frame,
            values=["По возрастанию", "По убыванию"],
            variable=self.sort_var
        )
        self.sort_combo.pack(pady=(5, 10), fill="x")

        # Фильтр по пользователю (только для админа)
        self.user_var = ctk.StringVar(value="Все пользователи")
        self.user_combo = ctk.CTkComboBox(filter_frame, variable=self.user_var, state="disabled")
        if self.user["role"] == "admin":
            ctk.CTkLabel(filter_frame, text="👤 Фильтр по пользователю", anchor="w").pack(pady=(0, 5), anchor="w")
            self.user_combo.pack(pady=(5, 10), fill="x")
            self.load_users()

        # Кнопки
        btns = ctk.CTkFrame(filter_frame, fg_color="transparent")
        btns.pack(fill="x", pady=(10, 0))

        ctk.CTkButton(btns, text="🎯 Применить", command=self.load_data).pack(side="left", padx=(0, 10), expand=True, fill="x")
        ctk.CTkButton(btns, text="🔄 Сброс", command=self.reset_filters).pack(side="left", expand=True, fill="x")

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
                command=self.bulk_delete_defs
            )
            self.bulk_delete_btn.pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="➕ Добавить определение",
            command=self.open_add_def
        ).pack(side="left", padx=(0, 10), expand=True, fill="x")

        ctk.CTkButton(
            btn_frame,
            text="⬅️ Назад",
            fg_color="gray",
            command=self.win.destroy
        ).pack(side="left", expand=True, fill="x")

        # Загрузка данных
        self.load_words_for_combo()
        self.load_data()

    def _role_rus(self):
        roles = {"admin": "Администратор", "student": "Студент"}
        return roles.get(self.user["role"], self.user["role"])

    def reset_filters(self):
        self.search_entry.delete(0, "end")
        self.sort_var.set("По убыванию")
        if self.user["role"] == "admin":
            self.user_var.set("Все пользователи")
        self.load_data()

    def load_users(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name FROM users ORDER BY name")
        users = [row["name"] for row in cur.fetchall()]
        conn.close()
        self.user_combo.configure(state="readonly", values=["Все пользователи"] + users)
        self.user_combo.set("Все пользователи")

    def load_words_for_combo(self):
        conn = get_connection()
        cur = conn.cursor()

        # Студент видит только свои + системные слова
        if self.user["role"] == "student":
            cur.execute("""
                SELECT word_id, word FROM vocabulary
                WHERE user_id = ? OR is_admin_preset = 1
            """, (self.user["user_id"],))
        else:
            cur.execute("SELECT word_id, word FROM vocabulary ORDER BY word")

        words = [row["word"] for row in cur.fetchall()]
        conn.close()

        # Передаём только слова (без ID) в комбобокс
        self.word_combo = ctk.CTkComboBox(self.win, values=words)
        self.word_combo.set("Выберите слово")  # или оставить пустым
        # Не показываем пока — используем только внутри формы

    def load_data(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.selected_ids.clear()

        search_query = self.search_entry.get().strip().lower()
        sort_order = "ASC" if self.sort_var.get() == "По возрастанию" else "DESC"
        user_filter = self.user_var.get() if self.user["role"] == "admin" else None

        conn = get_connection()
        cur = conn.cursor()

        # Основной запрос
        sql = """
            SELECT d.definition_id, d.word_id, d.ru_translation, d.def, d.example,
                   v.word, u.name as author, d.user_id as def_user_id, v.is_admin_preset
            FROM definition d
            JOIN vocabulary v ON d.word_id = v.word_id
            JOIN users u ON d.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        # Студент: видит только:
        # - свои определения
        # - определения к системным словам (is_admin_preset = 1)
        if self.user["role"] == "student":
            sql += " AND (d.user_id = ? OR v.is_admin_preset = 1)"
            params.append(self.user["user_id"])

        # Фильтр по пользователю (админ)
        if user_filter and user_filter != "Все пользователи":
            sql += " AND u.name = ?"
            params.append(user_filter)

        sql += f" ORDER BY d.definition_id {sort_order}"

        cur.execute(sql, params)
        rows = cur.fetchall()
        conn.close()

        for row in rows:
            # Локальный фильтр: студент не должен видеть чужие определения к не-системным словам
            if self.user["role"] == "student":
                if row["def_user_id"] != self.user["user_id"] and not row["is_admin_preset"]:
                    continue

            # Фильтр по поиску (по слову)
            if search_query and search_query not in row["word"].lower():
                continue

            frame = ctk.CTkFrame(self.scrollable_frame, corner_radius=10, fg_color=("gray90", "gray20"))
            frame.pack(fill="x", pady=5, padx=10)

            # Право редактирования
            can_edit = (
                self.user["role"] == "admin" or
                (self.user["role"] == "student" and row["def_user_id"] == self.user["user_id"])
            )

            # Чекбокс (удаление)
            if self.user["role"] == "admin" or can_edit:
                var = ctk.BooleanVar(value=False)
                checkbox = ctk.CTkCheckBox(frame, text="", width=30, variable=var)
                checkbox.pack(side="left", padx=(10, 5), pady=10)
                self.selected_ids[row["definition_id"]] = var
            else:
                ctk.CTkLabel(frame, text="", width=40).pack(side="left")  # выравнивание

            # Контент
            content = ctk.CTkFrame(frame, fg_color="transparent")
            content.pack(fill="x", side="left", padx=10, pady=10)

            # Заголовок
            bold_text = f"#{row['definition_id']} «{row['word']}»"
            if row["is_admin_preset"]:
                bold_text += " (системное)"
            ctk.CTkLabel(
                content,
                text=bold_text,
                font=ctk.CTkFont(weight="bold"),
                anchor="w"
            ).pack(anchor="w")

            # Мета
            meta = f"Перевод: {row['ru_translation'] or '—'}"
            if self.user["role"] == "admin":
                meta += f" | Автор: {row['author']}"
            ctk.CTkLabel(
                content,
                text=meta,
                text_color="blue",
                font=ctk.CTkFont(size=12),
                anchor="w"
            ).pack(anchor="w", pady=(2, 2))

            # Определение и пример
            if row["def"]:
                ctk.CTkLabel(
                    content,
                    text=f"🔹 {row['def']}",
                    wraplength=500,
                    justify="left",
                    anchor="w",
                    text_color="gray"
                ).pack(anchor="w", pady=(2, 2))

            if row["example"]:
                ctk.CTkLabel(
                    content,
                    text=f"📌 Пример: {row['example']}",
                    wraplength=500,
                    justify="left",
                    anchor="w",
                    text_color="green"
                ).pack(anchor="w", pady=(2, 2))

            # Кнопки редактирования
            if can_edit:
                btns = ctk.CTkFrame(frame, fg_color="transparent")
                btns.pack(side="right", padx=10, pady=10)

                ctk.CTkButton(
                    btns,
                    text="✏️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    command=lambda r=row: self.open_edit_def(r)
                ).pack(pady=2)

                ctk.CTkButton(
                    btns,
                    text="🗑️",
                    width=60,
                    height=30,
                    font=ctk.CTkFont(size=12),
                    fg_color="red",
                    hover_color="darkred",
                    command=lambda did=row["definition_id"]: self.delete_def(did)
                ).pack(pady=2)

    def open_add_def(self):
        # Открываем форму с выбором слова
        words = self.get_available_words()
        if not words:
            messagebox.showwarning("Ошибка", "Нет доступных слов для добавления определения.")
            return
        self.open_def_form("Добавить определение", word_choices=words)

    def open_edit_def(self, definition):
        self.open_def_form("Редактировать определение", definition=definition, word_choices=self.get_available_words())

    def get_available_words(self):
        """Возвращает список слов, к которым студент может добавить определение"""
        conn = get_connection()
        cur = conn.cursor()

        if self.user["role"] == "student":
            cur.execute("""
                SELECT word_id, word FROM vocabulary
                WHERE user_id = ? OR is_admin_preset = 1
            """, (self.user["user_id"],))
        else:
            cur.execute("SELECT word_id, word FROM vocabulary ORDER BY word")

        rows = cur.fetchall()
        conn.close()
        return [(r["word_id"], r["word"]) for r in rows]

    def open_def_form(self, title, definition=None, word_choices=None):
        form = ctk.CTkToplevel(self.win)
        form.title(title)
        form.geometry("700x600")
        form.transient(self.win)
        form.grab_set()
        form.focus_force()

        ctk.CTkLabel(form, text=title, font=ctk.CTkFont(size=18, weight="bold")).pack(pady=20)

        # Слово
        ctk.CTkLabel(form, text="Слово*", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        word_var = ctk.StringVar()
        word_combo = ctk.CTkComboBox(form, variable=word_var)
        word_combo.pack(pady=(5, 15), padx=40, fill="x")
        word_combo.configure(values=[word for _, word in word_choices or []])

        # Перевод
        ctk.CTkLabel(form, text="Перевод (RU)", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        ru_entry = ctk.CTkEntry(form, placeholder_text="например: бежать")
        ru_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Определение
        ctk.CTkLabel(form, text="Определение*", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        def_entry = ctk.CTkTextbox(form, height=100)
        def_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Пример
        ctk.CTkLabel(form, text="Пример", anchor="w").pack(pady=(10, 0), padx=40, anchor="w")
        example_entry = ctk.CTkTextbox(form, height=80)
        example_entry.pack(pady=(5, 15), padx=40, fill="x")

        # Заполнение при редактировании
        if definition:
            word_combo.set(definition["word"])
            ru_entry.insert(0, definition["ru_translation"] or "")
            def_entry.insert("0.0", definition["def"] or "")
            example_entry.insert("0.0", definition["example"] or "")

        def save():
            word_name = word_var.get().strip()
            ru = ru_entry.get().strip()
            definition_text = def_entry.get("0.0", "end").strip()
            example = example_entry.get("0.0", "end").strip()

            if not word_name:
                messagebox.showwarning("Ошибка", "Выберите слово")
                return
            if not definition_text:
                messagebox.showwarning("Ошибка", "Введите определение")
                return

            # Найдём word_id
            word_id = None
            for wid, word in word_choices or []:
                if word == word_name:
                    word_id = wid
                    break

            conn = get_connection()
            cur = conn.cursor()
            try:
                if definition:
                    # Проверка прав при редактировании
                    if self.user["role"] == "student" and definition["def_user_id"] != self.user["user_id"]:
                        messagebox.showerror("Ошибка", "Нельзя редактировать чужое определение")
                        return
                    if self.user["role"] == "student" and definition["is_admin_preset"]:
                        messagebox.showerror("Ошибка", "Нельзя редактировать определение к системному слову")
                        return

                    cur.execute("""
                        UPDATE definition SET word_id=?, ru_translation=?, def=?, example=?
                        WHERE definition_id=?
                    """, (word_id, ru, definition_text, example, definition["definition_id"]))
                else:
                    cur.execute("""
                        INSERT INTO definition (word_id, user_id, ru_translation, def, example)
                        VALUES (?, ?, ?, ?, ?)
                    """, (word_id, self.user["user_id"], ru, definition_text, example))

                conn.commit()
                messagebox.showinfo("Успех", "Определение сохранено!")
                form.destroy()
                self.load_data()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
            finally:
                conn.close()

        ctk.CTkButton(form, text="💾 Сохранить", height=40, command=save).pack(pady=10, padx=40, fill="x")
        ctk.CTkButton(form, text="Отмена", height=35, fg_color="gray", command=form.destroy).pack(pady=(0, 20), padx=40, fill="x")

    def bulk_delete_defs(self):
        selected = [did for did, var in self.selected_ids.items() if var.get()]
        if not selected:
            messagebox.showinfo("Информация", "Ничего не выбрано")
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить {len(selected)} определений?"):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            placeholders = ",".join("?" * len(selected))
            cur.execute(f"DELETE FROM definition WHERE definition_id IN ({placeholders})", selected)
            conn.commit()
            messagebox.showinfo("Успех", f"Удалено {len(selected)} определений")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при удалении: {e}")
        finally:
            conn.close()

    def delete_def(self, def_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT d.user_id, v.is_admin_preset
            FROM definition d
            JOIN vocabulary v ON d.word_id = v.word_id
            WHERE d.definition_id = ?
        """, (def_id,))
        row = cur.fetchone()
        conn.close()

        if not row:
            messagebox.showerror("Ошибка", "Определение не найдено")
            return

        # Проверка прав
        if self.user["role"] == "student":
            if row["user_id"] != self.user["user_id"]:
                messagebox.showerror("Ошибка", "Нельзя удалить чужое определение")
                return
            if row["is_admin_preset"]:
                messagebox.showerror("Ошибка", "Нельзя удалить определение к системному слову")
                return

        if not messagebox.askyesno("Подтверждение", "Удалить определение?"):
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM definition WHERE definition_id = ?", (def_id,))
            conn.commit()
            messagebox.showinfo("Успех", "Определение удалено")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
        finally:
            conn.close()
