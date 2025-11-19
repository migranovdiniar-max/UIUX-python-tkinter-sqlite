import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from app.db import get_connection

class DefinitionWindow:
    def __init__(self, user):
        self.user = user
        self.win = tk.Toplevel()
        self.win.title("Definitions")
        self.win.geometry("820x420")
        self.can_edit = self.user["role"] != "student"  # студент не редактирует

        cols = ("definition_id","word_id","word","ru_translation","def","example")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=130)
        self.tree.pack(fill="both", expand=True)

        frame = tk.Frame(self.win); frame.pack(fill="x", pady=6)
        tk.Button(frame, text="Add Definition", command=self.add_def).pack(side="left", padx=5)
        tk.Button(frame, text="Edit Definition", command=self.edit_def).pack(side="left", padx=5)
        tk.Button(frame, text="Delete", command=self.delete_def).pack(side="left", padx=5)
        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=5)

        self.load_data()

    def load_words(self):
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT word_id, word FROM vocabulary")
        rows = cur.fetchall(); conn.close()
        return [(r["word_id"], r["word"]) for r in rows]

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection(); cur = conn.cursor()
        cur.execute("""
            SELECT d.definition_id, d.word_id, v.word, d.ru_translation, d.def, d.example
            FROM definition d
            LEFT JOIN vocabulary v ON v.word_id = d.word_id
        """)
        for row in cur.fetchall():
            self.tree.insert("", "end", iid=row["definition_id"], values=(
                row["definition_id"], row["word_id"], row["word"] or "", row["ru_translation"], row["def"], row["example"]
            ))
        conn.close()

    def add_def(self):
        dlg = DefinitionDialog(self.win, words=self.load_words())
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("INSERT INTO definition (word_id, ru_translation, def, example) VALUES (?,?,?,?)",
                        (dlg.result["word_id"], dlg.result["ru"], dlg.result["def"], dlg.result["example"]))
            conn.commit(); conn.close()
            self.load_data()

    def edit_def(self):
        sel = self.tree.selection()
        if not sel: return
        did = sel[0]
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM definition WHERE definition_id=?", (did,))
        r = cur.fetchone(); conn.close()
        dlg = DefinitionDialog(self.win, data=r, words=self.load_words())
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("UPDATE definition SET word_id=?, ru_translation=?, def=?, example=? WHERE definition_id=?",
                        (dlg.result["word_id"], dlg.result["ru"], dlg.result["def"], dlg.result["example"], did))
            conn.commit(); conn.close()
            self.load_data()

    def delete_def(self):
        sel = self.tree.selection()
        if not sel: return
        if not messagebox.askyesno("Confirm", "Delete this definition?"): return
        did = sel[0]
        conn = get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM definition WHERE definition_id=?", (did,))
        conn.commit(); conn.close()
        self.load_data()

class DefinitionDialog:
    def __init__(self, parent, data=None, words=None):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("Add/Edit Definition")
        tk.Label(self.top, text="Word").grid(row=0, column=0)
        self.word_combo = ttk.Combobox(self.top, values=[f"{w[0]}: {w[1]}" for w in (words or [])])
        self.word_combo.grid(row=0, column=1)
        tk.Label(self.top, text="RU translation").grid(row=1, column=0)
        self.e_ru = tk.Entry(self.top); self.e_ru.grid(row=1, column=1)
        tk.Label(self.top, text="Definition").grid(row=2, column=0)
        self.e_def = tk.Entry(self.top); self.e_def.grid(row=2, column=1)
        tk.Label(self.top, text="Example").grid(row=3, column=0)
        self.e_ex = tk.Entry(self.top); self.e_ex.grid(row=3, column=1)
        tk.Button(self.top, text="Save", command=self.on_save).grid(row=4, column=0, columnspan=2)

        if data:
            if data["word_id"]:
                self.word_combo.set(f"{data['word_id']}")
            self.e_ru.insert(0, data["ru_translation"] or "")
            self.e_def.insert(0, data["def"] or "")
            self.e_ex.insert(0, data["example"] or "")

    def on_save(self):
        word_text = self.word_combo.get().strip()
        word_id = None
        if word_text:
            try:
                word_id = int(word_text.split(":")[0])
            except:
                word_id = None
        self.result = {
            "word_id": word_id,
            "ru": self.e_ru.get().strip(),
            "def": self.e_def.get().strip(),
            "example": self.e_ex.get().strip()
        }
        self.top.destroy()
