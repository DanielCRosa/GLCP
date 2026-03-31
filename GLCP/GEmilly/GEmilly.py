import tkinter as tk 
from tkinter import ttk, filedialog, messagebox, simpledialog
import json, zipfile, os, shutil
import xml.etree.ElementTree as ET
import subprocess
from github import Github, GithubException

class RuleEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GEmilly")
        self.rules = {}
        self.json_path = None
        self.github_owner = "DanielCRosa"
        self.github_repo = "Sistemas-Complexos"
        self.github_filepath = "regras.json"
        self.setup_dark_theme()
        self.create_widgets()

    def setup_dark_theme(self):
        style = ttk.Style()
        style.theme_use('clam')
        default_font = ("Helvetica", 10)
        style.configure('.', background='#2e2e2e', foreground='white',
                        fieldbackground='#3e3e3e', font=default_font)
        style.configure('TLabel', background='#2e2e2e', foreground='white', font=default_font)
        style.configure('TButton', background='#444', foreground='white', font=default_font)
        style.configure('Treeview', background='#3e3e3e', foreground='white',
                        fieldbackground='#3e3e3e', font=default_font)
        style.map('Treeview', background=[('selected', '#6a6a6a')])
        style.map('TButton', background=[('active', '#555'), ('pressed', '#666')])
        style.map('TNotebook.Tab', background=[('active', '#666'), ('selected', '#666')])
        style.configure("TCombobox",
                        fieldbackground='#3e3e3e', background='#444', foreground='white',
                        selectbackground='#444', lightcolor='#555', darkcolor='#444', font=default_font)

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)  

        self.tab_apply = ttk.Frame(self.notebook)
        self.tab_edit = ttk.Frame(self.notebook)
        self.tab_proteins = ttk.Frame(self.notebook)
        self.tab_remote = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_apply, text='Aplicar no GINsim')
        self.notebook.add(self.tab_edit, text='Editar Regras')
        self.notebook.add(self.tab_proteins, text='Visualizar Proteínas')
        self.notebook.add(self.tab_remote, text='Commit Remoto')

        self.create_apply_tab()
        self.create_edit_tab()
        self.create_protein_tab()
        self.create_remote_tab()
        
        self.notebook.pack(fill='both', expand=True)
        self.notebook.select(self.tab_apply)

    def create_apply_tab(self):
        frame = ttk.Frame(self.tab_apply, padding=10)
        frame.pack(fill='both', expand=True)
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=3)
        frame.columnconfigure(2, weight=1)

        ttk.Label(frame, text="Arquivo .zginml:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.entry_zginml = ttk.Entry(frame, width=50)
        self.entry_zginml.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(frame, text="Selecionar", command=lambda: self.browse_file(self.entry_zginml))\
            .grid(row=0, column=2, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="Arquivo de regras (.json):").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.entry_json_apply = ttk.Entry(frame, width=50)
        self.entry_json_apply.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(frame, text="Selecionar", command=self.load_rules_for_apply)\
            .grid(row=1, column=2, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="Linhagem:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.combo_linhagem = ttk.Combobox(frame, values=[""])
        self.combo_linhagem.set("")
        self.combo_linhagem.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        ttk.Label(frame, text="Salvar como (.zginml):").grid(row=3, column=0, sticky="e", padx=5, pady=5)
        self.entry_output = ttk.Entry(frame, width=50)
        self.entry_output.grid(row=3, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(frame, text="Salvar como", command=lambda: self.browse_save_file(self.entry_output))\
            .grid(row=3, column=2, sticky="w", padx=5, pady=5)

        ttk.Button(frame, text="Aplicar Regras no GINsim", command=self.apply_rules, width=30)\
            .grid(row=4, column=0, columnspan=3, pady=20)

        ttk.Label(frame, text="Executável GINsim (.jar):").grid(row=5, column=0, sticky="e", padx=5, pady=5)
        self.entry_jar = ttk.Entry(frame, width=50)
        self.entry_jar.grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        ttk.Button(frame, text="Selecionar", command=self.select_jar)\
            .grid(row=5, column=2, sticky="w", padx=5, pady=5)

        ttk.Button(frame, text="Abrir GINsim", command=self.launch_ginsim)\
            .grid(row=6, column=0, columnspan=3, pady=10)

    def load_rules_for_apply(self):
        file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file:
            return
        self.entry_json_apply.delete(0, tk.END)
        self.entry_json_apply.insert(0, file)
        try:
            with open(file, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar JSON: {e}")
            return

        self.available_lineages = sorted(set(
            rule[2] for regras in self.rules.values() for rule in regras if len(rule) >= 3 and rule[2] != ""
        ))
        self.combo_linhagem['values'] = [""] + self.available_lineages
        self.combo_linhagem.set("")

    def select_jar(self):
        file = filedialog.askopenfilename(filetypes=[("GINsim Executável", "*.jar")])
        if file:
            self.entry_jar.delete(0, tk.END)
            self.entry_jar.insert(0, file)

    def launch_ginsim(self):
        jar_path = self.entry_jar.get()
        if not jar_path or not os.path.isfile(jar_path):
            messagebox.showerror("Erro", "Caminho do GINsim.jar inválido.")
            return
        try:
            subprocess.Popen(["java", "-jar", jar_path])
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar o GINsim: {e}")

    def create_edit_tab(self):
        top_frame = ttk.Frame(self.tab_edit, padding=10)
        top_frame.pack(fill='x')

        ttk.Button(top_frame, text="Abrir JSON", command=self.load_json).pack(side='left')
        ttk.Button(top_frame, text="Criar novo JSON", command=self.create_new_json).pack(side='left', padx=5)
        ttk.Button(top_frame, text="Atualizar", command=self.refresh_table).pack(side='left', padx=5)

        self.search_type = tk.StringVar(value='Origem')
        ttk.Combobox(top_frame, textvariable=self.search_type,
                     values=['Origem','Destino','Tipo','Referência','Linhagem','Mecanismo','Descrição','Função'], width=10)\
            .pack(side='left', padx=5)
        self.search_entry = ttk.Entry(top_frame)
        self.search_entry.pack(side='left', padx=5)

        self.search_type2 = tk.StringVar(value='')
        ttk.Combobox(top_frame, textvariable=self.search_type2,
                     values=['', 'Origem', 'Destino', 'Tipo', 'Referência', 'Linhagem'], width=10)\
            .pack(side='left', padx=5)
        self.search_entry2 = ttk.Entry(top_frame)
        self.search_entry2.pack(side='left', padx=5)

        ttk.Button(top_frame, text="Buscar", command=self.search_rule).pack(side='left')

        add_frame = ttk.Frame(self.tab_edit, padding=10)
        add_frame.pack(fill='x')

        ttk.Label(add_frame, text="Origem").grid(row=0, column=0, padx=5, pady=(0,2), sticky='w')
        ttk.Label(add_frame, text="Destino").grid(row=0, column=1, padx=5, pady=(0,2), sticky='w')
        ttk.Label(add_frame, text="Tipo").grid(row=0, column=2, padx=5, pady=(0,2), sticky='w')
        ttk.Label(add_frame, text="Linhagem").grid(row=0, column=3, padx=5, pady=(0,2), sticky='w')
        ttk.Label(add_frame, text="Referência").grid(row=0, column=4, padx=5, pady=(0,2), sticky='w')
        ttk.Label(add_frame, text="Mecanismo").grid(row=0, column=5, padx=5, pady=(0,2))
        ttk.Label(add_frame, text="Descrição").grid(row=0, column=6, padx=5, pady=(0,2))
        ttk.Label(add_frame, text="Função").grid(row=0, column=7, padx=5, pady=(0,2))


        self.entry_origem = ttk.Entry(add_frame, width=10)
        self.entry_origem.grid(row=1, column=0, padx=5, pady=2)
        self.entry_destino = ttk.Entry(add_frame, width=10)
        self.entry_destino.grid(row=1, column=1, padx=5, pady=2)
        self.entry_mecanismo = ttk.Entry(add_frame, width=15)
        self.entry_mecanismo.grid(row=1, column=5, padx=5)
        self.entry_descricao = ttk.Entry(add_frame, width=20)
        self.entry_descricao.grid(row=1, column=6, padx=5)
        self.entry_funcao = ttk.Entry(add_frame, width=20)
        self.entry_funcao.grid(row=1, column=7, padx=5)

        # -> Combobox "Tipo" passa a ter três opções: '', '+' e '-'
        self.combo_type = tk.StringVar(value='')
        self.combo_tipo = ttk.Combobox(add_frame, textvariable=self.combo_type, values=['', '+', '-'], width=3)
        self.combo_tipo.grid(row=1, column=2, padx=5, pady=2)

        self.entry_linhagem = ttk.Entry(add_frame, width=10)
        self.entry_linhagem.grid(row=1, column=3, padx=5, pady=2)
        self.entry_referencia = ttk.Entry(add_frame, width=30)
        self.entry_referencia.grid(row=1, column=4, padx=5, pady=2)

        ttk.Button(add_frame, text="Adicionar Ligação", command=self.add_rule)\
            .grid(row=1, column=5, padx=10)

        self.tree = ttk.Treeview(
            self.tab_edit,
            columns=("origem","destino","tipo","linhagem","referencia","mecanismo","descricao","funcao"),
            show="headings"
        )
        for col in ("origem","destino","tipo","linhagem","referencia","mecanismo","descricao","funcao"):
                self.tree.heading(col, text=col.capitalize())
        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.tree.bind('<Double-1>', self.edit_cell)

        ttk.Button(self.tab_edit, text="Remover Selecionado", command=self.remove_selected)\
            .pack(pady=5)
        ttk.Button(self.tab_edit, text="Copiar Referência", command=self.copy_reference)\
            .pack(pady=5)

    def create_protein_tab(self):
        frame = ttk.Frame(self.tab_proteins, padding=10)
        frame.pack(fill='both', expand=True)

        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(filter_frame, text="Filtrar por proteína:").pack(side='left', padx=5)
        self.filter_proteina = ttk.Entry(filter_frame, width=20)
        self.filter_proteina.pack(side='left')
        ttk.Label(filter_frame, text="Filtrar por linhagem:").pack(side='left', padx=5)
        self.filter_linhagem = ttk.Entry(filter_frame, width=20)
        self.filter_linhagem.pack(side='left')
        ttk.Button(filter_frame, text="Aplicar Filtros", command=self.update_protein_list)\
            .pack(side='left', padx=10)

        self.protein_tree = ttk.Treeview(
            frame,
            columns=("proteina","linhagem","ligacoes"),
            show="headings"
        )
        self.protein_tree.heading("proteina", text="Proteína")
        self.protein_tree.heading("linhagem", text="Linhagem")
        self.protein_tree.heading("ligacoes", text="Nº de Ligações")
        self.protein_tree.column("proteina", width=150)
        self.protein_tree.column("linhagem", width=150)
        self.protein_tree.column("ligacoes", width=120, anchor='center')
        self.protein_tree.pack(fill='both', expand=True)

        ttk.Button(frame, text="Atualizar Lista", command=self.update_protein_list)\
            .pack(pady=10)

    def update_protein_list(self):
        filtro_proteina = self.filter_proteina.get().strip().lower()
        filtro_linhagem = self.filter_linhagem.get().strip().lower()

        self.protein_tree.delete(*self.protein_tree.get_children())
        contagem = {}
        for origem, targets in self.rules.items():
            for entry in targets:
                lin = entry[2] if len(entry)>=3 else ""
                key = (origem, lin)
                contagem[key] = contagem.get(key, 0) + 1

        destinos = set()
        for origem, targets in self.rules.items():
            for entry in targets:
                dest = entry[0]
                lin = entry[2] if len(entry)>=3 else ""
                destinos.add((dest, lin))
        for dest, lin in destinos:
            key = (dest, lin)
            if key not in contagem:
                contagem[key] = 0

        for (prot, lin), cnt in sorted(contagem.items()):
            if filtro_proteina and filtro_proteina not in prot.lower():
                continue
            if filtro_linhagem and filtro_linhagem not in lin.lower():
                continue
            self.protein_tree.insert("", "end", values=(prot, lin, cnt))

    def browse_file(self, entry):
        file = filedialog.askopenfilename()
        if file:
            entry.delete(0, tk.END)
            entry.insert(0, file)

    def browse_save_file(self, entry):
        file = filedialog.asksaveasfilename(defaultextension=".zginml")
        if file:
            entry.delete(0, tk.END)
            entry.insert(0, file)

    def load_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files","*.json")])
        if not path:
            return
        self.json_path = path
        try:
            with open(path, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)

            # 🔥 NORMALIZAÇÃO ROBUSTA
            clean_rules = {}

            for origem, regras in self.rules.items():
                if not isinstance(regras, list):
                    continue  # ignora lixo

                novas_regras = []

                for r in regras:
                    # garante que r é lista
                    if not isinstance(r, list):
                        continue

                    # garante tamanho mínimo
                    if len(r) < 7:
                        r = r + [""] * (7 - len(r))

                    novas_regras.append(r)

                clean_rules[origem] = novas_regras

            self.rules = clean_rules

            self.refresh_table()
            self.update_protein_list()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar JSON: {e}")

    def refresh_table(self):
        self.tree.delete(*self.tree.get_children())
        for origem, targets in self.rules.items():
            for entry in targets:
                destino = entry[0] if len(entry)>=1 else ""
                tipo    = entry[1] if len(entry)>=2 else ""
                linhagem= entry[2] if len(entry)>=3 else ""
                referencia= entry[3] if len(entry)>=4 else ""
                mec  = entry[4] if len(entry)>=5 else ""
                desc = entry[5] if len(entry)>=6 else ""
                func = entry[6] if len(entry)>=7 else ""

                self.tree.insert("", "end",
                    values=(origem, destino, tipo, linhagem, referencia, mec, desc, func))

    def add_rule(self):
        origem    = self.entry_origem.get().strip()
        destino   = self.entry_destino.get().strip()
        tipo      = self.combo_type.get().strip()    # aqui tipo pode ser "" ou "+" ou "-"
        linhagem  = self.entry_linhagem.get().strip()
        referencia= self.entry_referencia.get().strip()
        mecanismo = self.entry_mecanismo.get().strip()
        descricao = self.entry_descricao.get().strip()
        funcao    = self.entry_funcao.get().strip()

        # Passamos a exigir apenas origem e destino; tipo vazio é permitido
        if not (origem and destino):
            messagebox.showerror("Erro", "Os campos 'origem' e 'destino' são obrigatórios.")
            return
        if tipo not in ['', '+', '-']:
            messagebox.showerror("Erro", "O tipo deve ser '+', '-' ou em branco.")
            return

        self.rules.setdefault(origem, []).append([destino, tipo, linhagem, referencia, mecanismo, descricao, funcao])
        self.refresh_table()
        self.update_protein_list()
        self.clear_add_fields()
        self.save_to_json()

    def clear_add_fields(self):
        self.entry_origem.delete(0, tk.END)
        self.entry_destino.delete(0, tk.END)
        self.combo_tipo.set('')          # garantir que volte para blank
        self.entry_linhagem.delete(0, tk.END)
        self.entry_referencia.delete(0, tk.END)
        self.entry_mecanismo.delete(0, tk.END)
        self.entry_descricao.delete(0, tk.END)
        self.entry_funcao.delete(0, tk.END)

    def remove_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Nenhuma linha selecionada.")
            return
        for item in selected:
            ori, des, typ, lin, ref = self.tree.item(item)['values']
            if ori in self.rules:
                new = [r for r in self.rules[ori] if not (r[0]==des and r[1]==typ and r[2]==lin and r[3]==ref and 
                                                        (len(r)<5 or r[4]==mec) and
                                                        (len(r)<6 or r[5]==desc) and
                                                        (len(r)<7 or r[6]==func))]
                if new: self.rules[ori] = new
                else:    del self.rules[ori]
            self.tree.delete(item)
        self.save_to_json()
        self.update_protein_list()

    def search_rule(self):
        term1 = self.search_entry.get().strip().lower()
        type1 = self.search_type.get()
        term2 = self.search_entry2.get().strip().lower()
        type2 = self.search_type2.get()
        self.tree.delete(*self.tree.get_children())
        for ori, targets in self.rules.items():
            for entry in targets:
                dest = entry[0] if len(entry)>=1 else ""
                typ  = entry[1] if len(entry)>=2 else ""
                lin  = entry[2] if len(entry)>=3 else ""
                ref  = entry[3] if len(entry)>=4 else ""
                mec  = entry[4] if len(entry)>=5 else ""
                desc = entry[5] if len(entry)>=6 else ""
                func = entry[6] if len(entry)>=7 else ""
                data = {
                    'Origem': ori.lower(),
                    'Destino': dest.lower(),
                    'Tipo': typ.lower(),
                    'Linhagem': lin.lower(),
                    'Referência': ref.lower(),
                    'Mecanismo': mec.lower(),
                    'Descrição': desc.lower(),
                    'Função': func.lower()
                }
                ok1 = (not term1) or (term1 in data[type1])
                ok2 = (not term2) or (type2 and term2 in data[type2])
                if ok1 and ok2:
                    self.tree.insert("", "end", values=(ori, dest, typ, lin, ref))

    def edit_cell(self, event):
        item   = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        if not item or not column:
            return
        idx = int(column.replace('#','')) - 1
        x,y,w,h = self.tree.bbox(item, column)
        entry = tk.Entry(self.tree)
        entry.place(x=x, y=y, width=w, height=h)
        entry.insert(0, self.tree.item(item)['values'][idx])
        entry.focus()

        def save(e=None):
            new = entry.get().strip()
            vals = list(self.tree.item(item)['values'])
            vals[idx] = new
            self.tree.item(item, values=vals)
            entry.destroy()
            self.save_to_json()
            self.update_protein_list()

        entry.bind("<FocusOut>", save)
        entry.bind("<Return>", save)

    def save_to_json(self):
        if not self.json_path:
            return
        data = {}
        for row in self.tree.get_children():
            ori, des, typ, lin, ref, mec, desc, func = self.tree.item(row)['values']
            data.setdefault(ori, []).append([des, typ, lin, ref, mec, desc, func])
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            self.rules = data
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar JSON: {e}")

    def copy_reference(self):
        sel = self.tree.selection()
        if sel:
            ref = self.tree.item(sel[0])['values'][4]
            self.root.clipboard_clear()
            self.root.clipboard_append(ref)

    def apply_rules(self):
        try:
            with open(self.entry_json_apply.get(), 'r', encoding='utf-8') as f:
                rules = json.load(f)
            extract_folder = "extracted_ginml"
            os.makedirs(extract_folder, exist_ok=True)
            ginml = self.extract_ginml_from_zginml(self.entry_zginml.get(), extract_folder)
            tree, root_xml, graph, nodes = self.load_ginml(ginml)
            self.add_connections(graph, nodes, rules)
            tree.write(ginml)
            self.repackage_zginml(self.entry_zginml.get(), extract_folder, self.entry_output.get())
            shutil.rmtree(extract_folder)
            messagebox.showinfo("Sucesso", "Arquivo atualizado com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def extract_ginml_from_zginml(self, zginml, folder):
        with zipfile.ZipFile(zginml, 'r') as z:
            z.extractall(folder)
        return os.path.join(folder, "GINsim-data", "regulatoryGraph.ginml")

    def load_ginml(self, path):
        tree = ET.parse(path)
        root_xml = tree.getroot()
        graph = root_xml.find("graph")
        nodes = {n.get('id'): n for n in graph.findall('node')}
        return tree, root_xml, graph, nodes

    def add_connections(self, graph, nodes, rules):

        filt = self.combo_linhagem.get().strip()
        
        pairs = {}
        for src, lst in rules.items():
            for r in lst:
                
                if len(r) < 4:
                    continue
                tgt   = r[0].strip()
                inter = r[1].strip()  
                lin   = r[2].strip()  
                pairs.setdefault((src, tgt), []).append((inter, lin))

        
        for (src, tgt), options in pairs.items():
            choice = None       
            found_exact = False

            if filt:
                
                for inter, lin in options:
                    if lin == filt:
                        found_exact = True
                        if inter in ['+', '-']:
                            choice = inter   
                        else:
                            choice = None    
                        break

                if not found_exact:
                    
                    for inter, lin in options:
                        if lin == "":
                            if inter in ['+', '-']:
                                choice = inter
                            else:
                                choice = None
                            break

            else:
               
                for inter, lin in options:
                    if lin == "":
                        if inter in ['+', '-']:
                            choice = inter
                        else:
                            choice = None
                        break

           
            if choice and (src in nodes) and (tgt in nodes):
                edge = ET.SubElement(graph, 'edge', {
                    'id':       f"{src}:{tgt}",
                    'from':     src,
                    'to':       tgt,
                    'minvalue': "1",
                    'sign':     "positive" if choice == '+' else "negative"
                })
                ET.SubElement(edge, 'edgevisualsetting', {'anchor': "NE", 'style': ""})

    def repackage_zginml(self, orig, folder, out):
        with zipfile.ZipFile(orig, 'r') as zin:
            files = zin.namelist()
        with zipfile.ZipFile(out, 'w') as zout:
            for f in files:
                fp = os.path.join(folder, f)
                if os.path.exists(fp):
                    zout.write(fp, f)

    def create_new_json(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files","*.json")])
        if not path:
            return
        self.rules = {}
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=4, ensure_ascii=False)
            self.json_path = path
            messagebox.showinfo("Novo JSON", f"Novo arquivo JSON criado: {path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar novo JSON: {e}")

    def create_remote_tab(self):
        frame = ttk.Frame(self.tab_remote, padding=10)
        frame.pack(fill='both', expand=True)

        ttk.Label(frame, text="GitHub Token:").grid(row=0, column=0, sticky="w", pady=(0,10))
        self.entry_token = ttk.Entry(frame, show='*', width=50)
        self.entry_token.grid    (row=0, column=1, padx=5, pady=(0,10))

        ttk.Button(frame, text="Baixar JSON Remoto",    command=self.download_remote).grid(row=1, column=0, pady=5)
        ttk.Button(frame, text="Commit e Atualizar JSON", command=self.commit_remote).grid(row=1, column=1, pady=5)

    def download_remote(self):
        token     = self.entry_token.get().strip()
        owner     = self.github_owner
        repo_name = self.github_repo
        path      = self.github_filepath

        if not (token and owner and repo_name and path):
            messagebox.showerror("Erro", "Preencha todos os campos antes de baixar.")
            return
        try:
            gh   = Github(token)
            repo = gh.get_repo(f"{owner}/{repo_name}")
            contents = repo.get_contents(self.github_filepath, ref="main")
            data = contents.decoded_content.decode('utf-8')
            local = filedialog.asksaveasfilename(defaultextension=".json",
                                                 initialfile=os.path.basename(path))
            if not local:
                return
            with open(local, 'w', encoding='utf-8') as f:
                f.write(data)
            self.json_path = local
            messagebox.showinfo("Sucesso", f"Arquivo baixado para: {local}")
        except GithubException as e:
            messagebox.showerror("GitHub Error", f"{e.status}: {e.data.get('message',e)}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def commit_remote(self):
        token     = self.entry_token.get().strip()
        owner     = self.github_owner
        repo_name = self.github_repo
        path      = self.github_filepath

        if not (token and owner and repo_name and path and self.json_path):
            messagebox.showerror("Erro", "Preencha todos os campos e carregue um JSON antes.")
            return

        with open(self.json_path, 'r', encoding='utf-8') as f:
            content = f.read()

        user = simpledialog.askstring(
           "Usuário",
           "Nome do responsável:",
           parent=self.root
        )
        if not user:
           return

        changes = simpledialog.askstring(
          "Alterações",
          "Descreva as mudanças:",
           parent=self.root
        )
        if changes is None:
          return

        try:
            gh   = Github(token)
            repo = gh.get_repo(f"{owner}/{repo_name}")
            try:
                existing = repo.get_contents(path)
                repo.update_file(path, f"{user}: {changes}", content, existing.sha)
            except GithubException:
                repo.create_file(path, f"{user}: {changes}", content)
            messagebox.showinfo("Sucesso", "Commit remoto realizado com sucesso!")
        except GithubException as e:
            messagebox.showerror("GitHub Error", f"{e.status}: {e.data.get('message',e)}")
        except Exception as e:
            messagebox.showerror("Erro", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    root.minsize(800, 600)
    app = RuleEditorApp(root)
    root.mainloop()
