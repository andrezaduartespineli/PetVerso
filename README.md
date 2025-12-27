# 🐾 Pet Verso - Sistema de Gestão para Pet Shops

![Status](https://img.shields.io/badge/Status-Finalizado-success)
![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-2.x-lightgrey?logo=flask)
![License](https://img.shields.io/badge/License-MIT-green)

> **Pet Verso** é um sistema de gestão completo (ERP) desenvolvido para facilitar o dia a dia de Pet Shops e Clínicas Veterinárias. Com foco em usabilidade, ele gerencia agendamentos, financeiro, estoque e fidelização de clientes via WhatsApp.

---

## ✨ Funcionalidades Principais

### 📅 **Agenda Inteligente**
- Visualização **Diária** e **Mensal**.
- Controle de status: *Agendado, Concluído, Cancelado, Faltou*.
- Cálculo automático de taxa de **Taxi Dog**.
- Integração direta com ficha do pet.

### 💰 **Gestão Financeira**
- **Fluxo de Caixa:** Entradas e Saídas diárias/mensais.
- **Relatórios:** Geração de relatórios detalhados prontos para impressão/PDF.
- **Despesas Fixas:** Controle de contas recorrentes (aluguel, luz, etc.).
- **Notas e Recibos:** Emissão automática com cálculo de serviços + táxi.

### 📦 **Controle de Estoque**
- Cadastro de produtos e insumos.
- **Alerta Visual** de estoque baixo/crítico.
- Categorização inteligente (Uso Interno vs Venda).

### 👥 **Gestão de Equipe & Acesso**
- **Níveis de Acesso:** Gerente (Total) vs Funcionário (Limitado).
- Controle de permissões personalizáveis (quem pode ver o financeiro, quem pode deletar, etc.).

### 📱 **Automação & Fidelização (WhatsApp)**
- **Lembretes de Retorno:** O sistema identifica pets que não tomam banho há mais de 10 dias.
- **Mensagens Personalizadas:** Templates configuráveis com variáveis como `{tutor}`, `{pet}` e `{dias}`.
- **Botão de Envio:** Integração com WhatsApp Web para envio rápido.
- **Robô Autônomo:** Script Python extra (`robo_lembretes.py`) para envio em massa automático.

---

## 🛠️ Tecnologias Utilizadas

* **Back-end:** Python, Flask
* **Banco de Dados:** SQLite
* **Front-end:** HTML5, CSS3, JavaScript
* **Ícones:** Phosphor Icons
* **Automação:** PyWhatKit (para o robô de WhatsApp)

---

## 📂 Estrutura do Projeto

```text
petverso/
├── app.py                 # Coração do sistema (Rotas e Lógica)
├── petverso.db            # Banco de Dados SQLite
├── robo_lembretes.py      # Script de automação do WhatsApp
├── requirements.txt       # Lista de dependências
├── static/
│   ├── style.css          # Estilos e Design
│   └── logo.png           # Logotipo da empresa
└── templates/             # Páginas HTML
    ├── dashboard.html     # Painel principal
    ├── agenda.html        # Calendário
    ├── financeiro.html    # Fluxo de caixa
    ├── clientes.html      # Cadastro de clientes
    ├── estoque.html       # Controle de produtos
    ├── nota.html          # Recibo para impressão
    ├── lembretes.html     # Lista de repescagem
    └── configuracoes.html # Ajustes do sistema
```
---

<p align="center"> Desenvolvido com 💙 por Andreza Duarte Spineli </p>