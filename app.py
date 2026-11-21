import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import banco


def formatar_moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def ler_decimal(texto):
    texto_limpo = texto.strip().replace("R$", "").replace(" ", "").replace(",", ".")
    return float(texto_limpo)


class AplicacaoGCL:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestão Comunitária Livre (GCL)")
        self.root.geometry("1040x640")
        self.root.minsize(900, 560)
        self.root.configure(bg="#f4f6f8")

        banco.inicializar_banco()
        self.config = banco.obter_configuracao()

        self._configurar_estilos()
        self._montar_interface()
        self._configurar_atalhos()
        self.atualizar_lista()

    def _configurar_estilos(self):
        estilo = ttk.Style()
        estilo.theme_use("clam")

        estilo.configure("Treeview", font=("Arial", 11), rowheight=30)
        estilo.configure("Treeview.Heading", font=("Arial", 11, "bold"), background="#dce3ea", foreground="#1f2933")
        estilo.map("Treeview", background=[("selected", "#2b6cb0")], foreground=[("selected", "white")])

    def _montar_interface(self):
        # Topo com identificação do perfil comunitário
        topo = tk.Frame(self.root, bg="#1e3a5f", padx=14, pady=10)
        topo.pack(fill="x")

        self.lbl_titulo = tk.Label(
            topo,
            text="",
            font=("Arial", 15, "bold"),
            bg="#1e3a5f",
            fg="white",
        )
        self.lbl_titulo.pack(side="left")

        btn_perfil = tk.Button(
            topo,
            text="Configurar Perfil",
            font=("Arial", 10, "bold"),
            bg="#edf2f7",
            fg="#1e3a5f",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_janela_perfil,
        )
        btn_perfil.pack(side="right")

        # Barra de ações principais (botões grandes com atalhos F1 a F5)
        barra_acoes = tk.Frame(self.root, bg="#f4f6f8", padx=12, pady=10)
        barra_acoes.pack(fill="x")

        botoes = [
            ("[F1] Registrar Venda", "#2f855a", self.abrir_janela_venda),
            ("[F2] Cadastrar Produto", "#2b6cb0", self.abrir_janela_novo_produto),
            ("[F3] Buscar Produto", "#4a5568", self.focar_busca),
            ("[F4] Fechar Caixa", "#2c5282", self.abrir_janela_caixa),
            ("[F5] Ver Alertas", "#c05621", self.abrir_janela_alertas),
        ]

        for texto, cor, comando in botoes:
            btn = tk.Button(
                barra_acoes,
                text=texto,
                font=("Arial", 11, "bold"),
                bg=cor,
                fg="white",
                activebackground=cor,
                activeforeground="white",
                relief="flat",
                padx=12,
                pady=10,
                cursor="hand2",
                command=comando,
            )
            btn.pack(side="left", expand=True, fill="x", padx=4)

        # Barra de busca e filtro por categoria
        barra_filtro = tk.Frame(self.root, bg="#f4f6f8", padx=14, pady=4)
        barra_filtro.pack(fill="x")

        tk.Label(barra_filtro, text="Buscar (F3):", font=("Arial", 11, "bold"), bg="#f4f6f8").pack(side="left")

        self.var_busca = tk.StringVar()
        self.entry_busca = tk.Entry(barra_filtro, textvariable=self.var_busca, font=("Arial", 11), width=32)
        self.entry_busca.pack(side="left", padx=(6, 14), ipady=3)
        self.entry_busca.bind("<KeyRelease>", lambda e: self.atualizar_lista())

        tk.Label(barra_filtro, text="Categoria:", font=("Arial", 11, "bold"), bg="#f4f6f8").pack(side="left")

        self.var_categoria_filtro = tk.StringVar(value="Todas")
        self.combo_categoria_filtro = ttk.Combobox(
            barra_filtro,
            textvariable=self.var_categoria_filtro,
            state="readonly",
            font=("Arial", 11),
            width=20,
        )
        self.combo_categoria_filtro.pack(side="left", padx=6)
        self.combo_categoria_filtro.bind("<<ComboboxSelected>>", lambda e: self.atualizar_lista())

        btn_limpar = tk.Button(
            barra_filtro,
            text="Limpar Filtro",
            font=("Arial", 10),
            bg="#e2e8f0",
            relief="flat",
            padx=8,
            pady=4,
            cursor="hand2",
            command=self.limpar_filtros,
        )
        btn_limpar.pack(side="left", padx=6)

        # Botões secundários para o item selecionado na tabela
        btn_excluir = tk.Button(
            barra_filtro,
            text="Excluir Item",
            font=("Arial", 10, "bold"),
            bg="#e53e3e",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.excluir_produto_selecionado,
        )
        btn_excluir.pack(side="right", padx=(6, 0))

        btn_editar = tk.Button(
            barra_filtro,
            text="Editar Item",
            font=("Arial", 10, "bold"),
            bg="#4a5568",
            fg="white",
            relief="flat",
            padx=10,
            pady=4,
            cursor="hand2",
            command=self.abrir_janela_editar_produto,
        )
        btn_editar.pack(side="right")

        # Tabela principal de produtos e estoque
        frame_tabela = tk.Frame(self.root, bg="#f4f6f8", padx=14, pady=6)
        frame_tabela.pack(fill="both", expand=True)

        colunas = ("id", "nome", "categoria", "qtd", "minimo", "custo", "venda", "validade", "status")
        self.tabela = ttk.Treeview(frame_tabela, columns=colunas, show="headings", selectmode="browse")

        cabecalhos = {
            "id": ("Cód.", 50, "center"),
            "nome": ("Produto", 230, "w"),
            "categoria": ("Categoria", 130, "w"),
            "qtd": ("Estoque", 75, "center"),
            "minimo": ("Mínimo", 75, "center"),
            "custo": ("Custo", 90, "e"),
            "venda": ("Venda", 90, "e"),
            "validade": ("Validade", 100, "center"),
            "status": ("Situação", 150, "center"),
        }

        for col, (titulo, largura, alinhamento) in cabecalhos.items():
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura, anchor=alinhamento)

        # Cores dos alertas visuais
        self.tabela.tag_configure("vermelho", background="#fed7d7", foreground="#9b2c2c")
        self.tabela.tag_configure("amarelo", background="#fefcbf", foreground="#744210")
        self.tabela.tag_configure("normal", background="white", foreground="#1a202c")

        scroll_y = ttk.Scrollbar(frame_tabela, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=scroll_y.set)

        self.tabela.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        self.tabela.bind("<Double-1>", lambda e: self.abrir_janela_editar_produto())

        # Legenda e resumo rápido do dia no rodapé
        rodape = tk.Frame(self.root, bg="#e2e8f0", padx=14, pady=8)
        rodape.pack(fill="x")

        legenda = tk.Frame(rodape, bg="#e2e8f0")
        legenda.pack(side="left")

        tk.Label(legenda, text=" Vermelho: Estoque mínimo / vencido ", bg="#fed7d7", fg="#9b2c2c", font=("Arial", 9, "bold")).pack(side="left", padx=(0, 8))
        tk.Label(legenda, text=" Amarelo: Vence em até 15 dias ", bg="#fefcbf", fg="#744210", font=("Arial", 9, "bold")).pack(side="left")

        self.lbl_resumo = tk.Label(rodape, text="", font=("Arial", 10, "bold"), bg="#e2e8f0", fg="#1a202c")
        self.lbl_resumo.pack(side="right")

        self._atualizar_cabecalho()

    def _configurar_atalhos(self):
        self.root.bind("<F1>", lambda e: self.abrir_janela_venda())
        self.root.bind("<F2>", lambda e: self.abrir_janela_novo_produto())
        self.root.bind("<F3>", lambda e: self.focar_busca())
        self.root.bind("<F4>", lambda e: self.abrir_janela_caixa())
        self.root.bind("<F5>", lambda e: self.abrir_janela_alertas())

    def _atualizar_cabecalho(self):
        self.config = banco.obter_configuracao()
        self.lbl_titulo.config(text=f"GCL - {self.config['nome_negocio']}  |  Perfil: {self.config['perfil']}")

    def _atualizar_combo_categorias(self):
        perfil_atual = self.config["perfil"]
        padroes = banco.PERFIS_CATEGORIAS.get(perfil_atual, [])
        existentes = banco.listar_categorias_existentes()
        todas = sorted(set(padroes + existentes))
        self.combo_categoria_filtro["values"] = ["Todas"] + todas
        if self.var_categoria_filtro.get() not in self.combo_categoria_filtro["values"]:
            self.var_categoria_filtro.set("Todas")

    def focar_busca(self):
        self.entry_busca.focus_set()
        self.entry_busca.select_range(0, tk.END)

    def limpar_filtros(self):
        self.var_busca.set("")
        self.var_categoria_filtro.set("Todas")
        self.atualizar_lista()

    def atualizar_lista(self):
        self._atualizar_combo_categorias()

        for item in self.tabela.get_children():
            self.tabela.delete(item)

        produtos = banco.listar_produtos(
            termo_busca=self.var_busca.get(),
            categoria=self.var_categoria_filtro.get(),
        )

        for p in produtos:
            nivel, status = banco.avaliar_status_produto(p)
            self.tabela.insert(
                "",
                "end",
                iid=str(p["id"]),
                values=(
                    p["id"],
                    p["nome"],
                    p["categoria"],
                    p["quantidade"],
                    p["estoque_minimo"],
                    formatar_moeda(p["preco_custo"]),
                    formatar_moeda(p["preco_venda"]),
                    p["data_validade"] or "-",
                    status,
                ),
                tags=(nivel,),
            )

        resumo_hoje = banco.resumo_caixa_por_data()
        total_alertas = len(banco.listar_alertas_ordenados())
        self.lbl_resumo.config(
            text=(
                f"Produtos exibidos: {len(produtos)}   |   "
                f"Alertas ativos: {total_alertas}   |   "
                f"Vendas de hoje: {formatar_moeda(resumo_hoje['total_vendido'])}"
            )
        )

    def _obter_id_selecionado(self):
        selecionado = self.tabela.selection()
        if not selecionado:
            return None
        return int(selecionado[0])

    # -------------------- JANELA DE PERFIL --------------------
    def abrir_janela_perfil(self):
        janela = tk.Toplevel(self.root)
        janela.title("Configurar Perfil Comunitário")
        janela.geometry("420x230")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        frame = tk.Frame(janela, padx=16, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Nome do negócio ou empreendedor:", font=("Arial", 11, "bold")).pack(anchor="w")
        entry_nome = tk.Entry(frame, font=("Arial", 11))
        entry_nome.insert(0, self.config["nome_negocio"])
        entry_nome.pack(fill="x", pady=(4, 12), ipady=3)

        tk.Label(frame, text="Ramo de atividade (perfil de categorias):", font=("Arial", 11, "bold")).pack(anchor="w")
        combo_perfil = ttk.Combobox(
            frame,
            values=list(banco.PERFIS_CATEGORIAS.keys()),
            state="readonly",
            font=("Arial", 11),
        )
        combo_perfil.set(self.config["perfil"])
        combo_perfil.pack(fill="x", pady=(4, 16))

        def salvar():
            nome = entry_nome.get().strip()
            perfil = combo_perfil.get().strip()
            if not nome:
                messagebox.showwarning("Aviso", "Informe o nome do negócio.", parent=janela)
                return
            banco.salvar_configuracao(nome, perfil)
            self._atualizar_cabecalho()
            self.atualizar_lista()
            janela.destroy()

        tk.Button(
            frame,
            text="Salvar Perfil",
            font=("Arial", 11, "bold"),
            bg="#2b6cb0",
            fg="white",
            relief="flat",
            pady=8,
            cursor="hand2",
            command=salvar,
        ).pack(fill="x")

        janela.bind("<Escape>", lambda e: janela.destroy())

    # -------------------- CADASTRO / EDIÇÃO DE PRODUTO (F2) --------------------
    def abrir_janela_novo_produto(self):
        self._abrir_formulario_produto(produto=None)

    def abrir_janela_editar_produto(self):
        prod_id = self._obter_id_selecionado()
        if not prod_id:
            messagebox.showinfo("Aviso", "Selecione um produto na tabela para editar.")
            return
        prod = banco.buscar_produto_por_id(prod_id)
        if prod:
            self._abrir_formulario_produto(produto=prod)

    def _abrir_formulario_produto(self, produto=None):
        editando = produto is not None
        janela = tk.Toplevel(self.root)
        janela.title("Editar Produto" if editando else "Cadastrar Novo Produto (F2)")
        janela.geometry("450x430")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        frame = tk.Frame(janela, padx=18, pady=14)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Nome do produto:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        entry_nome = tk.Entry(frame, font=("Arial", 11))
        entry_nome.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 10), ipady=3)

        tk.Label(frame, text="Categoria:", font=("Arial", 11, "bold")).grid(row=2, column=0, columnspan=2, sticky="w")
        categorias_sugeridas = sorted(set(
            banco.PERFIS_CATEGORIAS.get(self.config["perfil"], []) + banco.listar_categorias_existentes()
        ))
        combo_cat = ttk.Combobox(frame, values=categorias_sugeridas, font=("Arial", 11))
        combo_cat.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(2, 10))

        tk.Label(frame, text="Preço de custo (R$):", font=("Arial", 11, "bold")).grid(row=4, column=0, sticky="w")
        tk.Label(frame, text="Preço de venda (R$):", font=("Arial", 11, "bold")).grid(row=4, column=1, sticky="w", padx=(10, 0))

        entry_custo = tk.Entry(frame, font=("Arial", 11))
        entry_custo.grid(row=5, column=0, sticky="ew", pady=(2, 10), ipady=3)
        entry_venda = tk.Entry(frame, font=("Arial", 11))
        entry_venda.grid(row=5, column=1, sticky="ew", padx=(10, 0), pady=(2, 10), ipady=3)

        tk.Label(frame, text="Quantidade em estoque:", font=("Arial", 11, "bold")).grid(row=6, column=0, sticky="w")
        tk.Label(frame, text="Estoque mínimo (alerta):", font=("Arial", 11, "bold")).grid(row=6, column=1, sticky="w", padx=(10, 0))

        entry_qtd = tk.Entry(frame, font=("Arial", 11))
        entry_qtd.grid(row=7, column=0, sticky="ew", pady=(2, 10), ipady=3)
        entry_min = tk.Entry(frame, font=("Arial", 11))
        entry_min.grid(row=7, column=1, sticky="ew", padx=(10, 0), pady=(2, 10), ipady=3)

        tk.Label(frame, text="Data de validade (DD/MM/AAAA - opcional):", font=("Arial", 11, "bold")).grid(row=8, column=0, columnspan=2, sticky="w")
        entry_val = tk.Entry(frame, font=("Arial", 11))
        entry_val.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(2, 16), ipady=3)

        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        if editando:
            entry_nome.insert(0, produto["nome"])
            combo_cat.set(produto["categoria"])
            entry_custo.insert(0, f"{produto['preco_custo']:.2f}".replace(".", ","))
            entry_venda.insert(0, f"{produto['preco_venda']:.2f}".replace(".", ","))
            entry_qtd.insert(0, str(produto["quantidade"]))
            entry_min.insert(0, str(produto["estoque_minimo"]))
            if produto["data_validade"]:
                entry_val.insert(0, produto["data_validade"])
        else:
            if categorias_sugeridas:
                combo_cat.set(categorias_sugeridas[0])
            entry_min.insert(0, "5")

        def salvar():
            nome = entry_nome.get().strip()
            cat = combo_cat.get().strip() or "Diversos"
            validade = entry_val.get().strip()

            if not nome:
                messagebox.showwarning("Aviso", "Digite o nome do produto.", parent=janela)
                return

            try:
                custo = ler_decimal(entry_custo.get() or "0")
                venda = ler_decimal(entry_venda.get())
                qtd = int(entry_qtd.get().strip())
                minimo = int(entry_min.get().strip() or "0")
            except ValueError:
                messagebox.showerror("Erro", "Verifique os valores numéricos de preço e quantidade.", parent=janela)
                return

            if custo < 0 or venda < 0 or qtd < 0 or minimo < 0:
                messagebox.showwarning("Aviso", "Os valores não podem ser negativos.", parent=janela)
                return

            if validade:
                try:
                    datetime.strptime(validade, "%d/%m/%Y")
                except ValueError:
                    messagebox.showerror("Erro", "Use a data de validade no formato DD/MM/AAAA (ex: 25/12/2026).", parent=janela)
                    return

            if editando:
                banco.atualizar_produto(produto["id"], nome, cat, custo, venda, qtd, minimo, validade)
            else:
                banco.inserir_produto(nome, cat, custo, venda, qtd, minimo, validade)

            self.atualizar_lista()
            janela.destroy()

        tk.Button(
            frame,
            text="Salvar Produto",
            font=("Arial", 11, "bold"),
            bg="#2f855a",
            fg="white",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=salvar,
        ).grid(row=10, column=0, columnspan=2, sticky="ew")

        entry_nome.focus_set()
        janela.bind("<Escape>", lambda e: janela.destroy())

    def excluir_produto_selecionado(self):
        prod_id = self._obter_id_selecionado()
        if not prod_id:
            messagebox.showinfo("Aviso", "Selecione um produto na tabela para excluir.")
            return
        prod = banco.buscar_produto_por_id(prod_id)
        if not prod:
            return
        if messagebox.askyesno("Confirmar", f"Deseja realmente excluir '{prod['nome']}' do estoque?"):
            banco.excluir_produto(prod_id)
            self.atualizar_lista()

    # -------------------- REGISTRO DE VENDA (F1) --------------------
    def abrir_janela_venda(self):
        produtos = banco.listar_produtos()
        if not produtos:
            messagebox.showinfo("Aviso", "Cadastre pelo menos um produto (F2) antes de registrar vendas.")
            return

        janela = tk.Toplevel(self.root)
        janela.title("Registrar Venda (F1)")
        janela.geometry("460x310")
        janela.resizable(False, False)
        janela.transient(self.root)
        janela.grab_set()

        frame = tk.Frame(janela, padx=18, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Selecione o produto:", font=("Arial", 11, "bold")).pack(anchor="w")

        mapa_produtos = {}
        opcoes = []
        id_pre_selecionado = self._obter_id_selecionado()
        texto_inicial = None

        for p in produtos:
            rotulo = f"{p['id']} - {p['nome']} (Estoque: {p['quantidade']} | {formatar_moeda(p['preco_venda'])})"
            mapa_produtos[rotulo] = p
            opcoes.append(rotulo)
            if p["id"] == id_pre_selecionado:
                texto_inicial = rotulo

        combo_prod = ttk.Combobox(frame, values=opcoes, state="readonly", font=("Arial", 11))
        combo_prod.set(texto_inicial or opcoes[0])
        combo_prod.pack(fill="x", pady=(4, 12))

        tk.Label(frame, text="Quantidade vendida:", font=("Arial", 11, "bold")).pack(anchor="w")
        var_qtd = tk.StringVar(value="1")
        entry_qtd = tk.Entry(frame, textvariable=var_qtd, font=("Arial", 12))
        entry_qtd.pack(fill="x", pady=(4, 12), ipady=4)

        lbl_total = tk.Label(frame, text="Total: R$ 0,00", font=("Arial", 14, "bold"), fg="#2f855a")
        lbl_total.pack(pady=(4, 16))

        def atualizar_total(*args):
            prod = mapa_produtos.get(combo_prod.get())
            try:
                qtd = int(var_qtd.get())
                if prod and qtd > 0:
                    total = prod["preco_venda"] * qtd
                    lbl_total.config(text=f"Total: {formatar_moeda(total)}")
                else:
                    lbl_total.config(text="Total: R$ 0,00")
            except ValueError:
                lbl_total.config(text="Total: R$ 0,00")

        combo_prod.bind("<<ComboboxSelected>>", atualizar_total)
        var_qtd.trace_add("write", atualizar_total)
        atualizar_total()

        def confirmar_venda():
            prod = mapa_produtos.get(combo_prod.get())
            try:
                qtd = int(var_qtd.get().strip())
            except ValueError:
                messagebox.showerror("Erro", "Informe uma quantidade inteira válida.", parent=janela)
                return

            try:
                total = banco.registrar_venda(prod["id"], qtd)
            except ValueError as err:
                messagebox.showwarning("Atenção", str(err), parent=janela)
                return

            self.atualizar_lista()
            messagebox.showinfo(
                "Venda Registrada",
                f"Venda confirmada!\nProduto: {prod['nome']}\nQuantidade: {qtd}\nTotal: {formatar_moeda(total)}",
                parent=janela,
            )
            janela.destroy()

        tk.Button(
            frame,
            text="Confirmar Venda e Dar Baixa no Estoque",
            font=("Arial", 11, "bold"),
            bg="#2f855a",
            fg="white",
            relief="flat",
            pady=10,
            cursor="hand2",
            command=confirmar_venda,
        ).pack(fill="x")

        entry_qtd.focus_set()
        entry_qtd.select_range(0, tk.END)
        janela.bind("<Return>", lambda e: confirmar_venda())
        janela.bind("<Escape>", lambda e: janela.destroy())

    # -------------------- FECHAMENTO DE CAIXA (F4) --------------------
    def abrir_janela_caixa(self):
        janela = tk.Toplevel(self.root)
        janela.title("Fechamento de Caixa Diário (F4)")
        janela.geometry("760x500")
        janela.transient(self.root)
        janela.grab_set()

        topo = tk.Frame(janela, padx=14, pady=10, bg="#f4f6f8")
        topo.pack(fill="x")

        tk.Label(topo, text="Data (DD/MM/AAAA):", font=("Arial", 11, "bold"), bg="#f4f6f8").pack(side="left")
        entry_data = tk.Entry(topo, font=("Arial", 11), width=14)
        entry_data.insert(0, datetime.now().strftime("%d/%m/%Y"))
        entry_data.pack(side="left", padx=8, ipady=2)

        frame_cards = tk.Frame(janela, padx=14, pady=6)
        frame_cards.pack(fill="x")

        lbl_vendas_qtd = tk.Label(frame_cards, text="", font=("Arial", 11, "bold"), bg="#edf2f7", padx=12, pady=8)
        lbl_vendas_qtd.pack(side="left", expand=True, fill="x", padx=4)

        lbl_total_dia = tk.Label(frame_cards, text="", font=("Arial", 11, "bold"), bg="#c6f6d5", fg="#22543d", padx=12, pady=8)
        lbl_total_dia.pack(side="left", expand=True, fill="x", padx=4)

        lbl_lucro_dia = tk.Label(frame_cards, text="", font=("Arial", 11, "bold"), bg="#bee3f8", fg="#2a4365", padx=12, pady=8)
        lbl_lucro_dia.pack(side="left", expand=True, fill="x", padx=4)

        frame_lista = tk.Frame(janela, padx=14, pady=8)
        frame_lista.pack(fill="both", expand=True)

        colunas = ("hora", "produto", "qtd", "unit", "total")
        tree = ttk.Treeview(frame_lista, columns=colunas, show="headings")
        tree.heading("hora", text="Horário")
        tree.heading("produto", text="Produto")
        tree.heading("qtd", text="Qtd.")
        tree.heading("unit", text="Unitário")
        tree.heading("total", text="Total")

        tree.column("hora", width=90, anchor="center")
        tree.column("produto", width=310, anchor="w")
        tree.column("qtd", width=70, anchor="center")
        tree.column("unit", width=110, anchor="e")
        tree.column("total", width=110, anchor="e")

        scroll = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        resumo_atual = {}

        def carregar_resumo():
            data_str = entry_data.get().strip()
            try:
                datetime.strptime(data_str, "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Erro", "Informe a data no formato DD/MM/AAAA.", parent=janela)
                return

            dados = banco.resumo_caixa_por_data(data_str)
            resumo_atual.clear()
            resumo_atual.update(dados)

            lbl_vendas_qtd.config(text=f"Vendas: {dados['qtd_vendas']} ({dados['total_itens']} itens)")
            lbl_total_dia.config(text=f"Faturamento: {formatar_moeda(dados['total_vendido'])}")
            lbl_lucro_dia.config(text=f"Lucro Estimado: {formatar_moeda(dados['lucro_estimado'])}")

            for item in tree.get_children():
                tree.delete(item)

            for v in dados["vendas"]:
                tree.insert(
                    "",
                    "end",
                    values=(
                        v["hora_venda"],
                        v["nome_produto"],
                        v["quantidade"],
                        formatar_moeda(v["preco_unitario"]),
                        formatar_moeda(v["valor_total"]),
                    ),
                )

        def exportar_txt():
            if not resumo_atual:
                return
            nome_sugerido = f"fechamento_{resumo_atual['data'].replace('/', '-')}.txt"
            caminho = filedialog.asksaveasfilename(
                parent=janela,
                title="Salvar Relatório de Fechamento de Caixa",
                initialfile=nome_sugerido,
                defaultextension=".txt",
                filetypes=[("Arquivo de texto", "*.txt")],
            )
            if not caminho:
                return

            linhas = [
                f"RELATÓRIO DE FECHAMENTO DE CAIXA - {self.config['nome_negocio']}",
                f"Data: {resumo_atual['data']}",
                "-" * 55,
                f"Quantidade de vendas: {resumo_atual['qtd_vendas']}",
                f"Total de itens vendidos: {resumo_atual['total_itens']}",
                f"Faturamento total: {formatar_moeda(resumo_atual['total_vendido'])}",
                f"Custo estimado: {formatar_moeda(resumo_atual['total_custo'])}",
                f"Lucro estimado: {formatar_moeda(resumo_atual['lucro_estimado'])}",
                "-" * 55,
                "VENDAS REGISTRADAS:",
            ]

            for v in resumo_atual["vendas"]:
                linhas.append(
                    f"[{v['hora_venda']}] {v['nome_produto']} - {v['quantidade']}x "
                    f"{formatar_moeda(v['preco_unitario'])} = {formatar_moeda(v['valor_total'])}"
                )

            with open(caminho, "w", encoding="utf-8") as f:
                f.write("\n".join(linhas))

            messagebox.showinfo("Sucesso", "Relatório de caixa salvo com sucesso!", parent=janela)

        tk.Button(
            topo,
            text="Consultar",
            font=("Arial", 10, "bold"),
            bg="#2b6cb0",
            fg="white",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=carregar_resumo,
        ).pack(side="left", padx=4)

        tk.Button(
            topo,
            text="Salvar Relatório (.txt)",
            font=("Arial", 10, "bold"),
            bg="#2f855a",
            fg="white",
            relief="flat",
            padx=12,
            pady=4,
            cursor="hand2",
            command=exportar_txt,
        ).pack(side="right")

        carregar_resumo()
        janela.bind("<Escape>", lambda e: janela.destroy())

    # -------------------- CENTRAL DE ALERTAS (F5) --------------------
    def abrir_janela_alertas(self):
        alertas = banco.listar_alertas_ordenados()

        janela = tk.Toplevel(self.root)
        janela.title("Alertas de Estoque e Validade (F5)")
        janela.geometry("720x420")
        janela.transient(self.root)
        janela.grab_set()

        tk.Label(
            janela,
            text="Produtos com estoque mínimo ou vencimento próximo (ordenados por urgência):",
            font=("Arial", 11, "bold"),
            padx=14,
            pady=10,
        ).pack(anchor="w")

        frame = tk.Frame(janela, padx=14, pady=4)
        frame.pack(fill="both", expand=True)

        colunas = ("produto", "categoria", "qtd", "minimo", "validade", "alerta")
        tree = ttk.Treeview(frame, columns=colunas, show="headings")
        tree.heading("produto", text="Produto")
        tree.heading("categoria", text="Categoria")
        tree.heading("qtd", text="Estoque")
        tree.heading("minimo", text="Mínimo")
        tree.heading("validade", text="Validade")
        tree.heading("alerta", text="Motivo do Alerta")

        tree.column("produto", width=200, anchor="w")
        tree.column("categoria", width=110, anchor="w")
        tree.column("qtd", width=65, anchor="center")
        tree.column("minimo", width=65, anchor="center")
        tree.column("validade", width=95, anchor="center")
        tree.column("alerta", width=155, anchor="center")

        tree.tag_configure("vermelho", background="#fed7d7", foreground="#9b2c2c")
        tree.tag_configure("amarelo", background="#fefcbf", foreground="#744210")

        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        if not alertas:
            messagebox.showinfo("Tudo certo!", "Nenhum produto está em alerta de estoque ou validade.", parent=janela)
        else:
            for item in alertas:
                p = item["produto"]
                tree.insert(
                    "",
                    "end",
                    values=(
                        p["nome"],
                        p["categoria"],
                        p["quantidade"],
                        p["estoque_minimo"],
                        p["data_validade"] or "-",
                        item["mensagem"],
                    ),
                    tags=(item["nivel"],),
                )

        janela.bind("<Escape>", lambda e: janela.destroy())


if __name__ == "__main__":
    raiz = tk.Tk()
    app = AplicacaoGCL(raiz)
    raiz.mainloop()
