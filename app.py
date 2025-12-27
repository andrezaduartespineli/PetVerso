from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from datetime import date, datetime, timedelta 


app = Flask(__name__)
app.secret_key = 'segredo_petverso' # Necessário para usar login/sessão
DB_NAME = "petverso.db"

# --- FUNÇÕES AUXILIARES ---
def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row # Permite chamar colunas pelo nome
    return conn

#--- 1. FUNÇÃO DE CONTROLE DE ACESSO (O CÉREBRO DAS PERMISSÕES) ---
def tem_permissao(area):
    # Se não tá logado, bloqueia
    if 'user_id' not in session: return False
    
    # Se é Gerente, LIBERA TUDO
    if session.get('cargo') == 'gerente': return True
    
    # Se é Funcionário, verifica a lista
    permissoes_usuario = session.get('permissoes', '')
    if not permissoes_usuario: return False
    
    # Verifica se a área está na lista (ex: "agenda,clientes")
    lista = permissoes_usuario.split(',')
    return area in lista

# Importante: Disponibilizar essa função para usar no HTML (Sidebar)
app.jinja_env.globals.update(tem_permissao=tem_permissao)

# --- ROTAS DE LOGIN ---

@app.route('/')
def index():
    return redirect('/login')

# --- 2. ROTA LOGIN (CORRIGIDA) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    erro = None
    if request.method == 'POST':
        usuario_form = request.form['usuario']
        senha_form = request.form['senha']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE usuario = ?', (usuario_form,)).fetchone()
        conn.close()

        if user and user['senha'] == senha_form:
            session.clear() # Limpa sessões velhas para evitar conflito
            
            session['user_id'] = user['id']
            session['nome'] = user['nome']
            session['cargo'] = user['cargo']
            # Carrega as permissões do banco para a sessão (ex: "agenda,estoque")
            session['permissoes'] = user['permissoes'] or '' 
            
            return redirect('/dashboard')
        else:
            erro = "Usuário ou senha incorretos!"

    return render_template('login.html', erro=erro)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

# --- ROTAS DO SISTEMA (Protegidas) ---

@app.route('/dashboard')
def dashboard():
    if 'usuario_logado' not in session: return redirect('/login')
    
    conn = get_db_connection()
    
    # Data de Hoje (para filtrar o que acontece hoje)
    hoje = date.today().strftime('%Y-%m-%d')

    # 1. TOTAL AGENDAMENTOS (Hoje)
    agendamentos_hoje = conn.execute("SELECT COUNT(*) FROM agenda WHERE data = ?", (hoje,)).fetchone()[0]

    # 2. FATURAMENTO (Hoje) - Soma apenas 'Entrada'
    resultado_fatura = conn.execute("SELECT SUM(valor) FROM financeiro WHERE tipo = 'Entrada' AND data = ?", (hoje,)).fetchone()[0]
    faturamento_hoje = resultado_fatura if resultado_fatura else 0.0 # Se for None, vira 0.0

    # 3. ESTOQUE CRÍTICO (Conta itens abaixo do mínimo)
    estoque_critico = conn.execute("SELECT COUNT(*) FROM estoque WHERE qtd_atual < qtd_minima").fetchone()[0]

    # 4. LISTA DOS PRÓXIMOS (Traz os agendamentos de hoje ordenados por hora)
    proximos_agendamentos = conn.execute("SELECT * FROM agenda WHERE data = ? ORDER BY hora ASC", (hoje,)).fetchall()

    conn.close()

    # Envia tudo para o HTML
    return render_template('dashboard.html', 
                           total_agendamentos=agendamentos_hoje,
                           faturamento=faturamento_hoje,
                           estoque_critico=estoque_critico,
                           proximos=proximos_agendamentos)

# ... (imports e configurações iniciais iguais)

# ROTA SERVIÇOS (NOVA)
@app.route('/servicos', methods=['GET', 'POST'])
def servicos():
    if not tem_permissao('servicos'): return redirect('/dashboard')
    
    conn = get_db_connection()

    if request.method == 'POST':
        # Adicionar novo serviço comum
        nome = request.form['nome']
        valor = request.form['valor']
        duracao = request.form['duracao']
        
        conn.execute("INSERT INTO servicos (nome, valor, duracao_minutos) VALUES (?, ?, ?)", 
                     (nome, valor, duracao))
        conn.commit()
        return redirect('/servicos')

    # Busca serviços normais
    lista_servicos = conn.execute("SELECT * FROM servicos ORDER BY nome").fetchall()
    
    # Busca preço do Taxi
    dado_taxi = conn.execute("SELECT valor FROM configuracoes WHERE chave='preco_taxi'").fetchone()
    preco_taxi = float(dado_taxi[0]) if dado_taxi else 20.00
    
    conn.close()

    return render_template('servicos.html', servicos=lista_servicos, preco_taxi=preco_taxi)

# ROTA NOVA: SÓ PARA ATUALIZAR O PREÇO DO TAXI
@app.route('/atualizar_taxi', methods=['POST'])
def atualizar_taxi():
    if not tem_permissao('servicos'): return redirect('/dashboard')
    
    novo_valor = request.form['valor_taxi']
    
    conn = get_db_connection()
    conn.execute("UPDATE configuracoes SET valor = ? WHERE chave = 'preco_taxi'", (novo_valor,))
    conn.commit()
    conn.close()
    
    return redirect('/servicos')

# ROTA AGENDA ATUALIZADA (Para carregar os serviços no dropdown)
# ROTA AGENDA ATUALIZADA (Agora busca Pets também)
# Não esqueça de garantir que 'calendar' e 'timedelta' estão importados lá no topo
import calendar
from datetime import timedelta, datetime, date

# --- ROTA AGENDA (SALVA COM ID) ---
@app.route('/agenda', methods=['GET', 'POST'])
def agenda():
    if not tem_permissao('agenda'): return redirect('/dashboard')
    
    conn = get_db_connection()

    # --- 1. CONFIGURAÇÃO DE DATAS E NAVEGAÇÃO (RESTAURADO) ---
    modo = request.args.get('modo', 'diario')
    data_str = request.args.get('data', date.today().strftime('%Y-%m-%d'))
    
    try:
        data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    except ValueError:
        data_obj = date.today()
        data_str = data_obj.strftime('%Y-%m-%d')

    if modo == 'mensal':
        import calendar
        # Calcula primeiro e último dia do mês para navegação
        dias_no_mes = calendar.monthrange(data_obj.year, data_obj.month)[1]
        data_proxima = (data_obj.replace(day=dias_no_mes) + timedelta(days=1)).strftime('%Y-%m-%d')
        data_anterior = (data_obj.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Título do Mês
        meses_nomes = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 
                       7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
        texto_titulo = f"{meses_nomes[data_obj.month]} de {data_obj.year}"
        
        # Filtro SQL para o mês inteiro
        query_sql = "strftime('%Y-%m', a.data) = ?"
        param_sql = data_obj.strftime('%Y-%m')
        calendario_matriz = calendar.monthcalendar(data_obj.year, data_obj.month)
        
    else:
        # Navegação dia a dia
        data_proxima = (data_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        data_anterior = (data_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Título do Dia
        texto_titulo = f"{data_obj.day}/{data_obj.month}"
        if data_str == date.today().strftime('%Y-%m-%d'):
            texto_titulo = f"Hoje, {texto_titulo}"
            
        # Filtro SQL para o dia específico
        query_sql = "a.data = ?"
        param_sql = data_str
        calendario_matriz = []

    # --- 2. SALVAR OU EDITAR (COM VÍNCULO DE ID) ---
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        # Pega o ID do Cliente (Oculto)
        cliente_id = request.form.get('cliente_id')
        if not cliente_id: cliente_id = None # Garante que seja None se vazio
        
        # Pega o Nome (Visual)
        nome_pet_input = request.form.get('nome_pet_input')
        nome_pet = nome_pet_input.split(' (')[0] if nome_pet_input else "Desconhecido"
        
        # Tenta descobrir o Tutor
        nome_tutor = ""
        if cliente_id:
            # Se tem ID, busca o tutor oficial no banco
            c = conn.execute("SELECT nome_tutor FROM clientes WHERE id=?", (cliente_id,)).fetchone()
            if c: nome_tutor = c[0]
        elif '(' in nome_pet_input and ')' in nome_pet_input:
            # Se não tem ID, tenta pegar do texto digitado "Pet (Tutor)"
            try:
                nome_tutor = nome_pet_input.split(' (')[1].replace(')', '')
            except:
                nome_tutor = ""

        servico = request.form.get('servico')
        data = request.form.get('data')
        hora = request.form.get('hora')
        taxi = 'Sim' if request.form.get('taxi') else 'Não'
        obs = request.form.get('observacoes')

        if acao == 'editar':
            id_agend = request.form.get('id')
            conn.execute('''
                UPDATE agenda 
                SET cliente_id=?, nome_pet=?, nome_tutor=?, servico=?, data=?, hora=?, taxi=?, observacoes=?
                WHERE id=?
            ''', (cliente_id, nome_pet, nome_tutor, servico, data, hora, taxi, obs, id_agend))
        else:
            conn.execute('''
                INSERT INTO agenda (cliente_id, nome_pet, nome_tutor, servico, data, hora, taxi, observacoes) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (cliente_id, nome_pet, nome_tutor, servico, data, hora, taxi, obs))
            
        conn.commit()
        return redirect(url_for('agenda', modo=modo, data=data))

    # --- 3. BUSCAR DADOS PARA EXIBIR ---
    # Busca agendamentos cruzando com tabela de clientes pelo ID
    agendamentos = conn.execute(f'''
        SELECT a.*, 
               c.raca, c.porte, c.comportamento, c.whatsapp, c.observacoes as obs_cliente
        FROM agenda a
        LEFT JOIN clientes c ON a.cliente_id = c.id
        WHERE {query_sql}
        ORDER BY a.hora
    ''', (param_sql,)).fetchall()
    
    # Organiza mapa para o calendário mensal
    mapa_agendamentos = {}
    if modo == 'mensal':
        for ag in agendamentos:
            d = ag['data']
            if d not in mapa_agendamentos: mapa_agendamentos[d] = []
            mapa_agendamentos[d].append(ag)

    # Dados para os modais e formulários
    opcoes_servicos = conn.execute("SELECT nome FROM servicos ORDER BY nome").fetchall()
    # Pega ID, Pet e Tutor para o Datalist inteligente
    opcoes_pets = conn.execute("SELECT id, nome_pet, nome_tutor FROM clientes ORDER BY nome_pet").fetchall()
    
    conn.close()
    
    # Retorna tudo para o HTML
    return render_template('agenda.html', 
                           agendamentos=agendamentos, 
                           opcoes_servicos=opcoes_servicos,
                           opcoes_pets=opcoes_pets,
                           modo=modo, 
                           data_atual=data_str, 
                           data_obj=data_obj,
                           texto_titulo=texto_titulo, 
                           link_anterior=data_anterior, 
                           link_proximo=data_proxima,
                           calendario=calendario_matriz, 
                           mapa_agendamentos=mapa_agendamentos)
    
@app.route('/nota/<id_agendamento>')
def gerar_nota(id_agendamento):
    if not tem_permissao('agenda'): return redirect('/dashboard')
    
    conn = get_db_connection()
    
    # 1. Pega configurações da Empresa (Novo!)
    empresa = get_config_dict(conn)
    
    # 2. Busca o agendamento
    agendamento = conn.execute("SELECT * FROM agenda WHERE id=?", (id_agendamento,)).fetchone()
    
    if not agendamento:
        conn.close()
        return "Erro: Agendamento não encontrado", 404

    # 3. Busca o Cliente pelo ID (Conexão perfeita)
    cliente = None
    if agendamento['cliente_id']:
        cliente = conn.execute("SELECT * FROM clientes WHERE id=?", (agendamento['cliente_id'],)).fetchone()
    
    # 4. Busca preço do taxi
    dado_taxi = conn.execute("SELECT valor FROM configuracoes WHERE chave='preco_taxi'").fetchone()
    preco_taxi = float(dado_taxi[0]) if dado_taxi else 20.00

    # 5. Busca o valor do Serviço
    servico_val = conn.execute("SELECT valor FROM servicos WHERE nome=?", (agendamento['servico'],)).fetchone()
    valor_servico = float(servico_val[0]) if servico_val else 0.0
    
    # --- FECHA A CONEXÃO AQUI ---
    conn.close()

    # 6. Cálculos
    total = valor_servico
    if agendamento['taxi'] == 'Sim': total += preco_taxi

    # 7. Monta dados da Nota
    info_nota = {
        # DADOS DA EMPRESA
        'empresa_nome': empresa.get('empresa_nome', 'Pet Shop'),
        'empresa_cnpj': empresa.get('empresa_cnpj', ''),
        'empresa_endereco': empresa.get('empresa_endereco', ''),
        'empresa_telefone': empresa.get('empresa_telefone', ''),
        'empresa_email': empresa.get('empresa_email', ''),
        'empresa_instagram': empresa.get('empresa_instagram', ''),

        # DADOS DO PEDIDO
        'id': agendamento['id'],
        'data': datetime.strptime(agendamento['data'], '%Y-%m-%d').strftime('%d/%m/%Y'),
        'hora': agendamento['hora'],
        'tutor': cliente['nome_tutor'] if cliente else agendamento['nome_tutor'],
        'pet': cliente['nome_pet'] if cliente else agendamento['nome_pet'],
        'cpf': cliente['cpf'] if cliente else 'Não informado',
        'endereco': cliente['endereco'] if cliente else 'Não informado',
        'whatsapp': cliente['whatsapp'] if cliente else '',
        'servico': agendamento['servico'],
        'valor_servico': valor_servico,
        'tem_taxi': (agendamento['taxi'] == 'Sim'),
        'valor_taxi': preco_taxi,
        'total': total,
        'observacoes': agendamento['observacoes']
    }
    
    return render_template('nota.html', nota=info_nota)
    
# --- NOVA ROTA: MUDAR STATUS RÁPIDO ---
@app.route('/atualizar_status', methods=['POST'])
def atualizar_status():
    if not tem_permissao('agenda'): return redirect('/dashboard')
    
    conn = get_db_connection()
    id_agend = request.form.get('id')
    novo_status = request.form.get('status') # Feito, Cancelado, etc.
    
    # Se quiser, pode adicionar lógica extra aqui (ex: se cancelar, liberar vaga)
    conn.execute("UPDATE agenda SET status = ? WHERE id = ?", (novo_status, id_agend))
    conn.commit()
    conn.close()
    
    # Volta para a página de onde veio
    return redirect(request.referrer)

@app.route('/financeiro', methods=['GET', 'POST'])
def financeiro():
    if not tem_permissao('financeiro'): return redirect('/dashboard')
    
    conn = get_db_connection()

   # --- CONFIGURAÇÃO: LER PREÇO DO TAXI DO BANCO ---
    # Busca no banco, se der erro usa 20.00 como segurança
    try:
        dado_banco = conn.execute("SELECT valor FROM configuracoes WHERE chave='preco_taxi'").fetchone()
        VALOR_TAXI = float(dado_banco[0]) if dado_banco else 20.00
    except:
        VALOR_TAXI = 20.00

    # --- 0. CONFIGURAÇÃO DE MODO (DIA ou MÊS) ---
    modo = request.args.get('modo', 'diario')
    data_str = request.args.get('data', date.today().strftime('%Y-%m-%d'))
    data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
    
    if modo == 'mensal':
        import calendar
        dias_no_mes = calendar.monthrange(data_obj.year, data_obj.month)[1]
        data_proxima = (data_obj.replace(day=dias_no_mes) + timedelta(days=1)).strftime('%Y-%m-%d')
        data_anterior = (data_obj.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-%d')
        
        meses_nomes = {1:'Janeiro', 2:'Fevereiro', 3:'Março', 4:'Abril', 5:'Maio', 6:'Junho', 7:'Julho', 8:'Agosto', 9:'Setembro', 10:'Outubro', 11:'Novembro', 12:'Dezembro'}
        texto_titulo = f"{meses_nomes[data_obj.month]} de {data_obj.year}"
        
        filtro_sql = data_obj.strftime('%Y-%m')
        query_data = "strftime('%Y-%m', data) = ?"
        query_agenda = "strftime('%Y-%m', a.data) = ?"
    else:
        data_proxima = (data_obj + timedelta(days=1)).strftime('%Y-%m-%d')
        data_anterior = (data_obj - timedelta(days=1)).strftime('%Y-%m-%d')
        
        meses_curtos = {1:'Jan', 2:'Fev', 3:'Mar', 4:'Abr', 5:'Mai', 6:'Jun', 7:'Jul', 8:'Ago', 9:'Set', 10:'Out', 11:'Nov', 12:'Dez'}
        texto_titulo = f"{data_obj.day} {meses_curtos[data_obj.month]}"
        if data_str == date.today().strftime('%Y-%m-%d'): texto_titulo = f"Hoje, {texto_titulo}"
            
        filtro_sql = data_str
        query_data = "data = ?"
        query_agenda = "a.data = ?"


    # POST: LANÇAR MOVIMENTAÇÃO
    if request.method == 'POST':
        tipo = request.form['tipo']
        descricao = request.form['descricao']
        valor = float(request.form['valor'])
        data_lancamento = request.form['data']
        conn.execute("INSERT INTO financeiro (tipo, descricao, valor, data) VALUES (?, ?, ?, ?)", (tipo, descricao, valor, data_lancamento))
        conn.commit()
        return redirect(url_for('financeiro', data=data_lancamento, modo=modo))


    # --- 1. CÁLCULOS FINANCEIROS (COM TAXI) ---

    # Receita Agenda (Soma Serviços + Taxas de Taxi)
    # A lógica SQL: Se taxi for 'Sim', soma o valor do serviço + VALOR_TAXI. Se não, só o serviço.
    receita_servicos = conn.execute(f'''
        SELECT SUM(s.valor + CASE WHEN a.taxi = 'Sim' THEN ? ELSE 0 END) 
        FROM agenda a
        JOIN servicos s ON a.servico = s.nome
        WHERE a.status = 'Concluído' AND {query_agenda}
    ''', (VALOR_TAXI, filtro_sql)).fetchone()[0] or 0.0

    # Movimentações Manuais
    total_entradas_manuais = conn.execute(f"SELECT SUM(valor) FROM financeiro WHERE tipo='Entrada' AND {query_data}", (filtro_sql,)).fetchone()[0] or 0.0
    total_saidas_manuais = conn.execute(f"SELECT SUM(valor) FROM financeiro WHERE tipo='Saida' AND {query_data}", (filtro_sql,)).fetchone()[0] or 0.0
    movimentacoes_lista = conn.execute(f"SELECT * FROM financeiro WHERE {query_data} ORDER BY data DESC", (filtro_sql,)).fetchall()

    # Despesas Fixas
    lista_fixas_todas = conn.execute("SELECT * FROM despesas_fixas ORDER BY dia_vencimento").fetchall()
    if modo == 'mensal':
        total_fixo = conn.execute("SELECT SUM(valor) FROM despesas_fixas").fetchone()[0] or 0.0
    else:
        dia_hoje = data_obj.day
        total_fixo = conn.execute("SELECT SUM(valor) FROM despesas_fixas WHERE dia_vencimento = ?", (dia_hoje,)).fetchone()[0] or 0.0

    # Totais Finais
    total_entradas = receita_servicos + total_entradas_manuais
    total_saidas = total_saidas_manuais + total_fixo
    saldo = total_entradas - total_saidas


    # --- 2. EXTRATO UNIFICADO ---
    extrato = []

    # A. Agenda (Detalhando o Taxi)
    # Precisamos buscar a coluna 'taxi' também
    servicos_db = conn.execute(f'''
        SELECT a.data, a.hora, a.nome_pet, a.servico, a.taxi, s.valor 
        FROM agenda a
        JOIN servicos s ON a.servico = s.nome
        WHERE a.status = 'Concluído' AND {query_agenda}
    ''', (filtro_sql,)).fetchall()

    for s in servicos_db:
        valor_final = s['valor']
        desc_extra = ""
        
        # Se tiver taxi, adiciona o valor e avisa na descrição
        if s['taxi'] == 'Sim':
            valor_final += VALOR_TAXI
            desc_extra = " + Taxi"

        desc = f"{s['data'].split('-')[2]}/{s['data'].split('-')[1]} - {s['nome_pet']} ({s['servico']}{desc_extra})" if modo == 'mensal' else f"Serviço: {s['nome_pet']} ({s['servico']}{desc_extra})"
        
        extrato.append({'data': s['data'], 'descricao': desc, 'valor': valor_final, 'tipo': 'Entrada', 'origem': 'Agenda'})

    # B. Manuais
    for m in movimentacoes_lista:
        desc = f"{m['data'].split('-')[2]}/{m['data'].split('-')[1]} - {m['descricao']}" if modo == 'mensal' else m['descricao']
        extrato.append({'data': m['data'], 'descricao': desc, 'valor': m['valor'], 'tipo': m['tipo'], 'origem': 'Manual'})

    # C. Fixas
    if modo == 'mensal':
        for f in lista_fixas_todas:
            extrato.append({'data': f"{data_str}-{f['dia_vencimento']:02d}", 'descricao': f"Dia {f['dia_vencimento']} - Fixo: {f['nome']}", 'valor': f['valor'], 'tipo': 'Saida', 'origem': 'Fixo'})
    else:
        fixas_hoje = [f for f in lista_fixas_todas if f['dia_vencimento'] == data_obj.day]
        for f in fixas_hoje:
            extrato.append({'data': data_str, 'descricao': f"Fixo: {f['nome']}", 'valor': f['valor'], 'tipo': 'Saida', 'origem': 'Fixo'})

    extrato.sort(key=lambda x: x['data'], reverse=True)
    conn.close()

    return render_template('financeiro.html', 
                           fixas=lista_fixas_todas,
                           movimentacoes=movimentacoes_lista,
                           extrato=extrato,
                           total_entradas=total_entradas,
                           total_saidas=total_saidas,
                           saldo=saldo,
                           data_atual=data_str,
                           texto_titulo=texto_titulo,
                           link_anterior=data_anterior,
                           link_proximo=data_proxima,
                           modo=modo)
    
# ROTA PARA ADICIONAR/REMOVER DESPESA FIXA
@app.route('/financeiro/fixo', methods=['POST'])
def financeiro_fixo():
    if not tem_permissao('financeiro'): return redirect('/dashboard')
    
    conn = get_db_connection()
    acao = request.form.get('acao') # 'adicionar' ou 'deletar'

    if acao == 'adicionar':
        nome = request.form['nome']
        valor = request.form['valor']
        dia = request.form['dia']
        conn.execute("INSERT INTO despesas_fixas (nome, valor, dia_vencimento) VALUES (?, ?, ?)", 
                     (nome, valor, dia))
    
    elif acao == 'deletar':
        id_fixo = request.form['id']
        conn.execute("DELETE FROM despesas_fixas WHERE id = ?", (id_fixo,))

    conn.commit()
    conn.close()
    return redirect('/financeiro')

@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    if not tem_permissao('clientes'): return redirect('/dashboard')
    
    conn = get_db_connection()

    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'deletar':
            id_cliente = request.form.get('id')
            conn.execute("DELETE FROM clientes WHERE id = ?", (id_cliente,))
            
        else:
            # --- SALVAR (Incluindo CPF) ---
            id_cliente = request.form.get('id')
            nome_tutor = request.form.get('nome_tutor')
            whatsapp = request.form.get('whatsapp')
            cpf = request.form.get('cpf')  # <--- NOVO
            cep = request.form.get('cep')
            endereco = request.form.get('endereco')
            nome_pet = request.form.get('nome_pet')
            raca = request.form.get('raca')
            porte = request.form.get('porte')
            comportamento = request.form.get('comportamento')
            observacoes = request.form.get('observacoes')

            if id_cliente:
                conn.execute('''
                    UPDATE clientes 
                    SET nome_tutor=?, whatsapp=?, cpf=?, cep=?, endereco=?, nome_pet=?, raca=?, porte=?, comportamento=?, observacoes=?
                    WHERE id=?
                ''', (nome_tutor, whatsapp, cpf, cep, endereco, nome_pet, raca, porte, comportamento, observacoes, id_cliente))
            else:
                conn.execute('''
                    INSERT INTO clientes (nome_tutor, whatsapp, cpf, cep, endereco, nome_pet, raca, porte, comportamento, observacoes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (nome_tutor, whatsapp, cpf, cep, endereco, nome_pet, raca, porte, comportamento, observacoes))
            
        conn.commit()
        return redirect('/clientes')

    lista_clientes = conn.execute("SELECT * FROM clientes ORDER BY nome_tutor").fetchall()
    conn.close()
    
    return render_template('clientes.html', clientes=lista_clientes)

@app.route('/estoque', methods=['GET', 'POST'])
def estoque():
    if not tem_permissao('estoque'): return redirect('/dashboard')
    
    conn = get_db_connection()

    # --- LÓGICA DE ADICIONAR / REMOVER ---
    if request.method == 'POST':
        acao = request.form.get('acao') # 'adicionar' ou 'deletar'
        
        if acao == 'adicionar':
            produto = request.form['produto']
            categoria = request.form['categoria']
            qtd_atual = int(request.form['qtd_atual'])
            qtd_minima = int(request.form['qtd_minima'])
            unidade = request.form['unidade']
            
            conn.execute('''
                INSERT INTO estoque (produto, categoria, qtd_atual, qtd_minima, unidade)
                VALUES (?, ?, ?, ?, ?)
            ''', (produto, categoria, qtd_atual, qtd_minima, unidade))
            
        elif acao == 'deletar':
            id_produto = request.form['id']
            conn.execute("DELETE FROM estoque WHERE id = ?", (id_produto,))
            
        conn.commit()
        return redirect('/estoque')

    # --- BUSCAR DADOS ---
    lista_estoque = conn.execute("SELECT * FROM estoque ORDER BY produto").fetchall()
    
    # Contar quantos produtos estão abaixo do mínimo (Alerta)
    alerta_baixo = conn.execute("SELECT COUNT(*) FROM estoque WHERE qtd_atual <= qtd_minima").fetchone()[0]
    
    # Calcular valor total do estoque (Opcional, se tiver preço de custo futuro)
    total_itens = conn.execute("SELECT SUM(qtd_atual) FROM estoque").fetchone()[0] or 0

    conn.close()

    return render_template('estoque.html', 
                           itens=lista_estoque, 
                           alerta_baixo=alerta_baixo,
                           total_itens=total_itens)

# --- 3. ROTA EQUIPA (PARA O GERENTE ESCOLHER AS PERMISSÕES) ---
@app.route('/equipa', methods=['GET', 'POST'])
def equipa():
    # Só gerente entra aqui
    if session.get('cargo') != 'gerente': return redirect('/dashboard')
    
    conn = get_db_connection()

    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'deletar':
            id_user = request.form.get('id')
            # Proteção: Não deixa deletar a si mesmo
            if int(id_user) != session['user_id']:
                conn.execute("DELETE FROM usuarios WHERE id=?", (id_user,))
        
        else:
            # SALVAR / EDITAR
            id_user = request.form.get('id')
            nome = request.form.get('nome')
            usuario = request.form.get('usuario')
            senha = request.form.get('senha')
            cargo = request.form.get('cargo')
            
            # Pega as caixinhas marcadas no HTML
            lista_perms = request.form.getlist('perms') # Retorna lista ['agenda', 'clientes']
            permissoes_str = ",".join(lista_perms) # Vira texto "agenda,clientes"

            if id_user:
                conn.execute('''UPDATE usuarios SET nome=?, usuario=?, senha=?, cargo=?, permissoes=? WHERE id=?''',
                             (nome, usuario, senha, cargo, permissoes_str, id_user))
            else:
                conn.execute('''INSERT INTO usuarios (nome, usuario, senha, cargo, permissoes) VALUES (?, ?, ?, ?, ?)''',
                             (nome, usuario, senha, cargo, permissoes_str))
        
        conn.commit()
        return redirect('/equipa')

    usuarios = conn.execute("SELECT * FROM usuarios").fetchall()
    conn.close()
    return render_template('equipa.html', usuarios=usuarios)

# ROTA PARA MARCAR COMO CONCLUÍDO
@app.route('/concluir_agendamento', methods=['POST'])
def concluir_agendamento():
    if not tem_permissao('agenda'): return redirect('/dashboard')
    
    id_agendamento = request.form['id']
    
    conn = get_db_connection()
    conn.execute("UPDATE agenda SET status = 'Concluído' WHERE id = ?", (id_agendamento,))
    conn.commit()
    conn.close()
    
    return redirect('/agenda')

# --- FUNÇÃO AUXILIAR (Coloque no início, junto com as outras funções) ---
def get_config_dict(conn):
    """Pega todas as configurações do banco e transforma num dicionário fácil de usar"""
    linhas = conn.execute("SELECT chave, valor FROM configuracoes").fetchall()
    # Transforma em algo tipo: {'empresa_nome': 'Pet Verso', 'preco_taxi': '20.00'}
    dados = {linha['chave']: linha['valor'] for linha in linhas}
    return dados

# --- NOVA ROTA: CONFIGURAÇÕES DA EMPRESA ---
@app.route('/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if not tem_permissao('financeiro'): return redirect('/dashboard') # Regra de segurança
    
    conn = get_db_connection()

    if request.method == 'POST':
        # Salva cada campo que veio do formulário
        campos = ['empresa_nome', 'empresa_cnpj', 'empresa_endereco', 'empresa_telefone', 'empresa_email', 'empresa_instagram']
        
        for campo in campos:
            valor = request.form.get(campo)
            # Atualiza ou Insere (UPSERT logic simples)
            conn.execute("INSERT OR REPLACE INTO configuracoes (chave, valor) VALUES (?, ?)", (campo, valor))
            
        conn.commit()
        conn.close()
        return redirect('/configuracoes')

    # Busca os dados para mostrar na tela
    conf = get_config_dict(conn)
    conn.close()
    
    return render_template('configuracoes.html', conf=conf)

if __name__ == '__main__':
    app.run(debug=True)