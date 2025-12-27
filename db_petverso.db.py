import sqlite3
import os

NOME_BANCO = "petverso.db"

def criar_tabelas():
    # 1. REMOVE O BANCO ANTIGO (Para garantir que não haja restos de versões velhas)
    if os.path.exists(NOME_BANCO):
        os.remove(NOME_BANCO)
        print("Banco de dados antigo removido. Recriando do zero...")

    conn = sqlite3.connect(NOME_BANCO)
    cursor = conn.cursor()

    print("--- Criando Tabelas ---")

    # 1. USUÁRIOS (Para o Login)
    cursor.execute('''
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT,
            email TEXT,
            telefone TEXT,
            endereco TEXT,
            cargo TEXT NOT NULL,
            usuario TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            permissoes TEXT
        )
    ''')
    print("✓ Tabela Usuarios")

    # 2. CLIENTES (Com CEP)
    cursor.execute('''
        CREATE TABLE clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_tutor TEXT NOT NULL,
            whatsapp TEXT,
            cep TEXT,
            endereco TEXT,
            nome_pet TEXT NOT NULL,
            raca TEXT,
            porte TEXT,
            comportamento TEXT,
            observacoes TEXT
        )
    ''')
    print("✓ Tabela Clientes")

    # 3. AGENDA
    cursor.execute('''
        CREATE TABLE agenda (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_pet TEXT NOT NULL,
            servico TEXT NOT NULL,
            data TEXT NOT NULL,
            hora TEXT NOT NULL,
            status TEXT DEFAULT 'Agendado',
            observacoes TEXT
        )
    ''')
    print("✓ Tabela Agenda")

    # 4. SERVIÇOS
    cursor.execute('''
        CREATE TABLE servicos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            valor REAL NOT NULL,
            duracao_minutos INTEGER DEFAULT 30
        )
    ''')
    print("✓ Tabela Serviços")

    # 5. ESTOQUE
    cursor.execute('''
        CREATE TABLE estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto TEXT NOT NULL,
            categoria TEXT,
            qtd_atual INTEGER NOT NULL,
            qtd_minima INTEGER DEFAULT 5,
            unidade TEXT
        )
    ''')
    print("✓ Tabela Estoque")

    # 6. FINANCEIRO (Movimentações Manuais)
    cursor.execute('''
        CREATE TABLE financeiro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT,      -- 'Entrada' ou 'Saida'
            categoria TEXT, -- Ex: 'Venda', 'Compra', 'Conta'
            descricao TEXT,
            valor REAL,
            data TEXT
        )
    ''')
    print("✓ Tabela Financeiro")

    # 7. DESPESAS FIXAS (Novo recurso)
    cursor.execute('''
        CREATE TABLE despesas_fixas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            valor REAL NOT NULL,
            dia_vencimento INTEGER
        )
    ''')
    print("✓ Tabela Despesas Fixas")

    # --- DADOS INICIAIS ---
    print("\n--- Inserindo Dados Padrão ---")
    
    # Criar Gerente (Login: admin / Senha: admin)
    cursor.execute("INSERT INTO usuarios (nome, cargo, usuario, senha, permissoes) VALUES (?, ?, ?, ?, ?)", 
                  ('Gerente Geral', 'gerente', 'admin', 'admin', 'all'))
    
    # Serviços Básicos
    cursor.execute("INSERT INTO servicos (nome, valor) VALUES (?, ?)", ('Banho Simples', 45.00))
    cursor.execute("INSERT INTO servicos (nome, valor) VALUES (?, ?)", ('Tosa Completa', 90.00))

    conn.commit()
    conn.close()
    print("\n>>> SUCESSO! O banco 'petverso.db' está pronto para uso. <<<")

if __name__ == '__main__':
    criar_tabelas()