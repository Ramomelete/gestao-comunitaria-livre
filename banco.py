import sqlite3
from datetime import datetime

NOME_BANCO = "gcl_dados.db"

PERFIS_CATEGORIAS = {
    "Comércio Geral": ["Alimentos", "Bebidas", "Limpeza", "Higiene", "Diversos"],
    "Feirante / Hortifrúti": ["Frutas", "Verduras", "Legumes", "Temperos", "Raízes"],
    "Mercearia Familiar": ["Mercearia Seca", "Laticínios", "Frios", "Bebidas", "Limpeza", "Padaria"],
    "Lanches Caseiros": ["Salgados", "Doces", "Bebidas", "Insumos", "Embalagens"],
    "Artesanato": ["Peças Prontas", "Matéria-Prima", "Acessórios", "Decoração", "Embalagens"],
}


def conectar(caminho_banco=NOME_BANCO):
    conn = sqlite3.connect(caminho_banco)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_banco(caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS configuracao (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            nome_negocio TEXT NOT NULL,
            perfil TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            preco_custo REAL NOT NULL DEFAULT 0,
            preco_venda REAL NOT NULL DEFAULT 0,
            quantidade INTEGER NOT NULL DEFAULT 0,
            estoque_minimo INTEGER NOT NULL DEFAULT 5,
            data_validade TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            nome_produto TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_custo REAL NOT NULL,
            preco_unitario REAL NOT NULL,
            valor_total REAL NOT NULL,
            data_venda TEXT NOT NULL,
            hora_venda TEXT NOT NULL,
            FOREIGN KEY (produto_id) REFERENCES produtos(id) ON DELETE SET NULL
        )
    """)

    cursor.execute("SELECT COUNT(*) FROM configuracao")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO configuracao (id, nome_negocio, perfil) VALUES (1, ?, ?)",
            ("Meu Negócio Comunitário", "Comércio Geral"),
        )

    conn.commit()
    conn.close()


def obter_configuracao(caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    row = conn.execute("SELECT nome_negocio, perfil FROM configuracao WHERE id = 1").fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"nome_negocio": "Meu Negócio Comunitário", "perfil": "Comércio Geral"}


def salvar_configuracao(nome_negocio, perfil, caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    conn.execute(
        "UPDATE configuracao SET nome_negocio = ?, perfil = ? WHERE id = 1",
        (nome_negocio.strip(), perfil.strip()),
    )
    conn.commit()
    conn.close()


def inserir_produto(nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo, data_validade, caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO produtos (nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo, data_validade)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (nome.strip(), categoria.strip(), preco_custo, preco_venda, quantidade, estoque_minimo, data_validade or None),
    )
    novo_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return novo_id


def atualizar_produto(produto_id, nome, categoria, preco_custo, preco_venda, quantidade, estoque_minimo, data_validade, caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    conn.execute(
        """
        UPDATE produtos
        SET nome = ?, categoria = ?, preco_custo = ?, preco_venda = ?,
            quantidade = ?, estoque_minimo = ?, data_validade = ?
        WHERE id = ?
        """,
        (nome.strip(), categoria.strip(), preco_custo, preco_venda, quantidade, estoque_minimo, data_validade or None, produto_id),
    )
    conn.commit()
    conn.close()


def excluir_produto(produto_id, caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    conn.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    conn.commit()
    conn.close()


def buscar_produto_por_id(produto_id, caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    row = conn.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def listar_produtos(termo_busca="", categoria="Todas", caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    query = "SELECT * FROM produtos WHERE 1=1"
    params = []

    if termo_busca.strip():
        query += " AND LOWER(nome) LIKE ?"
        params.append(f"%{termo_busca.strip().lower()}%")

    if categoria and categoria != "Todas":
        query += " AND categoria = ?"
        params.append(categoria)

    query += " ORDER BY nome ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def listar_categorias_existentes(caminho_banco=NOME_BANCO):
    conn = conectar(caminho_banco)
    rows = conn.execute("SELECT DISTINCT categoria FROM produtos ORDER BY categoria ASC").fetchall()
    conn.close()
    return [r["categoria"] for r in rows]


def calcular_dias_validade(data_str):
    if not data_str:
        return None
    try:
        dt = datetime.strptime(data_str, "%d/%m/%Y").date()
        hoje = datetime.now().date()
        return (dt - hoje).days
    except ValueError:
        return None


def avaliar_status_produto(produto):
    """
    Retorna tupla (nivel, mensagem):
    nivel: 'vermelho', 'amarelo' ou 'normal'
    """
    mensagens = []
    nivel = "normal"

    qtd = produto["quantidade"]
    minimo = produto["estoque_minimo"]
    dias = calcular_dias_validade(produto.get("data_validade"))

    if qtd <= minimo:
        nivel = "vermelho"
        if qtd == 0:
            mensagens.append("Sem estoque")
        else:
            mensagens.append("Estoque baixo")

    if dias is not None:
        if dias < 0:
            nivel = "vermelho"
            mensagens.append("Vencido")
        elif dias <= 15:
            if nivel != "vermelho":
                nivel = "amarelo"
            if dias == 0:
                mensagens.append("Vence hoje")
            else:
                mensagens.append(f"Vence em {dias}d")

    if not mensagens:
        return "normal", "OK"
    return nivel, " | ".join(mensagens)


def listar_alertas_ordenados(caminho_banco=NOME_BANCO):
    """
    Lista produtos em alerta ordenados por prioridade:
    1) Vermelho (estoque mínimo/zerado ou vencido)
    2) Amarelo (vencimento em até 15 dias), ordenados pelos dias restantes
    """
    produtos = listar_produtos(caminho_banco=caminho_banco)
    alertas = []

    for prod in produtos:
        nivel, msg = avaliar_status_produto(prod)
        if nivel != "normal":
            dias = calcular_dias_validade(prod.get("data_validade"))
            prioridade_nivel = 0 if nivel == "vermelho" else 1
            chave_dias = dias if dias is not None else 9999
            alertas.append({
                "produto": prod,
                "nivel": nivel,
                "mensagem": msg,
                "prioridade": (prioridade_nivel, prod["quantidade"] - prod["estoque_minimo"], chave_dias),
            })

    alertas.sort(key=lambda item: item["prioridade"])
    return alertas


def registrar_venda(produto_id, quantidade_vendida, caminho_banco=NOME_BANCO):
    if quantidade_vendida <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    conn = conectar(caminho_banco)
    cursor = conn.cursor()

    prod = cursor.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,)).fetchone()
    if not prod:
        conn.close()
        raise ValueError("Produto não encontrado.")

    if prod["quantidade"] < quantidade_vendida:
        conn.close()
        raise ValueError(f"Estoque insuficiente. Disponível: {prod['quantidade']}.")

    agora = datetime.now()
    data_str = agora.strftime("%d/%m/%Y")
    hora_str = agora.strftime("%H:%M:%S")
    valor_total = round(prod["preco_venda"] * quantidade_vendida, 2)

    cursor.execute(
        "UPDATE produtos SET quantidade = quantidade - ? WHERE id = ?",
        (quantidade_vendida, produto_id),
    )

    cursor.execute(
        """
        INSERT INTO vendas (produto_id, nome_produto, quantidade, preco_custo, preco_unitario, valor_total, data_venda, hora_venda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            prod["id"],
            prod["nome"],
            quantidade_vendida,
            prod["preco_custo"],
            prod["preco_venda"],
            valor_total,
            data_str,
            hora_str,
        ),
    )

    conn.commit()
    conn.close()
    return valor_total


def listar_vendas_por_data(data_str=None, caminho_banco=NOME_BANCO):
    if not data_str:
        data_str = datetime.now().strftime("%d/%m/%Y")

    conn = conectar(caminho_banco)
    rows = conn.execute(
        "SELECT * FROM vendas WHERE data_venda = ? ORDER BY id DESC",
        (data_str,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def resumo_caixa_por_data(data_str=None, caminho_banco=NOME_BANCO):
    vendas = listar_vendas_por_data(data_str, caminho_banco=caminho_banco)
    total_vendido = sum(v["valor_total"] for v in vendas)
    total_custo = sum(v["preco_custo"] * v["quantidade"] for v in vendas)
    total_itens = sum(v["quantidade"] for v in vendas)
    lucro_estimado = total_vendido - total_custo

    return {
        "data": data_str or datetime.now().strftime("%d/%m/%Y"),
        "qtd_vendas": len(vendas),
        "total_itens": total_itens,
        "total_vendido": round(total_vendido, 2),
        "total_custo": round(total_custo, 2),
        "lucro_estimado": round(lucro_estimado, 2),
        "vendas": vendas,
    }
