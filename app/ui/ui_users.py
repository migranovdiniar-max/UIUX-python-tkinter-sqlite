import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from app.db import get_connection

class UsersWindow:
    def __init__(self, user):
        self.user = user
        self.win = tk.Toplevel()
        self.win.title("Users Management")
        self.win.geometry("700x400")

        self.tree = ttk.Treeview(self.win, columns=("name","email","role","current_level","start_date","target_level"), show="headings")
        for col, title in [("name","Name"),("email","Email"),("role","Role"),
                           ("current_level","Current Level"),("start_date","Start Date"),("target_level","Target Level")]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True)

        frame = tk.Frame(self.win)
        frame.pack(fill="x", pady=6)
        tk.Button(frame, text="Add User", command=self.add_user).pack(side="left", padx=5)
        tk.Button(frame, text="Edit User", command=self.edit_user).pack(side="left", padx=5)
        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=5)
        self.load_data()

    def load_data(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, name, email, role, current_level, start_date, target_level FROM users")
        for row in cur.fetchall():
            self.tree.insert("", "end", iid=row["user_id"], values=(row["name"], row["email"], row["role"], row["current_level"], row["start_date"], row["target_level"]))
        conn.close()

    def add_user(self):
        dlg = UserDialog(self.win)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO users (name,email,role,current_level,start_date,target_level)
                VALUES (?,?,?,?,?,?)
            """, (dlg.result["name"], dlg.result["email"], dlg.result["role"], dlg.result["current_level"], dlg.result["start_date"], dlg.result["target_level"]))
            conn.commit()
            conn.close()
            self.load_data()

    def edit_user(self):
        sel = self.tree.selection()
        if not sel:
            return
        user_id = sel[0]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        r = cur.fetchone()
        conn.close()
        dlg = UserDialog(self.win, data=r)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("""
                UPDATE users
                SET name=?, email=?, role=?, current_level=?, start_date=?, target_level=?
                WHERE user_id=?
            """, (dlg.result["name"], dlg.result["email"], dlg.result["role"], dlg.result["current_level"], dlg.result["start_date"], dlg.result["target_level"], user_id))
            conn.commit()
            conn.close()
            self.load_data()

class UserDialog:
    def __init__(self, parent, data=None):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("Add / Edit User")
        labels = ["Name","Email","Role","Current Level","Start Date","Target Level"]
        self.entries = {}
        for i, label in enumerate(labels):
            tk.Label(self.top, text=label).grid(row=i, column=0)
            e = tk.Entry(self.top)
            e.grid(row=i, column=1)
            self.entries[label] = e
        tk.Button(self.top, text="Save", command=self.on_save).grid(row=len(labels), column=0, columnspan=2)
        if data:
            self.entries["Name"].insert(0, data["name"])
            self.entries["Email"].insert(0, data["email"])
            self.entries["Role"].insert(0, data["role"])
            self.entries["Current Level"].insert(0, data["current_level"] or "")
            self.entries["Start Date"].insert(0, data["start_date"] or "")
            self.entries["Target Level"].insert(0, data["target_level"] or "")

    def on_save(self):
        self.result = {k: self.entries[k].get().strip() for k in self.entries}
        self.top.destroy()
