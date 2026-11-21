# Gestão Comunitária Livre (GCL)

Sistema desktop gratuito e de código aberto para controle de estoque, validade de produtos e fluxo de caixa diário, desenvolvido como solução computacional do **Projeto de Extensão III** do curso de **Bacharelado em Ciência da Computação** (Guarapari/ES).

O projeto foi criado para apoiar pequenos empreendedores, feirantes, trabalhadores autônomos e comércios familiares da comunidade da Praia do Morro que ainda controlavam suas vendas e estoques em cadernos de papel.

## Funcionalidades

- **Tela única simplificada:** operações de estoque, busca e acesso rápido às vendas sem menus complexos.
- **Perfis personalizáveis:** categorias adaptadas para Feirante/Hortifrúti, Mercearia Familiar, Lanches Caseiros, Artesanato ou Comércio Geral.
- **Atalhos rápidos no teclado:**
  - `F1`: Registrar venda (com baixa automática no estoque)
  - `F2`: Cadastrar novo produto
  - `F3`: Buscar produto por nome/categoria
  - `F4`: Fechamento de caixa diário (com exportação em `.txt`)
  - `F5`: Visualizar alertas de estoque mínimo e validade
- **Alertas visuais por cores:**
  - **Vermelho:** produto sem estoque, abaixo do estoque mínimo ou vencido.
  - **Amarelo:** produto a até 15 dias da data de vencimento.
- **Funcionamento offline:** utiliza banco de dados relacional local **SQLite**, sem exigir conexão com a internet.

## Tecnologias Utilizadas

- **Python 3**
- **Tkinter / ttk** (interface gráfica nativa)
- **SQLite 3** (banco de dados local em arquivo único)
- **PyInstaller** (empacotamento em executável portátil para Windows)

## Estrutura do Projeto

```text
gestao-comunitaria-livre/
├── app.py          # Interface gráfica e controle de telas/atalhos
├── banco.py        # Conexão SQLite, CRUD de produtos/vendas e ordenação de alertas
├── README.md       # Documentação do projeto
├── LICENSE         # Licença MIT (uso e distribuição livre)
└── .gitignore      # Arquivos ignorados pelo Git
```

## Como Executar

Não é necessário instalar bibliotecas externas para rodar a partir do código-fonte (todas fazem parte da biblioteca padrão do Python 3).

```bash
python app.py
```

Na primeira execução, o arquivo `gcl_dados.db` será criado automaticamente na mesma pasta.

## Como Gerar o Executável Portátil (Windows)

Para distribuir o sistema via pen drive sem exigir a instalação do Python no computador do empreendedor:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name GCL app.py
```

O executável `GCL.exe` será gerado dentro da pasta `dist/`.

## Autor

**Ramon Moreira Gomes**  
Bacharelado em Ciência da Computação — Guarapari/ES  
Projeto de Extensão III — Programa de Inovação e Empreendedorismo (2026)

## Licença

Distribuído sob a licença **MIT**. Uso, cópia e modificação livres para a comunidade.
