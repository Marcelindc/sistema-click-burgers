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
    .card-despesas { border-left: 6px solid #E31837; } 
    .card-taxas { border-left: 6px solid #E31837; } 
    .pdv-card-title { font-size: 16px; font-weight: bold; color: #1E1E1E; margin-bottom: 2px; line-height: 1.2; height: 38px; overflow: hidden;}
    .pdv-card-price { font-size: 15px; color: #E31837; font-weight: bold; margin-bottom: 10px; }
    .pdv-card-price-old { font-size: 12px; color: #9E9E9E; text-decoration: line-through; }
    .pdv-resumo-box { background-color: #FFFFFF; padding: 20px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.03); border: 1px solid #EAEAEA; }
    .pdv-total-text { font-size: 24px; font-weight: 900; text-align: center; color: #1E1E1E; }
    .pdv-total-value { font-size: 36px; font-weight: 900; text-align: center; color: #E31837; }
    .login-box { background-color: white; padding: 40px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; }
    </style>
""", unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

try: supabase = init_connection()
except: st.error("Erro no Banco de Dados."); st.stop()

@st.cache_data(ttl=5)
def puxar_dados(tabela):
    try: return pd.DataFrame(supabase.table(tabela).select("*").execute().data)
    except: return pd.DataFrame()

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
            usuario_input = st.text_input("Usuário")
            senha_input = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar no Sistema", use_container_width=True, type="primary")
            if submit_login:
                df_usuarios = puxar_dados('Usuarios') 
                if not df_usuarios.empty:
                    df_usuarios['Usuario'] = df_usuarios['Usuario'].astype(str).str.strip()
                    df_usuarios['Senha'] = df_usuarios['Senha'].astype(str).str.strip()
                    match = df_usuarios[(df_usuarios['Usuario'] == usuario_input.strip()) & (df_usuarios['Senha'] == senha_input.strip())]
                    if not match.empty:
                        st.session_state["autenticado"] = True
                        st.session_state["usuario_logado"] = usuario_input.strip()
                        st.session_state["nome_logado"] = str(match['Nome'].values[0]).strip() if 'Nome' in df_usuarios.columns else usuario_input.strip()
                        st.rerun() 
                    else: st.error("❌ Credenciais incorretas!")
    st.stop() 

def processar_imagem(uploaded_file, tamanho=(250, 250), qualidade=70):
    if uploaded_file:
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
    st.success(f"👤 Olá, **{st.session_state.get('nome_logado', '')}**!")
    
    opcoes_menu = ["📊 Dashboard", "🛒 Frente de Caixa", "👥 Clientes", "🍔 Produtos", "📦 Estoque & Compras", "💸 Despesas"]
    menu_selecionado = st.radio("", opcoes_menu, label_visibility="collapsed")
    st.markdown("---")
    if st.button("🚪 Sair (Logout)", use_container_width=True):
        st.session_state["autenticado"] = False
        puxar_dados.clear() 
        st.rerun()
    st.caption("Sistema ERP v4.0 - Click Burgers")

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
        dict_precos = {r['Nome do Produto']: float(r.get('Valor de Venda', 0)) - float(r.get('Desconto', 0) if r.get('Desconto', 0) != '' and pd.notna(r.get('Desconto')) else 0.0) for _, r in df_produtos_atual.iterrows()}

        with st.container():
            st.markdown("#### Filtros de Análise")
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1: data_inicio = st.date_input("Data Inicial", df_vendas['Data'].min().date())
            with col_f2: data_fim = st.date_input("Data Final", datetime.date.today())
            with col_f3: produtos_filtrados = st.multiselect("Filtrar por Lanches:", list(dict_precos.keys()), placeholder="Todos")
        
        df_filtrado = df_vendas[(df_vendas['Data'] >= pd.to_datetime(data_inicio)) & (df_vendas['Data'] <= pd.to_datetime(data_fim))]
        
        total_despesas_periodo = 0.0
        if not df_despesas.empty:
            mascara_desp = (df_despesas['Data'] >= pd.to_datetime(data_inicio)) & (df_despesas['Data'] <= pd.to_datetime(data_fim))
            try: total_despesas_periodo = df_despesas.loc[mascara_desp]['Valor'].apply(lambda x: float(str(x).replace(',', '.'))).sum()
            except: total_despesas_periodo = df_despesas.loc[mascara_desp]['Valor'].sum()
        
        if not df_filtrado.empty:
            dados_itens = []
            for idx, row in df_filtrado.iterrows():
                subtotal_pedido = float(str(row.get('Subtotal', 0)).replace(',', '.'))
                taxas_pedido = float(str(row.get('Taxas Cartão', 0)).replace(',', '.'))
                lucro_pedido = float(str(row.get('Lucro Real', 0)).replace(',', '.'))
                cliente_nome = str(row.get('Cliente', 'Avulso'))
                for lanche in str(row['Itens']).split(', '):
                    match = re.match(r'(\d+)x\s+(.+)', lanche)
                    if match:
                        qtd, nome = int(match.group(1)), match.group(2)
                        receita_item = qtd * dict_precos.get(nome, 0)
                        peso = (receita_item / subtotal_pedido) if subtotal_pedido > 0 else 0
                        dados_itens.append({'Lanche': nome, 'Quantidade': qtd, 'Receita': receita_item, 'Lucro Proporcional': lucro_pedido * peso, 'Taxa Proporcional': taxas_pedido * peso, 'Cliente': cliente_nome})
            
            if produtos_filtrados:
                df_itens_filtrado = pd.DataFrame(dados_itens)[pd.DataFrame(dados_itens)['Lanche'].isin(produtos_filtrados)]
                vendas_totais_kpi, lucro_kpi, taxas_kpi = df_itens_filtrado['Receita'].sum(), df_itens_filtrado['Lucro Proporcional'].sum(), df_itens_filtrado['Taxa Proporcional'].sum()
                margem_kpi = (lucro_kpi / vendas_totais_kpi * 100) if vendas_totais_kpi > 0 else 0
            else:
                vendas_totais_kpi = df_filtrado['Total Pago'].sum()
                taxas_kpi = df_filtrado['Taxas Cartão'].sum()
                lucro_kpi = df_filtrado['Lucro Real'].sum() - total_despesas_periodo
                margem_kpi = (lucro_kpi / vendas_totais_kpi * 100) if vendas_totais_kpi > 0 else 0

            k1, k2, k3, k4 = st.columns(4)
            k1.markdown(f"""<div class="click-kpi-card card-faturamento"><div class="click-kpi-title">Faturamento</div><div class="click-kpi-value">R$ {vendas_totais_kpi:,.2f}</div></div>""", unsafe_allow_html=True)
            k2.markdown(f"""<div class="click-kpi-card card-lucro"><div class="click-kpi-title">Lucro Líquido</div><div class="click-kpi-value">R$ {lucro_kpi:,.2f}</div></div>""", unsafe_allow_html=True)
            k3.markdown(f"""<div class="click-kpi-card card-despesas"><div class="click-kpi-title">Despesas</div><div class="click-kpi-value">- R$ {total_despesas_periodo:,.2f}</div></div>""", unsafe_allow_html=True)
            k4.markdown(f"""<div class="click-kpi-card card-taxas"><div class="click-kpi-title">Margem</div><div class="click-kpi-value">{margem_kpi:,.1f}%</div></div>""", unsafe_allow_html=True)
            
            st.markdown("#### Evolução de Faturamento por Dia")
            df_linha = df_filtrado.groupby('Data')['Total Pago'].sum().reset_index()
            df_linha['Data_Formatada'] = df_linha['Data'].dt.strftime('%d/%m/%Y')
            fig_linha = px.line(df_linha, x='Data_Formatada', y='Total Pago', markers=True)
            fig_linha.update_traces(line=dict(color='#E31837', width=3), marker=dict(size=8, color='#E31837', line=dict(width=2, color='white')), fill='tozeroy', fillcolor='rgba(227, 24, 55, 0.1)', hovertemplate='Data: %{x}<br>Total: R$ %{y:.2f}') 
            fig_linha.update_layout(plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF', xaxis_title="", yaxis_title="R$", height=320, margin=dict(l=0, r=0, t=20, b=0), xaxis=dict(showgrid=False, type='category'), yaxis=dict(showgrid=True, gridcolor='#F0F0F0'))
            st.plotly_chart(fig_linha, use_container_width=True)

# -------------------------------------------------------------
# MÓDULO 2: FRENTE DE CAIXA 
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
        with col_topo1: cliente_selecionado = st.selectbox("👤 Identificar Cliente (Opcional):", lista_clientes)
        with col_topo2:
            with st.expander("➕ Cadastrar Cliente Rápido"):
                novo_nome = st.text_input("Nome", key="rapido_n")
                novo_zap = st.text_input("WhatsApp", key="rapido_z")
                if st.button("Salvar e Usar"):
                    supabase.table("Clientes").insert({"Nome": novo_nome, "Telefone": novo_zap, "Data de Nascimento": ""}).execute()
                    puxar_dados.clear(); st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        col_pdv_esq, col_pdv_dir = st.columns([6.5, 3.5]) 
        subtotal_pedido, custo_total_pedido, itens_comprados = 0.0, 0.0, []
        with col_pdv_esq:
            st.markdown("#### Lançamento de Itens")
            cols_grid = st.columns(3)
            for idx, row in df_produtos.iterrows():
                preco_padrao = float(row.get('Valor de Venda', 0))
                val_desc = float(row.get('Desconto', 0) if pd.notna(row.get('Desconto')) and str(row.get('Desconto')) != '' else 0.0)
                preco_final = preco_padrao - val_desc
                cat_prod = row.get('Categoria', 'OUTROS')
                with cols_grid[idx % 3]:
                    with st.container(border=True):
                        st.image(row.get('Imagem', '') if pd.notna(row.get('Imagem')) and str(row.get('Imagem')) != '' else "https://cdn-icons-png.flaticon.com/512/3075/3075977.png", use_container_width=True)
                        st.markdown(f"<div class='pdv-card-title'>{row['Nome do Produto']} <span style='color:#9E9E9E; font-size:10px;'>({cat_prod})</span></div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='pdv-card-price'>R$ {preco_final:.2f}</div>", unsafe_allow_html=True)
                        qtd_vendida = st.number_input("Qtd", min_value=0, step=1, value=0, label_visibility="collapsed", key=f"v_{row['id']}_{st.session_state.transacao_id}")
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
                for item in itens_comprados: st.write(f"{item['nome']} **x{item['qtd']}**")
                st.markdown("---")
                st.markdown(f"**Subtotal:** R$ {subtotal_pedido:.2f}")
                
                desconto_extra = st.number_input("Desconto Extra (R$)", min_value=0.0, step=0.01, value=0.0)
                total_a_pagar = subtotal_pedido - desconto_extra
                st.markdown(f"""<div class="pdv-resumo-box"><div class="pdv-total-text">Total a Cobrar:</div><div class="pdv-total-value">R$ {total_a_pagar:.2f}</div></div>""", unsafe_allow_html=True)
                
                st.markdown("##### Forma de Pagamento")
                p_c1, p_c2 = st.columns(2)
                with p_c1: val_pix = st.number_input("PIX", min_value=0.0, step=0.01, value=0.0)
                with p_c1: val_dinheiro = st.number_input("Dinheiro", min_value=0.0, step=0.01, value=0.0)
                with p_c2: val_debito = st.number_input("Débito", min_value=0.0, step=0.01, value=0.0)
                with p_c2: val_credito = st.number_input("Crédito", min_value=0.0, step=0.01, value=0.0)
                
                total_informado = val_pix + val_dinheiro + val_debito + val_credito
                
                if st.button("✨ Finalizar Venda", use_container_width=True, type="primary"):
                    if subtotal_pedido == 0: st.error("Adicione lanches!")
                    elif round(total_informado, 2) != round(total_a_pagar, 2): st.error("A soma do pagamento não bate!")
                    else:
                        total_taxas = round((val_debito * 0.0198) + (val_credito * 0.0498), 2)
                        lucro_real_final = round((total_a_pagar - total_taxas) - custo_total_pedido, 2)
                        # Dá baixa no Estoque dos Insumos usados nos Lanches!
                        df_insumos = puxar_dados("Insumos")
                        for item in itens_comprados:
                            receita_str = df_produtos[df_produtos['Nome do Produto'] == item['nome']].iloc[0]['Receita']
                            try:
                                receita_dict = json.loads(receita_str)
                                for nome_insumo, qtd_usada_na_receita in receita_dict.items():
                                    linha_insumo = df_insumos[df_insumos['Nome do Insumo'] == nome_insumo]
                                    if not linha_insumo.empty:
                                        estoque_antigo = float(linha_insumo.iloc[0].get('Estoque Atual', 0))
                                        estoque_novo = estoque_antigo - (qtd_usada_na_receita * item['qtd'])
                                        supabase.table("Insumos").update({"Estoque Atual": estoque_novo}).eq("id", int(linha_insumo.iloc[0]['id'])).execute()
                            except: pass

                        supabase.table("Vendas").insert({
                            "Data": data_formatada, "Pedido": id_pedido, 
                            "Itens": ", ".join([f"{i['qtd']}x {i['nome']}" for i in itens_comprados]), 
                            "Subtotal": subtotal_pedido, "Desconto": desconto_extra, "Total Pago": total_a_pagar,
                            "Pix": val_pix, "Dinheiro": val_dinheiro, "Débito": val_debito, "Crédito": val_credito, 
                            "Taxas Cartão": total_taxas, "Valor Líquido": round(total_a_pagar - total_taxas, 2), 
                            "Lucro Real": lucro_real_final, "Cliente": cliente_selecionado
                        }).execute()
                        puxar_dados.clear() 
                        st.success(f"🎉 Venda salva e estoque atualizado!")
                        time.sleep(1.5)
                        st.session_state.transacao_id = int(time.time()); st.rerun()

# -------------------------------------------------------------
# MÓDULO 3: ESTOQUE E COMPRAS (O SUPER MÓDULO)
# -------------------------------------------------------------
elif menu_selecionado == "📦 Estoque & Compras":
    st.title("📦 Gestão de Estoque e Compras")
    aba1, aba2, aba3 = st.tabs(["📊 Visão Geral do Estoque", "🛒 Planejar Lista de Compras", "📱 Modo Supermercado (Carrinho)"])
    
    # GARANTIR QUE AS COLUNAS EXISTEM (MVP)
    df_insumos = puxar_dados('Insumos')
    
    with aba1:
        st.markdown("#### Situação Atual do Estoque")
        col_e1, col_e2 = st.columns([2, 1])
        with col_e1:
            if not df_insumos.empty:
                # Trata dados vazios
                df_insumos['Estoque Atual'] = df_insumos.get('Estoque Atual', 0).fillna(0)
                df_insumos['Estoque Minimo'] = df_insumos.get('Estoque Minimo', 5).fillna(5)
                df_insumos['Unidade'] = df_insumos.get('Unidade', 'Unidade').fillna('Unidade')
                
                df_view = df_insumos[['Nome do Insumo', 'Estoque Atual', 'Unidade', 'Estoque Minimo']].copy()
                
                def colorir_estoque(row):
                    try:
                        atual = float(row['Estoque Atual'])
                        minimo = float(row['Estoque Minimo'])
                        if atual <= (minimo * 0.5): return ['background-color: #f8d7da; color: #721c24; font-weight: bold;'] * len(row) # Vermelho (Crítico)
                        elif atual <= minimo: return ['background-color: #fff3cd; color: #856404; font-weight: bold;'] * len(row) # Amarelo (Atenção)
                        else: return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row) # Verde (Tranquilo)
                    except: return [''] * len(row)

                df_estilizado = df_view.style.apply(colorir_estoque, axis=1)
                st.dataframe(df_estilizado, use_container_width=True, hide_index=True)
                st.caption("🟢 Acima do Mínimo | 🟡 Perto do Mínimo | 🔴 Crítico")
            else: st.info("Cadastre ingredientes na aba Insumos primeiro.")
            
        with col_e2:
            st.markdown("#### ✏️ Editar Estoque/Mínimo")
            if not df_insumos.empty:
                item_edit = st.selectbox("Selecione o Insumo:", ["-- Escolha --"] + df_insumos['Nome do Insumo'].tolist())
                if item_edit != "-- Escolha --":
                    dados_ins = df_insumos[df_insumos['Nome do Insumo'] == item_edit].iloc[0]
                    with st.form("form_edit_est"):
                        e_est = st.number_input("Estoque Atual", value=float(dados_ins.get('Estoque Atual', 0)), step=0.5)
                        e_min = st.number_input("Estoque Mínimo", value=float(dados_ins.get('Estoque Minimo', 5)), step=0.5)
                        e_uni = st.text_input("Unidade (Ex: Cx, Kg, Unid)", value=str(dados_ins.get('Unidade', 'Unidade')))
                        if st.form_submit_button("Atualizar Estoque"):
                            supabase.table("Insumos").update({"Estoque Atual": e_est, "Estoque Minimo": e_min, "Unidade": e_uni}).eq("id", int(dados_ins['id'])).execute()
                            puxar_dados.clear(); st.success("✅ Atualizado!"); time.sleep(1); st.rerun()

    with aba2:
        st.markdown("#### 🛒 Adicionar à Lista de Compras")
        df_carrinho = puxar_dados("CarrinhoCompras")
        
        if not df_insumos.empty:
            with st.form("form_add_lista"):
                itens_precisando = df_insumos[df_insumos['Estoque Atual'].astype(float) <= df_insumos['Estoque Minimo'].astype(float)]['Nome do Insumo'].tolist()
                st.info(f"💡 **Sugestão do Sistema:** {len(itens_precisando)} itens estão no vermelho ou amarelo.")
                
                insumo_selecionado = st.selectbox("Produto para comprar:", df_insumos['Nome do Insumo'].tolist())
                qtd_comprar = st.number_input("Quantidade que vai comprar:", min_value=0.5, step=0.5, value=1.0)
                
                if st.form_submit_button("➕ Adicionar à Lista"):
                    supabase.table("CarrinhoCompras").insert({"Insumo": insumo_selecionado, "Qtd Desejada": qtd_comprar, "Comprado": False, "Valor Pago": 0, "Qtd Comprada": 0}).execute()
                    puxar_dados.clear(); st.success(f"{insumo_selecionado} na lista!"); time.sleep(1); st.rerun()
                    
        st.divider()
        st.markdown("##### Itens Atuais na Lista (Planejamento)")
        if not df_carrinho.empty:
            pendentes = df_carrinho[df_carrinho['Comprado'] == False]
            if not pendentes.empty:
                for idx, row in pendentes.iterrows():
                    col_p1, col_p2 = st.columns([4, 1])
                    col_p1.write(f"🛒 **{row['Insumo']}** (Desejado: {row['Qtd Desejada']})")
                    if col_p2.button("❌ Remover", key=f"del_plan_{row['id']}"):
                        supabase.table("CarrinhoCompras").delete().eq("id", int(row['id'])).execute()
                        puxar_dados.clear(); st.rerun()
            else: st.write("Nenhum item pendente.")
        else: st.write("Lista vazia.")

    with aba3:
        st.markdown("#### 📱 Modo Supermercado (Pelo Celular)")
        st.caption("Quando colocar no carrinho físico, preencha os dados e clique em Peguei.")
        df_carrinho_mercado = puxar_dados("CarrinhoCompras")
        
        if not df_carrinho_mercado.empty:
            pendentes_mercado = df_carrinho_mercado[df_carrinho_mercado['Comprado'] == False]
            for idx, row in pendentes_mercado.iterrows():
                with st.container(border=True):
                    st.markdown(f"**{row['Insumo']}**")
                    m_c1, m_c2, m_c3 = st.columns(3)
                    with m_c1: qtd_real = st.number_input("Qtd Pega", value=float(row['Qtd Desejada']), step=0.5, key=f"q_{row['id']}")
                    with m_c2: valor_real = st.number_input("R$ Total", value=0.0, step=0.01, key=f"v_{row['id']}")
                    with m_c3:
                        st.write("")
                        if st.button("✅ Peguei", key=f"peguei_{row['id']}"):
                            supabase.table("CarrinhoCompras").update({"Comprado": True, "Qtd Comprada": qtd_real, "Valor Pago": valor_real}).eq("id", int(row['id'])).execute()
                            puxar_dados.clear(); st.rerun()
            
            st.divider()
            prontos = df_carrinho_mercado[df_carrinho_mercado['Comprado'] == True]
            if not prontos.empty:
                total_gasto = prontos['Valor Pago'].sum()
                st.success(f"🛒 Itens no Carrinho: {len(prontos)} | **Total Gasto: R$ {total_gasto:.2f}**")
                
                if st.button("🏁 Passar no Caixa (Finalizar Compra)", type="primary", use_container_width=True):
                    # 1. Dar entrada no Estoque & 2. Apagar da lista
                    for idx, row in prontos.iterrows():
                        insumo = df_insumos[df_insumos['Nome do Insumo'] == row['Insumo']]
                        if not insumo.empty:
                            novo_estoque = float(insumo.iloc[0].get('Estoque Atual', 0)) + float(row['Qtd Comprada'])
                            novo_custo_porcao = round(float(row['Valor Pago']) / float(insumo.iloc[0]['Rendimento']), 2) if float(row['Valor Pago']) > 0 else float(insumo.iloc[0]['Custo por Porção'])
                            supabase.table("Insumos").update({"Estoque Atual": novo_estoque, "Valor de Compra": float(row['Valor Pago']), "Custo por Porção": novo_custo_porcao}).eq("id", int(insumo.iloc[0]['id'])).execute()
                        supabase.table("CarrinhoCompras").delete().eq("id", int(row['id'])).execute()
                    
                    # 3. Lançar em Despesas
                    supabase.table("Despesas").insert({"Data": datetime.date.today().strftime('%d/%m/%Y'), "Categoria": "🛒 Supermercado (Uso Geral)", "Descrição": f"Compra Estoque ({len(prontos)} itens)", "Valor": total_gasto, "Comprovante": ""}).execute()
                    
                    puxar_dados.clear()
                    st.balloons()
                    st.success("Compra finalizada! Estoque atualizado e despesa lançada automaticamente.")
                    time.sleep(3); st.rerun()

# -------------------------------------------------------------
# OUTROS MÓDULOS (Clientes, Produtos, Despesas)
# -------------------------------------------------------------
elif menu_selecionado == "👥 Clientes":
    st.title("👥 Gestão de Clientes e CRM")
    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        with st.expander("➕ Cadastrar Novo Cliente", expanded=True):
            with st.form("form_cliente", clear_on_submit=True):
                nome_cli, tel_cli = st.text_input("Nome Completo"), st.text_input("Telefone")
                nasc_cli = st.date_input("Nascimento (Opcional)", value=None, min_value=datetime.date(1920, 1, 1))
                if st.form_submit_button("Salvar"):
                    if nome_cli:
                        supabase.table("Clientes").insert({"Nome": nome_cli, "Telefone": tel_cli, "Data de Nascimento": nasc_cli.strftime('%d/%m/%Y') if nasc_cli else ""}).execute()
                        puxar_dados.clear(); st.success("✅ Cadastrado!"); time.sleep(1); st.rerun()
        df_clientes = puxar_dados('Clientes')
        if not df_clientes.empty:
            with st.expander("✏️ Editar Cliente"):
                c_edit = st.selectbox("Selecione:", ["-- Escolha --"] + df_clientes['Nome'].tolist())
                if c_edit != "-- Escolha --":
                    d_c = df_clientes[df_clientes['Nome'] == c_edit].iloc[0]
                    with st.form("f_edit_c"):
                        en_c = st.text_input("Nome", value=str(d_c['Nome']))
                        et_c = st.text_input("Tel", value=str(d_c.get('Telefone', '')))
                        if st.form_submit_button("Atualizar"):
                            supabase.table("Clientes").update({"Nome": en_c, "Telefone": et_c}).eq("id", int(d_c['id'])).execute()
                            puxar_dados.clear(); st.rerun()
            st.dataframe(df_clientes, use_container_width=True, hide_index=True)

elif menu_selecionado == "🍔 Produtos":
    st.title("Gestão do Cardápio")
    df_insumos = puxar_dados('Insumos')
    if not df_insumos.empty:
        ingredientes_escolhidos = st.multiselect("Montar Receita (Insumos):", df_insumos['Nome do Insumo'].tolist())
        custo_total_lanche, receita_dict = 0.0, {}
        if ingredientes_escolhidos:
            col1, col2 = st.columns([2, 1]) 
            with col1:
                for item in ingredientes_escolhidos:
                    custo_u = float(df_insumos[df_insumos['Nome do Insumo'] == item]['Custo por Porção'].values[0])
                    qtd = st.number_input(f"Qtd de {item}?", min_value=1, step=1, value=1, key=f"prod_{item}")
                    custo_total_lanche += (custo_u * qtd)
                    receita_dict[item] = qtd
            col2.info(f"**Custo:**\n### R$ {custo_total_lanche:.2f}")
            
        with st.form("form_produtos", clear_on_submit=True):
            nome_p = st.text_input("Nome do Lanche")
            cat_p = st.selectbox("Categoria", ["HAMBÚRGUER", "ACOMPANHAMENTO", "BEBIDAS", "OUTROS"])
            v_venda = st.number_input("Valor (R$)", step=0.01)
            v_desc = st.number_input("Desconto (R$)", step=0.01)
            f_up = st.file_uploader("Foto", type=['jpg', 'png'])
            if st.form_submit_button("Salvar Produto") and nome_p:
                supabase.table("Produtos").insert({"Código": f"PRD-{random.randint(1000, 9999)}", "Nome do Produto": nome_p, "Custo Total": custo_total_lanche, "Valor de Venda": v_venda, "Lucro Bruto": round((v_venda - v_desc) - custo_total_lanche, 2), "Receita": json.dumps(receita_dict), "Imagem": processar_imagem(f_up), "Desconto": v_desc, "Categoria": cat_p}).execute()
                puxar_dados.clear(); st.success("✅ Salvo!")

    st.divider() 
    df_produtos_edit = puxar_dados('Produtos')
    if not df_produtos_edit.empty:
        p_sel = st.selectbox("Editar Produto:", ["-- Escolha --"] + df_produtos_edit['Nome do Produto'].tolist())
        if p_sel != "-- Escolha --":
            d_p = df_produtos_edit[df_produtos_edit['Nome do Produto'] == p_sel].iloc[0]
            with st.form("form_editar_p"):
                e_nome = st.text_input("Nome", value=str(d_p['Nome do Produto']))
                e_v = st.number_input("Valor (R$)", value=float(d_p['Valor de Venda']), step=0.01)
                e_d = st.number_input("Desconto (R$)", value=float(d_p.get('Desconto', 0) if pd.notna(d_p.get('Desconto')) else 0), step=0.01)
                if st.form_submit_button("Atualizar"):
                    supabase.table("Produtos").update({"Nome do Produto": e_nome, "Valor de Venda": e_v, "Desconto": e_d, "Lucro Bruto": round((e_v - e_d) - float(d_p['Custo Total']), 2)}).eq("id", int(d_p['id'])).execute()
                    puxar_dados.clear(); st.success("✅ Atualizado!"); time.sleep(1); st.rerun()

elif menu_selecionado == "💸 Despesas":
    st.title("💸 Gestão de Despesas")
    with st.form("form_despesas", clear_on_submit=True):
        col_d1, col_d2 = st.columns(2)
        with col_d1: dt_desp = st.date_input("Data").strftime('%d/%m/%Y')
        with col_d2: cat_desp = st.selectbox("Categoria", ["👨‍🍳 Folha", "💡 Custos Fixos", "🛒 Supermercado", "Outros"])
        desc_desp = st.text_input("Descrição")
        val_desp = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
        if st.form_submit_button("💰 Lançar Despesa") and desc_desp:
            supabase.table("Despesas").insert({"Data": dt_desp, "Categoria": cat_desp, "Descrição": desc_desp, "Valor": val_desp, "Comprovante": ""}).execute()
            puxar_dados.clear(); st.success("✅ Lançada!")
    st.divider()
    df_lista_despesas = puxar_dados('Despesas')
    if not df_lista_despesas.empty: st.dataframe(df_lista_despesas.tail(10).iloc[::-1], use_container_width=True, hide_index=True)
