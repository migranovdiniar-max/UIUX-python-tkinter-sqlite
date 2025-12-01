import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from app.db import get_connection


class ExerciseAnswerWindow:
    def __init__(self, user):
        self.user = user

        self.win = tk.Toplevel()
        self.win.title("Exercise Answers (master)")
        self.win.geometry("800x420")

        cols = ("answer_id", "exercise_id", "answer_text", "part_number", "user_name", "is_complete", "created_at")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=180)
        self.tree.pack(fill="both", expand=True)

        frame = tk.Frame(self.win); frame.pack(fill="x", pady=6)
        tk.Button(frame, text="Add Answer", command=self.add_answer).pack(side="left", padx=5)
        tk.Button(frame, text="Edit Answer", command=self.edit_answer).pack(side="left", padx=5)
        tk.Button(frame, text="Delete Answer", command=self.delete_answer).pack(side="left", padx=5)
        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=5)

        self.load_data()

    def load_data(self):
        for r in self.tree.get_children(): 
            self.tree.delete(r)

        conn = get_connection()
        cur = conn.cursor()

        if self.user["role"] == "student":
            # Студент видит ТОЛЬКО свои ответы
            cur.execute("""
                SELECT ea.answer_id, ea.exercise_id, ea.answer_text, ea.part_number,
                    ea.is_complete, strftime('%d.%m.%Y %H:%M', ea.created_at) AS created_at
                FROM exercise_answer ea
                WHERE ea.user_id = ?
                ORDER BY ea.created_at DESC
            """, (self.user["user_id"],))
        else:
            # Админ/учитель видит ВСЕ пользовательские ответы + может редактировать
            cur.execute("""
                SELECT ea.answer_id, ea.exercise_id, ea.answer_text, ea.part_number,
                    u.name AS user_name, ea.is_complete, 
                    strftime('%d.%m.%Y %H:%M', ea.created_at) AS created_at
                FROM exercise_answer ea
                LEFT JOIN users u ON u.user_id = ea.user_id
                WHERE ea.user_id IS NOT NULL
                ORDER BY ea.created_at DESC
            """)

        for row in cur.fetchall():
            values = (
                row["answer_id"],
                row["exercise_id"],
                row["answer_text"],
                row["part_number"],
                row["user_name"] if self.user["role"] != "student" else "",
                row["is_complete"],
                row["created_at"]
            )
            self.tree.insert("", "end", iid=row["answer_id"], values=values)

        conn.close()
    
    def add_answer(self):
        ex_id = simpledialog.askinteger("Exercise ID", "Enter Exercise ID:", parent=self.win)
        if ex_id is None: return
        ans = simpledialog.askstring("Your Answer", "Enter your answer:", parent=self.win)
        if ans is None or not ans.strip(): return

        # Только студент может добавить за себя
        if self.user["role"] == "student":
            user_id = self.user["user_id"]
        else:
            # Админ может выбрать user_id (упрощённо — можно оставить ввод)
            user_id = simpledialog.askinteger("User ID", "Enter User ID:", parent=self.win)
            if user_id is None: return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO exercise_answer 
                (exercise_id, answer_text, user_id, is_complete) 
                VALUES (?, ?, ?, 0)
            """, (ex_id, ans.strip(), user_id))
            conn.commit()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Error", str(e))
        finally:
            conn.close()


    def edit_answer(self):
        sel = self.tree.selection()
        if not sel: return
        aid = sel[0]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, answer_text FROM exercise_answer WHERE answer_id=?", (aid,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return

        # Проверка: только владелец или админ
        if self.user["role"] == "student" and row["user_id"] != self.user["user_id"]:
            messagebox.showerror("Access denied", "You can only edit your own answers")
            conn.close()
            return

        new_text = simpledialog.askstring("Edit Answer", "Update your answer:", initialvalue=row["answer_text"], parent=self.win)
        if new_text is None: return

        cur.execute("UPDATE exercise_answer SET answer_text=? WHERE answer_id=?", (new_text.strip(), aid))
        conn.commit()
        conn.close()
        self.load_data()


    def delete_answer(self):
        sel = self.tree.selection()
        if not sel: return
        if not messagebox.askyesno("Confirm", "Delete this exercise answer?"): return
        aid = sel[0]
        conn = get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM exercise_answer WHERE answer_id=?", (aid,))
        conn.commit(); conn.close()
        self.load_data()

class ExAnswerDialog:
    def __init__(self, parent, data=None):
        self.result = None
        self.top = tk.Toplevel(parent)
        tk.Label(self.top, text="Exercise ID").grid(row=0, column=0)
        self.e_ex = tk.Entry(self.top); self.e_ex.grid(row=0, column=1)
        tk.Label(self.top, text="Answer Text").grid(row=1, column=0)
        self.e_ans = tk.Entry(self.top); self.e_ans.grid(row=1, column=1)
        tk.Label(self.top, text="Part Number").grid(row=2, column=0)
        self.e_part = tk.Entry(self.top); self.e_part.grid(row=2, column=1)
        tk.Button(self.top, text="Save", command=self.on_save).grid(row=3, column=0, columnspan=2)

        if data:
            self.e_ex.insert(0, data["exercise_id"])
            self.e_ans.insert(0, data["answer_text"])
            self.e_part.insert(0, data["part_number"])

    def on_save(self):
        exid = None
        try:
            exid = int(self.e_ex.get().strip())
        except:
            exid = None
        part = 1
        try:
            part = int(self.e_part.get().strip())
        except:
            part = 1
        self.result = {
            "exercise_id": exid,
            "answer_text": self.e_ans.get().strip(),
            "part_number": part
        }
        self.top.destroy()
