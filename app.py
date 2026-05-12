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
    "membro1": "green2024",
    "joao": "vasco123"
}

if 'logado' not in st.session_state:
    st.session_state['logado'] = False

if not st.session_state['logado']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔒 Área Restrita")
        st.markdown("Bem-vindo ao Motor de Tendências VIP. Faça o login para acessar.")
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
# ⚽ CONFIGURAÇÕES DO MOTOR DE BUSCA (DISFARCE DE IPHONE)
# ==========================================
HEADERS = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Accept": "*/*",
    "Accept-Language": "pt-BR,pt;q=0.9",
    "Origin": "https://www.sofascore.com",
    "Referer": "https://www.sofascore.com/",
    "Connection": "keep-alive"
}

def buscar_id_do_time(nome_time):
    url = f"https://api.sofascore.com/api/v1/search/all?q={nome_time}&page=0"
    try:
        # Usando impersonate de Safari (iPhone)
        resposta = requests.get(url, headers=HEADERS, impersonate="safari15_5", timeout=20)
        if resposta.status_code == 200:
            times_validos = []
            for resultado in resposta.json().get('results', []):
                if resultado.get('type') == 'team':
                    t = resultado['entity']
                    nome = t.get('name', '')
                    esp = t.get('sport', {}).get('name', '').lower()
                    cat = t.get('category', {}).get('name', '').lower()
                    if esp in ['football', 'futebol'] and 'esoccer' not in cat and 'amateur' not in cat:
                        if not any(x in nome.lower() for x in ['u20', 'u19', 'u17', 'feminino', 'women', ' b', 'esports']):
                            times_validos.append({'id': t['id'], 'name': nome, 'seg': t.get('userCount', 0)})
            if times_validos:
                times_validos.sort(key=lambda x: x['seg'], reverse=True)
                return times_validos[0]['id'], times_validos[0]['name']
        elif resposta.status_code == 403:
            st.error("🚫 O site bloqueou o acesso temporariamente. O disfarce falhou.")
    except Exception as e:
        st.error(f"⚠️ Erro de conexão: {e}")
    return None, None

def buscar_estatisticas_partida(id_partida):
    url = f"https://api.sofascore.com/api/v1/event/{id_partida}/statistics"
    est = {'escanteios': 0, 'cartoes_amarelos': 0, 'cartoes_vermelhos': 0}
    try:
        resposta = requests.get(url, headers=HEADERS, impersonate="safari15_5", timeout=20)
        if resposta.status_code == 200:
            for periodo in resposta.json().get('statistics', []):
                if periodo.get('period') == 'ALL':
                    for grupo in periodo.get('groups', []):
                        for stat in grupo.get('statisticsItems', []):
                            n = stat.get('name', '').lower().strip()
                            try:
                                vc = int(str(stat.get('home', stat.get('homeValue', '0'))).split()[0])
                                vf = int(str(stat.get('away', stat.get('awayValue', '0'))).split()[0])
                            except: vc, vf = 0, 0
                            
                            if n in ['corner kicks', 'escanteios']: est['escanteios'] = vc + vf
                            elif n in ['yellow cards', 'cartões amarelos', 'cartoes amarelos']: est['cartoes_amarelos'] = vc + vf
                            elif n in ['red cards', 'cartões vermelhos', 'cartoes vermelhos']: est['cartoes_vermelhos'] = vc + vf
    except: pass
    return est

def obter_todos_jogos_recentes(id_time, paginas=4):
    eventos = []
    for p in range(paginas):
        url = f"https://api.sofascore.com/api/v1/team/{id_time}/events/last/{p}"
        try:
            resp = requests.get(url, headers=HEADERS, impersonate="safari15_5", timeout=20)
            if resp.status_code == 200: eventos.extend(resp.json().get('events', []))
            else: break
        except: break
        time.sleep(0.5)
    eventos.sort(key=lambda x: x.get('startTimestamp', 0), reverse=True)
    return eventos

# --- INTERFACE DO APLICATIVO ---
with st.sidebar:
    st.success(f"✅ Logado como: **{st.session_state['usuario'].upper()}**")
    if st.button("🚪 Sair (Logout)", use_container_width=True):
        st.session_state.clear()
        st.rerun()
    st.markdown("---")
    st.title("⚙️ Painel de Controle")
    st.info("Utilize as abas principais para analisar tendências individuais ou confrontos diretos.")

st.title("🔥 Máquina de Análise VIP")
st.markdown("Sistema exclusivo de mapeamento de tendências esportivas.")

aba1, aba2 = st.tabs(["📊 Analisar um Time", "⚔️ Confronto Direto (H2H)"])

# ABA 1: TIME SOZINHO
with aba1:
    col1, col2 = st.columns(2)
    with col1: time_alvo = st.text_input("Digite o nome do time:", key="input_t1")
    with col2: qtd_jogos = st.number_input("Quantidade de jogos", min_value=5, max_value=30, value=15, step=5, key="qtd1")
    
    b1, b2, b3 = st.columns([2, 2, 6])
    with b1: btn_buscar1 = st.button("Buscar Análise", type="primary", use_container_width=True)
    with b2:
        if st.button("🔄 Limpar Dados", key="limpar1", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['logado', 'usuario']: del st.session_state[key]
            st.rerun()
            
    if btn_buscar1:
        if time_alvo:
            with st.spinner(f"Vasculhando o banco de dados do {time_alvo}..."):
                id_time, nome_oficial = buscar_id_do_time(time_alvo)
                if id_time:
                    st.success(f"✅ Equipe localizada: **{nome_oficial}**")
                    eventos = obter_todos_jogos_recentes(id_time, paginas=max(4, (qtd_jogos // 15) + 2))
                    
                    jogos_analisados = 0
                    tabela_jogos = []
                    stats = {'over15': 0, 'over25': 0, 'btts': 0, 'escanteios': 0, 'cartoes': 0}
                    barra = st.progress(0, text="Lendo estatísticas jogo a jogo...")
                    
                    for i, jogo in enumerate(eventos):
                        if jogos_analisados >= qtd_jogos: break
                        if jogo['status']['type'] == 'finished':
                            id_p = jogo['id']
                            tc, tf = jogo['homeTeam']['name'], jogo['awayTeam']['name']
                            gc, gf = jogo['homeScore'].get('current', 0), jogo['awayScore'].get('current', 0)
                            data_jogo = datetime.fromtimestamp(jogo['startTimestamp']).strftime('%d/%m/%Y')
                            
                            time.sleep(0.4) # Pausa um pouco maior para evitar bloqueio
                            est = buscar_estatisticas_partida(id_p)
                            soma = gc + gf
                            tot_cartoes = est['cartoes_amarelos'] + est['cartoes_vermelhos']
                            
                            if soma >= 2: stats['over15'] += 1
                            if soma >= 3: stats['over25'] += 1
                            if gc > 0 and gf > 0: stats['btts'] += 1
                            if est['escanteios'] >= 9: stats['escanteios'] += 1
                            if tot_cartoes >= 5: stats['cartoes'] += 1
                            
                            tabela_jogos.append({"Data": data_jogo, "Casa": tc, "Gols C.": gc, "X": "X", "Gols F.": gf, "Fora": tf, "🚩 Esc": est['escanteios'], "🟨 Amar": est['cartoes_amarelos'], "🟥 Verm": est['cartoes_vermelhos']})
                            jogos_analisados += 1
                            barra.progress(jogos_analisados / qtd_jogos, text=f"Analisando {jogos_analisados}/{qtd_jogos}...")
                    
                    barra.empty() 
                    st.subheader("🎯 Tendências do Mercado")
                    c1, c2, c3, c4, c5 = st.columns(5)
                    c1.metric("Over 1.5 Gols", f"{(stats['over15']/jogos_analisados)*100:.0f}%", f"{stats['over15']} de {jogos_analisados}")
                    c2.metric("Over 2.5 Gols", f"{(stats['over25']/jogos_analisados)*100:.0f}%", f"{stats['over25']} de {jogos_analisados}")
                    c3.metric("Ambas Marcam", f"{(stats['btts']/jogos_analisados)*100:.0f}%", f"{stats['btts']} de {jogos_analisados}")
                    c4.metric("+8.5 Escanteios", f"{(stats['escanteios']/jogos_analisados)*100:.0f}%", f"{stats['escanteios']} de {jogos_analisados}")
                    c5.metric("+4.5 Cartões", f"{(stats['cartoes']/jogos_analisados)*100:.0f}%", f"{stats['cartoes']} de {jogos_analisados}")
                    
                    st.subheader("📋 Histórico Recente")
                    st.dataframe(tabela_jogos, use_container_width=True)
                else:
                    st.error("Time não encontrado.")

# ABA 2: CONFRONTO DIRETO
with aba2:
    col1, col2, col3 = st.columns(3)
    with col1: time_a = st.text_input("Mandante (Time A):", key="input_h2h_1")
    with col2: time_b = st.text_input("Visitante (Time B):", key="input_h2h_2")
    with col3: qtd_h2h = st.number_input("Qtd de Clássicos", min_value=3, max_value=20, value=10, step=1, key="qtd2")

    b3, b4, b5 = st.columns([2, 2, 6])
    with b3: btn_buscar2 = st.button("Buscar Confronto", type="primary", use_container_width=True)
    with b4:
        if st.button("🔄 Limpar Dados", key="limpar2", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['logado', 'usuario']: del st.session_state[key]
            st.rerun()

    if btn_buscar2:
        if time_a and time_b:
            with st.spinner("Escaneando anos de histórico..."):
                id_a, nome_a = buscar_id_do_time(time_a)
                id_b, nome_b = buscar_id_do_time(time_b)
                if id_a and id_b:
                    st.success(f"✅ Clássico localizado: **{nome_a} x {nome_b}**")
                    eventos = obter_todos_jogos_recentes(id_a, paginas=25)
                    jogos_h2h, ids_vistos = [], set()
                    for jogo in eventos:
                        if jogo['status']['type'] == 'finished':
                            ic, f_id, id_j = jogo['homeTeam']['id'], jogo['awayTeam']['id'], jogo['id']
                            if (ic == id_a and f_id == id_b) or (ic == id_b and f_id == id_a):
                                if id_j not in ids_vistos:
                                    jogos_h2h.append(jogo)
                                    ids_vistos.add(id_j)
                                    if len(jogos_h2h) >= qtd_h2h: break
                    
                    if not jogos_h2h: st.warning("Nenhum confronto direto recente encontrado.")
                    else:
                        stats = {'over15': 0, 'over25': 0, 'btts': 0, 'escanteios': 0, 'cartoes': 0}
                        vitorias_a, vitorias_b, empates = 0, 0, 0
                        tabela_h2h = []
                        jogos_analisados = len(jogos_h2h)
                        barra_h2h = st.progress(0, text="Processando dados do clássico...")
                        
                        for i, jogo in enumerate(jogos_h2h):
                            id_p, tc, tf = jogo['id'], jogo['homeTeam']['name'], jogo['awayTeam']['name']
                            gc, gf = jogo['homeScore'].get('current', 0), jogo['awayScore'].get('current', 0)
                            data_jogo = datetime.fromtimestamp(jogo['startTimestamp']).strftime('%d/%m/%Y')
                            
                            if gc > gf:
                                if jogo['homeTeam']['id'] == id_a: vitorias_a += 1
                                else: vitorias_b += 1
                            elif gf > gc:
                                if jogo['homeTeam']['id'] == id_a: vitorias_b += 1
                                else: vitorias_a += 1
                            else: empates += 1
                                
                            time.sleep(0.4)
                            est = buscar_estatisticas_partida(id_p)
                            soma = gc + gf
                            tot_car = est['cartoes_amarelos'] + est['cartoes_vermelhos']
                            
                            if soma >= 2: stats['over15'] += 1
                            if soma >= 3: stats['over25'] += 1
                            if gc > 0 and gf > 0: stats['btts'] += 1
                            if est['escanteios'] >= 9: stats['escanteios'] += 1
                            if tot_car >= 5: stats['cartoes'] += 1
                            
                            tabela_h2h.append({"Data": data_jogo, "Casa": tc, "Gols C.": gc, "X": "X", "Gols F.": gf, "Fora": tf, "🚩 Esc": est['escanteios'], "🟨 Amar": est['cartoes_amarelos'], "🟥 Verm": est['cartoes_vermelhos']})
                            barra_h2h.progress((i+1) / jogos_analisados)
                            
                        barra_h2h.empty()
                        perc_a, perc_b = (vitorias_a / jogos_analisados) * 100, (vitorias_b / jogos_analisados) * 100
                        if vitorias_a > vitorias_b: favorito = f"👑 {nome_a} ({perc_a:.0f}%)"
                        elif vitorias_b > vitorias_a: favorito = f"👑 {nome_b} ({perc_b:.0f}%)"
                        else: favorito = "⚖️ Equilibrado"

                        st.subheader(f"🏆 Favorito pelo Histórico: {favorito}")
                        st.write(f"Vitórias {nome_a}: **{vitorias_a}** | Vitórias {nome_b}: **{vitorias_b}** | Empates: **{empates}**")
                        st.markdown("---")
                        c1, c2, c3, c4, c5 = st.columns(5)
                        c1.metric("Over 1.5 Gols", f"{(stats['over15']/jogos_analisados)*100:.0f}%")
                        c2.metric("Over 2.5 Gols", f"{(stats['over25']/jogos_analisados)*100:.0f}%")
                        c3.metric("Ambas Marcam", f"{(stats['btts']/jogos_analisados)*100:.0f}%")
                        c4.metric("+8.5 Escanteios", f"{(stats['escanteios']/jogos_analisados)*100:.0f}%")
                        c5.metric("+4.5 Cartões", f"{(stats['cartoes']/jogos_analisados)*100:.0f}%")
                        st.subheader("📋 Lista de Confrontos")
                        st.dataframe(tabela_h2h, use_container_width=True)
