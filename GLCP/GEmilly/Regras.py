import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import zipfile
import shutil
import xml.etree.ElementTree as ET
import subprocess
import traceback
import re


class RuleManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de Regras Lógicas")
        self.root.geometry("900x650")
        self.rules = {}
        self.setup_dark_theme()
        self.create_tabs()

    def setup_dark_theme(self):
        style = ttk.Style()
        style.theme_use('clam')

        default_font = ("Helvetica", 10)

        style.configure('.',
            background='#2e2e2e',
            foreground='white',
            fieldbackground='#3e3e3e',
            font=default_font
        )

        style.configure('TLabel',
            background='#2e2e2e',
            foreground='white'
        )

        style.configure('Dark.TLabel',
            background='#2e2e2e',
            foreground='white'
        )

        style.configure('TButton',
            background='#444',
            foreground='white'
        )

        style.configure('Treeview',
            background='#3e3e3e',
            foreground='white',
            fieldbackground='#3e3e3e'
        )

        style.map('Treeview', background=[('selected', '#6a6a6a')])

        # 🔥 CORREÇÃO CRÍTICA
        style.configure('TEntry',
            fieldbackground='#3e3e3e',
            foreground='white'
        )

        style.configure('TCombobox',
            fieldbackground='#3e3e3e',
            background='#444',
            foreground='black'
        )

        style.configure('TCheckbutton',
            background='#2e2e2e',
            foreground='white'
        )

    def create_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.tab_apply = ttk.Frame(self.notebook)
        self.tab_database = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_apply, text="Aplicar Regras")
        self.notebook.add(self.tab_database, text="Banco de Regras")
        self.notebook.pack(fill='both', expand=True)

        self.create_apply_tab()
        self.create_database_tab()

    # -------------------- Aba Aplicar Regras --------------------
    def create_apply_tab(self):
        frame = ttk.Frame(self.tab_apply, padding=10)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Arquivo .zginml:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_zginml = ttk.Entry(frame, width=70)
        self.entry_zginml.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Selecionar", command=lambda: self.browse_file(self.entry_zginml)).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(frame, text="Arquivo de regras (.json):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_json_apply = ttk.Entry(frame, width=70)
        self.entry_json_apply.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Selecionar", command=lambda: self.browse_file(self.entry_json_apply)).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(frame, text="Salvar como (.zginml):").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.entry_output = ttk.Entry(frame, width=70)
        self.entry_output.grid(row=2, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Selecionar", command=lambda: self.browse_save_file(self.entry_output)).grid(row=2, column=2, padx=5, pady=5)

        ttk.Button(frame, text="Aplicar Regras", command=self.apply_rules, width=30).grid(row=3, column=0, columnspan=3, pady=12)

        # GINSIM jar
        ttk.Label(frame, text="Caminho do GINsim.jar:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
        self.entry_jar = ttk.Entry(frame, width=70)
        self.entry_jar.grid(row=4, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Procurar", command=lambda: self.select_jar(self.entry_jar)).grid(row=4, column=2, padx=5, pady=5)

        ttk.Button(frame, text="Abrir no GINsim", command=lambda: self.launch_ginsim(self.entry_jar, self.entry_zginml)).grid(row=5, column=0, columnspan=3, pady=10)

    # -------------------- Funções auxiliares --------------------
    def browse_file(self, entry):
        file = filedialog.askopenfilename(filetypes=[("GINsim / JSON files/TXT", "*.zginml *.json *.txt *.ginml *.zip"), ("All files", "*.*")])
        if file:
            entry.delete(0, tk.END)
            entry.insert(0, file)

    def browse_save_file(self, entry):
        file = filedialog.asksaveasfilename(defaultextension=".zginml")
        if file:
            entry.delete(0, tk.END)
            entry.insert(0, file)

    def extract_ginml_from_zginml(self, zginml, folder):
        try:
            if not os.path.isfile(zginml):
                raise Exception("Caminho inválido")

            # ✅ CASO 1: já é um .ginml → só retorna
            if zginml.lower().endswith(".ginml"):
                return zginml

            # ✅ CASO 2: zip ou zginml
            if zginml.lower().endswith(".zginml") or zginml.lower().endswith(".zip"):

                with zipfile.ZipFile(zginml, 'r') as z:
                    z.extractall(folder)

                ginml_dir = os.path.join(folder, "GINsim-data")

                if not os.path.isdir(ginml_dir):
                    raise Exception("Pasta GINsim-data não encontrada")

                for file in os.listdir(ginml_dir):
                    if file.lower().endswith(".ginml"):
                        return os.path.join(ginml_dir, file)

                raise Exception("Arquivo .ginml não encontrado")

            else:
                raise Exception("Formato não suportado")

        except Exception as e:
            print(f"Erro ao extrair {zginml}: {e}")
            return None

    # -------------------- Tela de configuração das regras por proteína --------------------
    def open_logic_table(self, reguladores_dict, callback, regras_json=None):
        popup = tk.Toplevel(self.root)
        popup.title("Configurar Lógicas por Proteína")
        popup.geometry("820x480")
        popup.grab_set()

        frame = ttk.Frame(popup, padding=10)
        frame.pack(fill="both", expand=True)

        cols = ("Proteína", "Regra Padrão", "Ações")
        tree = ttk.Treeview(frame, columns=cols, show="headings", height=18)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=260 if col != "Ações" else 100, anchor="center")
        tree.pack(fill="both", expand=True)

        # Dicionário para armazenar escolhas do usuário
        self.logic_choices = {}

        # Preencher tabela
        for prot_id, regs in reguladores_dict.items():
            ativadores = [r[0] for r in regs if r[1] == "+"]
            inibidores = [r[0] for r in regs if r[1] == "-"]

            default_expr = ""
            if ativadores:
                default_expr += "(" + " | ".join(ativadores) + ")"
            if inibidores:
                if default_expr:
                    default_expr += " & "
                default_expr += "(" + " & ".join("!" + i for i in inibidores) + ")"

            usar_regra = prot_id in (regras_json or {})
            regra_padrao = f"{default_expr}" + (" + regra do arquivo" if usar_regra else "")

            iid = tree.insert("", "end", values=(prot_id, regra_padrao, "Editar"))

            # Inicializa escolhas
            self.logic_choices[prot_id] = {
                "ativador_logic": "or",
                "inibidor_logic": "and",
                "usar_regra": usar_regra,
                # custom_expr pode ser adicionado depois via edição inline
            }

        # Duplo clique: ações e edição inline
        def on_double_click(event):
            region = tree.identify("region", event.x, event.y)
            if region != "cell":
                return

            col = tree.identify_column(event.x)
            row = tree.identify_row(event.y)
            if not row:
                return

            # Coluna "Ações" -> abre editor por proteína
            if col == "#3":
                iid = row
                prot_id = tree.item(iid, "values")[0]
                regs = reguladores_dict.get(prot_id, [])
                regra_json_prot = regras_json.get(prot_id) if regras_json else None
                self.edit_logic_for_protein(tree, iid, prot_id, regs, regra_json_prot)
                return

            # Coluna "Regra Padrão" -> edição inline, captura row/col com closure
            if col == "#2":
                x, y, width, height = tree.bbox(row, col)
                value = tree.set(row, col)

                entry = ttk.Entry(tree)
                entry.place(x=x, y=y, width=width, height=height)
                entry.insert(0, value)
                entry.focus()

                def salvar_edicao(event=None, r=row, c=col, ent=entry):
                    novo_valor = ent.get()
                    tree.set(r, c, novo_valor)
                    ent.destroy()

                    prot_id = tree.item(r, "values")[0]
                    if prot_id in self.logic_choices:
                        self.logic_choices[prot_id]["custom_expr"] = novo_valor
                    else:
                        self.logic_choices[prot_id] = {"custom_expr": novo_valor}
                    # debug
                    print("Atualizado (logic_choices):", prot_id, self.logic_choices[prot_id])

                entry.bind("<Return>", salvar_edicao)
                entry.bind("<FocusOut>", salvar_edicao)

        tree.bind("<Double-1>", on_double_click)

        def confirmar():
            popup.destroy()
            # envia escolhas de lógica para o callback (aplicar regras)
            callback(self.logic_choices)

        ttk.Button(popup, text="Confirmar", command=confirmar).pack(pady=8)

    # Função de edição por proteína com aparência escura
    def edit_logic_for_protein(self, tree, iid, prot_id, regs, regra_json_prot=None):
        editor = tk.Toplevel(self.root)
        editor.title(f"Editar lógica: {prot_id}")
        editor.geometry("420x200")
        editor.after(10, editor.grab_set)
        editor.configure(bg="#2e2e2e")

        ttk.Style().configure("Dark.TLabel", background="#2e2e2e", foreground="white")
        ttk.Label(editor, text="Ativadores:", style="Dark.TLabel").grid(row=0, column=0, padx=5, pady=5)
        cb_ativ = ttk.Combobox(editor, values=["and", "or"], state="readonly")
        cb_ativ.set(self.logic_choices[prot_id].get("ativador_logic", "or"))
        cb_ativ.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(editor, text="Inibidores:", style="Dark.TLabel").grid(row=1, column=0, padx=5, pady=5)
        cb_inib = ttk.Combobox(editor, values=["and", "or"], state="readonly")
        cb_inib.set(self.logic_choices[prot_id].get("inibidor_logic", "and"))
        cb_inib.grid(row=1, column=1, padx=5, pady=5)

        usar_var = tk.BooleanVar(value=self.logic_choices[prot_id].get("usar_regra", False))
        chk = ttk.Checkbutton(editor, text="Usar regra do arquivo", variable=usar_var)
        chk.grid(row=2, column=0, columnspan=2, pady=8)

        def salvar():
            # atualiza escolhas
            self.logic_choices[prot_id] = {
                "ativador_logic": cb_ativ.get(),
                "inibidor_logic": cb_inib.get(),
                "usar_regra": bool(usar_var.get())
            }

            # monta expressão padrão com base nos regs
            ativadores = [r[0] for r in regs if r[1] == "+"]
            inibidores = [r[0] for r in regs if r[1] == "-"]

            default_expr = ""
            if ativadores:
                sep = " & " if cb_ativ.get() == "and" else " | "
                default_expr += "(" + sep.join(ativadores) + ")"
            if inibidores:
                sep = " & " if cb_inib.get() == "and" else " | "
                if default_expr:
                    default_expr += " & "
                default_expr += "(" + sep.join("!" + i for i in inibidores) + ")"

            # se escolher usar regra do arquivo, combina com regra_json_prot
            if usar_var.get() and regra_json_prot:
                json_rules_exprs = [rule_entry[0].strip() for rule_entry in regra_json_prot]
                if json_rules_exprs:
                    default_expr = f"({default_expr}) & ({' & '.join(json_rules_exprs)})" if default_expr else " & ".join(json_rules_exprs)

            # atualiza a tabela (coluna Regra Padrão)
            tree.set(iid, column="Regra Padrão", value=default_expr)
            # também coloca em custom_expr para garantir prioridade caso queira
            self.logic_choices[prot_id]["custom_expr"] = default_expr
            editor.destroy()

        ttk.Button(editor, text="Salvar", command=salvar).grid(row=3, column=0, columnspan=2, pady=10)

    def apply_rules(self):
        zginml_file = self.entry_zginml.get()
        if not zginml_file or not os.path.isfile(zginml_file):
            messagebox.showerror("Erro", "Selecione um arquivo .zginml válido.")
            return

        temp_folder = os.path.join(os.path.dirname(zginml_file), "temp_extract")
        os.makedirs(temp_folder, exist_ok=True)
        try:
            ginml_file = self.extract_ginml_from_zginml(zginml_file, temp_folder)
        except Exception as e:
            shutil.rmtree(temp_folder, ignore_errors=True)
            messagebox.showerror("Erro", f"Falha ao extrair .zginml: {e}")
            return

        # monta reguladores_dict e abre a tela
        tree = ET.parse(ginml_file)
        root = tree.getroot()

        reguladores_dict = {}
        for edge in root.findall(".//edge"):
            from_node = edge.get("from")
            to_node = edge.get("to")
            sign = edge.get("sign")
            if to_node not in reguladores_dict:
                reguladores_dict[to_node] = []
            reguladores_dict[to_node].append((from_node, "+" if sign == "positive" else "-"))

        # abre a tabela e, ao confirmar, chama _apply_rules_with_table
        self.open_logic_table(reguladores_dict, self._apply_rules_with_table)

    def _apply_rules_with_table(self, logic_choices):
        zginml_file = self.entry_zginml.get()
        output_file = self.entry_output.get()
        json_file = self.entry_json_apply.get()

        if not zginml_file or not os.path.isfile(zginml_file):
            messagebox.showerror("Erro", "Selecione um arquivo .zginml válido.")
            return
        if not output_file:
            messagebox.showerror("Erro", "Selecione um arquivo de saída (.zginml).")
            return

        regras_json = {}
        if json_file and os.path.isfile(json_file):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    regras_json = json.load(f)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao ler arquivo de regras: {e}")
                return

        temp_folder = os.path.join(os.path.dirname(output_file), "temp_extract")
        os.makedirs(temp_folder, exist_ok=True)

        try:
            ginml_file = self.extract_ginml_from_zginml(zginml_file, temp_folder)
            tree = ET.parse(ginml_file)
            root = tree.getroot()

            reguladores_dict = {}
            for edge in root.findall(".//edge"):
                from_node = edge.get("from")
                to_node = edge.get("to")
                sign = edge.get("sign")
                if to_node not in reguladores_dict:
                    reguladores_dict[to_node] = []
                reguladores_dict[to_node].append((from_node, "+" if sign == "positive" else "-"))

            regulatoryGraph = root.find("regulatoryGraph")
            if regulatoryGraph is None:
                regulatoryGraph = ET.SubElement(root, "regulatoryGraph")

            def tokenize_logic(expr):
                expr = expr.replace("(", " ( ").replace(")", " ) ").strip()
                return re.findall(r'\w+|[&|!()]+', expr)

            def apply_json_rule_to_node(default_expr, json_expr):
                default_tokens = tokenize_logic(default_expr)
                json_tokens = tokenize_logic(json_expr)
                result_tokens = []
                for dt, jt in zip(default_tokens, json_tokens):
                    if dt in ["&", "|"] and jt in ["&", "|"]:
                        result_tokens.append(dt)
                    else:
                        result_tokens.append(dt)
                if len(default_tokens) > len(json_tokens):
                    result_tokens.extend(default_tokens[len(json_tokens):])
                return " ".join(result_tokens)

            for node_id, regs in reguladores_dict.items():
                node_elem = root.find(f".//node[@id='{node_id}']")
                if node_elem is None:
                    node_elem = ET.SubElement(regulatoryGraph, "node", id=node_id, maxvalue="1")

                value_elem = node_elem.find("value")
                if value_elem is None:
                    value_elem = ET.SubElement(node_elem, "value", val="1")
                else:
                    # remove exps antigas
                    for exp in value_elem.findall("exp"):
                        value_elem.remove(exp)

                # se houver expressão customizada, usa ela (prioridade)
                custom = logic_choices.get(node_id, {}).get("custom_expr")
                if custom and custom.strip():
                    final_expr = custom.strip()
                else:
                    exp_parts = []
                    ativadores = [r[0] for r in regs if r[1] == "+"]
                    inibidores = [r[0] for r in regs if r[1] == "-"]

                    ativador_logic = logic_choices.get(node_id, {}).get("ativador_logic", "or")
                    inibidor_logic = logic_choices.get(node_id, {}).get("inibidor_logic", "and")

                    if ativadores:
                        sep = " & " if ativador_logic == "and" else " | "
                        exp_parts.append("(" + sep.join(ativadores) + ")")

                    if inibidores:
                        sep = " & " if inibidor_logic == "and" else " | "
                        inib_expr = sep.join("!" + i for i in inibidores)
                        exp_parts.append(f"({inib_expr})")

                    default_expr = " & ".join(exp_parts) if exp_parts else ""

                    if node_id in regras_json and regras_json[node_id]:
                        custom_rules = [rule_entry[0].strip() for rule_entry in regras_json[node_id]]
                        adjusted_rules = [apply_json_rule_to_node(default_expr, r) for r in custom_rules]
                        if default_expr:
                            final_expr = f"({default_expr}) & ({' & '.join(adjusted_rules)})"
                        else:
                            final_expr = " & ".join(adjusted_rules)
                    else:
                        final_expr = default_expr

                # cria o elemento <exp> com o atributo str (o que o GINsim espera)
                # cria o elemento <exp>
                    ET.SubElement(value_elem, "exp", str=final_expr)
                # =========================
                # CORREÇÃO GINSIM
                # =========================
            ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

            for link in root.findall(".//link"):
                href = link.get("{http://www.w3.org/1999/xlink}href")

                if href is None or href.strip() == "":
                    link.set("{http://www.w3.org/1999/xlink}href", "http://example.com")

            # Corrigir expressões
 

            # Corrigir comentários
            for comment in root.findall(".//comment"):
                if comment.text is None or comment.text.strip() == "":
                    comment.text = " "

            # Corrigir annotations vazias (ESSA É A MAIS IMPORTANTE)
            for annotation in root.findall(".//annotation"):
                for link in list(annotation.findall("link")):
                    href = link.get("{http://www.w3.org/1999/xlink}href") or link.get("href")

                    if href is None or href.strip() == "":
                        annotation.remove(link)

                        
            # salva o arquivo resultante
            tree.write(output_file, encoding="utf-8", xml_declaration=True)
            messagebox.showinfo("Sucesso", f"Arquivo ZGINML gerado: {output_file}")

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Erro", f"Falha ao aplicar regras: {e}")

        finally:
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder, ignore_errors=True)

    # -------------------- Banco de Regras (CRUD) --------------------
    def load_rules(self, entry):
        file = filedialog.askopenfilename(filetypes=[("Regras JSON/TXT", "*.json *.txt")])
        if file:
            entry.delete(0, tk.END)
            entry.insert(0, file)
            messagebox.showinfo("Banco de Regras", f"Regras carregadas de {file}")

    def select_jar(self, entry):
        file = filedialog.askopenfilename(filetypes=[("GINsim Executável", "*.jar")])
        if file:
            entry.delete(0, tk.END)
            entry.insert(0, file)

    def launch_ginsim(self, entry_jar, entry_ginml=None, open_empty=True):
        jar_path = entry_jar.get()
        if not jar_path or not os.path.isfile(jar_path):
            messagebox.showerror("Erro", "Caminho do GINsim.jar inválido.")
            return

        cmd = ["java", "-jar", jar_path]
        if not open_empty and entry_ginml:
            ginml_path = entry_ginml.get()
            if ginml_path and os.path.isfile(ginml_path):
                cmd.append(ginml_path)

        try:
            subprocess.Popen(cmd)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar o GINsim: {e}")

    # -------------------- Aba Banco de Regras --------------------
    def create_database_tab(self):
        frame = ttk.Frame(self.tab_database, padding=10)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="Arquivo de regras (.json):").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_json_db = ttk.Entry(frame, width=60)
        self.entry_json_db.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Selecionar", command=self.load_json_file).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(frame, text="Novo Arquivo", command=self.new_json_file).grid(row=0, column=3, padx=5, pady=5)

        self.tree = ttk.Treeview(frame, columns=("Proteina", "Regra", "Referencia"), show="headings", height=15)
        self.tree.heading("Proteina", text="Proteína")
        self.tree.heading("Regra", text="Regra Lógica")
        self.tree.heading("Referencia", text="Referência")
        self.tree.column("Proteina", width=150)
        self.tree.column("Regra", width=400)
        self.tree.column("Referencia", width=200)
        self.tree.grid(row=1, column=0, columnspan=4, pady=10)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        ttk.Button(btn_frame, text="Adicionar", command=self.add_rule).grid(row=0, column=0, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.edit_rule).grid(row=0, column=1, padx=5)
        ttk.Button(btn_frame, text="Excluir", command=self.delete_rule).grid(row=0, column=2, padx=5)
        ttk.Button(btn_frame, text="Salvar Arquivo", command=self.save_json_file).grid(row=0, column=3, padx=5)

    def load_json_file(self):
        file = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file:
            self.entry_json_db.delete(0, tk.END)
            self.entry_json_db.insert(0, file)
            try:
                with open(file, "r", encoding="utf-8") as f:
                    self.rules = json.load(f)
                self.refresh_tree()
                messagebox.showinfo("Sucesso", "Regras carregadas com sucesso!")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao carregar JSON: {e}")

    def new_json_file(self):
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file:
            self.entry_json_db.delete(0, tk.END)
            self.entry_json_db.insert(0, file)
            self.rules = {}
            self.refresh_tree()
            with open(file, "w", encoding="utf-8") as f:
                json.dump(self.rules, f, indent=4)

    def save_json_file(self):
        file = self.entry_json_db.get()
        if not file:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado.")
            return
        try:
            with open(file, "w", encoding="utf-8") as f:
                json.dump(self.rules, f, indent=4, ensure_ascii=False)
            messagebox.showinfo("Sucesso", "Regras salvas com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar JSON: {e}")

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for prot, lista_regras in self.rules.items():
            for regra in lista_regras:
                self.tree.insert("", tk.END, values=(prot, regra[0], regra[1]))

    def add_rule(self):
        self.open_rule_editor()

    def edit_rule(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma regra para editar.")
            return
        values = self.tree.item(selected[0], "values")
        self.open_rule_editor(values, selected[0])

    def delete_rule(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecione uma regra para excluir.")
            return
        values = self.tree.item(selected[0], "values")
        prot = values[0]
        regra = values[1]
        ref = values[2]

        if prot in self.rules:
            self.rules[prot] = [r for r in self.rules[prot] if not (r[0] == regra and r[1] == ref)]
            if not self.rules[prot]:
                del self.rules[prot]
            self.refresh_tree()

    def open_rule_editor(self, values=None, item_id=None):
        editor = tk.Toplevel(self.root)
        editor.title("Editor de Regra")
        editor.geometry("500x190")

        ttk.Label(editor, text="Proteína:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        entry_prot = ttk.Entry(editor, width=40)
        entry_prot.grid(row=0, column=1, padx=5, pady=5)
        entry_prot.insert(0, "SNAIL1")

        ttk.Label(editor, text="Regra Lógica:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        entry_rule = ttk.Entry(editor, width=40)
        entry_rule.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(editor, text="Referência:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        entry_ref = ttk.Entry(editor, width=40)
        entry_ref.grid(row=2, column=1, padx=5, pady=5)

        if values:
            entry_prot.delete(0, tk.END)
            entry_prot.insert(0, values[0])
            entry_rule.insert(0, values[1])
            entry_ref.insert(0, values[2])

        def salvar():
            prot = entry_prot.get().strip()
            regra = entry_rule.get().strip()
            ref = entry_ref.get().strip()

            if not prot or not regra:
                messagebox.showerror("Erro", "Proteína e Regra são obrigatórios.")
                return

            if prot not in self.rules:
                self.rules[prot] = []

            if values and item_id:
                self.rules[prot] = [
                    r for r in self.rules[prot] if not (r[0] == values[1] and r[1] == values[2])
                ]

            self.rules[prot].append([regra, ref])
            self.refresh_tree()
            editor.destroy()

        ttk.Button(editor, text="Salvar", command=salvar).grid(row=3, column=0, columnspan=2, pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    app = RuleManagerApp(root)
    root.mainloop()
