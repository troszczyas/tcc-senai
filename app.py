import os
import re
import random
import unicodedata
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ================= ESTOQUE E USUÁRIOS FICTÍCIOS (MOCK) =================
ESTOQUE_MOCK = [
    {"id_produto": "00001", "nome": "Alicate", "area": "Geral", "quantidade": 10, "descricao": "Ferramenta manual usada para segurar, cortar, dobrar e apertar materiais.", "preco": 35.90, "link_midia": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS66xbAeYwltYSUHqGq4qKWALJX3lkY1ojqbRLkKs82Yw&s=10"},
    {"id_produto": "10001", "nome": "Pregos", "area": "Mecânica", "quantidade": 200, "descricao": "Peças metálicas usadas para fixar materiais, principalmente madeira.", "preco": 0.15, "link_midia": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSuleVPCTMLQEhf4lkkzlW9AEMXDfDEqw4RAwsZjdZ-jw&s=10"},
    {"id_produto": "10002", "nome": "Parafusos", "area": "Mecânica", "quantidade": 200, "descricao": "Peças metálicas usadas para unir e fixar materiais.", "preco": 0.25, "link_midia": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlm_v8Khvn-wORVgWlbuepAl0Urz62I7pJCK2UQ3-nnQ&s=10"},
    {"id_produto": "20001", "nome": "Serrote", "area": "Manual", "quantidade": 2, "descricao": "Ferramenta manual usada para cortar madeira.", "preco": 45.00, "link_midia": "https://www.incorzul.com.br/serrote-profissional-22-pol-100112-paraboni?srsltid=AfmBOooLCrh57Y6HbgqBUnunnwkgjC1MZx84gRXzzrK4Qq5dPWd6_mLa"},
    {"id_produto": "00002", "nome": "Chave philips", "area": "Geral", "quantidade": 7, "descricao": "Ferramenta manual usada para apertar e soltar parafusos de cabeça cruzada.", "preco": 18.50, "link_midia": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRMOMqwTSGR4S2soHpfyq7s5czjFTB6h6zBHHycqd2ZRg&s=10"}
]

USUARIOS_MOCK = {
    "admin": {"senha": "Roger", "role": "admin"},
    "ale": {"senha": "456", "role": "user"},
    "roger": {"senha": "000", "role": "user"},
    "duda": {"senha": "789", "role": "user"}
}

# ================= CONEXÃO COM O BANCO DE DADOS =================
def obter_conexao():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  
        database="almoxarifado_db"
    )

# ================= FUNÇÕES AUXILIARES =================

def limpar_texto(texto):
    if not texto:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', texto)
    texto_sem_acento = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    texto_limpo = texto_sem_acento.strip().lower()
    return texto_limpo.capitalize()

def gerar_proximo_id(area):
    prefixos = {'Geral': '0', 'Mecânica': '1', 'Elétrica': '2', 'Manual': '2'}
    prefixo = prefixos.get(area, '0')
    
    try:
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
    except Exception:
        ids_existentes = [int(item['id_produto']) for item in ESTOQUE_MOCK]
    
    inicio_sequencia = int(prefixo + "0001")
    proximo_numero = inicio_sequencia
    while proximo_numero in ids_existentes:
        proximo_numero += 1
        
    return str(proximo_numero).zfill(5)


# ================= ROTAS DO SISTEMA =================

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/logar', methods=['POST'])
def logar():
    usuario = request.form['usuario']
    senha = request.form['senha']

    try:
        conexao = obter_conexao()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE login = %s", (usuario,))
        user = cursor.fetchone()
        cursor.close()
        conexao.close()

        if user:
            if senha == user['senha']:
                session['usuario'] = usuario
                session['permissao'] = user['role']
                return redirect('/home')
    except Exception:
        user_lower = usuario.lower()
        if user_lower in USUARIOS_MOCK and senha == USUARIOS_MOCK[user_lower]['senha']:
            session['usuario'] = usuario
            session['permissao'] = USUARIOS_MOCK[user_lower]['role']
            return redirect('/home')

    flash("Login inválido ou senha incorreta!", "error")
    return redirect('/')


@app.route('/home')
def home():
    if 'usuario' not in session:
        return redirect('/')

    pesquisa = request.args.get('search', '').strip()
    
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor(dictionary=True)

        if pesquisa:
            sql = """
                SELECT id_produto, nome, area, quantidade, preco, descricao, link_midia 
                FROM estoque WHERE nome LIKE %s OR area LIKE %s 
                ORDER BY id_produto ASC
            """
            try:
                cursor.execute(sql, (f"%{pesquisa}%", f"%{pesquisa}%"))
            except Exception:
                sql = "SELECT id_produto, nome, area, quantidade, descricao, link_midia FROM estoque WHERE nome LIKE %s OR area LIKE %s ORDER BY id_produto ASC"
                cursor.execute(sql, (f"%{pesquisa}%", f"%{pesquisa}%"))
        else:
            try:
                cursor.execute("SELECT id_produto, nome, area, quantidade, preco, descricao, link_midia FROM estoque ORDER BY id_produto ASC")
            except Exception:
                cursor.execute("SELECT id_produto, nome, area, quantidade, descricao, link_midia FROM estoque ORDER BY id_produto ASC")

        itens = cursor.fetchall()
        
        for item in itens:
            if 'preco' not in item or item['preco'] is None:
                mock_correspondente = next((m for m in ESTOQUE_MOCK if m["id_produto"] == item["id_produto"]), None)
                item['preco'] = mock_correspondente['preco'] if mock_correspondente else 10.00

        cursor.close()
        conexao.close()
    except Exception:
        if pesquisa:
            itens = [item for item in ESTOQUE_MOCK if pesquisa.lower() in item['nome'].lower() or pesquisa.lower() in item['area'].lower()]
        else:
            itens = ESTOQUE_MOCK
    
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
    area = request.form['categoria']  
    quantidade = int(request.form['quantidade'])
    descricao = limpar_texto(request.form.get('descricao', ''))
    link_midia = request.form.get('link_midia', '')

    try:
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
    except Exception:
        flash("Item salvo no modo simulação!", "success")

    return redirect('/home')


@app.route('/movimentacao')
def movimentacao():
    if 'usuario' not in session:
        return redirect('/')

    try:
        conexao = obter_conexao()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM estoque ORDER BY id_produto ASC")
        itens = cursor.fetchall()
        
        for item in itens:
            if 'preco' not in item or item['preco'] is None:
                item['preco'] = 10.00
                
        cursor.close()
        conexao.close()
    except Exception:
        itens = ESTOQUE_MOCK

    return render_template('movimentacao.html', itens=itens)


@app.route('/movimentar', methods=['POST'])
def movimentar():
    if 'usuario' not in session:
        return redirect('/')

    item_id = request.form['item']
    quantidade = int(request.form['quantidade'])
    tipo = request.form['tipo']

    try:
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
            # CORRIGIDO: quantidade em vez de quantity
            if quantidade > estoque_atual:
                cursor.close()
                conexao.close()
                flash("Quantidade solicitada é superior ao estoque disponível!", "error")
                return redirect('/movimentacao')
            novo_total = estoque_atual - quantidade

        cursor.execute("UPDATE estoque SET quantidade = %s WHERE id_produto = %s", (novo_total, item_id))
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception:
        flash("Movimentação registrada com sucesso! (Modo Simulação)", "success")

    return redirect('/home')


@app.route('/editar')
def editar():
    if 'usuario' not in session:
        return redirect('/')
    return render_template('editar.html')


@app.route('/api/buscar_item_edicao')
def buscar_item_edicao():
    termo = request.args.get('nome', '').lower()
    resultados = []
    
    if len(termo) >= 2:
        try:
            conexao = obter_conexao()
            cursor = conexao.cursor(dictionary=True)
            sql = "SELECT id_produto AS id, nome, area AS categoria, descricao FROM estoque WHERE nome LIKE %s LIMIT 5"
            cursor.execute(sql, (f"%{termo}%",))
            resultados = cursor.fetchall()
            
            for r in resultados:
                r['preco'] = 'Uso Interno'
                
            cursor.close()
            conexao.close()
        except Exception:
            for item in ESTOQUE_MOCK:
                if termo in item['nome'].lower():
                    resultados.append({
                        "id": item['id_produto'],
                        "nome": item['nome'],
                        "categoria": item['area'],
                        "preco": "Uso Interno",
                        "descricao": item['descricao']
                    })
                
    return jsonify(resultados)


@app.route('/atualizar_item', methods=['POST'])
def atualizar_item():
    if 'usuario' not in session:
        return redirect('/')

    item_id = request.form['item_id']
    categoria = request.form['categoria']
    descricao = limpar_texto(request.form.get('descricao', ''))

    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = "UPDATE estoque SET area = %s, descricao = %s WHERE id_produto = %s"
        cursor.execute(sql, (categoria, descricao, item_id))
        conexao.commit()
        cursor.close()
        conexao.close()
    except Exception:
        flash("Alterações salvas no modo de simulação!", "success")

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

    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        sql = "INSERT INTO usuarios (login, senha, status, role) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (usuario, senha, 'ativo', permissao))
        conexao.commit()
        cursor.close()
        conexao.close()
        flash("Usuário cadastrado com sucesso!", "success")
    except Exception as e:
        print(f"Erro ao salvar usuário: {e}")
        flash("Usuário cadastrado com sucesso! (Modo Simulação)", "success")

    return redirect('/home')


# ================= SEÇÃO DE PERFIL COM VALIDAÇÃO DE CÓDIGO =================

@app.route('/perfil')
def perfil():
    if 'usuario' not in session:
        return redirect('/')
    
    try:
        conexao = obter_conexao()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute("SELECT * FROM usuarios WHERE login = %s", (session['usuario'],))
        dados_usuario = cursor.fetchone()
        cursor.close()
        conexao.close()
    except Exception:
        dados_usuario = {
            "login": session['usuario'],
            "nome_completo": "Usuário de Teste SENAI",
            "email": "admin@senai.br",
            "data_nascimento": "2000-01-01",
            "area_atuacao": "Geral",
            "estado": "SP",
            "cidade": "São Paulo"
        }
    
    return render_template('atualizar_perfil.html', user=dados_usuario)


@app.route('/enviar_codigo_perfil', methods=['POST'])
def enviar_codigo_perfil():
    if 'usuario' not in session:
        return jsonify({"status": "error", "message": "Sessão expirada."})
    
    codigo = str(random.randint(100000, 999999))
    session['codigo_verificacao'] = codigo
    
    return jsonify({
        "status": "success", 
        "message": f"Código de segurança gerado! Use o número: {codigo}"
    })


@app.route('/atualizar_perfil', methods=['POST'])
def atualizar_perfil():
    if 'usuario' not in session:
        return redirect('/')

    nova_senha = request.form.get('senha')
    codigo_inserido = request.form.get('codigo_verificacao')
    nova_area = request.form.get('area')
    novo_estado = request.form.get('estado')
    nova_cidade = request.form.get('cidade')

    if nova_senha:
        codigo_salvo = session.get('codigo_verificacao')
        if not codigo_inserido or codigo_inserido != codigo_salvo:
            flash("Código de verificação incorreto! A senha não foi alterada.", "error")
            return redirect('/perfil')
        
        session.pop('codigo_verificacao', None)

    try:
        conexao = obter_conexao()
        cursor = conexao.cursor()
        
        if nova_senha:
            sql = "UPDATE usuarios SET senha = %s, area_atuacao = %s, estado = %s, city = %s WHERE login = %s"
            cursor.execute(sql, (nova_senha, nova_area, novo_estado, nova_cidade, session['usuario']))
        else:
            sql = "UPDATE usuarios SET area_atuacao = %s, estado = %s, city = %s WHERE login = %s"
            cursor.execute(sql, (nova_area, novo_estado, nova_cidade, session['usuario']))
            
        conexao.commit()
        cursor.close()
        conexao.close()
        flash("Perfil atualizado com sucesso!", "success")
    except Exception:
        flash("Perfil atualizado com sucesso! (Modo Simulação)", "success")

    return redirect('/perfil')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True, port=5000)