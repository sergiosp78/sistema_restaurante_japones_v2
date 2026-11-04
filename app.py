import streamlit as st
import sqlite3

# Configuração da página
st.set_page_config(page_title="Sistema Restaurante", layout="wide")


# Função para conectar ao banco
def conectar():
    return sqlite3.connect('restaurante.db')


# --- MENU LATERAL ---
st.sidebar.title("Menu")
opcao = st.sidebar.radio("Escolha uma opção:", ["Cadastrar Prato", "Registrar Pedido"])

# --- TELA 1: CADASTRAR PRATO ---
if opcao == "Cadastrar Prato":
    st.title("Cadastro de Prato")

    # Formulário para não recarregar a tela toda hora
    with st.form("form_cadastro_prato"):
        nome = st.text_input("Nome do Prato")
        preco = st.number_input("Preço (R$)", min_value=0.0, format="%.2f")

        # Busca as categorias no banco para preencher o selectbox
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome FROM categoria")
        categorias = cursor.fetchall()
        conexao.close()

        # Cria a lista de opções para o dropdown
        opcoes_categorias = {cat[1]: cat[0] for cat in categorias}
        categoria_nome = st.selectbox("Categoria", list(opcoes_categorias.keys()))

        # Botão de salvar
        submit = st.form_submit_button("Salvar")

        if submit:
            if nome == "":
                st.error("O nome do prato é obrigatório.")
            else:
                categoria_id = opcoes_categorias[categoria_nome]

                # Insere no banco de dados
                conexao = conectar()
                cursor = conexao.cursor()
                cursor.execute("INSERT INTO prato (nome, preco, categoria_id) VALUES (?, ?, ?)",
                               (nome, preco, categoria_id))
                conexao.commit()
                conexao.close()

                st.success(f"Prato '{nome}' cadastrado com sucesso!")

# --- TELA 2: REGISTRAR PEDIDO (Em breve) ---
# --- TELA 2: REGISTRAR PEDIDO ---
elif opcao == "Registrar Pedido":
    st.title("Registrar Pedido")

    # Inicializa a lista de itens na memória da sessão, se não existir
    if 'itens_pedido' not in st.session_state:
        st.session_state.itens_pedido = []

    # Formulário para adicionar itens ao carrinho
    with st.form("form_adicionar_item"):
        mesa = st.number_input("Mesa", min_value=1, step=1)

        # Busca os pratos do banco
        conexao = conectar()
        cursor = conexao.cursor()
        cursor.execute("SELECT id, nome, preco FROM prato")
        pratos = cursor.fetchall()
        conexao.close()

        opcoes_pratos = {p[1]: (p[0], p[2]) for p in pratos}  # nome: (id, preco)
        prato_selecionado = st.selectbox("Prato", list(opcoes_pratos.keys()))
        quantidade = st.number_input("Quantidade", min_value=1, step=1)

        adicionar = st.form_submit_button("Adicionar")

        if adicionar:
            id_prato, preco_unitario = opcoes_pratos[prato_selecionado]
            novo_item = {
                "pedido_id": None,  # Será preenchido ao confirmar
                "mesa": mesa,
                "prato_id": id_prato,
                "nome": prato_selecionado,
                "quantidade": quantidade,
                "preco_unitario": preco_unitario
            }
            st.session_state.itens_pedido.append(novo_item)
            st.success(f"{quantidade}x {prato_selecionado} adicionado!")

    # Exibe a lista de itens e o Total
    st.subheader("Itens do Pedido")
    total = 0.0
    if st.session_state.itens_pedido:
        for item in st.session_state.itens_pedido:
            subtotal = item['quantidade'] * item['preco_unitario']
            total += subtotal
            st.write(f"{item['quantidade']}x {item['nome']} - R$ {subtotal:.2f}")
    else:
        st.write("Nenhum item adicionado.")

    st.markdown(f"### Total: R$ {total:.2f}")

    # Botão para confirmar o pedido e salvar no banco
    if st.button("Confirmar Pedido"):
        if not st.session_state.itens_pedido:
            st.error("Adicione pelo menos um item ao pedido.")
        else:
            from datetime import datetime

            data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            mesa = st.session_state.itens_pedido[0]['mesa']  # Pega a mesa do primeiro item

            conexao = conectar()
            cursor = conexao.cursor()

            # 1. Insere o Pedido
            cursor.execute("INSERT INTO pedido (mesa, data_hora, status) VALUES (?, ?, ?)",
                           (mesa, data_atual, "Em preparo"))
            id_pedido = cursor.lastrowid

            # 2. Insere todos os Itens do Pedido
            for item in st.session_state.itens_pedido:
                cursor.execute(
                    "INSERT INTO item_pedido (pedido_id, prato_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
                    (id_pedido, item['prato_id'], item['quantidade'], item['preco_unitario']))

            conexao.commit()
            conexao.close()

            st.success(f"Pedido da Mesa {mesa} confirmado com sucesso! Total: R$ {total:.2f}")
            st.session_state.itens_pedido = []  # Limpa o carrinho

