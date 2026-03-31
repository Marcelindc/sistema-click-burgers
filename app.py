import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time
import re
import json
import plotly.express as px
import base64
from io import BytesIO
from PIL import Image
import random
import datetime

# ==========================================
# 1. CONFIGURAÇÃO INICIAL E LOGIN
# ==========================================
st.set_page_config(page_title="Click Burgers", page_icon="🍔", layout="wide", initial_sidebar_state="expanded")

if "autenticado" not in st.session_state: st.session_state["autenticado"] = False
if "transacao_id" not in st.session_state: st.session_state.transacao_id = int(time.time())
if "usuario_logado" not in st.session_state: st.session_state["usuario_logado"] = ""
if "nome_logado" not in st.session_state: st.session_state["nome_logado"] = ""

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stAppViewContainer"] { background-color: #F4F6F9; }
    [data-testid="stSidebar"] { background-color: #FFFFFF; border-right: 1px solid #EAEAEA; }
    div[data-testid="metric-container"] { display: none !important; }
    .block-container { padding-top: 3rem !important; padding-bottom: 1rem !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label { padding: 10px 15px !important; border-radius: 8px !important; margin-bottom: 5px !important; transition: all 0.2s ease !important; border: 1px solid transparent; }
    div[data-testid="stRadio"] div[role="radiogroup"] label:hover { background-color: #F4F6F9 !important; }
    div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) { background-color: #FFF0F2 !important; border-left: 5px solid #E31837 !important; border-radius: 4px 8px 8px 4px !important; }
    .click-kpi-card { background-color: #FFFFFF; padding: 20px 25px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); display: flex; flex-direction: column; justify-content: center; height: 130px; margin-bottom: 20px; }
    .click-kpi-title { color: #6C757D; font-weight: 600; font-size: 14px; margin-bottom: 5px; }
    .click-kpi-value { color: #1E1E1E; font-weight: 800; font-size: 28px; }
    .card-faturamento { border-left: 6px solid #E31837; } 
    .card-lucro { border-left: 6px solid #28A745; } 
    .card-lucro .click-kpi-value { color: #28A745 !important; } 
    .card-despesas { border-left: 6px solid #E31837; } 
    .card-taxas { border-left: 6px solid #E31837; } 
    .card-ticket { border-left: 6px solid #1E1E1E; } 
    .card-margem { border-left: 6px solid #0DCAF0; } 
    .card-cmv { border-left: 6px solid #FD7E14; } 
    .card-desc { border-left: 6px solid #E31837; } 
    .pdv-card-title { font-size: 16px; font-weight: bold; color: #1E1E1E; margin-bottom: 2px; line-height: 1.2; height: 38px; overflow: hidden;}
    .pdv-card-price { font-size: 15px; color: #E31837; font-weight: bold; margin-bottom: 10px; }
    .pdv-card-price-old { font-size: 12px; color: #9E9E9E; text-decoration: line-through; }
    .pdv-resumo-box { background-color: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: 1px solid #EAEAEA; }
    .pdv-total-text { font-size: 24px; font-weight: 900; text-align: center; color: #1E1E1E; }
    .pdv-total-value { font-size: 36px; font-weight: 900; text-align: center; color: #E31837; }
    h1, h2, h3, h4 { color: #1E1E1E; font-weight: 700; }
    hr { border-color: #EAEAEA; }
    .login-box { background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; }
    </style>
""", unsafe_allow_html=True)

# 🚀 CONEXÃO TURBO COM O SUPABASE
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("Erro ao conectar com o banco de dados. Verifique os Segredos (Secrets).")
    st.stop()

# 🛡️ AMORTECEDOR DE REQUISIÇÕES
@st.cache_data(ttl=5)
def puxar_dados(tabela):
    try:
        response = supabase.table(tabela).select("*").execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

# ==========================================
# 🛑 TELA DE LOGIN 
# ==========================================
if not st.session_state["autenticado"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_esq, col_logo, col_form, col_dir = st.columns([1, 1.5, 2, 1])
    
    with col_logo:
        st.markdown("<br>", unsafe_allow_html=True) 
        try: st.image("LOGOCLICKVERMELHA.png", use_container_width=True)
        except: st.warning("⚠️ Imagem não encontrada.")
            
    with col_form:
        st.markdown("### 🔒 Acesso Restrito")
        with st.form("login_form"):
            usuario_input = st.text_input("Usuário", placeholder="Digite seu usuário")
            senha_input = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submit_login = st.form_submit_button("Entrar no Sistema", use_container_width=True, type="primary")
            
            if submit_login:
                if usuario_input and senha_input:
                    df_usuarios = puxar_dados('Usuarios') 
                    if df_usuarios.empty: st.error("❌ Nenhum usuário cadastrado!")
                    else:
                        df_usuarios['Usuario'] = df_usuarios['Usuario'].astype(str).str.strip()
                        df_usuarios['Senha'] = df_usuarios['Senha'].astype(str).str.strip()
                        match = df_usuarios[(df_usuarios['Usuario'] == usuario_input.strip()) & (df_usuarios['Senha'] == senha_input.strip())]
                        
                        if not match.empty:
                            st.session_state["autenticado"] = True
                            st.session_state["usuario_logado"] = usuario_input.strip()
                            if 'Nome' in df_usuarios.columns: st.session_state["nome_logado"] = str(match['Nome'].values[0]).strip()
                            else: st.session_state["nome_logado"] = usuario_input.strip()
                            st.rerun() 
                        else: st.error("❌ Usuário ou senha incorretos!")
                else: st.warning("Preencha os campos.")
    st.stop() 

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def processar_imagem(uploaded_file, tamanho=(250, 250), qualidade=70):
    if uploaded_file is not None:
        try:
            img = Image.open(uploaded_file)
            if img.mode in ("RGBA", "P"): img = img.convert("RGB")
            img.thumbnail(tamanho) 
            buffered = BytesIO()
            img.save(buffered, format="JPEG", quality=qualidade)
            return f"data:image/jpeg;base64,{base64.b64encode(buffered.getvalue()).decode()}"
        except: return ""
    return ""

with st.sidebar:
    try: st.image("LOGOCLICKVERMELHA.png", width=140)
    except: pass
    st.markdown("<br>", unsafe_allow_html=True)
    
    nome_exibicao = st.session_state.get('nome_logado', st.session_state.get('usuario_logado', ''))
    st.success(f"👤 Olá, **{nome_exibicao}**!")
    
    # Módulos do Sistema
    opcoes_menu = ["📊 Dashboard", "🛒 Frente de Caixa", "👥 Clientes", "💸 Despesas", "🍔 Produtos", "🍅 Insumos", "📝 Lista de Compras"]
    menu_selecionado = st.radio("", opcoes_menu, label_visibility="collapsed")
    st.markdown("---")
    
    if st.button("🚪 Sair (Logout)", use_container_width=True):
        st.session_state["autenticado"] = False
        st.session_state["usuario_logado"] = ""
        st.session_state["nome_logado"] = ""
        puxar_dados.clear() 
        st.rerun()
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Sistema Cloud v3.0 - Click Burgers")

# -------------------------------------------------------------
# MÓDULO 1: DASHBOARD 
# -------------------------------------------------------------
if menu_selecionado == "📊 Dashboard":
    st.title("Visão Estratégica")
    df_vendas = puxar_dados('Vendas')
    df_despesas = puxar_dados('Despesas')
    
    if df_vendas.empty: st.info("Aguardando as primeiras vendas...")
    else:
        df_vendas['Data'] = pd.to_datetime(df_vendas['Data'], format='%d/%m/%Y')
        if not df_despesas.empty: df_despesas['Data'] = pd.to_datetime(df_despesas['Data'], format='%d/%m/%Y')
        
        df_produtos_atual = puxar_dados('Produtos')
        dict_precos = {}
        for _, r in df_produtos_atual.iterrows():
            p_padrao = float(r.get('Valor de Venda', 0))
            d_prod = float(r.get('Desconto', 0) if r.get('Desconto', 0) != '' and pd.notna(r.get('Desconto')) else 0.0)
            dict_precos[r['Nome do Produto']] = p_padrao - d_prod

        with st.container():
            st.markdown("#### Filtros de Análise")
            col_f1, col_f2, col_f3 = st.columns(3)
            primeira_data = df_vendas['Data'].min().date()
            data_hoje = datetime.date.today()
            with col_f1: data_inicio = st.date_input("Data Inicial", primeira_data)
            with col_f2: data_fim = st.date_input("Data Final", data_hoje)
            with col_f3: produtos_filtrados = st.multiselect("Filtrar por Lanches:", list(dict_precos.keys()), placeholder="Todos os produtos")
        
        mascara_vendas = (df_vendas['Data'] >= pd.to_datetime(data_inicio)) & (df_vendas['Data'] <= pd.to_datetime(data_fim))
        df_filtrado = df_vendas.loc[mascara_vendas]
        
        total_despesas_periodo = 0.0
        if not df_despesas.empty:
            mascara_desp = (df_despesas['Data'] >= pd.to_datetime(data_inicio)) & (df_despesas['Data'] <= pd.to_datetime(data_fim))
            try:
                df_despesas['Valor Num'] = df_despesas['Valor'].apply(lambda x: float(str(x).replace(',', '.')) if str(x).strip() != '' else 0.0)
                total_despesas_periodo = df_despesas.loc[mascara_desp]['Valor Num'].sum()
            except: total_despesas_periodo = df_despesas.loc[mascara_desp]['Valor'].sum()
        
        if df_filtrado.empty: st.warning("Nenhum dado encontrado para os filtros selecionados.")
        else:
            dados_itens = []
            for idx, row in df_filtrado.iterrows():
                try: subtotal_pedido = float(str(row.get('Subtotal', 0)).replace(',', '.'))
                except: subtotal_pedido = 0.0
                try: taxas_pedido = float(str(row.get('Taxas Cartão', 0)).replace(',', '.'))
                except: taxas_pedido = 0.0
                try: lucro_pedido = float(str(row.get('Lucro Real', 0)).replace(',', '.'))
                except: lucro_pedido = 0.0
                
                cliente_nome = str(row.get('Cliente', 'Avulso'))
                for lanche in str(row['Itens']).split(', '):
                    match = re.match(r'(\d+)x\s+(.+)', lanche)
                    if match:
                        qtd, nome = int(match.group(1)), match.group(2)
                        receita_item = qtd * dict_precos.get(nome, 0)
                        peso = (receita_item / subtotal_pedido) if subtotal_pedido > 0 else 0
                        dados_itens.append({'Lanche': nome, 'Quantidade': qtd, 'Receita': receita_item, 'Lucro Proporcional': lucro_pedido * peso, 'Taxa Proporcional': taxas_pedido * peso, 'Cliente': cliente_nome})
            
            df_itens = pd.DataFrame(dados_itens)
            if produtos_filtrados:
                df_itens_filtrado = df_itens[df_itens['Lanche'].isin(produtos_filtrados)]
                vendas_totais_kpi = df_itens_filtrado['Receita'].sum()
                lucro_kpi = df_itens_filtrado['Lucro Proporcional'].sum()
                taxas_kpi = df_itens_filtrado['Taxa Proporcional'].sum()
                despesas_mostrar = 0.0 
                qtd_unidades_kpi = df_itens_filtrado['Quantidade'].sum()
                ticket_kpi = vendas_totais_kpi / qtd_unidades_kpi if qtd_unidades_kpi > 0 else 0
                margem_kpi = (lucro_kpi / vendas_totais_kpi * 100) if vendas_totais_kpi > 0 else 0
                cmv_valor = vendas_totais_kpi - lucro_kpi 
                cmv_perc = (cmv_valor / vendas_totais_kpi * 100) if vendas_totais_kpi > 0 else 0
                descontos_kpi = 0.0
                tit_k1, tit_k2, tit_k3, tit_k4 = "Receita (Filtro)", "Margem Bruta", "Despesas (N/A)", "Taxas (Filtro)"
                tit_k5, tit_k6, tit_k7, tit_k8 = "Preço Médio (Unid.)", "Margem (%)", "CMV (Insumos %)", "Descontos (N/A)"
            else:
                vendas_totais_kpi = df_filtrado['Total Pago'].sum()
                taxas_kpi = df_filtrado['Taxas Cartão'].sum()
                despesas_mostrar = total_despesas_periodo
                lucro_kpi = df_filtrado['Lucro Real'].sum() - total_despesas_periodo
                qtd_pedidos = len(df_filtrado)
                ticket_kpi = vendas_totais_kpi / qtd_pedidos if qtd_pedidos > 0 else 0
                margem_kpi = (lucro_kpi / vendas_totais_kpi * 100) if vendas_totais_kpi > 0 else 0
                lucro_bruto = df_filtrado['Lucro Real'].sum()
                cmv_valor = (df_filtrado['Total Pago'].sum() - df_filtrado['Taxas Cartão'].sum()) - lucro_bruto
                cmv_perc = (cmv_valor / vendas_totais_kpi * 100) if vendas_totais_kpi > 0 else 0
                try: descontos_kpi = df_filtrado['Desconto'].sum()
                except: descontos_kpi = 0.0
                tit_k1, tit_k2, tit_k3, tit_k4 = "Faturamento Bruto", "Lucro Líquido Real", "Despesas Operacionais", "Taxas Pagas"
                tit_k5, tit_k6, tit_k7, tit_k8 = "Ticket Médio", "Margem Líquida (%)", "CMV (Custo Comida)", "Descontos Concedidos"
            
            st.markdown(f"<span style='color:#6C757D; font-size:14px'><b>Total de Pedidos no período:</b> {len(df_filtrado)}</span>", unsafe_allow_html=True)
            
            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(f"""<div class="click-kpi-card card-faturamento"><div class="click-kpi-title">{tit_k1}</div><div class="click-kpi-value">R$ {vendas_totais_kpi:,.2f}</div></div>""", unsafe_allow_html=True)
            k2.markdown(f"""<div class="click-kpi-card card-lucro"><div class="click-kpi-title">{tit_k2}</div><div class="click-kpi-value">R$ {lucro_kpi:,.2f}</div></div>""", unsafe_allow_html=True)
            k3.markdown(f"""<div class="click-kpi-card card-despesas"><div class="click-kpi-title">{tit_k3}</div><div class="click-kpi-value">- R$ {despesas_mostrar:,.2f}</div></div>""", unsafe_allow_html=True)
            k4.markdown(f"""<div class="click-kpi-card card-taxas"><div class="click-kpi-title">{tit_k4}</div><div class="click-kpi-value">- R$ {taxas_kpi:,.2f}</div></div>""", unsafe_allow_html=True)
            
            k5, k6, k7, k8 = st.columns(4)
            k5.markdown(f"""<div class="click-kpi-card card-ticket"><div class="click-kpi-title">{tit_k5}</div><div class="click-kpi-value">R$ {ticket_kpi:,.2f}</div></div>""", unsafe_allow_html=True)
            k6.markdown(f"""<div class="click-kpi-card card-margem"><div class="click-kpi-title">{tit_k6}</div><div class="click-kpi-value">{margem_kpi:,.1f}%</div></div>""", unsafe_allow_html=True)
            k7.markdown(f"""<div class="click-kpi-card card-cmv"><div class="click-kpi-title">{tit_k7}</div><div class="click-kpi-value">R$ {cmv_valor:,.2f} <span style="font-size:16px; font-weight:normal">({cmv_perc:.1f}%)</span></div></div>""", unsafe_allow_html=True)
            k8.markdown(f"""<div class="click-kpi-card card-desc"><div class="click-kpi-title">{tit_k8}</div><div class="click-kpi-value">- R$ {descontos_kpi:,.2f}</div></div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            g_col0, g_col1, g_col2 = st.columns([1, 1, 1])
            with g_col0:
                st.markdown("#### 🏆 Top 5 Clientes VIP")
                if 'Cliente' in df_filtrado.columns:
                    if produtos_filtrados:
                        df_base_vips = df_itens_filtrado
                        coluna_valor = 'Receita'
                    else:
                        df_base_vips = df_filtrado
                        coluna_valor = 'Subtotal'
                    df_vendas_clientes = df_base_vips[(df_base_vips['Cliente'] != 'Avulso') & (df_base_vips['Cliente'].notna()) & (df_base_vips['Cliente'] != '')]
                    if not df_vendas_clientes.empty:
                        top_clientes = df_vendas_clientes.groupby('Cliente')[coluna_valor].sum().reset_index().sort_values(coluna_valor, ascending=False).head(5)
                        fig_vips = px.bar(top_clientes, x=coluna_valor, y='Cliente', orientation='h', text=coluna_valor, color_discrete_sequence=['#FFC107']) 
                        fig_vips.update_traces(textposition='outside', texttemplate='R$ %{x:.2f}', hovertemplate='Cliente: %{y}<br>Gasto: R$ %{x:.2f}')
                        fig_vips.update_layout(bargap=0.4, plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', height=320, margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(showgrid=False), yaxis=dict(showgrid=False), yaxis_categoryorder='total ascending')
                        st.plotly_chart(fig_vips, use_container_width=True)
                    else: st.info("Nenhuma venda VIP registrada nestes filtros.")
                else: st.info("O campo de Clientes ainda não possui dados de vendas.")
                    
            with g_col1:
                st.markdown("#### Evolução de Faturamento por Dia")
                df_linha = df_filtrado.groupby('Data')['Total Pago'].sum().reset_index()
                df_linha['Data_Formatada'] = df_linha['Data'].dt.strftime('%d/%m/%Y')
                fig_linha = px.line(df_linha, x='Data_Formatada', y='Total Pago', markers=True)
                fig_linha.update_traces(line=dict(color='#E31837', width=3), marker=dict(size=8, color='#E31837', line=dict(width=2, color='white')), fill='tozeroy', fillcolor='rgba(227, 24, 55, 0.1)', hovertemplate='Data: %{x}<br>Total: R$ %{y:.2f}') 
                fig_linha.update_layout(plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', xaxis_title="", yaxis_title="R$", height=320, margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(showgrid=False, type='category'), yaxis=dict(showgrid=True, gridcolor='#F0F0F0'))
                st.plotly_chart(fig_linha, use_container_width=True)

            with g_col2:
                st.markdown("#### Divisão de Pagamentos")
                if produtos_filtrados:
                    dados_itens_pag = []
                    for idx, row in df_filtrado.iterrows():
                        try: subtotal_pedido = float(str(row.get('Subtotal', 0)).replace(',', '.'))
                        except: subtotal_pedido = 0.0
                        try: val_pix = float(str(row.get('Pix', 0)).replace(',', '.'))
                        except: val_pix = 0.0
                        try: val_din = float(str(row.get('Dinheiro', 0)).replace(',', '.'))
                        except: val_din = 0.0
                        try: val_deb = float(str(row.get('Débito', 0)).replace(',', '.'))
                        except: val_deb = 0.0
                        try: val_cred = float(str(row.get('Crédito', 0)).replace(',', '.'))
                        except: val_cred = 0.0
                        for lanche in str(row['Itens']).split(', '):
                            match = re.match(r'(\d+)x\s+(.+)', lanche)
                            if match:
                                qtd = int(match.group(1))
                                nome = match.group(2)
                                if nome in produtos_filtrados:
                                    preco_atual = dict_precos.get(nome, 0)
                                    receita_item = qtd * preco_atual
                                    peso = (receita_item / subtotal_pedido) if subtotal_pedido > 0 else 0
                                    dados_itens_pag.append({'Pix Prop': val_pix * peso, 'Dinheiro Prop': val_din * peso, 'Débito Prop': val_deb * peso, 'Crédito Prop': val_cred * peso})
                    if dados_itens_pag:
                        df_itens_pag = pd.DataFrame(dados_itens_pag)
                        soma_pix, soma_din = round(df_itens_pag['Pix Prop'].sum(), 2), round(df_itens_pag['Dinheiro Prop'].sum(), 2)
                        soma_deb, soma_cred = round(df_itens_pag['Débito Prop'].sum(), 2), round(df_itens_pag['Crédito Prop'].sum(), 2)
                    else: soma_pix = soma_din = soma_deb = soma_cred = 0.0
                else:
                    soma_pix, soma_din = round(df_filtrado['Pix'].sum(), 2), round(df_filtrado['Dinheiro'].sum(), 2)
                    soma_deb, soma_cred = round(df_filtrado['Débito'].sum(), 2), round(df_filtrado['Crédito'].sum(), 2)
                df_pagamentos = pd.DataFrame({'Modalidade': ['PIX', 'Dinheiro', 'Débito', 'Crédito'], 'Valor (R$)': [soma_pix, soma_din, soma_deb, soma_cred]})
                df_pagamentos = df_pagamentos[df_pagamentos['Valor (R$)'] > 0]
                if not df_pagamentos.empty:
                    fig_rosca = px.pie(df_pagamentos, values='Valor (R$)', names='Modalidade', hole=0.6, color_discrete_sequence=['#1E1E1E', '#FFC107', '#9E9E9E', '#E31837'])
                    fig_rosca.update_traces(textposition='inside', textinfo='percent+label', hovertemplate='Modalidade: %{label}<br>Valor: R$ %{value:.2f}', marker=dict(line=dict(color='#FFFFFF', width=2)))
                    fig_rosca.update_layout(plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', height=320, margin=dict(l=0, r=0, t=20, b=0), showlegend=False)
                    st.plotly_chart(fig_rosca, use_container_width=True)
                else: st.info("Sem pagamentos registrados.")

# -------------------------------------------------------------
# MÓDULO 2: CLIENTES E CRM
# -------------------------------------------------------------
elif menu_selecionado == "👥 Clientes":
    st.title("👥 Gestão de Clientes e CRM")
    col_c1, col_c2 = st.columns([2, 1])
    
    with col_c1:
        st.markdown("#### ➕ Cadastrar Novo Cliente")
        with st.form("form_cliente", clear_on_submit=True):
            nome_cli = st.text_input("Nome Completo")
            tel_cli = st.text_input("Telefone / WhatsApp (Ex: 11999998888)")
            nasc_cli = st.date_input("Data de Nascimento (Opcional)", value=None, min_value=datetime.date(1920, 1, 1))
            
            if st.form_submit_button("Salvar Cliente"):
                if nome_cli:
                    nasc_str = nasc_cli.strftime('%d/%m/%Y') if nasc_cli else ""
                    supabase.table("Clientes").insert({"Nome": nome_cli, "Telefone": tel_cli, "Data de Nascimento": nasc_str}).execute()
                    puxar_dados.clear()
                    st.success(f"✅ Cliente {nome_cli} cadastrado!")
                    time.sleep(1)
                    st.rerun()
                else: st.error("O Nome é obrigatório!")

        st.divider()

        st.markdown("#### ✏️ Editar Cliente")
        df_clientes_edit = puxar_dados('Clientes')
        
        if not df_clientes_edit.empty:
            cliente_selecionado = st.selectbox("Selecione o Cliente para editar:", ["-- Escolha --"] + df_clientes_edit['Nome'].tolist())
            
            if cliente_selecionado != "-- Escolha --":
                dados_atuais_c = df_clientes_edit[df_clientes_edit['Nome'] == cliente_selecionado].iloc[0]
                try: data_nasc_atual = datetime.datetime.strptime(str(dados_atuais_c.get('Data de Nascimento', '')), '%d/%m/%Y').date()
                except: data_nasc_atual = None

                with st.form("form_editar_cliente"):
                    edit_nome_c = st.text_input("Nome", value=str(dados_atuais_c['Nome']))
                    edit_tel_c = st.text_input("Telefone", value=str(dados_atuais_c.get('Telefone', '')))
                    edit_nasc_c = st.date_input("Data de Nascimento", value=data_nasc_atual, min_value=datetime.date(1920, 1, 1))

                    if st.form_submit_button("Atualizar Cliente"):
                        nasc_str_edit = edit_nasc_c.strftime('%d/%m/%Y') if edit_nasc_c else ""
                        supabase.table("Clientes").update({
                            "Nome": edit_nome_c, "Telefone": edit_tel_c, "Data de Nascimento": nasc_str_edit
                        }).eq("id", int(dados_atuais_c['id'])).execute()

                        puxar_dados.clear()
                        st.success("✅ Cliente atualizado com sucesso!")
                        time.sleep(1)
                        st.rerun()

        st.divider()
        st.markdown("#### Lista de Clientes")
        df_clientes = puxar_dados('Clientes')
        if not df_clientes.empty: st.dataframe(df_clientes, use_container_width=True, hide_index=True)
        else: st.info("Nenhum cliente cadastrado ainda.")

    with col_c2:
        st.markdown("#### 🎉 Aniversariantes do Mês")
        if not df_clientes.empty and 'Data de Nascimento' in df_clientes.columns:
            mes_atual = datetime.date.today().month
            aniversariantes = []
            for _, row in df_clientes.iterrows():
                try:
                    data_str = str(row['Data de Nascimento'])
                    if data_str and data_str != 'None':
                        dt_nasc = datetime.datetime.strptime(data_str, '%d/%m/%Y')
                        if dt_nasc.month == mes_atual:
                            aniversariantes.append({'Nome': row['Nome'], 'Dia': dt_nasc.day, 'Whats': row.get('Telefone', '')})
                except: pass
            if aniversariantes:
                aniversariantes.sort(key=lambda x: x['Dia'])
                for aniv in aniversariantes:
                    with st.container(border=True):
                        st.markdown(f"🎂 **Dia {aniv['Dia']:02d}** - {aniv['Nome']}")
                        if aniv['Whats']: st.markdown(f"📱 {aniv['Whats']}")
            else: st.info("Nenhum cliente faz aniversário este mês.")

# -------------------------------------------------------------
# MÓDULO 3: FRENTE DE CAIXA 
# -------------------------------------------------------------
elif menu_selecionado == "🛒 Frente de Caixa":
    st.title("Frente de Caixa (PDV)")
    df_produtos = puxar_dados('Produtos')
    df_clientes = puxar_dados('Clientes')
    lista_clientes = ["Avulso"] + df_clientes['Nome'].tolist() if not df_clientes.empty else ["Avulso"]

    if df_produtos.empty: st.warning("Cadastre Produtos primeiro.")
    else:
        id_pedido = f"PED-{st.session_state.transacao_id}"
        col_topo1, col_topo2 = st.columns([3, 1])
        with col_topo1: cliente_selecionado = st.selectbox("👤 Identificar Cliente (Opcional):", lista_clientes, help="Digite o nome para pesquisar")
        with col_topo2:
            with st.expander("➕ Cadastrar Cliente Rápido"):
                novo_nome = st.text_input("Nome", key="rapido_n")
                novo_zap = st.text_input("WhatsApp", key="rapido_z")
                if st.button("Salvar e Usar"):
                    if novo_nome:
                        supabase.table("Clientes").insert({"Nome": novo_nome, "Telefone": novo_zap, "Data de Nascimento": ""}).execute()
                        puxar_dados.clear() 
                        st.success("Salvo! Recarregue a página.")
        st.markdown("<br>", unsafe_allow_html=True)
        col_pdv_esq, col_pdv_dir = st.columns([6.5, 3.5]) 
        subtotal_pedido, custo_total_pedido, itens_comprados = 0.0, 0.0, []
        with col_pdv_esq:
            st.markdown("#### Lançamento de Itens")
            cols_grid = st.columns(3)
            for idx, row in df_produtos.iterrows():
                preco_padrao = float(row.get('Valor de Venda', 0))
                val_desc = float(row.get('Desconto', 0) if row.get('Desconto', 0) != '' and pd.notna(row.get('Desconto')) else 0.0)
                preco_final = preco_padrao - val_desc
                cat_prod = row.get('Categoria', 'OUTROS') if row.get('Categoria', 'OUTROS') != '' else 'OUTROS'
                with cols_grid[idx % 3]:
                    with st.container(border=True):
                        img_str = row.get('Imagem', '')
                        st.image(img_str if pd.notna(img_str) and img_str != '' else "https://cdn-icons-png.flaticon.com/512/3075/3075977.png", use_container_width=True)
                        st.markdown(f"<div class='pdv-card-title'>{row['Nome do Produto']} <span style='color:#9E9E9E; font-size:10px; font-weight:normal;'>({cat_prod})</span></div>", unsafe_allow_html=True)
                        if val_desc > 0: st.markdown(f"<div class='pdv-card-price'><span class='pdv-card-price-old'>R$ {preco_padrao:.2f}</span><br>R$ {preco_final:.2f}</div>", unsafe_allow_html=True)
                        else: st.markdown(f"<div class='pdv-card-price'><br>R$ {preco_final:.2f}</div>", unsafe_allow_html=True)
                        qtd_vendida = st.number_input("Qtd", min_value=0, step=1, value=0, label_visibility="collapsed", key=f"v_{row['Nome do Produto']}_{st.session_state.transacao_id}")
                        if qtd_vendida > 0:
                            subtotal_pedido += (qtd_vendida * preco_final)
                            custo_total_pedido += (qtd_vendida * float(row['Custo Total']))
                            itens_comprados.append({'nome': row['Nome do Produto'], 'qtd': qtd_vendida, 'preco': preco_final})
        with col_pdv_dir:
            st.markdown("#### Resumo do Pedido")
            with st.container(border=True):
                st.info(f"**Nº do Pedido:** `{id_pedido}`\n\n👤 **Cliente:** `{cliente_selecionado}`")
                data_formatada = st.date_input("Data", label_visibility="collapsed").strftime('%d/%m/%Y')
                st.markdown("---")
                if not itens_comprados: st.write("Nenhum item adicionado.")
                else:
                    for item in itens_comprados: st.write(f"{item['nome']} **x{item['qtd']}**")
                st.markdown("---")
                st.markdown(f"**Subtotal (Valor Cheio):** R$ {subtotal_pedido:.2f}")

        st.divider()
        st.markdown("#### Controles de Pagamento")
        col_pag_esq, col_pag_dir = st.columns([6.5, 3.5])
        with col_pag_esq:
            with st.container(border=True):
                p_col1, p_col2 = st.columns(2)
                with p_col1: 
                    desconto_extra = st.number_input("Desconto Extra (R$)", min_value=0.0, step=0.01, value=0.0, key=f"d_{st.session_state.transacao_id}")
                    val_pix = st.number_input("PIX", min_value=0.0, step=0.01, value=0.0, key=f"p_{st.session_state.transacao_id}")
                    val_debito = st.number_input("Débito", min_value=0.0, step=0.01, value=0.0, key=f"de_{st.session_state.transacao_id}")
                with p_col2:
                    st.write("\n\n") 
                    val_dinheiro = st.number_input("Dinheiro", min_value=0.0, step=0.01, value=0.0, key=f"di_{st.session_state.transacao_id}")
                    val_credito = st.number_input("Crédito", min_value=0.0, step=0.01, value=0.0, key=f"c_{st.session_state.transacao_id}")
        total_a_pagar = subtotal_pedido - desconto_extra
        total_informado = val_pix + val_dinheiro + val_debito + val_credito
        with col_pag_dir:
            st.markdown(f"""<div class="pdv-resumo-box"><div class="pdv-total-text">Total a Cobrar:</div><div class="pdv-total-value">R$ {total_a_pagar:.2f}</div></div>""", unsafe_allow_html=True)
            st.write("") 
            if st.button("✨ Finalizar Venda", use_container_width=True, type="primary"):
                if subtotal_pedido == 0: st.error("Adicione lanches!")
                elif round(total_informado, 2) != round(total_a_pagar, 2): st.error("A soma do pagamento não bate!")
                else:
                    total_taxas = round((val_debito * 0.0198) + (val_credito * 0.0498), 2)
                    lucro_real_final = round((total_a_pagar - total_taxas) - custo_total_pedido, 2)
                    
                    dados_venda = {
                        "Data": data_formatada, "Pedido": id_pedido, 
                        "Itens": ", ".join([f"{i['qtd']}x {i['nome']}" for i in itens_comprados]), 
                        "Subtotal": subtotal_pedido, "Desconto": desconto_extra, "Total Pago": total_a_pagar,
                        "Pix": val_pix, "Dinheiro": val_dinheiro, "Débito": val_debito, "Crédito": val_credito, 
                        "Taxas Cartão": total_taxas, "Valor Líquido": round(total_a_pagar - total_taxas, 2), 
                        "Lucro Real": lucro_real_final, "Cliente": cliente_selecionado
                    }
                    supabase.table("Vendas").insert(dados_venda).execute()
                    
                    puxar_dados.clear() 
                    st.success(f"🎉 Venda salva!")
                    time.sleep(1.5)
                    st.session_state.transacao_id = int(time.time())
                    st.rerun()

# -------------------------------------------------------------
# MÓDULO 4: DESPESAS
# -------------------------------------------------------------
elif menu_selecionado == "💸 Despesas":
    st.title("💸 Gestão de Despesas")
    categorias_despesas = ["👨‍🍳 Folha de Pagamento", "📦 Embalagens & Logística", "💡 Custos Fixos & Estrutura", "📣 Marketing & Software", "🚨 Imprevistos & Manutenção", "🛒 Supermercado (Uso Geral)", "Outros"]
    with st.form("form_despesas", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1: data_despesa = st.date_input("Data do Gasto").strftime('%d/%m/%Y')
        with col_d2: categoria = st.selectbox("Categoria", categorias_despesas)
        descricao = st.text_input("Descrição do Gasto")
        col_d3, col_d4 = st.columns(2)
        with col_d3: valor_despesa = st.number_input("Valor Pago (R$)", min_value=0.01, step=0.01)
        with col_d4: comp_upload = st.file_uploader("🧾 Comprovante", type=['jpg', 'png', 'jpeg'])
        if st.form_submit_button("💰 Lançar Despesa"):
            if descricao and valor_despesa > 0:
                img_b64 = processar_imagem(comp_upload, tamanho=(500, 500), qualidade=60)
                supabase.table("Despesas").insert({"Data": data_despesa, "Categoria": categoria, "Descrição": descricao, "Valor": valor_despesa, "Comprovante": img_b64}).execute()
                puxar_dados.clear() 
                st.success(f"✅ Despesa lançada!")
    st.divider()
    st.markdown("#### Últimas Despesas Lançadas")
    df_lista_despesas = puxar_dados('Despesas')
    if not df_lista_despesas.empty:
        ultimas = df_lista_despesas.tail(10).iloc[::-1]
        c_head1, c_head2, c_head3, c_head4, c_head5 = st.columns([1.5, 2, 3, 1.5, 1.5])
        c_head1.write("**Data**"); c_head2.write("**Categoria**"); c_head3.write("**Descrição**"); c_head4.write("**Valor**"); c_head5.write("**Comp.**")
        st.markdown("<hr style='margin:0px; padding:0px'>", unsafe_allow_html=True)
        for idx, row in ultimas.iterrows():
            c1, c2, c3, c4, c5 = st.columns([1.5, 2, 3, 1.5, 1.5])
            c1.write(f"{row.get('Data', '')}"); c2.write(f"{row.get('Categoria', '')}"); c3.write(f"{row.get('Descrição', '')}")
            try: val_form = float(str(row.get('Valor', 0)).replace(',', '.'))
            except: val_form = 0.0
            c4.write(f"R$ {val_form:.2f}")
            comp_str = row.get('Comprovante', '')
            if pd.notna(comp_str) and comp_str != '':
                with c5:
                    with st.popover("👁️ Abrir"): st.image(comp_str, use_container_width=True)
            else: c5.write("-")
            st.markdown("<hr style='margin:0px; padding:0px; border-color:#F0F0F0'>", unsafe_allow_html=True)

# -------------------------------------------------------------
# MÓDULO 5: PRODUTOS
# -------------------------------------------------------------
elif menu_selecionado == "🍔 Produtos":
    st.title("Gestão do Cardápio")
    categorias_opcoes = ["HAMBÚRGUER", "SANDUBA", "ACOMPANHAMENTO", "BEBIDAS", "CHURRASCO", "COMBOS", "SOBREMESA", "OUTROS"]
    df_insumos = puxar_dados('Insumos')
    if not df_insumos.empty:
        ingredientes_escolhidos = st.multiselect("Ingredientes:", df_insumos['Nome do Insumo'].tolist())
        custo_total_lanche, receita_dict = 0.0, {}
        if ingredientes_escolhidos:
            col1, col2 = st.columns([2, 1]) 
            with col1:
                for item in ingredientes_escolhidos:
                    custo_unitario = float(df_insumos[df_insumos['Nome do Insumo'] == item]['Custo por Porção'].values[0])
                    qtd = st.number_input(f"Qtd de {item}?", min_value=1, step=1, value=1, key=f"prod_{item}")
                    custo_total_lanche += (custo_unitario * qtd)
                    receita_dict[item] = qtd
            with col2: st.info(f"**Custo:**\n### R$ {custo_total_lanche:.2f}")
            
        with st.form("form_produtos", clear_on_submit=True):
            nome_produto = st.text_input("Nome do Produto")
            categoria_produto = st.selectbox("Categoria", categorias_opcoes)
            col_v1, col_v2 = st.columns(2)
            with col_v1: valor_venda = st.number_input("Valor de Venda (R$)", min_value=0.0, step=0.01)
            with col_v2: desconto_produto = st.number_input("Desconto de Combo (R$)", min_value=0.0, step=0.01, value=0.0)
            foto_upload = st.file_uploader("Foto", type=['jpg', 'png', 'jpeg'])
            if st.form_submit_button("Salvar Produto") and nome_produto:
                codigo_gerado = f"PRD-{random.randint(1000, 9999)}"
                preco_final = valor_venda - desconto_produto
                img_b64 = processar_imagem(foto_upload)
                
                supabase.table("Produtos").insert({
                    "Código": codigo_gerado, "Nome do Produto": nome_produto, "Custo Total": custo_total_lanche, 
                    "Valor de Venda": valor_venda, "Lucro Bruto": round(preco_final - custo_total_lanche, 2), 
                    "Receita": json.dumps(receita_dict), "Imagem": img_b64, 
                    "Desconto": desconto_produto, "Categoria": categoria_produto
                }).execute()
                
                puxar_dados.clear() 
                st.success("✅ Produto salvo!")
    st.divider() 
    df_produtos_edit = puxar_dados('Produtos')
    if not df_produtos_edit.empty:
        produto_selecionado = st.selectbox("Selecione Produto:", ["-- Escolha --"] + df_produtos_edit['Nome do Produto'].tolist())
        if produto_selecionado != "-- Escolha --":
            dados_atuais_p = df_produtos_edit[df_produtos_edit['Nome do Produto'] == produto_selecionado].iloc[0]
            val_desc_atual = float(dados_atuais_p.get('Desconto', 0) if dados_atuais_p.get('Desconto', 0) != '' and pd.notna(dados_atuais_p.get('Desconto')) else 0.0)
            cat_atual = dados_atuais_p.get('Categoria', 'OUTROS') if dados_atuais_p.get('Categoria', 'OUTROS') in categorias_opcoes else 'OUTROS'
            with st.form("form_editar_produto"):
                edit_nome_p = st.text_input("Nome", value=str(dados_atuais_p['Nome do Produto']))
                edit_categoria = st.selectbox("Categoria", categorias_opcoes, index=categorias_opcoes.index(cat_atual))
                col_e1, col_e2 = st.columns(2)
                with col_e1: edit_valor_venda = st.number_input("Valor (R$)", value=float(dados_atuais_p['Valor de Venda']), step=0.01)
                with col_e2: edit_desconto = st.number_input("Desconto (R$)", value=val_desc_atual, step=0.01)
                nova_foto_upload = st.file_uploader("Nova Foto", type=['jpg', 'png', 'jpeg'])
                if st.form_submit_button("Atualizar"):
                    lucro_recalculado = round((edit_valor_venda - edit_desconto) - float(dados_atuais_p['Custo Total']), 2)
                    
                    update_data = {
                        "Nome do Produto": edit_nome_p, "Valor de Venda": edit_valor_venda, 
                        "Lucro Bruto": lucro_recalculado, "Desconto": edit_desconto, "Categoria": edit_categoria
                    }
                    if nova_foto_upload is not None: update_data["Imagem"] = processar_imagem(nova_foto_upload)
                    
                    supabase.table("Produtos").update(update_data).eq("id", int(dados_atuais_p['id'])).execute()
                    
                    puxar_dados.clear() 
                    st.success("✅ Atualizado!")

# -------------------------------------------------------------
# MÓDULO 6: INSUMOS
# -------------------------------------------------------------
elif menu_selecionado == "🍅 Insumos":
    st.title("Gestão de Insumos")
    with st.form("form_insumos", clear_on_submit=True):
        nome_insumo = st.text_input("Nome do Insumo (Ex: Pão Brioche)")
        valor_compra = st.number_input("Valor da Compra (R$)", min_value=0.0, step=0.01)
        rendimento = st.number_input("Rendimento (porções)", min_value=1, step=1)
        if st.form_submit_button("Salvar Insumo") and nome_insumo and valor_compra > 0 and rendimento > 0:
            supabase.table("Insumos").insert({
                "Nome do Insumo": nome_insumo, "Valor de Compra": valor_compra, 
                "Rendimento": rendimento, "Custo por Porção": round(valor_compra / rendimento, 2)
            }).execute()
            puxar_dados.clear() 
            st.success(f"✅ Insumo salvo!")
    st.divider() 
    df_insumos_edit = puxar_dados('Insumos')
    if not df_insumos_edit.empty:
        insumo_selecionado = st.selectbox("Selecione o insumo:", ["-- Escolha --"] + df_insumos_edit['Nome do Insumo'].tolist())
        if insumo_selecionado != "-- Escolha --":
            dados_atuais = df_insumos_edit[df_insumos_edit['Nome do Insumo'] == insumo_selecionado].iloc[0]
            with st.form("form_editar_insumo"):
                edit_nome = st.text_input("Nome", value=str(dados_atuais['Nome do Insumo']))
                edit_valor = st.number_input("Novo Valor (R$)", value=float(dados_atuais['Valor de Compra']), step=0.01)
                edit_rend = st.number_input("Novo Rendimento", value=int(dados_atuais['Rendimento']), step=1)
                if st.form_submit_button("Atualizar e Recalcular"):
                    novo_custo_porcao = round(edit_valor / edit_rend, 2)
                    supabase.table("Insumos").update({
                        "Nome do Insumo": edit_nome, "Valor de Compra": edit_valor, 
                        "Rendimento": edit_rend, "Custo por Porção": novo_custo_porcao
                    }).eq("id", int(dados_atuais['id'])).execute()
                    
                    df_produtos_recalc = puxar_dados('Produtos')
                    if not df_produtos_recalc.empty and 'Receita' in df_produtos_recalc.columns:
                        for idx_prod, row_prod in df_produtos_recalc.iterrows():
                            try:
                                receita = json.loads(str(row_prod['Receita']))
                                if insumo_selecionado in receita or edit_nome in receita:
                                    df_insumos_atualizado = pd.DataFrame(supabase.table("Insumos").select("*").execute().data)
                                    novo_custo_total = sum([float(df_insumos_atualizado[df_insumos_atualizado['Nome do Insumo'] == n]['Custo por Porção'].values[0]) * q for n, q in receita.items()])
                                    val_desc_recalc = float(row_prod.get('Desconto', 0) if row_prod.get('Desconto', 0) != '' and pd.notna(row_prod.get('Desconto')) else 0.0)
                                    novo_lucro = round((float(row_prod['Valor de Venda']) - val_desc_recalc) - novo_custo_total, 2)
                                    
                                    supabase.table("Produtos").update({
                                        "Custo Total": round(novo_custo_total, 2), "Lucro Bruto": novo_lucro
                                    }).eq("id", int(row_prod['id'])).execute()
                            except: pass 
                    puxar_dados.clear() 
                    st.success("✅ Insumo e Cardápio recalculados!")

# -------------------------------------------------------------
# MÓDULO 7: LISTA DE COMPRAS E ESTOQUE
# -------------------------------------------------------------
elif menu_selecionado == "📝 Lista de Compras":
    st.title("📝 Lista de Compras e Estoque")
    
    col_l1, col_l2 = st.columns([1, 2])
    
    with col_l1:
        st.markdown("#### ➕ Adicionar à Lista")
        with st.form("form_lista_compras", clear_on_submit=True):
            compra_nome = st.text_input("Nome do Produto (Ex: Maionese Heinz)")
            compra_fornecedor = st.text_input("Fornecedor / Mercado (Opcional)")
            
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                compra_valor = st.number_input("Valor Estimado (R$)", min_value=0.0, step=0.01)
            with c_col2:
                compra_unidade = st.selectbox("Vendido por", ["Unidade", "Caixa", "Kg", "Pacote", "Fardo"])
                
            compra_qtd = st.number_input("Quantidade em Estoque", min_value=0.0, step=0.5, value=0.0)
            
            if st.form_submit_button("Salvar na Lista"):
                if compra_nome:
                    supabase.table("ListaCompras").insert({
                        "Produto": compra_nome, 
                        "Fornecedor": compra_fornecedor, 
                        "Valor": compra_valor, 
                        "Quantidade": compra_qtd, 
                        "Unidade": compra_unidade
                    }).execute()
                    puxar_dados.clear()
                    st.success(f"✅ {compra_nome} adicionado à lista!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("O nome do produto é obrigatório!")

        st.divider()
        st.markdown("#### ✏️ Editar Produto")
        df_compras_edit = puxar_dados('ListaCompras')
        
        if not df_compras_edit.empty:
            item_selecionado = st.selectbox("Selecione o produto para editar:", ["-- Escolha --"] + df_compras_edit['Produto'].tolist())
            
            if item_selecionado != "-- Escolha --":
                dados_item = df_compras_edit[df_compras_edit['Produto'] == item_selecionado].iloc[0]
                
                with st.form("form_edit_compras"):
                    edit_nome_comp = st.text_input("Nome do Produto", value=str(dados_item['Produto']))
                    edit_forn_comp = st.text_input("Fornecedor", value=str(dados_item.get('Fornecedor', '')))
                    
                    e_col1, e_col2 = st.columns(2)
                    with e_col1:
                        edit_val_comp = st.number_input("Valor Estimado (R$)", value=float(dados_item.get('Valor', 0)), step=0.01)
                    with e_col2:
                        opcoes_unid = ["Unidade", "Caixa", "Kg", "Pacote", "Fardo"]
                        idx_unid = opcoes_unid.index(dados_item.get('Unidade', 'Unidade')) if dados_item.get('Unidade', 'Unidade') in opcoes_unid else 0
                        edit_unid_comp = st.selectbox("Vendido por", opcoes_unid, index=idx_unid)
                        
                    edit_qtd_comp = st.number_input("Quantidade em Estoque", value=float(dados_item.get('Quantidade', 0)), step=0.5)
                    
                    if st.form_submit_button("Atualizar Produto"):
                        supabase.table("ListaCompras").update({
                            "Produto": edit_nome_comp,
                            "Fornecedor": edit_forn_comp,
                            "Valor": edit_val_comp,
                            "Quantidade": edit_qtd_comp,
                            "Unidade": edit_unid_comp
                        }).eq("id", int(dados_item['id'])).execute()
                        
                        puxar_dados.clear()
                        st.success("✅ Produto atualizado!")
                        time.sleep(1)
                        st.rerun()

    with col_l2:
        st.markdown("#### 🛒 Situação do Estoque")
        df_compras_view = puxar_dados('ListaCompras')
        
        if not df_compras_view.empty:
            # Multiplica quantidade pelo valor para dar uma previsão de gastos
            custo_estimado = (df_compras_view['Quantidade'] * df_compras_view['Valor']).sum()
            st.info(f"💰 **Valor Estimado em Estoque / Lista:** R$ {custo_estimado:,.2f}")
            
            # Função para pintar as linhas baseado na Quantidade
            def colorir_estoque(valor):
                try:
                    v = float(valor)
                    if v > 5: return 'background-color: #d4edda; color: #155724; font-weight: bold;' # Verde
                    elif v >= 2: return 'background-color: #fff3cd; color: #856404; font-weight: bold;' # Amarelo
                    else: return 'background-color: #f8d7da; color: #721c24; font-weight: bold;' # Vermelho
                except:
                    return ''

            df_estilizado = df_compras_view.drop(columns=['id']).style.map(colorir_estoque, subset=['Quantidade'])
            st.dataframe(df_estilizado, use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.caption("🟢 Acima de 5 | 🟡 Entre 2 e 5 | 🔴 Abaixo de 2")
        else:
            st.info("Sua lista de compras está vazia! Adicione o primeiro item.")
