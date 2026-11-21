# Gestão Comunitária Livre (GCL)

Sistema simples em Python para controle de estoque, validade e fluxo de caixa diário.

Fiz esse projeto para o Projeto de Extensão III de Ciência da Computação (Guarapari/ES), com a ideia de ajudar feirantes, autônomos e pequenos comerciantes da Praia do Morro que ainda faziam o controle de vendas e mercadorias no caderno.

## O que o sistema faz

- Cadastro, edição e exclusão de produtos (com preço de custo, venda, estoque mínimo e validade)
- Registro de vendas com baixa automática no estoque
- Fechamento de caixa diário com opção de salvar o resumo em `.txt`
- Alerta visual na tabela: vermelho para estoque baixo/vencido e amarelo para itens a até 15 dias do vencimento
- Perfis de categorias adaptáveis (Feirante/Hortifrúti, Mercearia Familiar, Lanches Caseiros, Artesanato e Comércio Geral)
- Funciona totalmente offline usando SQLite

Atalhos na tela principal:
- F1: Registrar venda
- F2: Cadastrar produto
- F3: Buscar produto
- F4: Fechamento de caixa
- F5: Ver alertas

## Tecnologias

- Python 3
- Tkinter (interface gráfica)
- SQLite3 (banco local)
- PyInstaller (para gerar o `.exe`)

## Como rodar

Não precisa instalar nenhuma biblioteca externa, só ter o Python 3 instalado:

```bash
python app.py