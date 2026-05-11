import streamlit as st
from curl_cffi import requests
import time
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Robô VIP de Análise", page_icon="🔒", layout="wide")

# ==========================================
# 🔒 SISTEMA DE LOGIN VIP 
# ==========================================
USUARIOS_VIP = {
    "admin": "123456",
    "membro1": "green2024"
}

if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Área Restrita")
        with st.form("form_login"):
            usuario = st.text_input("👤 Usuário")
            senha = st.text_input("🔑 Senha", type="password")
            submit = st.form_submit_button("Entrar no Sistema", use_container_width=True)
            if submit:
                if usuario in USUARIOS_VIP and USUARIOS_VIP[usuario] == senha:
                    st.session_state['logado'] = True
                    st.session_state['usuario'] = usuario
                    st.rerun()
                else:
                    st.error("❌ Usuário ou senha incorretos!")
    st.stop()

# ==========================================
# ⚽ CONFIGURAÇÕES DO MOTOR DE BUSCA
# ==========================================

# Cabeçalhos ultra-reforçados para evitar bloqueio na Nuvem
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache"
}

def buscar_id_do_time(nome_time):
    url = f"https://api.sofascore.com/api/v1/search/all?q={nome_time}&page=0"
    try:
        # Usando impersonate="chrome110" que é mais estável em servidores
        resposta = requests.get(url, headers=HEADERS, impersonate="chrome110", timeout=20)
        if resposta.status_code == 200:
            results = resposta.json().get('results', [])
            times_validos = []
            for resultado in results:
                if resultado.get('type') == 'team':
                    t = resultado['entity']
                    if t.get('sport', {}).get('name') == 'Football':
                        times_validos.append({'id': t['id'], 'name': t['name'], 'seg': t.get('userCount', 0)})
            if times_validos:
                times_validos.sort(key=lambda x: x['seg'], reverse=True)
                return times_validos[0]['id'], times_validos[0]['name']
        elif resposta.status_code == 403:
            st.error("🚫 O site bloqueou o acesso temporariamente. Tente novamente em alguns minutos.")
    except Exception as e:
        st.error(f"⚠️ Erro na conexão: {e}")
    return None, None

def buscar_estatisticas_partida(id_partida):
    url = f"https://api.sofascore.com/api/v1/event/{id_partida}/statistics"
    est = {'escanteios': 0, 'cartoes_amarelos': 0, 'cartoes_vermelhos': 0}
    try:
        resposta = requests.get(url, headers=HEADERS, impersonate="chrome110", timeout=20)
        if resposta.status_code == 200:
            stats_data = resposta.json().get('statistics', [])
            for periodo in stats_data:
                if periodo.get('period') == 'ALL':
                    for grupo in periodo.get('groups', []):
                        for stat in grupo.get('statisticsItems', []):
                            n = stat.get('name', '').lower().strip()
                            try:
                                vc = int(str(stat.get('home', stat.get('homeValue', '0'))).split()[0])
                                vf = int(str(stat.get('away', stat.get('awayValue', '0'))).split()[0])
                            except: vc, vf = 0, 0
                            
                            if n in ['corner kicks', 'escanteios']: est['escanteios'] = vc + vf
                            elif n in ['yellow cards', 'cartões amarelos']: est['cartoes_amarelos'] = vc + vf
                            elif n in ['red cards', 'cartões vermelhos']: est['cartoes_vermelhos'] = vc + vf
    except: pass
    return est

def obter_todos_jogos_recentes(id_time, paginas=3):
    eventos = []
    for p in range(paginas):
        url = f"https://api.sofascore.com/api/v1/team/{id_time}/events/last/{p}"
        try:
            resp = requests.get(url, headers=HEADERS, impersonate="chrome110", timeout=20)
            if resp.status_code == 200:
                eventos.extend(resp.json().get('events', []))
            else: break
        except: break
        time.sleep(0.5)
    eventos.sort(key=lambda x: x.get('startTimestamp', 0), reverse=True)
    return eventos

# --- INTERFACE ---
with st.sidebar:
    st.success(f"✅ VIP: **{st.session_state['usuario'].upper()}**")
    if st.button("🚪 Sair"):
        st.session_state.clear()
        st.rerun()

st.title("⚽ Máquina de Análise VIP")

aba1, aba2 = st.tabs(["📊 Analisar Time", "⚔️ Confronto Direto"])

with aba1:
    c1, c2 = st.columns(2)
    time_alvo = c1.text_input("Nome do time:", key="t1")
    qtd_jogos = c2.number_input("Jogos:", 5, 30, 10, key="q1")
    
    if st.button("🚀 Iniciar Análise", type="primary"):
        id_t, nome_f = buscar_id_do_time(time_alvo)
        if id_t:
            st.write(f"### Analisando: {nome_f}")
            eventos = obter_todos_jogos_recentes(id_t)
            
            cont, tabela, stt = 0, [], {'o15':0, 'o25':0, 'btts':0, 'esc':0, 'car':0}
            prog = st.progress(0)
            
            for jogo in eventos:
                if cont >= qtd_jogos: break
                if jogo['status']['type'] == 'finished':
                    id_p = jogo['id']
                    gc, gf = jogo['homeScore'].get('current', 0), jogo['awayScore'].get('current', 0)
                    data = datetime.fromtimestamp(jogo['startTimestamp']).strftime('%d/%m/%Y')
                    
                    est = buscar_estatisticas_partida(id_p)
                    
                    soma = gc + gf
                    if soma >= 2: stt['o15']+=1
                    if soma >= 3: stt['o25']+=1
                    if gc > 0 and gf > 0: stt['btts']+=1
                    if est['escanteios'] >= 9: stt['esc']+=1
                    if (est['cartoes_amarelos'] + est['cartoes_vermelhos']) >= 5: stt['car']+=1
                    
                    tabela.append({
                        "Data": data,
                        "Casa": jogo['homeTeam']['name'], "Placar": f"{gc} x {gf}", "Fora": jogo['awayTeam']['name'],
                        "🚩 Esc": est['escanteios'], "🟨 Card": est['cartoes_amarelos'] + est['cartoes_vermelhos']
                    })
                    cont += 1
                    prog.progress(cont/qtd_jogos)
                    time.sleep(0.2)
            
            st.divider()
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Over 1.5", f"{(stt['o15']/cont)*100:.0f}%")
            m2.metric("Over 2.5", f"{(stt['o25']/cont)*100:.0f}%")
            m3.metric("BTTS", f"{(stt['btts']/cont)*100:.0f}%")
            m4.metric("Esc 9+", f"{(stt['esc']/cont)*100:.0f}%")
            m5.metric("Card 5+", f"{(stt['car']/cont)*100:.0f}%")
            st.dataframe(tabela, use_container_width=True)
        else:
            st.warning("Time não encontrado ou erro de conexão.")

# (Aba 2 segue a mesma lógica de busca simplificada se desejar)
