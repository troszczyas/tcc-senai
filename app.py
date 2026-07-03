import os
import re
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ================= CONEXÃO COM O BANCO DE DADOS =================
def obter_conexao():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Deixe vazio se você não usa senha no Workbench
        database="almoxarifado_db"
    )

# ================= FUNÇÕES AUXILIARES INTEGRAIS =================

def limpar_texto(texto):
    if not texto:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    texto_limpo = texto_sem_acento.strip().lower()
    return texto_limpo.capitalize()

def gerar_proximo_id(area):
    prefixos = {'Geral': '0', 'Mecânica': '1', 'Elétrica': '2'}
    prefixo = prefixos.get(area, '0')
    
    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT id_produto FROM estoque 
        WHERE CAST(id_produto AS CHAR) LIKE %s 
        ORDER BY id_produto ASC
    """, (prefixo + '%',))
    
    ids_existentes = [int(row['id_produto']) for row in cursor.fetchall()]
    cursor.close()
    conexao.close()
    
    inicio_sequencia = int(prefixo + "0001")
    proximo_numero = inicio_sequencia
    while proximo_numero in ids_existentes:
        proximo_numero += 1
        
    return str(proximo_numero).zfill(5)

# ================= CRIAR USUÁRIO PADRÃO AUTOMATICAMENTE =================
@app.before_request
def criar_usuario_padrao():
    if request.endpoint == 'static':
        return
        
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as total FROM usuarios")
        result = cursor.fetchone()
        
        if result and result['total'] == 0:
            cursor.execute("""
                INSERT INTO usuarios (login, senha, status, role) 
                VALUES (%s, %s, %s, %s)
            """, ("admin", "123", "ativo", "admin"))
            conexao.commit()
            print("-> Usuário padrão criado! Login: admin | Senha: 123")
        cursor.close()
        conexao.close()
    except Exception as e:
        print(f"Aviso na inicialização do banco: {e}")


# ================= ROTAS DO SISTEMA =================

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/logar', methods=['POST'])
def logar():
    usuario = request.form['usuario']
    senha = request.form['senha']

    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE login = %s", (usuario,))
    user = cursor.fetchone()
    cursor.close()
    conexao.close()

    if user:
        senha_bd = user['senha']
        if senha == senha_bd:
            session['usuario'] = usuario
            session['permissao'] = user['role']
            return redirect('/home')

    flash("Login inválido ou senha incorreta!", "error")
    return redirect('/')


@app.route('/home')
def home():
    if 'usuario' not in session:
        return redirect('/')

    pesquisa = request.args.get('search', '').strip()
    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)

    if pesquisa:
        sql = """
            SELECT id_produto, nome, area, quantidade, descricao, link_midia 
            FROM estoque WHERE nome LIKE %s OR area LIKE %s 
            ORDER BY id_produto ASC
        """
        cursor.execute(sql, (f"%{pesquisa}%", f"%{pesquisa}%"))
    else:
        sql = "SELECT id_produto, nome, area, quantidade, descricao, link_midia FROM estoque ORDER BY id_produto ASC"
        cursor.execute(sql)

    itens = cursor.fetchall()
    cursor.close()
    conexao.close()
    
    return render_template('home.html', itens=itens, search_query=pesquisa)

@app.route('/cadastrar_item')
def cadastrar_item():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('cadastrar_item.html')


@app.route('/salvar_item', methods=['POST'])
def salvar_item():
    if 'usuario' not in session:
        return redirect('/')

    nome = limpar_texto(request.form['nome'])
    area = request.form['categoria']  # 'categoria' vinda do formulário HTML
    quantidade = int(request.form['quantidade'])
    descricao = limpar_texto(request.form.get('descricao', ''))
    link_midia = request.form.get('link_midia', '')

    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM estoque WHERE nome = %s AND area = %s", (nome, area))
    produto_existente = cursor.fetchone()

    if produto_existente:
        nova_qtd = produto_existente['quantidade'] + quantidade
        cursor.execute("UPDATE estoque SET quantidade = %s WHERE id_produto = %s", (nova_qtd, produto_existente['id_produto']))
    else:
        id_customizado = gerar_proximo_id(area)
        sql = """
            INSERT INTO estoque (id_produto, nome, area, quantidade, descricao, link_midia)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (id_customizado, nome, area, quantidade, descricao, link_midia))

    conexao.commit()
    cursor.close()
    conexao.close()
    return redirect('/home')


@app.route('/movimentacao')
def movimentacao():
    if 'usuario' not in session:
        return redirect('/')

    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM estoque ORDER BY id_produto ASC")
    itens = cursor.fetchall()
    cursor.close()
    conexao.close()

    return render_template('movimentacao.html', itens=itens)


@app.route('/movimentar', methods=['POST'])
def movimentar():
    if 'usuario' not in session:
        return redirect('/')

    item_id = request.form['item']
    quantidade = int(request.form['quantidade'])
    tipo = request.form['tipo']

    conexao = obter_conexao()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM estoque WHERE id_produto = %s", (item_id,))
    produto = cursor.fetchone()

    if not produto:
        cursor.close()
        conexao.close()
        flash("Produto não localizado!", "error")
        return redirect('/movimentacao')

    estoque_atual = produto['quantidade']

    if tipo == "entrada":
        novo_total = estoque_atual + quantidade
    else:
        if quantidade > estoque_atual:
            cursor.close()
            conexao.close()
            flash("Quantidade solicitada é superior ao estoque disponível!", "error")
            return redirect('/movimentacao')
        novo_total = estoque_atual - quantidade

    cursor.execute("UPDATE estoque SET quantidade = %s WHERE id_produto = %s", (novo_total, item_id))
    conexao.commit()
    cursor.close()
    cursor.close()
    conexao.close()

    return redirect('/home')


@app.route('/cadastrar_usuario')
def cadastrar_usuario():
    if 'usuario' not in session:
        return redirect('/')

    if session.get('permissao') != 'admin':
        return "Acesso negado - Permissão insuficiente."

    return render_template('cadastrar_usuario.html')


@app.route('/salvar_usuario', methods=['POST'])
def salvar_usuario():
    if 'usuario' not in session:
        return redirect('/')

    if session.get('permissao') != 'admin':
        return "Acesso negado - Permissão insuficiente."

    usuario = request.form['usuario']
    senha = request.form['senha']
    permissao = request.form['permissao']

    conexao = obter_conexao()
    cursor = conexao.cursor()
    sql = "INSERT INTO usuarios (login, senha, status, role) VALUES (%s, %s, %s, %s)"
    
    try:
        cursor.execute(sql, (usuario, senha, 'ativo', permissao))
        conexao.commit()
    except Exception as e:
        print(f"Erro ao salvar usuário: {e}")
        flash("Este nome de usuário já existe!", "error")

    cursor.close()
    conexao.close()
    return redirect('/')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    # Mantido sem o 0.0.0.0 para evitar os bloqueios de rede do SENAI
    app.run(debug=True)