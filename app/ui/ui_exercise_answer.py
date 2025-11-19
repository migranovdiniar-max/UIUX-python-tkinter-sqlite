import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from app.db import get_connection


class ExerciseAnswerWindow:
    def __init__(self, user):
        self.user = user

        #  проверка роли
        if self.user["role"] == "student":
            import tkinter.messagebox as messagebox
            messagebox.showerror("Access denied", "You have no permission to view model answers.")
            return  # окно не создаём

        self.win = tk.Toplevel()
        self.win.title("Exercise Answers (master)")
        self.win.geometry("800x420")

        cols = ("answer_id","exercise_id","answer_text","part_number")
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
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM exercise_answer")
        for row in cur.fetchall():
            self.tree.insert("", "end", iid=row["answer_id"], values=(row["answer_id"], row["exercise_id"], row["answer_text"], row["part_number"]))
        conn.close()

    def add_answer(self):
        dlg = ExAnswerDialog(self.win)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("INSERT INTO exercise_answer (exercise_id, answer_text, part_number) VALUES (?,?,?)",
                        (dlg.result["exercise_id"], dlg.result["answer_text"], dlg.result["part_number"]))
            conn.commit(); conn.close()
            self.load_data()

    def edit_answer(self):
        sel = self.tree.selection()
        if not sel: return
        aid = sel[0]
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM exercise_answer WHERE answer_id=?", (aid,))
        r = cur.fetchone(); conn.close()
        dlg = ExAnswerDialog(self.win, data=r)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("UPDATE exercise_answer SET exercise_id=?, answer_text=?, part_number=? WHERE answer_id=?",
                        (dlg.result["exercise_id"], dlg.result["answer_text"], dlg.result["part_number"], aid))
            conn.commit(); conn.close()
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
