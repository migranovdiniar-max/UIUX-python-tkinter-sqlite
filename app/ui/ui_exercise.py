import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from app.db import get_connection

class ExerciseWindow:
    def __init__(self, user):
        self.user = user
        self.win = tk.Toplevel()
        self.win.title("Exercises")
        self.win.geometry("900x420")

        cols = ("exercise_id","problem","type","exercise_level","topic_id","rule_id")
        self.tree = ttk.Treeview(self.win, columns=cols, show="headings")
        for c in cols:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140)
        self.tree.pack(fill="both", expand=True, padx=6, pady=6)

        frame = tk.Frame(self.win); frame.pack(fill="x", pady=6)
        tk.Button(frame, text="Add Exercise", command=self.add_exercise).pack(side="left", padx=4)
        tk.Button(frame, text="Edit Exercise", command=self.edit_exercise).pack(side="left", padx=4)
        tk.Button(frame, text="Delete Exercise", command=self.delete_exercise).pack(side="left", padx=4)
        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=4)

        self.load_data()

    def load_data(self):
        for r in self.tree.get_children(): self.tree.delete(r)
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM exercise ORDER BY exercise_id DESC")
        for row in cur.fetchall():
            self.tree.insert("", "end", iid=row["exercise_id"], values=(
                row["exercise_id"], row["problem"][:80], row["type"], row["exercise_level"], row["topic_id"], row["rule_id"]
            ))
        conn.close()

    def load_topics(self):
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT topic_id, name FROM topic ORDER BY topic_id")
        rows = cur.fetchall(); conn.close()
        return [(r["topic_id"], r["name"]) for r in rows]

    def load_rules_for_topic(self, topic_id):
        conn = get_connection(); cur = conn.cursor()
        if topic_id is None:
            cur.execute("SELECT rule_id, title FROM grammar_rule ORDER BY rule_id")
        else:
            cur.execute("SELECT rule_id, title FROM grammar_rule WHERE topic_id = ? ORDER BY rule_id", (topic_id,))
        rows = cur.fetchall(); conn.close()
        return [(r["rule_id"], r["title"]) for r in rows]

    def add_exercise(self):
        dlg = ExerciseDialog(self.win, topics=self.load_topics(), load_rules=self.load_rules_for_topic)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                INSERT INTO exercise (problem, media_url, type, exercise_level, topic_id, rule_id)
                VALUES (?,?,?,?,?,?)
            """, (dlg.result["problem"], dlg.result["media_url"], dlg.result["type"], dlg.result["level"], dlg.result["topic_id"], dlg.result["rule_id"]))
            conn.commit(); conn.close()
            self.load_data()

    def edit_exercise(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Info", "Select exercise to edit")
            return
        ex_id = int(sel[0])
        conn = get_connection(); cur = conn.cursor()
        cur.execute("SELECT * FROM exercise WHERE exercise_id=?", (ex_id,))
        r = cur.fetchone(); conn.close()
        dlg = ExerciseDialog(self.win, data=r, topics=self.load_topics(), load_rules=self.load_rules_for_topic)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection(); cur = conn.cursor()
            cur.execute("""
                UPDATE exercise
                SET problem=?, media_url=?, type=?, exercise_level=?, topic_id=?, rule_id=?
                WHERE exercise_id=?
            """, (dlg.result["problem"], dlg.result["media_url"], dlg.result["type"], dlg.result["level"], dlg.result["topic_id"], dlg.result["rule_id"], ex_id))
            conn.commit(); conn.close()
            self.load_data()

    def delete_exercise(self):
        sel = self.tree.selection()
        if not sel: return
        if not messagebox.askyesno("Confirm", "Delete selected exercise? This will also delete related exercise_answer rows (ON DELETE CASCADE)."):
            return
        ex_id = int(sel[0])
        conn = get_connection(); cur = conn.cursor()
        cur.execute("DELETE FROM exercise WHERE exercise_id=?", (ex_id,))
        conn.commit(); conn.close()
        self.load_data()

class ExerciseDialog:
    def __init__(self, parent, data=None, topics=None, load_rules=None):
        self.result = None
        self.load_rules = load_rules
        self.top = tk.Toplevel(parent)
        self.top.title("Add / Edit Exercise")
        # Problem (multi-line)
        tk.Label(self.top, text="Problem").grid(row=0, column=0, sticky="nw")
        self.t_problem = tk.Text(self.top, width=60, height=6); self.t_problem.grid(row=0, column=1, pady=4)
        # media_url
        tk.Label(self.top, text="Media URL").grid(row=1, column=0, sticky="w")
        self.e_media = tk.Entry(self.top, width=50); self.e_media.grid(row=1, column=1, pady=2, sticky="w")
        # type and level
        tk.Label(self.top, text="Type").grid(row=2, column=0, sticky="w")
        self.e_type = tk.Entry(self.top); self.e_type.grid(row=2, column=1, sticky="w")
        tk.Label(self.top, text="Level").grid(row=3, column=0, sticky="w")
        self.e_level = tk.Entry(self.top); self.e_level.grid(row=3, column=1, sticky="w")
        # Topic combobox
        tk.Label(self.top, text="Topic").grid(row=4, column=0, sticky="w")
        topics = topics or []
        self.topic_map = {f"{t[0]}: {t[1]}": t[0] for t in topics}
        self.topic_combo = ttk.Combobox(self.top, values=list(self.topic_map.keys()), state="readonly", width=47)
        self.topic_combo.grid(row=4, column=1, sticky="w")
        self.topic_combo.bind("<<ComboboxSelected>>", self.on_topic_change)
        # Rule combobox (will be filled by topic)
        tk.Label(self.top, text="Grammar Rule (optional)").grid(row=5, column=0, sticky="w")
        self.rule_map = {}  # text -> id
        self.rule_combo = ttk.Combobox(self.top, values=[], state="readonly", width=47)
        self.rule_combo.grid(row=5, column=1, sticky="w")

        tk.Button(self.top, text="Save", command=self.on_save).grid(row=6, column=0, columnspan=2, pady=8)

        # fill values if editing
        if data:
            self.t_problem.insert("1.0", data["problem"] or "")
            self.e_media.insert(0, data["media_url"] or "")
            self.e_type.insert(0, data["type"] or "")
            self.e_level.insert(0, data["exercise_level"] or "")
            if data["topic_id"]:
                # set topic combo to matching "id: name"
                # try to find name for topic_id
                topics_all = topics
                for t in topics_all:
                    if t[0] == data["topic_id"]:
                        self.topic_combo.set(f"{t[0]}: {t[1]}")
                        break
            # load rules for this topic and set rule
            try:
                tid = data["topic_id"]
                rules = load_rules(tid)
                self.rule_map = {f"{r[0]}: {r[1]}": r[0] for r in rules}
                self.rule_combo["values"] = list(self.rule_map.keys())
                if data["rule_id"]:
                    for k, v in self.rule_map.items():
                        if v == data["rule_id"]:
                            self.rule_combo.set(k)
                            break
            except Exception:
                pass

    def on_topic_change(self, event=None):
        sel = self.topic_combo.get().strip()
        if not sel:
            self.rule_combo["values"] = []
            self.rule_map = {}
            return
        try:
            tid = int(sel.split(":")[0])
        except:
            tid = None
        rules = self.load_rules(tid)
        self.rule_map = {f"{r[0]}: {r[1]}": r[0] for r in rules}
        self.rule_combo["values"] = list(self.rule_map.keys())
        self.rule_combo.set("")  # reset selection

    def on_save(self):
        problem = self.t_problem.get("1.0", "end").strip()
        media = self.e_media.get().strip()
        typ = self.e_type.get().strip()
        level = self.e_level.get().strip()
        topic_text = self.topic_combo.get().strip()
        topic_id = None
        if topic_text:
            try:
                topic_id = int(topic_text.split(":")[0])
            except:
                topic_id = None
        rule_text = self.rule_combo.get().strip()
        rule_id = None
        if rule_text:
            try:
                rule_id = int(rule_text.split(":")[0])
            except:
                rule_id = None

        if not problem or not typ:
            messagebox.showerror("Error", "Problem and Type are required")
            return

        self.result = {
            "problem": problem,
            "media_url": media or None,
            "type": typ,
            "level": level or None,
            "topic_id": topic_id,
            "rule_id": rule_id
        }
        self.top.destroy()
