import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from app.db import get_connection

class TopicWindow:
    def __init__(self, user):
        self.user = user

        self.win = tk.Toplevel()
        self.win.title("Topics")
        self.win.geometry("600x380")

        cols = ("topic_id","name","description")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=180)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        frame = tk.Frame(self.win)
        frame.pack(fill="x", pady=6)

        self.btn_add = tk.Button(frame, text="Add Topic", command=self.add_topic)
        self.btn_add.pack(side="left", padx=4)

        self.btn_edit = tk.Button(frame, text="Edit Topic", command=self.edit_topic)
        self.btn_edit.pack(side="left", padx=4)

        self.btn_delete = tk.Button(frame, text="Delete Topic", command=self.delete_topic)
        self.btn_delete.pack(side="left", padx=4)

        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=4)

        # запрет редактирования для студента
        if self.user["role"] == "student":
            self.btn_add.config(state="disabled")
            self.btn_edit.config(state="disabled")
            self.btn_delete.config(state="disabled")

        self.load_data()

    def load_data(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT topic_id, name, description FROM topic ORDER BY topic_id")
        for row in cur.fetchall():
            self.tree.insert("", "end", iid=row["topic_id"],
                             values=(row["topic_id"], row["name"], row["description"] or ""))
        conn.close()

    def add_topic(self):
        if self.user["role"] == "student":
            return  # Защита от обхода
        dlg = TopicDialog(self.win)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("INSERT INTO topic (name, description) VALUES (?, ?)",
                        (dlg.result["name"], dlg.result["description"]))
            conn.commit(); conn.close()
            self.load_data()

    def edit_topic(self):
        if self.user["role"] == "student":
            return  # Защита
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a topic to edit")
            return
        tid = int(sel[0])
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM topic WHERE topic_id=?", (tid,))
        row = cur.fetchone(); conn.close()
        if not row:
            messagebox.showerror("Error", "Topic not found")
            return
        dlg = TopicDialog(self.win, data=row)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("UPDATE topic SET name=?, description=? WHERE topic_id=?",
                        (dlg.result["name"], dlg.result["description"], tid))
            conn.commit(); conn.close()
            self.load_data()

    def delete_topic(self):
        if self.user["role"] == "student":
            return  # Защита
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select a topic to delete")
            return
        if not messagebox.askyesno("Confirm", "Delete selected topic?"):
            return
        tid = int(sel[0])
        conn = get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM topic WHERE topic_id=?", (tid,))
        conn.commit(); conn.close()
        self.load_data()


class TopicDialog:
    def __init__(self, parent, data=None):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("Add / Edit Topic")
        tk.Label(self.top, text="Name").grid(row=0, column=0, sticky="w", padx=6, pady=4)
        self.e_name = tk.Entry(self.top, width=40); self.e_name.grid(row=0, column=1, pady=4)
        tk.Label(self.top, text="Description").grid(row=1, column=0, sticky="nw", padx=6, pady=4)
        self.t_desc = tk.Text(self.top, width=40, height=6); self.t_desc.grid(row=1, column=1, pady=4)
        tk.Button(self.top, text="Save", command=self.on_save).grid(row=2, column=0, columnspan=2, pady=8)

        if data:
            self.e_name.insert(0, data["name"])
            if data["description"]:
                self.t_desc.insert("1.0", data["description"])

    def on_save(self):
        name = self.e_name.get().strip()
        desc = self.t_desc.get("1.0", "end").strip()
        if not name:
            messagebox.showerror("Error", "Topic name required")
            return
        self.result = {"name": name, "description": desc}
        self.top.destroy()
