import tkinter as tk
from tkinter import ttk, messagebox
from app.db import get_connection
import sqlite3


class DefinitionExerciseWindow:
    def __init__(self, user):
        self.user = user
        self.win = tk.Toplevel()
        self.win.title("Definition ? Exercise Links")
        self.win.geometry("600x400")

        cols = ("definition_id", "word", "exercise_id", "problem")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True)

        frame = tk.Frame(self.win); frame.pack(fill="x", pady=6)
        tk.Button(frame, text="Link", command=self.link).pack(side="left", padx=5)
        tk.Button(frame, text="Unlink", command=self.unlink).pack(side="left", padx=5)
        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=5)

        self.load_data()

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT de.definition_id, d.word, de.exercise_id, e.problem
            FROM definition_exercise de
            JOIN definition d ON d.definition_id = de.definition_id
            JOIN exercise e ON e.exercise_id = de.exercise_id
            ORDER BY d.word
        """)
        for row in cur.fetchall():
            iid = f"{row['definition_id']}_{row['exercise_id']}"
            self.tree.insert("", "end", iid=iid, values=(
                row["definition_id"], row["word"], row["exercise_id"], row["problem"][:60]
            ))
        conn.close()

    def link(self):
        # Диалог выбора definition и exercise
        definitions = self.load_definitions()
        exercises = self.load_exercises()
        if not definitions or not exercises:
            messagebox.showinfo("Info", "No definitions or exercises")
            return

        dlg = LinkDialog(self.win, definitions, exercises)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection()
            cur = conn.cursor()
            try:
                cur.execute("""
                    INSERT INTO definition_exercise (definition_id, exercise_id)
                    VALUES (?, ?)
                """, (dlg.result["def_id"], dlg.result["ex_id"]))
                conn.commit()
                self.load_data()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Link already exists")
            finally:
                conn.close()

    def unlink(self):
        sel = self.tree.selection()
        if not sel: return
        iid = sel[0]
        def_id, ex_id = map(int, iid.split("_"))
        if not messagebox.askyesno("Confirm", "Unlink?"):
            return
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM definition_exercise WHERE definition_id=? AND exercise_id=?", (def_id, ex_id))
        conn.commit()
        conn.close()
        self.load_data()

    def load_definitions(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT definition_id, word FROM definition")
        rows = cur.fetchall()
        conn.close()
        return [(r["definition_id"], r["word"]) for r in rows]

    def load_exercises(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT exercise_id, problem FROM exercise")
        rows = cur.fetchall()
        conn.close()
        return [(r["exercise_id"], r["problem"]) for r in rows]

class LinkDialog:
    def __init__(self, parent, definitions, exercises):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("Link Definition and Exercise")
        tk.Label(self.top, text="Definition").grid(row=0, column=0)
        self.def_combo = ttk.Combobox(self.top, values=[f"{d[0]}: {d[1]}" for d in definitions], state="readonly")
        self.def_combo.grid(row=0, column=1)
        tk.Label(self.top, text="Exercise").grid(row=1, column=0)
        self.ex_combo = ttk.Combobox(self.top, values=[f"{e[0]}: {e[1]}" for e in exercises], state="readonly")
        self.ex_combo.grid(row=1, column=1)
        tk.Button(self.top, text="Save", command=self.on_save).grid(row=2, column=0, columnspan=2)

    def on_save(self):
        try:
            def_id = int(self.def_combo.get().split(":")[0])
            ex_id = int(self.ex_combo.get().split(":")[0])
            self.result = {"def_id": def_id, "ex_id": ex_id}
            self.top.destroy()
        except:
            messagebox.showerror("Error", "Invalid selection")
