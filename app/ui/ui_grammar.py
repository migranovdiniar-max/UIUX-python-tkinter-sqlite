import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from app.db import get_connection

class GrammarWindow:
    def __init__(self, user):
        self.user = user

        self.win = tk.Toplevel()
        self.win.title("Grammar Rules")
        self.win.geometry("800x420")

        cols = ("rule_id","title","grammar_level","topic_id","description","example")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=120)
        self.tree.pack(fill="both", expand=True)

        frame = tk.Frame(self.win)
        frame.pack(fill="x", pady=6)

        self.btn_add = tk.Button(frame, text="Add Rule", command=self.add_rule)
        self.btn_add.pack(side="left", padx=5)

        self.btn_edit = tk.Button(frame, text="Edit Rule", command=self.edit_rule)
        self.btn_edit.pack(side="left", padx=5)

        self.btn_delete = tk.Button(frame, text="Delete Rule", command=self.delete_rule)
        self.btn_delete.pack(side="left", padx=5)

        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=5)

        # запрет студенту
        if self.user["role"] == "student":
            self.btn_add.config(state="disabled")
            self.btn_edit.config(state="disabled")
            self.btn_delete.config(state="disabled")

        self.load_data()

    def load_topics(self):
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT topic_id, name FROM topic")
        topics = cur.fetchall()
        conn.close()
        return [(r["topic_id"], r["name"]) for r in topics]

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM grammar_rule")
        for row in cur.fetchall():
            self.tree.insert("", "end", iid=row["rule_id"], values=(
                row["rule_id"], row["title"], row["grammar_level"], row["topic_id"],
                row["description"], row["example"]
            ))
        conn.close()

    def add_rule(self):
        if self.user["role"] == "student":
            return  # защитa
        dlg = GrammarDialog(self.win, topics=self.load_topics())
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                INSERT INTO grammar_rule (title, description, example, grammar_level, topic_id)
                VALUES (?,?,?,?,?)
            """, (dlg.result["title"], dlg.result["description"], dlg.result["example"],
                  dlg.result["level"], dlg.result["topic_id"]))
            conn.commit(); conn.close()
            self.load_data()

    def edit_rule(self):
        if self.user["role"] == "student":
            return
        sel = self.tree.selection()
        if not sel: return
        rid = sel[0]
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM grammar_rule WHERE rule_id=?", (rid,))
        r = cur.fetchone(); conn.close()
        dlg = GrammarDialog(self.win, data=r, topics=self.load_topics())
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                UPDATE grammar_rule
                SET title=?, description=?, example=?, grammar_level=?, topic_id=?
                WHERE rule_id=?
            """, (dlg.result["title"], dlg.result["description"], dlg.result["example"],
                  dlg.result["level"], dlg.result["topic_id"], rid))
            conn.commit(); conn.close()
            self.load_data()

    def delete_rule(self):
        if self.user["role"] == "student":
            return
        sel = self.tree.selection()
        if not sel: return
        if not messagebox.askyesno("Confirm", "Delete selected rule?"): return
        rid = sel[0]
        conn = get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM grammar_rule WHERE rule_id=?", (rid,))
        conn.commit(); conn.close()
        self.load_data()


class GrammarDialog:
    def __init__(self, parent, data=None, topics=None):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("Add/Edit Grammar Rule")
        tk.Label(self.top, text="Title").grid(row=0, column=0)
        self.e_title = tk.Entry(self.top); self.e_title.grid(row=0, column=1)
        tk.Label(self.top, text="Level").grid(row=1, column=0)
        self.e_level = tk.Entry(self.top); self.e_level.grid(row=1, column=1)
        tk.Label(self.top, text="Topic").grid(row=2, column=0)

        self.topic_var = tk.StringVar(self.top)
        topics = topics or []
        self.topic_map = {str(t[0]): t[0] for t in topics}
        topic_names = [f"{t[0]}: {t[1]}" for t in topics]
        self.topic_menu = ttk.Combobox(self.top, values=topic_names)
        self.topic_menu.grid(row=2, column=1)

        tk.Label(self.top, text="Description").grid(row=3, column=0)
        self.e_desc = tk.Entry(self.top); self.e_desc.grid(row=3, column=1)
        tk.Label(self.top, text="Example").grid(row=4, column=0)
        self.e_ex = tk.Entry(self.top); self.e_ex.grid(row=4, column=1)

        tk.Button(self.top, text="Save", command=self.on_save).grid(row=5, column=0, columnspan=2)

        if data:
            self.e_title.insert(0, data["title"])
            self.e_level.insert(0, data["grammar_level"] or "")
            if data["topic_id"]:
                self.topic_menu.set(f"{data['topic_id']}")
            self.e_desc.insert(0, data["description"] or "")
            self.e_ex.insert(0, data["example"] or "")

    def on_save(self):
        topic_text = self.topic_menu.get().strip()
        topic_id = None
        if topic_text:
            parts = topic_text.split(":")
            try:
                topic_id = int(parts[0])
            except:
                topic_id = None
        self.result = {
            "title": self.e_title.get().strip(),
            "level": self.e_level.get().strip(),
            "topic_id": topic_id,
            "description": self.e_desc.get().strip(),
            "example": self.e_ex.get().strip()
        }
        self.top.destroy()
