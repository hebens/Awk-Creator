""" Awk Studio Pro
    Author: Heinz Ebensperger
    Date: 23.12.2025

    This tool allows to build awk commands, I used it in order to learn awk. It's provided as is, without waranty and support.
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess
import platform
from collections import Counter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class FilterRow:
    def __init__(self, master, index, remove_callback):
        self.frame = ctk.CTkFrame(master, fg_color="transparent")
        self.frame.pack(fill="x", pady=2)

        self.connector = ctk.StringVar(value="&&")
        if index > 0:
            self.conn_menu = ctk.CTkOptionMenu(self.frame, variable=self.connector, values=["&&", "||"], width=75, fg_color="#444")
            self.conn_menu.pack(side="left", padx=5)
        else:
            ctk.CTkLabel(self.frame, text="IF", width=75, font=("Arial", 12, "bold"), text_color="#3a86ff").pack(side="left", padx=5)

        self.col = ctk.StringVar()
        self.entry_col = ctk.CTkEntry(self.frame, textvariable=self.col, width=60, placeholder_text="$Col")
        self.entry_col.pack(side="left", padx=5)

        self.op = ctk.StringVar(value="==")
        ctk.CTkOptionMenu(self.frame, variable=self.op, values=["==", "!=", "~", ">", "<"], width=75).pack(side="left", padx=5)

        self.val = ctk.StringVar()
        ctk.CTkEntry(self.frame, textvariable=self.val, width=180, placeholder_text="Value").pack(side="left", padx=5)

        if index > 0:
            ctk.CTkButton(self.frame, text="×", width=30, fg_color="#882222", hover_color="#aa2222", command=lambda: remove_callback(self)).pack(side="left", padx=5)

class AwkStudio(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("AWK Studio Pro - Analytics & Cleaning")
        self.geometry("1300x1000")
        self.filepath = ""
        self.filter_rows = []
        
        # UI Variables
        self.delimiter = ctk.StringVar(value=",")
        self.print_cols = ctk.StringVar()
        self.search_var = ctk.StringVar()
        self.calc_mode = ctk.StringVar(value="None") 
        self.stat_col = ctk.StringVar()
        self.dedup_var = ctk.BooleanVar(value=False)
        self.os_target = ctk.StringVar(value="Windows" if platform.system() == "Windows" else "Linux/macOS")

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.create_sidebar()
        self.create_main_content()
        self.add_filter_row()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        ctk.CTkLabel(self.sidebar, text="HISTORY", font=("Roboto", 16, "bold")).pack(pady=20)
        self.history_listbox = tk.Listbox(self.sidebar, bg="#1e1e1e", fg="#3a86ff", borderwidth=0, highlightthickness=0)
        self.history_listbox.pack(expand=True, fill="both", padx=15)
        ctk.CTkButton(self.sidebar, text="Clear History", fg_color="transparent", border_width=1, command=lambda: self.history_listbox.delete(0, tk.END)).pack(pady=20)

    def create_main_content(self):
        self.main_frame = ctk.CTkScrollableFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        # Header
        header = ctk.CTkFrame(self.main_frame)
        header.pack(fill="x", pady=5)
        ctk.CTkButton(header, text="Open File...", command=self.load_file).pack(side="left", padx=10, pady=10)
        self.file_label = ctk.CTkLabel(header, text="No file selected", text_color="gray")
        self.file_label.pack(side="left", padx=5)
        ctk.CTkSegmentedButton(header, values=["Windows", "Linux/macOS"], variable=self.os_target).pack(side="right", padx=10)

        # Visual Column Picker
        self.picker_frame = ctk.CTkFrame(self.main_frame)
        self.picker_frame.pack(fill="x", pady=5, padx=10)
        self.button_container = ctk.CTkFrame(self.picker_frame, fg_color="transparent")
        self.button_container.pack(fill="x", padx=10, pady=5)

        # Preview
        self.preview_box = ctk.CTkTextbox(self.main_frame, height=120, font=("Courier New", 12), fg_color="#000")
        self.preview_box.pack(fill="x", padx=10, pady=5)

        # Filter Section
        self.filter_container = ctk.CTkFrame(self.main_frame)
        self.filter_container.pack(fill="x", pady=10, padx=10)
        self.rows_inner_frame = ctk.CTkFrame(self.filter_container, fg_color="transparent")
        self.rows_inner_frame.pack(fill="x", padx=10)
        ctk.CTkButton(self.filter_container, text="+ Add Condition", command=self.add_filter_row).pack(pady=10, padx=10, anchor="w")

        # --- Statistics & Cleaning Tools ---
        tools_frame = ctk.CTkFrame(self.main_frame, border_width=1, border_color="#3a86ff")
        tools_frame.pack(fill="x", pady=10, padx=10)
        
        ctk.CTkLabel(tools_frame, text="Math:", font=("Arial", 12, "bold")).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkOptionMenu(tools_frame, variable=self.calc_mode, values=["None", "Sum", "Average"], width=100).grid(row=0, column=1, padx=5)
        self.stat_entry = ctk.CTkEntry(tools_frame, textvariable=self.stat_col, width=50, placeholder_text="$#")
        self.stat_entry.grid(row=0, column=2, padx=5)

        ctk.CTkLabel(tools_frame, text="|  Cleaning:", font=("Arial", 12, "bold")).grid(row=0, column=3, padx=10)
        ctk.CTkCheckBox(tools_frame, text="Remove Duplicates", variable=self.dedup_var).grid(row=0, column=4, padx=5)

        # Config (Print Columns Restored)
        config_frame = ctk.CTkFrame(self.main_frame)
        config_frame.pack(fill="x", pady=5, padx=10)
        ctk.CTkLabel(config_frame, text="Sep:").grid(row=0, column=0, padx=10, pady=10)
        self.delim_menu = ctk.CTkOptionMenu(config_frame, variable=self.delimiter, values=[",", ";", "|", ":", "Space/Tab"], command=lambda e: self.refresh_headers())
        self.delim_menu.grid(row=0, column=1)
        
        ctk.CTkLabel(config_frame, text="Show Columns:").grid(row=0, column=2, padx=10)
        self.print_entry = ctk.CTkEntry(config_frame, textvariable=self.print_cols, width=350, placeholder_text="e.g. 1, 3")
        self.print_entry.grid(row=0, column=3, padx=10)

        # Actions & Output
        action_output_container = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        action_output_container.pack(fill="x", pady=10)
        btn_col = ctk.CTkFrame(action_output_container, fg_color="transparent")
        btn_col.pack(side="left", padx=10, anchor="n")
        ctk.CTkButton(btn_col, text="⚡ RUN AWK", command=self.run_awk, height=50, width=180, font=("Arial", 16, "bold"), fg_color="#2c8558").pack(pady=5)
        ctk.CTkButton(btn_col, text="💾 Export CSV", command=self.export_to_csv, width=180).pack(pady=5)
        ctk.CTkButton(btn_col, text="🔄 Reset", width=180, command=self.reset_ui).pack(pady=5)

        out_col = ctk.CTkFrame(action_output_container, fg_color="transparent")
        out_col.pack(side="left", fill="both", expand=True, padx=10)
        self.cmd_display = ctk.CTkEntry(out_col, font=("Courier New", 12), height=35)
        self.cmd_display.pack(fill="x", pady=(0, 10))
        self.output_box = ctk.CTkTextbox(out_col, height=300, font=("Courier New", 12))
        self.output_box.pack(fill="both", expand=True)

    def build_awk_program(self):
        # 1. Deduplication
        dedup_logic = "!a[$0]++" if self.dedup_var.get() else ""
        
        # 2. Filtering
        cond_parts = []
        for i, row in enumerate(self.filter_rows):
            c, o, v = row.col.get(), row.op.get(), row.val.get()
            if c and v:
                if o == "~" or not v.replace('.','',1).isdigit(): v = f'"{v}"'
                cond_parts.append(f"{row.connector.get()} ${c} {o} {v}" if i > 0 else f"${c} {o} {v}")
        
        full_cond = " ".join(cond_parts)
        
        # 3. Stats and Printing
        mode = self.calc_mode.get()
        target = self.stat_col.get()
        p_cols = self.print_cols.get()
        
        body_parts = []
        if dedup_logic: body_parts.append(dedup_logic)
        if mode != "None" and target: body_parts.append(f"s += ${target}; count++")
        
        # Format Column Output
        if p_cols:
            col_list = ", ".join(['$'+x.strip() for x in p_cols.split(',')])
            body_parts.append(f"print {col_list}")
        elif mode == "None":
            body_parts.append("print $0")

        # Combine Body
        body_logic = "; ".join(body_parts)
        main_block = f"{full_cond} {{ {body_logic} }}" if full_cond else f"{{ {body_logic} }}"
        
        # END Block
        end_block = ""
        if mode == "Sum":
            end_block = " END { print \"--- TOTAL SUM: \", s }"
        elif mode == "Average":
            end_block = " END { if(count>0) print \"--- AVERAGE: \", s/count; else print \"--- NO DATA\" }"
            
        return f"{main_block}{end_block}"

    # --- Rest of helper methods (load_file, refresh_headers, etc.) ---
    def use_column(self, idx):
        focused = self.focus_get()
        if focused == self.stat_entry: self.stat_col.set(str(idx))
        elif focused == self.print_entry:
            cur = self.print_cols.get()
            self.print_cols.set(f"{cur}, {idx}" if cur else str(idx))
        elif isinstance(focused, (tk.Entry, ctk.CTkEntry)):
            focused.delete(0, tk.END); focused.insert(0, str(idx))
        else:
            cur = self.print_cols.get()
            self.print_cols.set(f"{cur}, {idx}" if cur else str(idx))

    def load_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.filepath = path
            self.file_label.configure(text=path.split("/")[-1])
            with open(path, 'r') as f:
                line = f.readline()
                counts = Counter(c for c in line if c in ",;|:")
                self.delimiter.set(counts.most_common(1)[0][0] if counts else "Space/Tab")
            self.refresh_headers()
            self.refresh_preview()

    def refresh_headers(self):
        if not self.filepath: return
        for w in self.button_container.winfo_children(): w.destroy()
        try:
            with open(self.filepath, 'r') as f:
                d = self.delimiter.get()
                sep = None if d == "Space/Tab" else d
                headers = f.readline().strip().split(sep)
                for i, name in enumerate(headers, 1):
                    ctk.CTkButton(self.button_container, text=f"{name} (${i})", width=80, command=lambda idx=i: self.use_column(idx)).pack(side="left", padx=2)
        except: pass

    def refresh_preview(self):
        with open(self.filepath, 'r') as f:
            self.preview_box.delete("1.0", tk.END)
            self.preview_box.insert("1.0", "".join([f"{i+1:3} | {f.readline()}" for i in range(10)]))

    def run_awk(self):
        if not self.filepath: return
        program = self.build_awk_program()
        fs = self.delimiter.get() if self.delimiter.get() != "Space/Tab" else ""
        cmd = ["awk"]
        if fs: cmd.extend(["-F", fs])
        cmd.extend([program, self.filepath])
        q = '"' if self.os_target.get() == "Windows" else "'"
        self.cmd_display.delete(0, tk.END)
        self.cmd_display.insert(0, f"awk {('-F '+q+fs+q+' ') if fs else ''}{q}{program}{q} \"{self.filepath}\"")
        try:
            res = subprocess.run(cmd, capture_output=True, text=True)
            self.output_box.delete("1.0", tk.END)
            self.output_box.insert("1.0", res.stdout if not res.stderr else f"Error: {res.stderr}")
        except Exception as e: self.output_box.insert("1.0", str(e))

    def reset_ui(self):
        for r in self.filter_rows[1:]: r.frame.destroy()
        self.filter_rows = [self.filter_rows[0]]; self.filter_rows[0].col.set(""); self.filter_rows[0].val.set("")
        self.calc_mode.set("None"); self.stat_col.set(""); self.print_cols.set(""); self.dedup_var.set(False); self.output_box.delete("1.0", tk.END)

    def add_filter_row(self):
        self.filter_rows.append(FilterRow(self.rows_inner_frame, len(self.filter_rows), self.remove_filter_row))
    def remove_filter_row(self, obj):
        if len(self.filter_rows) > 1: obj.frame.destroy(); self.filter_rows.remove(obj)
    def export_to_csv(self): pass
    def highlight_search(self, *args): pass

if __name__ == "__main__":
    app = AwkStudio()
    app.mainloop()