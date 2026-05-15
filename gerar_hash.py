import bcrypt

# senha do administrador
senha = "admin123"

# gerar hash
senha_hash = bcrypt.hashpw(
    senha.encode('utf-8'),
    bcrypt.gensalt()
)

# mostrar hash
print(senha_hash.decode('utf-8'))