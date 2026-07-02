from flask import Flask, render_template, request, redirect, jsonify, session, flash

app = Flask(__name__)
app.secret_key = 'chave_secreta_para_apresentacao_tcc'

# --- BANCO DE DADOS DESATIVADO TEMPORARIAMENTE PARA TESTES DE LAYOUT ---
# Dados fictícios para simular o estoque do Almoxarifado SENAI
ESTOQUE_MOCK = [
    {"id_produto": 1, "nome": "Chave Phillips 1/4", "area": "Mecânica", "quantidade": 15, "descricao": "Ferramenta de aperto com ponta imantada.", "preco": "25.90", "link_midia": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?q=80&w=200"},
    {"id_produto": 2, "nome": "Multímetro Digital", "area": "Elétrica", "quantidade": 7, "descricao": "Medidor de tensão AC/DC e corrente.", "preco": "89.90", "link_midia": ""},
    {"id_produto": 3, "nome": "Parafuso Sextavado M8", "area": "Geral", "quantidade": 120, "descricao": "Fixador zincado para estruturas metálicas.", "preco": "0.50", "link_midia": ""},
    {"id_produto": 4, "nome": "Alicate Universal 8", "area": "Mecânica", "quantidade": 10, "descricao": "Alicate isolado 1000V de alta resistência.", "preco": "45.00", "link_midia": ""}
]

# ROTA 1: TELA DE LOGIN
@app.route('/')
def login():
    return render_template('login.html')

# ROTA 2: PROCESSAR O LOGIN (Ignora o banco e deixa passar direto)
@app.route('/logar', methods=['POST'])
def logar():
    usuario = request.form.get('usuario')
    senha = request.form.get('senha')
    
    # Simulação de login bem-sucedido
    session['usuario'] = "admin"
    session['permissao'] = "admin"
    return redirect('/home')

# ROTA 3: TELA HOME (Mostra a tabela de estoque com busca simulada)
@app.route('/home')
def home():
    search_query = request.args.get('search', '').lower()
    
    # Se o usuário pesquisar algo, filtramos a nossa lista simulada
    if search_query:
        itens_filtrados = [
            item for item in ESTOQUE_MOCK 
            if search_query in item['nome'].lower() or search_query in item['area'].lower()
        ]
    else:
        itens_filtrados = ESTOQUE_MOCK

    return render_template('home.html', itens=itens_filtrados, search_query=request.args.get('search', ''))

# ROTA 4: TELA DE CADASTRAR ITEM
@app.route('/cadastrar_item')
def cadastrar_item():
    return render_template('cadastrar_item.html')

# ACTION DO CADASTRO DE ITEM (Simula o salvamento)
@app.route('/salvar_item', methods=['POST'])
def salvar_item():
    flash('Item cadastrado com sucesso! (Modo de Simulação)', 'success')
    return redirect('/home')

# ROTA 5: TELA DE MOVIMENTAÇÕES (Preenche o select com os itens simulados)
@app.route('/movimentacao')
def movimentacao():
    return render_template('movimentacao.html', itens=ESTOQUE_MOCK)

# ACTION DA MOVIMENTAÇÃO (Simula a entrada/saída)
@app.route('/movimentar', methods=['POST'])
def movimentar():
    flash('Movimentação registrada com sucesso! (Modo de Simulação)', 'success')
    return redirect('/movimentacao')

# ROTA 6: TELA DE EDITAR ITENS
@app.route('/editar')
def editar():
    return render_template('editar.html')

# API DE BUSCA DO AUTOCOMPLETE (A mágica da caixinha de busca inteligente)
@app.route('/api/buscar_item_edicao')
def buscar_item_edicao():
    termo = request.args.get('nome', '').lower()
    
    # Procura na nossa lista simulada itens que começam ou contém o texto digitado
    resultados = []
    if len(termo) >= 2:
        for item in ESTOQUE_MOCK:
            if termo in item['nome'].lower():
                resultados.append({
                    "id": item['id_produto'],
                    "nome": item['nome'],
                    "categoria": item['area'],
                    "preco": item['preco'],
                    "descricao": item['descricao']
                })
                
    return jsonify(resultados)

# ACTION DE ATUALIZAR ITEM EDIÇÃO (Simula o update)
@app.route('/atualizar_item', methods=['POST'])
def atualizar_item():
    flash('Alterações do item salvas com sucesso! (Modo de Simulação)', 'success')
    return redirect('/home')

# ROTA 7: TELA DE CADASTRAR USUÁRIO
@app.route('/cadastrar_usuario')
def cadastrar_usuario():
    return render_template('cadastrar_usuario.html')

# ACTION DE CADASTRAR USUÁRIO (Simula a criação)
@app.route('/salvar_usuario', methods=['POST'])
def salvar_usuario():
    flash('Novo usuário cadastrado com sucesso! (Modo de Simulação)', 'success')
    return redirect('/cadastrar_usuario')

# --- INICIALIZAÇÃO DO SERVIDOR ---
if __name__ == '__main__':
    # Rodando em modo de debug para atualizar automático ao salvar alterações
    app.run(debug=True, port=5000)