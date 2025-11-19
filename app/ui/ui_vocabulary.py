import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from app.db import get_connection


class VocabularyWindow:
    def __init__(self, user):
        self.user = user

        self.win = tk.Toplevel()
        self.win.title("Vocabulary")
        self.win.geometry("700x400")

        self.tree = ttk.Treeview(self.win, 
                                 columns=("word","synonym",
                                          "antonym","pos","level"), 
                                 show="headings")
        
        for col, title in [("word","Word"),("synonym","Synonym"),("antonym","Antonym"),
                           ("pos","Part"),("level","Level")]:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=120)

        self.tree.pack(fill="both", expand=True)

        frame = tk.Frame(self.win)
        frame.pack(fill='x', pady=6)

        # все кнопки доступны для всех
        tk.Button(frame, text="Add", command=self.add_word).pack(side="left", padx=5)
        tk.Button(frame, text="Edit", command=self.edit_word).pack(side="left", padx=5)
        tk.Button(frame, text="Delete", command=self.delete_word).pack(side="left", padx=5)
        tk.Button(frame, text="Refresh", command=self.load_data).pack(side="left", padx=5)

        self.load_data()



    def load_data(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT word_id, word, synonym, antonym, part_of_speech, word_level FROM vocabulary")
        for row in cur.fetchall():
            self.tree.insert("", "end", iid=row["word_id"], values=(row["word"], row["synonym"], row["antonym"], row["part_of_speech"], row["word_level"]))
        conn.close()

    def add_word(self):
        dlg = AddEditWord(self.win)
        self.win.wait_window(dlg.top)

        if dlg.result:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("INSERT INTO vocabulary (word, synonym, antonym, part_of_speech, word_level) VALUES (?, ?, ?, ?, ?)",
                        (dlg.result["word"], dlg.result["synonym"], dlg.result["antonym"], dlg.result["pos"], dlg.result["level"]))
            conn.commit()
            conn.close()
            self.load_data()

    def edit_word(self):
        sel = self.tree.selection()
        if not sel:
            return 
        
        word_id = sel[0]
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM vocabulary WHERE word_id = ?", (word_id,))
        r = cur.fetchone()

        conn.close()
        dlg = AddEditWord(self.win, data=r)
        self.win.wait_window(dlg.top)
        if dlg.result:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("UPDATE vocabulary SET word=?, synonym=?, antonym=?, part_of_speech=?, word_level=? WHERE word_id=?",
                        (dlg.result["word"], dlg.result["synonym"], dlg.result["antonym"], dlg.result["pos"], dlg.result["level"], word_id))
            conn.commit()
            conn.close()
            self.load_data()

    def delete_word(self):
        sel = self.tree.selection()
        if not sel:
            return
        
        word_id = sel[0]
        if not messagebox.askyesno("Confirm", "Delete selected word?"):
            return
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM vocabulary WHERE word_id=?", (word_id,))
        conn.commit()
        conn.close()
        self.load_data()


class AddEditWord:
    def __init__(self, parent, data=None):
        self.result = None
        self.top = tk.Toplevel(parent)
        self.top.title("Add / Edit Word")
        tk.Label(self.top, text="Word").grid(row=0, column=0)
        self.e_word = tk.Entry(self.top); self.e_word.grid(row=0, column=1)
        tk.Label(self.top, text="Synonym").grid(row=1, column=0)
        self.e_syn = tk.Entry(self.top); self.e_syn.grid(row=1, column=1)
        tk.Label(self.top, text="Antonym").grid(row=2, column=0)
        self.e_ant = tk.Entry(self.top); self.e_ant.grid(row=2, column=1)
        tk.Label(self.top, text="POS").grid(row=3, column=0)
        self.e_pos = tk.Entry(self.top); self.e_pos.grid(row=3, column=1)
        tk.Label(self.top, text="Level").grid(row=4, column=0)
        self.e_level = tk.Entry(self.top); self.e_level.grid(row=4, column=1)

        tk.Button(self.top, text="Save", command=self.on_save).grid(row=5, column=0, columnspan=2)

        if data:
            self.e_word.insert(0, data["word"])
            self.e_syn.insert(0, data["synonym"])
            self.e_ant.insert(0, data["antonym"])
            self.e_pos.insert(0, data["part_of_speech"])
            self.e_level.insert(0, data["word_level"])

    def on_save(self):
        self.result = {
            "word": self.e_word.get().strip(),
            "synonym": self.e_syn.get().strip(),
            "antonym": self.e_ant.get().strip(),
            "pos": self.e_pos.get().strip(),
            "level": self.e_level.get().strip(),
        }
        self.top.destroy()
