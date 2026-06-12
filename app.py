import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from data_loader import load_all_competitions, load_matches_for_season, load_match_events, load_match_lineups

# --- PAGE SETUP & TITLE ---
st.set_page_config(page_title="Tactical Insight Hub", layout="wide")

# --- CUSTOM CSS (LIGHT THEME, FIX TOOLBARS & STRICT MOBILE 50/50 GRID) ---
custom_css = """
<style>
/* UKRYWANIE PASKÓW STREAMLITA (TEN DZIWNY ZNACZEK "streamlitApp") */
[data-testid="stElementToolbar"], 
[data-testid="stElementActions"], 
.st-emotion-cache-1vt4ygl { display: none !important; }

/* Reset i podstawy */
html, body, [data-testid="stAppViewContainer"], [data-testid="stMainBlockContainer"] { overflow-x: hidden !important; max-width: 100vw !important; }
* { box-sizing: border-box !important; }
header[data-testid="stHeader"] { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding-top: 5rem !important; padding-bottom: 1rem !important; }
h1, h2, h3, h4, h5, h6, p, span, div, label { font-family: sans-serif; }

/* Sticky Header */
.fixed-match-header { position: fixed; top: 0; left: 0; width: 100vw; background-color: rgba(255, 255, 255, 0.98); backdrop-filter: blur(5px); z-index: 999999; border-bottom: 1px solid #e0e4ec; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05); padding: 8px 0; }
.fixed-header-content { max-width: 95%; margin: 0 auto; display: flex; align-items: center; justify-content: center; gap: 40px; }

/* Subtelne Przyciski (Analyze / Back) */
button[kind="secondary"] { background-color: transparent !important; border: none !important; box-shadow: none !important; color: #888888 !important; font-size: 0.8rem !important; font-weight: 800 !important; letter-spacing: 2px !important; text-transform: uppercase !important; padding: 0 !important; }
button[kind="secondary"]:hover { color: #ff6e40 !important; background-color: transparent !important; }
.back-btn-container button { margin-top: -15px !important; margin-bottom: 10px !important; }
[data-testid="stButton"] { margin-top: -5px; margin-bottom: 15px; text-align: center; }

/* Legenda pod wykresami */
.legend-box { background: #fdfdfd; padding: 10px 15px; border-radius: 4px; border: 1px solid #e0e4ec; font-size: 0.85rem; color: #555; margin-top: 10px; margin-bottom: 20px; text-align: center; text-transform: uppercase; letter-spacing: 0.5px; width: 100%;}
.legend-box strong { color: #222; }

/* --- KLASYCZNY PASEK MECZOWY --- */
.classic-match-card { display: flex; align-items: center; justify-content: space-between; border-radius: 5px; padding: 15px; border: 1px solid #e0e4ec; margin-bottom: 10px; width: 100%; }
.mc-logo { width: 45px; flex-shrink: 0; text-align: center; }
.mc-logo img { width: 100%; height: auto; }
.mc-team-home { flex: 1; text-align: right; padding-right: 15px; overflow: hidden; }
.mc-team-away { flex: 1; text-align: left; padding-left: 15px; overflow: hidden; }
.mc-score { width: 90px; flex-shrink: 0; text-align: center; }
.mc-team-home h4, .mc-team-away h4 { margin: 0; color: #222; font-size: 1.1rem; }
.mc-score h3 { margin: 0; color: #ff4b4b; font-size: 1.5rem; font-weight: bold; }
.mc-score small { color: #888; display: block; margin-bottom: 5px; font-size: 0.8rem; }
.team-name-header { text-align: center; color: #111; margin-top: 0; margin-bottom: 8px; font-size: 1.2rem; width: 100%;}

/* --- KOMPONENTY HTML --- */
.xi-container { background: #fff; border: 1px solid #e0e4ec; border-radius: 6px; overflow: hidden; margin-top: 10px; width: 100%; height: 100%; box-sizing: border-box;}
.xi-header { background: #f4f6f9; padding: 8px; text-align: center; font-weight: bold; color: #444; font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid #e0e4ec; }
.xi-row { display: flex; align-items: center; padding: 6px 10px; border-bottom: 1px solid #f0f2f6; }
.xi-num { width: 25px; font-weight: bold; color: #ff6e40; font-size: 0.9rem; flex-shrink: 0; }
.xi-name { font-size: 0.85rem; color: #111; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.ppda-container { background: #fff; border: 1px solid #e0e4ec; border-radius: 6px; padding: 15px; text-align: center; margin-top: 10px; height: 100%; width: 100%; box-sizing: border-box;}
.ppda-header { background: #f4f6f9; padding: 8px; font-size: 0.75rem; font-weight: bold; color: #444; text-transform: uppercase; margin: -15px -15px 15px -15px; border-bottom: 1px solid #e0e4ec; }
.ppda-val { font-size: 2rem; font-weight: 900; color: #111; font-family: monospace;}
.ppda-desc { font-size: 0.65rem; color: #888; margin-bottom: 8px; text-transform: uppercase; }

.zones-container { background: #fff; padding: 12px; border-radius: 6px; border: 1px solid #e0e4ec; margin-bottom: 15px; width: 100%; box-sizing: border-box; }
.zones-header { display: flex; justify-content: space-between; font-size: 0.8rem; color: #555; font-weight: bold; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.5px; }
.zones-bar { display: flex; height: 12px; border-radius: 6px; overflow: hidden; background: #eee; }

/* ------------------------------------------------------------------- */
/* BEZWZGLĘDNA SIATKA DLA TELEFONÓW - BLOKADA ŁAMANIA KOLUMN W CHMURZE */
/* ------------------------------------------------------------------- */
@media (max-width: 768px) {
    /* 1. Margines zeby tekst nie wchodził pod header */
    .block-container, [data-testid="stMainBlockContainer"] { padding-top: 6.5rem !important; padding-left: 0.5rem !important; padding-right: 0.5rem !important; }
    .hide-mobile { display: none !important; }
    .fixed-header-content { padding: 5px 0; gap: 10px; }
    
    /* 2. Brutalne wymuszenie układu GRID 50/50 na kolumnach Streamlita */
    div[data-testid="stHorizontalBlock"] { 
        flex-direction: row !important; 
        flex-wrap: wrap !important; 
        display: flex !important;
        gap: 0px !important;
    }
    
    /* Wszystkie kolumny w raporcie zmuszone na 50% szerokości */
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 50% !important; 
        flex: 0 0 50% !important; 
        min-width: 50% !important; 
        padding-left: 0.25rem !important;
        padding-right: 0.25rem !important;
    }

    /* WYJĄTEK: Pierwszy blok to filtry ligowe - one mają być na 100% żeby dalo sie w nie kliknąć */
    div[data-testid="stHorizontalBlock"]:first-of-type > div[data-testid="column"] {
        width: 100% !important;
        flex: 0 0 100% !important;
        min-width: 100% !important;
        padding: 0 !important;
    }
    
    /* Zabezpieczenie boisk z Matplotlib */
    [data-testid="stImage"] img, .element-container img { max-width: 100% !important; height: auto !important; }

    /* Pasek meczowy na mobile */
    .classic-match-card { padding: 10px 5px !important; gap: 2px !important; }
    .mc-logo { width: 25px !important; }
    .mc-team-home { padding-right: 5px !important; }
    .mc-team-away { padding-left: 5px !important; }
    .mc-team-home h4, .mc-team-away h4 { font-size: 0.75rem !important; white-space: normal !important; line-height: 1.2 !important; }
    .mc-score { width: 65px !important; }
    .mc-score h3 { font-size: 1.05rem !important; white-space: nowrap; }
    .mc-score small { font-size: 0.55rem !important; margin-bottom: 2px !important; }
    
    h3 { font-size: 1.1rem !important; }
    .team-name-header { font-size: 0.85rem !important; margin-bottom: 5px !important; }
    
    /* Elementy HTML dopasowane do wąskich, 50% kolumn */
    .xi-header { font-size: 0.6rem; padding: 4px; }
    .xi-row { padding: 4px; }
    .xi-num { font-size: 0.6rem; width: 15px; }
    .xi-name { font-size: 0.55rem; }
    
    .ppda-container { padding: 8px; }
    .ppda-header { font-size: 0.55rem; padding: 4px; margin: -8px -8px 8px -8px; }
    .ppda-val { font-size: 1.3rem; }
    .ppda-desc { font-size: 0.5rem; }
    
    .zones-container { padding: 8px; }
    .zones-header { font-size: 0.55rem; flex-direction: column; text-align: center; gap: 2px;}
    .zones-bar { height: 6px; }
    .legend-box { font-size: 0.55rem; padding: 6px; }
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# LOGO DATABASE
logo_dict = {
    "Barcelona": "https://images.fotmob.com/image_resources/logo/teamlogo/8634.png",
    "Real Madrid": "https://images.fotmob.com/image_resources/logo/teamlogo/8633.png",
    "Atlético Madrid": "https://images.fotmob.com/image_resources/logo/teamlogo/9906.png",
    "Sevilla": "https://images.fotmob.com/image_resources/logo/teamlogo/8302.png",
    "Real Sociedad": "https://images.fotmob.com/image_resources/logo/teamlogo/8560.png",
    "Villarreal": "https://images.fotmob.com/image_resources/logo/teamlogo/10205.png",
    "Real Betis": "https://images.fotmob.com/image_resources/logo/teamlogo/8603.png",
    "Athletic Club": "https://images.fotmob.com/image_resources/logo/teamlogo/8315.png",
    "Celta Vigo": "https://images.fotmob.com/image_resources/logo/teamlogo/9910.png",
    "Valencia": "https://images.fotmob.com/image_resources/logo/teamlogo/10267.png",
    "Osasuna": "https://images.fotmob.com/image_resources/logo/teamlogo/8371.png",
    "Getafe": "https://images.fotmob.com/image_resources/logo/teamlogo/8305.png",
    "Deportivo Alavés": "https://images.fotmob.com/image_resources/logo/teamlogo/9866.png",
    "Levante UD": "https://images.fotmob.com/image_resources/logo/teamlogo/8581.png",
    "Granada": "https://images.fotmob.com/image_resources/logo/teamlogo/9867.png",
    "Cádiz": "https://images.fotmob.com/image_resources/logo/teamlogo/8385.png",
    "Elche": "https://images.fotmob.com/image_resources/logo/teamlogo/10268.png",
    "Real Valladolid": "https://images.fotmob.com/image_resources/logo/teamlogo/10281.png",
    "Huesca": "https://images.fotmob.com/image_resources/logo/teamlogo/9910.png",
    "Eibar": "https://images.fotmob.com/image_resources/logo/teamlogo/8372.png",
    "Bayern Munich": "https://media.api-sports.io/football/teams/157.png",
    "Borussia Dortmund": "https://media.api-sports.io/football/teams/165.png",
    "Bayer Leverkusen": "https://media.api-sports.io/football/teams/168.png",
    "RB Leipzig": "https://media.api-sports.io/football/teams/173.png",
    "Eintracht Frankfurt": "https://media.api-sports.io/football/teams/169.png",
    "VfL Wolfsburg": "https://media.api-sports.io/football/teams/161.png",
    "Borussia Mönchengladbach": "https://media.api-sports.io/football/teams/163.png",
    "VfB Stuttgart": "https://media.api-sports.io/football/teams/172.png",
    "SC Freiburg": "https://media.api-sports.io/football/teams/160.png",
    "TSG Hoffenheim": "https://media.api-sports.io/football/teams/167.png",
    "Union Berlin": "https://media.api-sports.io/football/teams/192.png",
    "Mainz 05": "https://media.api-sports.io/football/teams/164.png",
    "Augsburg": "https://media.api-sports.io/football/teams/170.png",
    "Werder Bremen": "https://media.api-sports.io/football/teams/162.png",
    "Schalke 04": "https://media.api-sports.io/football/teams/174.png",
    "VfL Bochum": "https://media.api-sports.io/football/teams/176.png",
    "Arsenal": "https://media.api-sports.io/football/teams/42.png",
    "Aston Villa": "https://media.api-sports.io/football/teams/66.png",
    "Chelsea": "https://media.api-sports.io/football/teams/49.png",
    "Everton": "https://media.api-sports.io/football/teams/45.png",
    "Liverpool": "https://media.api-sports.io/football/teams/40.png",
    "Manchester City": "https://media.api-sports.io/football/teams/50.png",
    "Manchester United": "https://media.api-sports.io/football/teams/33.png",
    "Newcastle United": "https://media.api-sports.io/football/teams/34.png",
    "Tottenham Hotspur": "https://media.api-sports.io/football/teams/47.png",
    "Wolverhampton Wanderers": "https://media.api-sports.io/football/teams/39.png",
    "Leicester City": "https://media.api-sports.io/football/teams/46.png",
    "West Ham United": "https://media.api-sports.io/football/teams/48.png",
    "Leeds United": "https://media.api-sports.io/football/teams/63.png",
    "Crystal Palace": "https://media.api-sports.io/football/teams/52.png",
    "Brighton & Hove Albion": "https://media.api-sports.io/football/teams/51.png",
    "Brentford": "https://media.api-sports.io/football/teams/55.png",
    "Fulham": "https://media.api-sports.io/football/teams/36.png",
    "Nottingham Forest": "https://media.api-sports.io/football/teams/65.png",
    "Bournemouth": "https://media.api-sports.io/football/teams/35.png",
    "Southampton": "https://media.api-sports.io/football/teams/41.png",
    "Qatar": "https://flagcdn.com/w80/qa.png",
    "Ecuador": "https://flagcdn.com/w80/ec.png",
    "Senegal": "https://flagcdn.com/w80/sn.png",
    "Netherlands": "https://flagcdn.com/w80/nl.png",
    "England": "https://flagcdn.com/w80/gb-eng.png",
    "Iran": "https://flagcdn.com/w80/ir.png",
    "United States": "https://flagcdn.com/w80/us.png",
    "Wales": "https://flagcdn.com/w80/gb-wls.png",
    "Argentina": "https://flagcdn.com/w80/ar.png",
    "Saudi Arabia": "https://flagcdn.com/w80/sa.png",
    "Mexico": "https://flagcdn.com/w80/mx.png",
    "Poland": "https://flagcdn.com/w80/pl.png",
    "France": "https://flagcdn.com/w80/fr.png",
    "Australia": "https://flagcdn.com/w80/au.png",
    "Denmark": "https://flagcdn.com/w80/dk.png",
    "Tunisia": "https://flagcdn.com/w80/tn.png",
    "Spain": "https://flagcdn.com/w80/es.png",
    "Costa Rica": "https://flagcdn.com/w80/cr.png",
    "Germany": "https://flagcdn.com/w80/de.png",
    "Japan": "https://flagcdn.com/w80/jp.png",
    "Belgium": "https://flagcdn.com/w80/be.png",
    "Canada": "https://flagcdn.com/w80/ca.png",
    "Morocco": "https://flagcdn.com/w80/ma.png",
    "Croatia": "https://flagcdn.com/w80/hr.png",
    "Brazil": "https://flagcdn.com/w80/br.png",
    "Serbia": "https://flagcdn.com/w80/rs.png",
    "Switzerland": "https://flagcdn.com/w80/ch.png",
    "Cameroon": "https://flagcdn.com/w80/cm.png",
    "Portugal": "https://flagcdn.com/w80/pt.png",
    "Ghana": "https://flagcdn.com/w80/gh.png",
    "Uruguay": "https://flagcdn.com/w80/uy.png",
    "South Korea": "https://flagcdn.com/w80/kr.png"
}
default_logo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# =====================================================================
# FUNKCJE ANALITYCZNE I WIZUALIZACYJNE
# =====================================================================
def clean_name(name):
    if pd.isna(name): return ""
    parts = str(name).split()
    parts = [p for p in parts if p.lower() != 'i']
    if len(parts) == 1: return parts[0]
    if len(parts) == 2: return parts[1]
    particles = ['de', 'van', 'der', 'ter', 'da', 'dos', 'di', 'mac', 'mc']
    if parts[-2].lower() in particles:
        return f"{parts[-2]} {parts[-1]}"
    if len(parts) >= 3 and parts[-3].lower() in particles:
        return f"{parts[-3]} {parts[-2]} {parts[-1]}"
    return parts[-2]

def get_display_name_mapping(lineup_df):
    mapping = {}
    for _, row in lineup_df.iterrows():
        raw_name = row['player_name']
        if 'player_nickname' in row and pd.notna(row['player_nickname']):
            mapping[raw_name] = row['player_nickname']
        else:
            mapping[raw_name] = clean_name(raw_name)
    return mapping

def draw_passing_network(df_events, team_name, lineup_df, min_passes=3):
    name_mapping = get_display_name_mapping(lineup_df)
    subs = df_events[(df_events['type'] == 'Substitution') & (df_events['team'] == team_name)]
    first_sub_min = subs['minute'].min() if not subs.empty else 120
    
    passes = df_events[(df_events['type'] == 'Pass') & (df_events['team'] == team_name) & (df_events['minute'] < first_sub_min)].copy()
    passes = passes[passes['pass_outcome'].isna()] 
    if passes.empty: return None
        
    passes[['x', 'y']] = pd.DataFrame(passes['location'].tolist(), index=passes.index)
    passes['player_name'] = passes['player'].map(name_mapping).fillna(passes['player'].apply(clean_name))
    passes['recipient_name'] = passes['pass_recipient'].map(name_mapping).fillna(passes['pass_recipient'].apply(clean_name))
    
    nodes = passes.groupby('player_name').agg({'x': 'mean', 'y': 'mean', 'id': 'count'}).reset_index()
    nodes.rename(columns={'id': 'total_passes'}, inplace=True)
    
    edges = passes.groupby(['player_name', 'recipient_name']).size().reset_index(name='pass_count')
    edges = edges[edges['pass_count'] >= min_passes] 
    
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#f4f6f9', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(8, 6))
    
    for i, row in edges.iterrows():
        passer = nodes[nodes['player_name'] == row['player_name']]
        recipient = nodes[nodes['player_name'] == row['recipient_name']]
        if not passer.empty and not recipient.empty:
            x_start, y_start = passer['x'].values[0], passer['y'].values[0]
            x_end, y_end = recipient['x'].values[0], recipient['y'].values[0]
            line_width = (row['pass_count'] / edges['pass_count'].max()) * 6
            alpha = max(0.3, (row['pass_count'] / edges['pass_count'].max()))
            pitch.arrows(x_start, y_start, x_end, y_end, width=line_width, headwidth=3, headlength=4, color='#1e3d59', ax=ax, alpha=alpha)

    for i, row in nodes.iterrows():
        marker_size = (row['total_passes'] / nodes['total_passes'].max()) * 600
        pitch.scatter(row['x'], row['y'], s=marker_size, color='#ff6e40', edgecolors='#b33c00', linewidths=2, ax=ax, zorder=2)
        ax.text(row['x'], row['y'] - 3.5, row['player_name'], ha='center', va='center', fontsize=10, fontweight='bold', fontfamily='sans-serif', zorder=3)
    return fig

def get_starting_xi_list(df_events, lineup_df, team_name):
    try:
        name_mapping = get_display_name_mapping(lineup_df)
        number_mapping = dict(zip(lineup_df['player_name'], lineup_df['jersey_number']))
        row = df_events[(df_events['type'] == 'Starting XI') & (df_events['team'] == team_name)].iloc[0]
        tactics = row.get('tactics_lineup') or row.get('tactics', {}).get('lineup')
        starters = []
        for p in tactics:
            raw_name = p['player']['name']
            disp_name = name_mapping.get(raw_name, clean_name(raw_name))
            number = number_mapping.get(raw_name, p.get('jersey_number', '-'))
            starters.append({'number': int(number) if pd.notna(number) else '-', 'name': disp_name})
        return starters
    except Exception as e:
        return []

def generate_xi_html(starters):
    html = """
    <div class="xi-container">
        <div class="xi-header">Starting XI</div>
    """
    for s in starters:
        html += f"<div class='xi-row'><div class='xi-num'>{s['number']}</div><div class='xi-name'>{s['name']}</div></div>"
    html += "</div>"
    return html

# IDEALNA, NIERUSZONA WERSJA TACTICAL INSIGHTS Z SZARYMI DOPISKAMI
def get_key_insights_html(df_events, team_name, lineup_df):
    try:
        name_mapping = get_display_name_mapping(lineup_df)
        passes = df_events[(df_events['type'] == 'Pass') & (df_events['team'] == team_name)].copy()
        passes = passes[passes['pass_outcome'].isna()] 
        if passes.empty: return ""
            
        passes['player_name'] = passes['player'].map(name_mapping).fillna(passes['player'].apply(clean_name))
        passes['recipient_name'] = passes['pass_recipient'].map(name_mapping).fillna(passes['pass_recipient'].apply(clean_name))
        
        top_passer = passes['player_name'].value_counts().index[0]
        top_passer_count = passes['player_name'].value_counts().iloc[0]
        top_recipient = passes['recipient_name'].value_counts().index[0]
        top_recipient_count = passes['recipient_name'].value_counts().iloc[0]
        
        pairs = passes.groupby(['player_name', 'recipient_name']).size().sort_values(ascending=False)
        top_pair = pairs.index[0]
        top_pair_count = pairs.iloc[0]
        
        html = f"""
<div style='width: 100%; margin: 10px auto 30px auto; background-color: #ffffff; border-left: 4px solid #ff6e40; border-top: 1px solid #e0e4ec; border-right: 1px solid #e0e4ec; border-bottom: 1px solid #e0e4ec; border-radius: 0 8px 8px 0; padding: 15px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); box-sizing: border-box; height: 100%; display: flex; flex-direction: column; justify-content: center;'>
    <h5 style='margin-top: 0; margin-bottom: 12px; color: #111; font-family: sans-serif; font-size: 0.95rem; text-transform: uppercase; letter-spacing: 0.5px;'>Tactical Insights <span style="font-size: 0.7rem; color: #888; text-transform: none;">(Full Match)</span></h5>
    <div style='color: #444; font-family: sans-serif; font-size: 0.85rem; line-height: 1.6;'>
        <div style='margin-bottom: 10px;'><strong>Main Hub:</strong> <span style='color: #ff6e40; font-weight: bold;'>{top_passer}</span> ({top_passer_count} passes) <br><em style='color: #888; font-size: 0.75rem;'>Target for man-marking.</em></div>
        <div style='margin-bottom: 10px;'><strong>Primary Outlet:</strong> <span style='color: #ff6e40; font-weight: bold;'>{top_recipient}</span> ({top_recipient_count} received) <br><em style='color: #888; font-size: 0.75rem;'>Key progression target.</em></div>
        <div><strong>Strongest Link:</strong> <span style='color: #ff6e40; font-weight: bold;'>{top_pair[0]} ➔ {top_pair[1]}</span> ({top_pair_count} times) <br><em style='color: #888; font-size: 0.75rem;'>Prime pressing trigger.</em></div>
    </div>
</div>
"""
        return html
    except Exception as e:
        return ""

def draw_progressive_passes(df_events, team_name):
    passes = df_events[(df_events['type'] == 'Pass') & (df_events['team'] == team_name)].copy()
    passes = passes[passes['pass_outcome'].isna()] 
    if passes.empty or 'pass_end_location' not in passes.columns: return None

    passes[['x', 'y']] = pd.DataFrame(passes['location'].tolist(), index=passes.index)
    passes[['end_x', 'end_y']] = pd.DataFrame(passes['pass_end_location'].tolist(), index=passes.index)
    final_third_entries = passes[(passes['x'] < 80) & (passes['end_x'] >= 80)]
    if final_third_entries.empty: return None

    pitch = Pitch(pitch_type='statsbomb', pitch_color='#f4f6f9', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(8, 6))
    pitch.arrows(final_third_entries['x'], final_third_entries['y'], final_third_entries['end_x'], final_third_entries['end_y'], width=2, headwidth=4, headlength=4, color='#3498db', ax=ax, alpha=0.6)
    pitch.scatter(final_third_entries['x'], final_third_entries['y'], color='#2980b9', s=30, ax=ax, zorder=2)
    return fig

def draw_turnover_map(df_events, team_name):
    turnovers = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(['Dispossessed', 'Miscontrol']))].copy()
    if turnovers.empty: return None
    turnovers[['x', 'y']] = pd.DataFrame(turnovers['location'].tolist(), index=turnovers.index)

    pitch = Pitch(pitch_type='statsbomb', pitch_color='#f4f6f9', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(8, 6))
    try:
        pitch.kdeplot(turnovers['x'], turnovers['y'], ax=ax, fill=True, cmap='Reds', alpha=0.6, levels=100, zorder=1)
    except:
        pitch.hexbin(turnovers['x'], turnovers['y'], ax=ax, edgecolors='#f4f6f9', gridsize=(8, 8), cmap='Reds', alpha=0.7, zorder=1)
    pitch.scatter(turnovers['x'], turnovers['y'], color='#c0392b', edgecolors='#fff', linewidth=1, s=60, ax=ax, alpha=0.9, zorder=2)
    return fig

def get_action_zones_html(df_events, team_name):
    events = df_events[(df_events['team'] == team_name) & (df_events['location'].notna())].copy()
    if events.empty: return ""
    events['x'] = events['location'].apply(lambda loc: loc[0] if isinstance(loc, list) and len(loc) > 0 else 0)
    
    def_third = len(events[events['x'] < 40])
    mid_third = len(events[(events['x'] >= 40) & (events['x'] <= 80)])
    att_third = len(events[events['x'] > 80])
    
    total = def_third + mid_third + att_third
    if total == 0: return ""
    
    p_def = int(def_third/total * 100)
    p_mid = int(mid_third/total * 100)
    p_att = 100 - p_def - p_mid
    
    html = f"""
    <div class="zones-container">
        <div class="zones-header">
            <span>Own Third ({p_def}%)</span>
            <span>Midfield ({p_mid}%)</span>
            <span>Final Third ({p_att}%)</span>
        </div>
        <div class="zones-bar">
            <div style="width: {p_def}%; background: #95a5a6; display: flex; align-items: center; justify-content: center;"></div>
            <div style="width: {p_mid}%; background: #bdc3c7; display: flex; align-items: center; justify-content: center;"></div>
            <div style="width: {p_att}%; background: #ff6e40; display: flex; align-items: center; justify-content: center;"></div>
        </div>
    </div>
    """
    return html

def draw_defensive_actions_map(df_events, team_name):
    def_types = ['Tackle', 'Interception', 'Block', 'Ball Recovery', 'Duel']
    def_events = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(def_types))].copy()
    if def_events.empty: return None
    
    def_events[['x', 'y']] = pd.DataFrame(def_events['location'].tolist(), index=def_events.index)
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#f4f6f9', line_color='#c7d5cc')
    fig, ax = pitch.draw(figsize=(8, 6))
    try:
        pitch.kdeplot(def_events['x'], def_events['y'], ax=ax, fill=True, cmap='Blues', alpha=0.6, levels=100, zorder=1)
    except:
        pitch.hexbin(def_events['x'], def_events['y'], ax=ax, edgecolors='#f4f6f9', gridsize=(8, 8), cmap='Blues', alpha=0.7, zorder=1)
    pitch.scatter(def_events['x'], def_events['y'], color='#2980b9', edgecolors='#fff', linewidth=1, s=40, ax=ax, alpha=0.8, zorder=2)
    return fig

def get_ppda_html(df_events, team_name, opponent_name):
    try:
        opp_passes = df_events[(df_events['team'] == opponent_name) & (df_events['type'] == 'Pass')].copy()
        opp_passes['x'] = opp_passes['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else 0)
        opp_passes_count = len(opp_passes[opp_passes['x'] <= 80])
        
        def_types = ['Tackle', 'Interception', 'Block', 'Foul Committed', 'Duel']
        our_def = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(def_types))].copy()
        our_def['x'] = our_def['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else 0)
        our_def_count = len(our_def[our_def['x'] >= 40])
        
        if our_def_count == 0: return ""
        ppda_value = round(opp_passes_count / our_def_count, 1)
        
        if ppda_value < 10.0:
            status = "Aggressive Press"
            color = "#2ecc71"
        elif ppda_value <= 14.0:
            status = "Moderate Press"
            color = "#f1c40f"
        else:
            status = "Passive Block"
            color = "#95a5a6"
            
        html = f"""
        <div class="ppda-container">
            <div class="ppda-header">PPDA Pressing Intensity</div>
            <div class="ppda-val">{ppda_value}</div>
            <div class="ppda-desc">Opponent passes / def. action</div>
            <span style='background: {color}; color: #fff; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: bold;'>{status}</span>
        </div>
        """
        return html
    except:
        return ""

def get_tactical_dossier_html(df_events, team_name, opponent_name, lineup_df, template_idx=0):
    try:
        name_mapping = get_display_name_mapping(lineup_df)
        
        passes = df_events[(df_events['type'] == 'Pass') & (df_events['team'] == team_name) & (df_events['pass_outcome'].isna())].copy()
        if not passes.empty:
            passes['player_name'] = passes['player'].map(name_mapping).fillna(passes['player'].apply(clean_name))
            top_passer = passes['player_name'].value_counts().index[0]
        else:
            top_passer = "their key playmaker"

        if not passes.empty and 'pass_end_location' in passes.columns:
            passes[['end_x', 'end_y']] = pd.DataFrame(passes['pass_end_location'].tolist(), index=passes.index)
            final_third = passes[passes['end_x'] >= 80]
            if not final_third.empty:
                avg_y = final_third['end_y'].mean()
                if avg_y < 26.6: wing = "left wing"
                elif avg_y > 53.3: wing = "right wing"
                else: wing = "central areas"
            else: wing = "central areas"
        else: wing = "central areas"
            
        turnovers = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(['Dispossessed', 'Miscontrol']))].copy()
        if not turnovers.empty:
            turnovers['x'] = turnovers['location'].apply(lambda loc: loc[0])
            avg_x = turnovers['x'].mean()
            if avg_x < 40: vul_zone = "their own defensive third"
            elif avg_x > 80: vul_zone = "the attacking third"
            else: vul_zone = "the midfield sector"
        else: vul_zone = "the midfield sector"
            
        try:
            opp_passes = df_events[(df_events['team'] == opponent_name) & (df_events['type'] == 'Pass')].copy()
            opp_passes['x'] = opp_passes['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else 0)
            opp_passes_count = len(opp_passes[opp_passes['x'] <= 80])
            
            def_types = ['Tackle', 'Interception', 'Block', 'Foul Committed', 'Duel']
            our_def = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(def_types))].copy()
            our_def['x'] = our_def['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else 0)
            our_def_count = len(our_def[our_def['x'] >= 40])
            
            ppda_value = round(opp_passes_count / our_def_count, 1) if our_def_count > 0 else 15.0
            
            if ppda_value < 10.0: press_style = "an aggressive, high-intensity pressing scheme"
            elif ppda_value <= 14.0: press_style = "a moderate, trigger-based pressing system"
            else: press_style = "a passive, low-block defensive structure"
        except:
            ppda_value = "N/A"
            press_style = "a balanced defensive structure"

        if template_idx == 0:
            para1 = f"The build-up phase is heavily dictated by <strong>{top_passer}</strong>, who acts as the primary connective tissue for ball progression. When transitioning into the final attacking third, {team_name} shows a clear structural bias, predominantly overloading the <strong>{wing}</strong> to create goal-scoring opportunities."
            para2 = f"Defensively, the team operates with <strong>{press_style}</strong> (PPDA: {ppda_value}). However, under sustained opposition pressure, their technical structure tends to fracture, with the highest concentration of dispossessions and miscontrols occurring in <strong>{vul_zone}</strong>."
            para3 = f"To successfully disrupt {team_name}, the defensive block must force the ball into {vul_zone} and set aggressive pressing traps. By man-marking {top_passer} and defensively reinforcing the {wing}, we can neutralize their primary progression vectors and force high-turnover situations."
        else:
            para1 = f"In possession, {team_name} routes the majority of their play through <strong>{top_passer}</strong>. Their attacking geometry is highly asymmetrical, as they consistently look to exploit the <strong>{wing}</strong> when penetrating the opposition's defensive block."
            para2 = f"Without the ball, they deploy <strong>{press_style}</strong>, reflected in a PPDA of {ppda_value}. Despite this, their build-up is prone to collapsing under aggressive pressing, giving up possession most frequently in <strong>{vul_zone}</strong>."
            para3 = f"The optimal counter-strategy involves isolating <strong>{top_passer}</strong> out of the game while heavily shifting the defensive shape to cover the <strong>{wing}</strong>. Pressing triggers should be activated immediately whenever the ball enters <strong>{vul_zone}</strong>."

        html = f"""
        <div style="background: #ffffff; color: #333; padding: 25px; border-radius: 10px; margin-top: 10px; border-top: 4px solid #ff6e40; box-shadow: 0 4px 12px rgba(0,0,0,0.05); font-family: sans-serif; border: 1px solid #e0e4ec; width: 100%; box-sizing: border-box;">
            <h3 style="margin-top: 0; color: #111; border-bottom: 1px solid #e0e4ec; padding-bottom: 12px; text-transform: uppercase; letter-spacing: 1.5px; font-size: 1.15rem;">Post-Match Tactical Dossier</h3>
            <h5 style="color: #ff6e40; margin-top: 15px; margin-bottom: 5px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">1. In Possession (Build-up & Attack)</h5>
            <p style="font-size: 0.9rem; line-height: 1.6; color: #444; margin-top: 0;">{para1}</p>
            <h5 style="color: #ff6e40; margin-top: 15px; margin-bottom: 5px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">2. Out of Possession (Defensive Shape)</h5>
            <p style="font-size: 0.9rem; line-height: 1.6; color: #444; margin-top: 0;">{para2}</p>
            <div style="background: rgba(255, 110, 64, 0.05); padding: 15px; border-left: 3px solid #ff6e40; margin-top: 20px; border-radius: 0 4px 4px 0;">
                <h5 style="color: #ff6e40; margin-top: 0; margin-bottom: 8px; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 1px;">Exploitation Strategy</h5>
                <p style="font-size: 0.9rem; line-height: 1.5; color: #111; margin-bottom: 0; font-weight: 500;">{para3}</p>
            </div>
        </div>
        """
        return html
    except Exception as e:
        return ""

# =====================================================================
# SYSTEM ROUTINGU & URL SYNC
# =====================================================================
default_comp_idx = 0
default_season_idx = 0
saved_team = None

if "comp_id" in st.query_params:
    try: saved_comp_id = int(st.query_params["comp_id"])
    except: pass
    if "season_id" in st.query_params:
        try: saved_season_id = int(st.query_params["season_id"])
        except: pass
    if "team" in st.query_params:
        saved_team = st.query_params["team"]

if "match_id" not in st.query_params:

    st.title("Tactical Insight Hub")
    st.markdown("**Audience POV:** Coaching staff looking to optimize pressing triggers to disrupt the opponent's ball progression.")
    st.markdown("**Working Hypothesis:** Every opponent exhibits specific, repetitive spatial vulnerabilities under pressure that can be identified through event data and exploited tactically.")
    st.divider()

    with st.spinner("Loading StatsBomb database..."):
        df_comps = load_all_competitions()

    st.subheader("1. Configure Opponent Analysis")
    col1, col2, col3 = st.columns(3)

    with col1:
        unique_comps = sorted(df_comps['competition_name'].unique())
        if "comp_id" in st.query_params:
            try:
                c_row = df_comps[df_comps['competition_id'] == saved_comp_id]
                if not c_row.empty and c_row.iloc[0]['competition_name'] in unique_comps:
                    default_comp_idx = unique_comps.index(c_row.iloc[0]['competition_name'])
            except: pass
        selected_comp = st.selectbox("Select competition:", unique_comps, index=default_comp_idx)

    comp_filtered = df_comps[df_comps['competition_name'] == selected_comp]
    c_id = comp_filtered.iloc[0]['competition_id']

    with col2:
        unique_seasons = sorted(comp_filtered['season_name'].unique(), reverse=True)
        if "season_id" in st.query_params:
            try:
                s_row = comp_filtered[comp_filtered['season_id'] == saved_season_id]
                if not s_row.empty and s_row.iloc[0]['season_name'] in unique_seasons:
                    default_season_idx = unique_seasons.index(s_row.iloc[0]['season_name'])
            except: pass
        selected_season = st.selectbox("Select season:", unique_seasons, index=default_season_idx)

    selected_row = comp_filtered[comp_filtered['season_name'] == selected_season].iloc[0]
    s_id = selected_row['season_id']
    df_matches = load_matches_for_season(c_id, s_id)

    with col3:
        all_teams = ["All Teams"] + sorted(list(set(df_matches['home_team']).union(set(df_matches['away_team']))))
        default_team_idx = 0
        if saved_team and saved_team in all_teams:
            default_team_idx = all_teams.index(saved_team)
        selected_team = st.selectbox("Select team (Opponent):", all_teams, index=default_team_idx)

    st.divider()
    
    if selected_team == "All Teams":
        st.subheader(f"All matches in the {selected_season} season")
        team_matches = df_matches
    else:
        st.subheader(f"Matches for {selected_team} in the {selected_season} season")
        team_matches = df_matches[(df_matches['home_team'] == selected_team) | (df_matches['away_team'] == selected_team)]
        
    display_df = team_matches.sort_values('match_date').drop_duplicates(subset=['match_id']).reset_index(drop=True)
    
    for index, row in display_df.iterrows():
        date_obj = pd.to_datetime(row['match_date'])
        formatted_date = date_obj.strftime('%d.%m.%Y')

        home_logo_url = logo_dict.get(row['home_team'], default_logo)
        away_logo_url = logo_dict.get(row['away_team'], default_logo)

        home_color, away_color = "rgba(0,0,0,0)", "rgba(0,0,0,0)"
        green, red, blue = "rgba(46, 204, 113, 0.2)", "rgba(231, 76, 60, 0.2)", "rgba(52, 152, 219, 0.2)"

        if row['home_score'] > row['away_score']:
            home_color = green; away_color = red
        elif row['home_score'] < row['away_score']:
            home_color = red; away_color = green
        else:
            home_color = blue; away_color = blue

        card_html = f"""
        <div class="classic-match-card" style="background: linear-gradient(90deg, {home_color} 0%, rgba(255,255,255,0) 25%, rgba(255,255,255,0) 75%, {away_color} 100%);">
            <div class="mc-logo"><img src="{home_logo_url}"></div>
            <div class="mc-team-home"><h4>{row['home_team']}</h4></div>
            <div class="mc-score">
                <small>{formatted_date}</small>
                <h3>{row['home_score']} : {row['away_score']}</h3>
            </div>
            <div class="mc-team-away"><h4>{row['away_team']}</h4></div>
            <div class="mc-logo"><img src="{away_logo_url}"></div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        if st.button("Analyze", key=f"btn_{row['match_id']}", use_container_width=True, type="secondary"):
            st.query_params["comp_id"] = str(c_id)
            st.query_params["season_id"] = str(s_id)
            st.query_params["team"] = selected_team
            st.query_params["match_id"] = str(row['match_id'])
            st.rerun()

else:
    # =====================================================================
    # WIDOK 2: ANALIZA MECZU 
    # =====================================================================
    c_id = int(st.query_params["comp_id"])
    s_id = int(st.query_params["season_id"])
    m_id = int(st.query_params["match_id"])
    
    df_matches = load_matches_for_season(c_id, s_id)
    match = df_matches[df_matches['match_id'] == m_id].iloc[0]
    date_obj = pd.to_datetime(match['match_date'])

    home_logo = logo_dict.get(match['home_team'], default_logo)
    away_logo = logo_dict.get(match['away_team'], default_logo)

    header_html = f"""
    <div class="fixed-match-header">
        <div class="fixed-header-content">
            <div class="hide-mobile" style="flex: 1; text-align: right; display: flex; justify-content: flex-end;">
                <h3 style="margin: 0; font-family: sans-serif; font-size: 1.35rem; font-weight: 600; color: #111111;">{match['home_team']}</h3>
            </div>
            <div style="display: flex; flex-direction: column; align-items: center;">
                <div style="display: flex; align-items: center; gap: 15px;">
                    <img src="{home_logo}" width="38" style="vertical-align: middle;" class="hide-mobile">
                    <span style="font-size: 1.5rem; font-weight: bold; color: #FF4B4B; background: #f4f6f9; padding: 4px 14px; border-radius: 4px; font-family: monospace; border: 1px solid #e0e4ec;">
                        {match['home_score']} : {match['away_score']}
                    </span>
                    <img src="{away_logo}" width="38" style="vertical-align: middle;" class="hide-mobile">
                </div>
                <div style="margin-top: 4px;">
                    <small style="color: #888888; font-family: sans-serif; font-size: 0.75rem;">{date_obj.strftime('%d.%m.%Y')} | ID: {match['match_id']}</small>
                </div>
            </div>
            <div class="hide-mobile" style="flex: 1; text-align: left; display: flex; justify-content: flex-start;">
                <h3 style="margin: 0; font-family: sans-serif; font-size: 1.35rem; font-weight: 600; color: #111111;">{match['away_team']}</h3>
            </div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
    if st.button("← Back to Match List", type="secondary"):
        st.query_params.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    with st.spinner("Extracting match events & computing tactical metrics..."):
        df_events = load_match_events(m_id)
        lineups = load_match_lineups(m_id)

    home_lineup = lineups[match['home_team']]
    away_lineup = lineups[match['away_team']]

    # ---------------------------------------------------------------------
    # ACTION ZONES
    # ---------------------------------------------------------------------
    col_zones1, col_zones2 = st.columns(2)
    with col_zones1:
        st.markdown(f"<div class='team-name-header'>{match['home_team']}</div>", unsafe_allow_html=True)
        st.markdown(get_action_zones_html(df_events, match['home_team']), unsafe_allow_html=True)
    with col_zones2:
        st.markdown(f"<div class='team-name-header'>{match['away_team']}</div>", unsafe_allow_html=True)
        st.markdown(get_action_zones_html(df_events, match['away_team']), unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # ROW 1: PASSING NETWORKS
    # ---------------------------------------------------------------------
    st.subheader("1. Passing Networks (Starting XI)")
    st.markdown("Networks represent successful passes made before the first substitution to ensure tactical accuracy (Minimum 3 passes between players).")
    
    col_pass1, col_pass2 = st.columns(2)
    with col_pass1:
        st.markdown(f"<div class='team-name-header'>{match['home_team']}</div>", unsafe_allow_html=True)
        fig_home = draw_passing_network(df_events, match['home_team'], home_lineup, min_passes=3)
        if fig_home: st.pyplot(fig_home, use_container_width=True)
        else: st.warning("Insufficient passing data for this team.")
    with col_pass2:
        st.markdown(f"<div class='team-name-header'>{match['away_team']}</div>", unsafe_allow_html=True)
        fig_away = draw_passing_network(df_events, match['away_team'], away_lineup, min_passes=3)
        if fig_away: st.pyplot(fig_away, use_container_width=True)
        else: st.warning("Insufficient passing data for this team.")
        
    col_xi1, col_xi2 = st.columns(2)
    with col_xi1:
        if fig_home: 
            starters_home = get_starting_xi_list(df_events, home_lineup, match['home_team'])
            st.markdown(generate_xi_html(starters_home), unsafe_allow_html=True)
    with col_xi2:
        if fig_away:
            starters_away = get_starting_xi_list(df_events, away_lineup, match['away_team'])
            st.markdown(generate_xi_html(starters_away), unsafe_allow_html=True)

    col_ins1, col_ins2 = st.columns(2)
    with col_ins1:
        if fig_home: st.markdown(get_key_insights_html(df_events, match['home_team'], home_lineup), unsafe_allow_html=True)
    with col_ins2:
        if fig_away: st.markdown(get_key_insights_html(df_events, match['away_team'], away_lineup), unsafe_allow_html=True)

    st.divider()

    # ---------------------------------------------------------------------
    # ROW 2: FINAL THIRD ENTRIES
    # ---------------------------------------------------------------------
    st.subheader("2. Final Third Entries (Full Match)")
    st.markdown("How they transport the ball into the attacking zone throughout the match. Watch for asymmetry.")
    
    col_entry1, col_entry2 = st.columns(2)
    with col_entry1:
        st.markdown(f"<div class='team-name-header'>{match['home_team']}</div>", unsafe_allow_html=True)
        fig_prog_home = draw_progressive_passes(df_events, match['home_team'])
        if fig_prog_home: st.pyplot(fig_prog_home, use_container_width=True)
        else: st.info("No final third entries found.")
        
    with col_entry2:
        st.markdown(f"<div class='team-name-header'>{match['away_team']}</div>", unsafe_allow_html=True)
        fig_prog_away = draw_progressive_passes(df_events, match['away_team'])
        if fig_prog_away: st.pyplot(fig_prog_away, use_container_width=True)
        else: st.info("No final third entries found.")

    st.markdown("""
<div class='legend-box'>
<strong>Legend:</strong> Dot = Origin of the pass | Arrow = Destination | <strong>Attacking Direction:</strong> Always Left to Right
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ---------------------------------------------------------------------
    # ROW 3: VULNERABILITY MAP
    # ---------------------------------------------------------------------
    st.subheader("3. Vulnerability Map (Turnovers under Pressure, Full Match)")
    st.markdown("Where they lose the ball. Heatmap of Dispossessions and Miscontrols throughout the entire match. Identify your pressing triggers here.")

    col_vuln1, col_vuln2 = st.columns(2)
    with col_vuln1:
        st.markdown(f"<div class='team-name-header'>{match['home_team']}</div>", unsafe_allow_html=True)
        fig_vuln_home = draw_turnover_map(df_events, match['home_team'])
        if fig_vuln_home: st.pyplot(fig_vuln_home, use_container_width=True)
        else: st.info("No turnover data found.")
            
    with col_vuln2:
        st.markdown(f"<div class='team-name-header'>{match['away_team']}</div>", unsafe_allow_html=True)
        fig_vuln_away = draw_turnover_map(df_events, match['away_team'])
        if fig_vuln_away: st.pyplot(fig_vuln_away, use_container_width=True)
        else: st.info("No turnover data found.")

    st.markdown("""
<div class='legend-box'>
<strong>Legend:</strong> Red Dot = Single ball loss (Dispossessed/Miscontrol) | Heatmap = High-density turnover zones | <strong>Attacking Direction:</strong> Always Left to Right
</div>
""", unsafe_allow_html=True)

    st.divider()

    # ---------------------------------------------------------------------
    # ROW 4: DEFENSIVE ACTIONS & PPDA
    # ---------------------------------------------------------------------
    st.subheader("4. Defensive Actions & Pressing Intensity (Full Match)")
    st.markdown("Where they try to win the ball back. Heatmap of Tackles, Interceptions, and Recoveries paired with PPDA score.")

    col_def1, col_def2 = st.columns(2)
    with col_def1:
        st.markdown(f"<div class='team-name-header'>{match['home_team']}</div>", unsafe_allow_html=True)
        fig_def_home = draw_defensive_actions_map(df_events, match['home_team'])
        if fig_def_home: st.pyplot(fig_def_home, use_container_width=True)
        else: st.info("No defensive data found.")
            
    with col_def2:
        st.markdown(f"<div class='team-name-header'>{match['away_team']}</div>", unsafe_allow_html=True)
        fig_def_away = draw_defensive_actions_map(df_events, match['away_team'])
        if fig_def_away: st.pyplot(fig_def_away, use_container_width=True)
        else: st.info("No defensive data found.")

    st.markdown("""
<div class='legend-box'>
<strong>Legend:</strong> Blue Dot = Successful Defensive Action | Heatmap = High-density pressing zones | <strong>Attacking Direction:</strong> Always Left to Right
</div>
""", unsafe_allow_html=True)

    col_ppda1, col_ppda2 = st.columns(2)
    with col_ppda1:
        if fig_def_home: st.markdown(get_ppda_html(df_events, match['home_team'], match['away_team']), unsafe_allow_html=True)
    with col_ppda2:
        if fig_def_away: st.markdown(get_ppda_html(df_events, match['away_team'], match['home_team']), unsafe_allow_html=True)

    st.divider()

    # ---------------------------------------------------------------------
    # THE TACTICAL DOSSIER
    # ---------------------------------------------------------------------
    st.subheader("5. Post-Match Tactical Dossier")
    st.markdown("Comprehensive scouting report based on spatial and event data analysis.")
    
    col_dos1, col_dos2 = st.columns(2)
    with col_dos1:
        st.markdown(get_tactical_dossier_html(df_events, match['home_team'], match['away_team'], home_lineup, 0), unsafe_allow_html=True)
    with col_dos2:
        st.markdown(get_tactical_dossier_html(df_events, match['away_team'], match['home_team'], away_lineup, 1), unsafe_allow_html=True)

    st.divider()
    st.caption("Data provided by **StatsBomb Open Data**. Visualization designed for educational purposes.")
