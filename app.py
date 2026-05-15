from flask import Flask, render_template, request, redirect, session
import mysql.connector
import bcrypt

app = Flask(__name__)
app.secret_key = "senai"

# conexão com banco
conexao = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="almoxarifado"
)


# ================= LOGIN =================

@app.route('/')
def login():
    return render_template('login.html')


@app.route('/logar', methods=['POST'])
def logar():

    usuario = request.form['usuario']
    senha = request.form['senha']

    cursor = conexao.cursor(dictionary=True)

    sql = "SELECT * FROM usuarios WHERE user=%s"
    cursor.execute(sql, (usuario,))

    user = cursor.fetchone()

    if user:

        senha_bd = user['password']

        if bcrypt.checkpw(
            senha.encode('utf-8'),
            senha_bd.encode('utf-8')
        ):
            session['usuario'] = usuario
            session['permissao'] = user['permissao']

            return redirect('/home')

    return "Login inválido"


# ================= HOME =================

@app.route('/home')
def home():

    if 'usuario' not in session:
        return redirect('/')

    cursor = conexao.cursor(dictionary=True)

    sql = "SELECT * FROM estoque"
    cursor.execute(sql)

    itens = cursor.fetchall()

    return render_template(
        'home.html',
        itens=itens
    )


# ================= CADASTRAR ITEM =================

@app.route('/cadastrar_item')
def cadastrar_item():

    if 'usuario' not in session:
        return redirect('/')

    return render_template('cadastrar_item.html')


@app.route('/salvar_item', methods=['POST'])
def salvar_item():

    if 'usuario' not in session:
        return redirect('/')

    nome = request.form['nome']
    quantidade = request.form['quantidade']
    minimo = request.form['minimo']
    descricao = request.form['descricao']
    preco = request.form['preco']
    categoria = request.form['categoria']

    cursor = conexao.cursor()

    sql = """
    INSERT INTO estoque
    (nome, quantidade, estoque_minimo, descricao, preco, categoria)
    VALUES (%s,%s,%s,%s,%s,%s)
    """

    valores = (
        nome,
        quantidade,
        minimo,
        descricao,
        preco,
        categoria
    )

    cursor.execute(sql, valores)
    conexao.commit()

    return redirect('/home')


# ================= MOVIMENTAÇÃO =================

@app.route('/movimentacao')
def movimentacao():

    if 'usuario' not in session:
        return redirect('/')

    cursor = conexao.cursor(dictionary=True)

    sql = "SELECT * FROM estoque"
    cursor.execute(sql)

    itens = cursor.fetchall()

    return render_template(
        'movimentacao.html',
        itens=itens
    )


@app.route('/movimentar', methods=['POST'])
def movimentar():

    if 'usuario' not in session:
        return redirect('/')

    item = request.form['item']
    quantidade = int(request.form['quantidade'])
    tipo = request.form['tipo']

    cursor = conexao.cursor(dictionary=True)

    sql = "SELECT * FROM estoque WHERE id=%s"
    cursor.execute(sql, (item,))

    produto = cursor.fetchone()

    estoque_atual = produto['quantidade']

    if tipo == "entrada":
        novo = estoque_atual + quantidade

    else:
        if quantidade > estoque_atual:
            return "Estoque insuficiente"

        novo = estoque_atual - quantidade

    sql_update = """
    UPDATE estoque
    SET quantidade=%s
    WHERE id=%s
    """

    cursor.execute(sql_update, (novo, item))
    conexao.commit()

    return redirect('/home')


# ================= CADASTRAR USUÁRIO =================

@app.route('/cadastrar_usuario')
def cadastrar_usuario():

    if 'usuario' not in session:
        return redirect('/')

    if session['permissao'] != 'admin':
        return "Acesso negado"

    return render_template(
        'cadastrar_usuario.html'
    )


@app.route('/salvar_usuario', methods=['POST'])
def salvar_usuario():

    if 'usuario' not in session:
        return redirect('/')

    if session['permissao'] != 'admin':
        return "Acesso negado"

    usuario = request.form['usuario']
    senha = request.form['senha']
    permissao = request.form['permissao']

    senha_hash = bcrypt.hashpw(
        senha.encode('utf-8'),
        bcrypt.gensalt()
    )

    cursor = conexao.cursor()

    sql = """
    INSERT INTO usuarios
    (user, password, permissao)
    VALUES (%s,%s,%s)
    """

    valores = (
        usuario,
        senha_hash.decode('utf-8'),
        permissao
    )

    cursor.execute(sql, valores)
    conexao.commit()

    return redirect('/')


# ================= LOGOUT =================

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ================= INICIAR =================

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )