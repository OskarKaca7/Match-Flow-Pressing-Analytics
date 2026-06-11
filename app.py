import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from data_loader import load_all_competitions, load_matches_for_season, load_match_events, load_match_lineups

# --- PAGE SETUP & TITLE ---
st.set_page_config(page_title="Tactical Insight Hub", layout="wide")

# --- CUSTOM CSS (PREMIUM SPORTS-TECH AESTHETIC) ---
custom_css = """
<style>
/* Wymuszony Dark Mode dla całej aplikacji */
.stApp { background-color: #0b0f19 !important; }
h1, h2, h3, h4, h5, h6, p, span, div, label { color: #cbd5e1; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }

header[data-testid="stHeader"] { display: none !important; }
.block-container, [data-testid="stMainBlockContainer"] { padding-top: 4rem !important; padding-bottom: 2rem !important; max-width: 1400px !important; }

/* Sticky Header dla analizy meczu */
.fixed-match-header { position: fixed; top: 0; left: 0; width: 100vw; background-color: rgba(11, 15, 25, 0.98); backdrop-filter: blur(8px); z-index: 999999; border-bottom: 1px solid #1e293b; padding: 12px 0; }
.fixed-header-content { max-width: 1400px; margin: 0 auto; display: flex; align-items: center; justify-content: center; padding: 0 3rem; }

/* Ukrycie standardowych labeli selectboxów (używamy własnych HTML) */
div[data-testid="stSelectbox"] label { display: none !important; }
div[data-testid="stSelectbox"] div[data-baseweb="select"] { background-color: #11141c !important; border: 1px solid #1e293b !important; border-radius: 6px !important; }
div[data-testid="stSelectbox"] div[data-baseweb="select"] * { color: #f8fafc !important; font-size: 0.85rem !important; }

/* Przyciski */
[data-testid="stButton"] button { transition: all 0.2s ease-in-out !important; }
/* Przycisk powrotu w Sticky Header */
.back-btn-container button { background-color: transparent !important; border: none !important; box-shadow: none !important; color: #94a3b8 !important; font-size: 0.75rem !important; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; padding: 0 !important; }
.back-btn-container button:hover { color: #00e5ff !important; }
/* Przycisk Analyze w liście meczów */
.analyze-btn-container button { background-color: #00e5ff !important; border: none !important; color: #0b0f19 !important; font-weight: 800 !important; padding: 8px 0 !important; border-radius: 6px !important; font-size: 0.75rem !important; text-transform: uppercase; letter-spacing: 1px; width: 100%; margin-top: 15px;}
.analyze-btn-container button:hover { background-color: #ffffff !important; box-shadow: 0 0 10px rgba(0, 229, 255, 0.3) !important;}

/* Legenda pod wykresami */
.legend-box { background: #11141c; padding: 12px 25px; border-radius: 6px; border: 1px solid #1e293b; font-size: 0.7rem; color: #64748b; margin-top: 0; margin-bottom: 30px; text-align: left; text-transform: uppercase; letter-spacing: 1px; display: flex; justify-content: center; gap: 30px;}
.legend-box strong { color: #cbd5e1; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# LOGO DATABASE
logo_dict = {
    "Barcelona": "https://images.fotmob.com/image_resources/logo/teamlogo/8634.png",
    "Real Madrid": "https://images.fotmob.com/image_resources/logo/teamlogo/8633.png",
    "Atlético Madrid": "https://images.fotmob.com/image_resources/logo/teamlogo/9906.png",
    "Bayern Munich": "https://media.api-sports.io/football/teams/157.png",
    "Bayer Leverkusen": "https://media.api-sports.io/football/teams/168.png",
    "Arsenal": "https://media.api-sports.io/football/teams/42.png",
    "Liverpool": "https://media.api-sports.io/football/teams/40.png",
    "Manchester City": "https://media.api-sports.io/football/teams/50.png",
    "Paris Saint-Germain": "https://media.api-sports.io/football/teams/85.png",
    "Internazionale": "https://media.api-sports.io/football/teams/505.png",
    "Argentina": "https://flagcdn.com/w80/ar.png",
    "France": "https://flagcdn.com/w80/fr.png",
}
default_logo = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="

# KOLORY AKCENTÓW
COLOR_HOME = "#00e5ff" # Cyan
COLOR_AWAY = "#f97316" # Orange

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
    if parts[-2].lower() in particles: return f"{parts[-2]} {parts[-1]}"
    if len(parts) >= 3 and parts[-3].lower() in particles: return f"{parts[-3]} {parts[-2]} {parts[-1]}"
    return parts[-2]

def get_display_name_mapping(lineup_df):
    mapping = {}
    for _, row in lineup_df.iterrows():
        raw_name = row['player_name']
        if 'player_nickname' in row and pd.notna(row['player_nickname']): mapping[raw_name] = row['player_nickname']
        else: mapping[raw_name] = clean_name(raw_name)
    return mapping

def draw_passing_network(df_events, team_name, lineup_df, accent_color, min_passes=3):
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
    
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#0e1117', line_color='#1e293b')
    fig, ax = pitch.draw(figsize=(8, 5.5))
    fig.patch.set_facecolor('#0b0f19')
    
    for i, row in edges.iterrows():
        passer = nodes[nodes['player_name'] == row['player_name']]
        recipient = nodes[nodes['player_name'] == row['recipient_name']]
        if not passer.empty and not recipient.empty:
            x_start, y_start = passer['x'].values[0], passer['y'].values[0]
            x_end, y_end = recipient['x'].values[0], recipient['y'].values[0]
            line_width = (row['pass_count'] / edges['pass_count'].max()) * 4
            alpha = max(0.3, (row['pass_count'] / edges['pass_count'].max()))
            pitch.arrows(x_start, y_start, x_end, y_end, width=line_width, headwidth=3, headlength=4, color=accent_color, ax=ax, alpha=alpha)

    for i, row in nodes.iterrows():
        marker_size = (row['total_passes'] / nodes['total_passes'].max()) * 500
        pitch.scatter(row['x'], row['y'], s=marker_size, color=accent_color, edgecolors='#0e1117', linewidths=1.5, ax=ax, zorder=2)
        ax.text(row['x'], row['y'] - 3.5, row['player_name'], ha='center', va='center', fontsize=9, fontweight='bold', fontfamily='sans-serif', color='#f8fafc', zorder=3)
    return fig

def draw_progressive_passes(df_events, team_name, accent_color):
    passes = df_events[(df_events['type'] == 'Pass') & (df_events['team'] == team_name)].copy()
    passes = passes[passes['pass_outcome'].isna()] 
    if passes.empty or 'pass_end_location' not in passes.columns: return None

    passes[['x', 'y']] = pd.DataFrame(passes['location'].tolist(), index=passes.index)
    passes[['end_x', 'end_y']] = pd.DataFrame(passes['pass_end_location'].tolist(), index=passes.index)
    final_third_entries = passes[(passes['x'] < 80) & (passes['end_x'] >= 80)]
    if final_third_entries.empty: return None

    pitch = Pitch(pitch_type='statsbomb', pitch_color='#0e1117', line_color='#1e293b')
    fig, ax = pitch.draw(figsize=(8, 5.5))
    fig.patch.set_facecolor('#0b0f19')
    pitch.arrows(final_third_entries['x'], final_third_entries['y'], final_third_entries['end_x'], final_third_entries['end_y'], width=1.5, headwidth=4, headlength=4, color=accent_color, ax=ax, alpha=0.8)
    pitch.scatter(final_third_entries['x'], final_third_entries['y'], color=accent_color, s=25, ax=ax, zorder=2)
    return fig

def draw_turnover_map(df_events, team_name):
    turnovers = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(['Dispossessed', 'Miscontrol']))].copy()
    if turnovers.empty: return None
    turnovers[['x', 'y']] = pd.DataFrame(turnovers['location'].tolist(), index=turnovers.index)

    pitch = Pitch(pitch_type='statsbomb', pitch_color='#0e1117', line_color='#1e293b')
    fig, ax = pitch.draw(figsize=(8, 5.5))
    fig.patch.set_facecolor('#0b0f19')
    try:
        pitch.kdeplot(turnovers['x'], turnovers['y'], ax=ax, fill=True, cmap='Oranges', alpha=0.4, levels=100, zorder=1)
    except:
        pass
    pitch.scatter(turnovers['x'], turnovers['y'], color='#f97316', edgecolors='#0e1117', linewidth=1, s=40, ax=ax, alpha=0.9, zorder=2)
    return fig

def draw_defensive_actions_map(df_events, team_name):
    def_types = ['Tackle', 'Interception', 'Block', 'Ball Recovery', 'Duel']
    def_events = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(def_types))].copy()
    if def_events.empty: return None
    
    def_events[['x', 'y']] = pd.DataFrame(def_events['location'].tolist(), index=def_events.index)
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#0e1117', line_color='#1e293b')
    fig, ax = pitch.draw(figsize=(8, 5.5))
    fig.patch.set_facecolor('#0b0f19')
    try:
        pitch.kdeplot(def_events['x'], def_events['y'], ax=ax, fill=True, cmap='Blues', alpha=0.3, levels=100, zorder=1)
    except:
        pass
    pitch.scatter(def_events['x'], def_events['y'], color='#3b82f6', edgecolors='#0e1117', linewidth=1, s=30, ax=ax, alpha=0.8, zorder=2)
    return fig

# --- STATYSTYKI WIDGETÓW ---
def get_action_zones_stats(df_events, team_name):
    events = df_events[(df_events['team'] == team_name) & (df_events['location'].notna())].copy()
    if events.empty: return 0, 0, 0
    events['x'] = events['location'].apply(lambda loc: loc[0] if isinstance(loc, list) and len(loc) > 0 else 0)
    
    total = len(events)
    if total == 0: return 0, 0, 0
    p_def = int(len(events[events['x'] < 40]) / total * 100)
    p_mid = int(len(events[(events['x'] >= 40) & (events['x'] <= 80)]) / total * 100)
    p_att = 100 - p_def - p_mid
    return p_def, p_mid, p_att

def get_ppda_value(df_events, team_name, opponent_name):
    try:
        opp_passes = df_events[(df_events['team'] == opponent_name) & (df_events['type'] == 'Pass')].copy()
        opp_passes['x'] = opp_passes['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else 0)
        opp_passes_count = len(opp_passes[opp_passes['x'] <= 80])
        
        def_types = ['Tackle', 'Interception', 'Block', 'Foul Committed', 'Duel']
        our_def = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(def_types))].copy()
        our_def['x'] = our_def['location'].apply(lambda loc: loc[0] if isinstance(loc, list) else 0)
        our_def_count = len(our_def[our_def['x'] >= 40])
        
        if our_def_count == 0: return 15.0
        return round(opp_passes_count / our_def_count, 1)
    except:
        return 15.0

# --- KOMPONENTY HTML ---
def render_section_header(num, title, subtext=""):
    return f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 3.5rem; margin-bottom: 1rem; border-bottom: 1px solid #1e293b; padding-bottom: 8px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="color: #00e5ff; font-weight: 900; font-size: 1.1rem; font-family: monospace;">{num}</span>
            <span style="color: #f8fafc; font-weight: 600; font-size: 1.1rem; letter-spacing: 0.5px;">{title}</span>
        </div>
        <div style="color: #64748b; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600;">{subtext}</div>
    </div>
    """

def get_action_zones_html(team_name, p_def, p_mid, p_att, accent_color):
    return f"""
    <div style="background: #11141c; padding: 15px 20px; border-radius: 6px; border: 1px solid #1e293b; margin-bottom: 10px;">
        <div style="color: #f8fafc; font-size: 0.9rem; font-weight: bold; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <div style="width: 8px; height: 8px; border-radius: 50%; background-color: {accent_color};"></div>
            {team_name}
        </div>
        <div style="display: flex; height: 6px; border-radius: 3px; overflow: hidden; background: #1e293b; margin-bottom: 10px;">
            <div style="width: {p_def}%; background: #334155;"></div>
            <div style="width: {p_mid}%; background: #475569;"></div>
            <div style="width: {p_att}%; background: {accent_color}; box-shadow: 0 0 10px {accent_color};"></div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.65rem; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px;">
            <span>Own Third <span style="color:#f8fafc;">{p_def}%</span></span>
            <span>Midfield <span style="color:#f8fafc;">{p_mid}%</span></span>
            <span style="color:{accent_color};">Final Third {p_att}%</span>
        </div>
    </div>
    """

def get_ppda_html(team_name, ppda_value):
    if ppda_value < 10.0:
        status = "AGGRESSIVE HIGH PRESS"
        border_color = "rgba(239, 68, 68, 0.3)" # Red border
        text_color = "#ef4444"
    elif ppda_value <= 14.0:
        status = "MODERATE PRESSING"
        border_color = "rgba(234, 179, 8, 0.3)" # Yellow border
        text_color = "#eab308"
    else:
        status = "PASSIVE BLOCK"
        border_color = "rgba(59, 130, 246, 0.3)" # Blue border
        text_color = "#3b82f6"
        
    return f"""
    <div style='background: #11141c; border: 1px solid #1e293b; border-radius: 6px; padding: 20px; margin-top: 10px; height: 100%; display: flex; flex-direction: column;'>
        <div style='display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px;'>
            <div>
                <div style='font-size: 0.6rem; color: #64748b; font-weight: bold; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 4px;'>PPDA — Passes allowed per def. action</div>
                <div style='font-size: 1rem; color: #f8fafc; font-weight: 600;'>{team_name}</div>
            </div>
            <div style='border: 1px solid {border_color}; color: {text_color}; background: rgba(0,0,0,0.2); font-size: 0.6rem; font-weight: 800; padding: 4px 8px; border-radius: 4px; text-transform: uppercase; letter-spacing: 1px;'>{status}</div>
        </div>
        <div style='display: flex; align-items: baseline; gap: 12px; margin-bottom: 15px;'>
            <div style='font-size: 4rem; font-weight: 800; color: #f8fafc; line-height: 1; font-family: monospace;'>{ppda_value}</div>
            <div style='font-size: 0.7rem; color: #64748b; letter-spacing: 1px;'>passes / defensive action</div>
        </div>
        <div style='font-size: 0.75rem; color: #64748b; line-height: 1.5; margin-top: auto;'>
            Lower values indicate higher pressing intensity inside the opposition half. Calculation scope: opponent passes attempted in the defensive 60% of the pitch divided by tackles, interceptions, fouls, and challenges in the same zone.
        </div>
    </div>
    """

def get_tactical_dossier_html(df_events, team_name, opponent_name, lineup_df, accent_color, template_idx):
    try:
        name_mapping = get_display_name_mapping(lineup_df)
        passes = df_events[(df_events['type'] == 'Pass') & (df_events['team'] == team_name) & (df_events['pass_outcome'].isna())].copy()
        if not passes.empty:
            passes['player_name'] = passes['player'].map(name_mapping).fillna(passes['player'].apply(clean_name))
            top_passer = passes['player_name'].value_counts().index[0]
            top_passer_val = passes['player_name'].value_counts().iloc[0]
        else: 
            top_passer = "the pivot"
            top_passer_val = 0

        if not passes.empty and 'pass_end_location' in passes.columns:
            passes[['end_x', 'end_y']] = pd.DataFrame(passes['pass_end_location'].tolist(), index=passes.index)
            final_third = passes[passes['end_x'] >= 80]
            if not final_third.empty:
                avg_y = final_third['end_y'].mean()
                if avg_y < 26.6: wing = "left wing"
                elif avg_y > 53.3: wing = "right wing"
                else: wing = "central corridor"
            else: wing = "central corridor"
        else: wing = "central corridor"
            
        turnovers = df_events[(df_events['team'] == team_name) & (df_events['type'].isin(['Dispossessed', 'Miscontrol']))].copy()
        if not turnovers.empty:
            turnovers['x'] = turnovers['location'].apply(lambda loc: loc[0])
            avg_x = turnovers['x'].mean()
            if avg_x < 40: vul_zone = "their own defensive third"
            elif avg_x > 80: vul_zone = "the advanced attacking phase"
            else: vul_zone = "the central midfield seam"
        else: vul_zone = "the central midfield seam"
            
        ppda_value = get_ppda_value(df_events, team_name, opponent_name)
        _, _, p_att = get_action_zones_stats(df_events, team_name)

        if template_idx == 0:
            para1 = f"{team_name} construct their build-up around <strong>{top_passer}</strong>, who anchors the first phase and acts as the principal circulation node with {top_passer_val} attempted passes. Entries into the final third skew decisively toward the <strong>{wing}</strong>, leveraging width rather than central penetration, with {p_att}% of total possession spent inside the attacking third."
            para2 = f"Defensively, {team_name} registers a PPDA of {ppda_value}. Loss-of-possession density concentrates in <strong>{vul_zone}</strong>, identifying the principal technical fracture point of the system."
            dir1 = f"Deny <strong>{top_passer}</strong> clean reception angles by shadow-marking; severing this node degrades distribution quality immediately."
            dir2 = f"Engineer pressing traps at the identified turnover stefa (<strong>{vul_zone}</strong>) — orient the press to funnel circulation into this zone."
        else:
            para1 = f"Out of build-up, {team_name} route the majority of their traffic through <strong>{top_passer}</strong> ({top_passer_val} passes). Their progressive footprint is weighted to the <strong>{wing}</strong>, manufacturing isolation duels rather than direct central thrusts. Territorial control settles at {p_att}% in the attacking third."
            para2 = f"In its defensive phase the side returns a PPDA reading of {ppda_value}. The turnover stefa — <strong>{vul_zone}</strong> — represents the recurring break-down point and is the most exploitable seam in the team's distribution chain."
            dir1 = f"Neutralise <strong>{top_passer}</strong>'s passing radius via man-oriented zonal coverage; restrict turn-and-face actions."
            dir2 = f"Bait the relay chain by leaving the apparent passing lane open, applying aggressive lateral pressure once the ball enters <strong>{vul_zone}</strong>."

        html = f"""
        <div style="background: #11141c; padding: 25px; border-radius: 8px; border-top: 2px solid {accent_color}; border-left: 1px solid #1e293b; border-right: 1px solid #1e293b; border-bottom: 1px solid #1e293b; height: 100%; display: flex; flex-direction: column;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 25px;">
                <div>
                    <div style="font-size: 0.6rem; color: #eab308; letter-spacing: 2px; text-transform: uppercase; font-weight: 800; margin-bottom: 6px;">Scouting Dossier · {team_name}</div>
                    <div style="font-size: 1.25rem; color: #f8fafc; font-weight: bold;">{team_name}</div>
                </div>
                <div style="text-align: right; font-size: 0.65rem; color: #64748b; letter-spacing: 1px; font-family: monospace;">
                    <div>PPDA {ppda_value}</div>
                    <div>{p_att}% FINAL THIRD</div>
                </div>
            </div>
            
            <div style="display: flex; gap: 30px; margin-bottom: 30px; flex: 1;">
                <div style="flex: 1;">
                    <div style="color: #94a3b8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; margin-bottom: 12px;">1 · In Possession — Build-up & Attack</div>
                    <p style="font-size: 0.8rem; line-height: 1.7; margin: 0; color: #cbd5e1;">{para1}</p>
                </div>
                <div style="flex: 1;">
                    <div style="color: #94a3b8; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 600; margin-bottom: 12px;">2 · Out of Possession — Defensive Shape</div>
                    <p style="font-size: 0.8rem; line-height: 1.7; margin: 0; color: #cbd5e1;">{para2}</p>
                </div>
            </div>
            
            <div style="border: 1px solid rgba(234, 179, 8, 0.2); border-radius: 6px; padding: 20px; background: rgba(234, 179, 8, 0.03); margin-top: auto;">
                <div style="color: #eab308; font-size: 0.65rem; text-transform: uppercase; margin-bottom: 15px; letter-spacing: 1.5px; font-weight: 800; display: flex; align-items: center; gap: 8px;">
                    <div style="width: 6px; height: 6px; border-radius: 50%; background-color: #eab308;"></div>
                    Exploitation Strategy — Coaching Directives
                </div>
                <div style="display: flex; gap: 12px; margin-bottom: 12px;">
                    <div style="color: #eab308; font-weight: 800; font-size: 0.8rem; font-family: monospace; padding-top: 2px;">01</div>
                    <div style="font-size: 0.8rem; line-height: 1.6; color: #cbd5e1;">{dir1}</div>
                </div>
                <div style="display: flex; gap: 12px;">
                    <div style="color: #eab308; font-weight: 800; font-size: 0.8rem; font-family: monospace; padding-top: 2px;">02</div>
                    <div style="font-size: 0.8rem; line-height: 1.6; color: #cbd5e1;">{dir2}</div>
                </div>
            </div>
        </div>
        """
        return html
    except Exception as e:
        return ""

# =====================================================================
# SYSTEM ROUTINGU & ODCZYT STANU 
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
    # --- WIDOK 1: MATCH SELECTION DASHBOARD ---
    
    st.markdown("""
    <div style='display: flex; align-items: center; gap: 15px; margin-bottom: 2rem;'>
        <div style='background: #00e5ff; color: #0b0f19; font-weight: 900; padding: 4px 8px; border-radius: 4px; font-size: 0.9rem; letter-spacing: 1px;'>BTS</div>
        <div>
            <div style='color: #f8fafc; font-size: 1.1rem; font-weight: 800; letter-spacing: 0.5px;'>Breaking the System</div>
            <div style='color: #64748b; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px;'>Passing Network · Pressing Analysis</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Loading StatsBomb database..."):
        df_comps = load_all_competitions()

    # DEDYKOWANE ETYKIETY HTML DLA DROPDOWNÓW
    st.markdown("""
    <div style='display: flex; justify-content: space-between; align-items: flex-end;'>
        <div style='flex: 1; padding-right: 15px;'><div style='color: #64748b; font-size: 0.65rem; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;'>Competition</div></div>
        <div style='flex: 1; padding-right: 15px;'><div style='color: #64748b; font-size: 0.65rem; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;'>Season</div></div>
        <div style='flex: 1; padding-right: 15px;'><div style='color: #64748b; font-size: 0.65rem; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; margin-bottom: 5px;'>Target Team</div></div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        unique_comps = sorted(df_comps['competition_name'].unique())
        if "comp_id" in st.query_params:
            try:
                c_row = df_comps[df_comps['competition_id'] == saved_comp_id]
                if not c_row.empty and c_row.iloc[0]['competition_name'] in unique_comps:
                    default_comp_idx = unique_comps.index(c_row.iloc[0]['competition_name'])
            except: pass
        selected_comp = st.selectbox("COMP", unique_comps, index=default_comp_idx, label_visibility="collapsed")

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
        selected_season = st.selectbox("SEA", unique_seasons, index=default_season_idx, label_visibility="collapsed")

    selected_row = comp_filtered[comp_filtered['season_name'] == selected_season].iloc[0]
    s_id = selected_row['season_id']
    df_matches = load_matches_for_season(c_id, s_id)

    with col3:
        all_teams = sorted(list(set(df_matches['home_team']).union(set(df_matches['away_team']))))
        default_team_idx = 0
        if saved_team and saved_team in all_teams:
            default_team_idx = all_teams.index(saved_team)
        selected_team = st.selectbox("TEAM", all_teams, index=default_team_idx, label_visibility="collapsed")

    st.markdown("<hr style='border-color: #1e293b; margin: 3rem 0 2rem 0;'>", unsafe_allow_html=True)
    
    st.markdown("""
    <div style='margin-bottom: 2rem;'>
        <div style='color: #00e5ff; font-size: 0.65rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 8px;'>Match Selection Dashboard</div>
        <div style='display: flex; justify-content: space-between; align-items: flex-end;'>
            <div>
                <h2 style='color: #f8fafc; font-size: 2rem; margin: 0 0 5px 0; font-weight: 700;'>Fixture Library</h2>
                <div style='color: #64748b; font-size: 0.85rem;'>Select a fixture below to load the full tactical analysis report.</div>
            </div>
            <div style='color: #64748b; font-size: 0.65rem; font-weight: bold; letter-spacing: 1.5px; text-transform: uppercase; font-family: monospace;'>Fixtures Indexed</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    team_matches = df_matches[(df_matches['home_team'] == selected_team) | (df_matches['away_team'] == selected_team)]
    display_df = team_matches.sort_values('match_date').drop_duplicates(subset=['match_id']).reset_index(drop=True)
    
    for index, row in display_df.iterrows():
        date_obj = pd.to_datetime(row['match_date'])
        formatted_date = date_obj.strftime('%d %b %Y').upper()

        home_logo_url = logo_dict.get(row['home_team'], default_logo)
        away_logo_url = logo_dict.get(row['away_team'], default_logo)

        home_color, away_color = "rgba(0,0,0,0)", "rgba(0,0,0,0)"
        green, red, blue = "rgba(46, 204, 113, 0.2)", "rgba(239, 68, 68, 0.2)", "rgba(59, 130, 246, 0.2)"

        if row['home_score'] > row['away_score']:
            home_color = green; away_color = red
        elif row['home_score'] < row['away_score']:
            home_color = red; away_color = green
        else:
            home_color = blue; away_color = blue

        card_html = f"""
        <div style="display: flex; align-items: center; justify-content: space-between; background: #11141c; padding: 20px 25px; border-radius: 8px; border: 1px solid #1e293b; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.2);">
            <div style="flex: 1.5; display: flex; flex-direction: column;">
                <span style="color: #64748b; font-size: 0.6rem; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 4px;">{selected_comp}</span>
                <span style="color: #475569; font-size: 0.65rem; font-weight: bold; letter-spacing: 1px;">{selected_season}</span>
            </div>
            
            <div style="flex: 2; display: flex; align-items: center; justify-content: flex-end; gap: 15px;">
                <div style="text-align: right;">
                    <div style="color: #f8fafc; font-weight: 600; font-size: 0.9rem;">{row['home_team']}</div>
                    <div style="color: #64748b; font-size: 0.55rem; font-weight: 800; letter-spacing: 1px;">HOME</div>
                </div>
                <div style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: #1e293b; border-radius: 50%;"><img src="{home_logo_url}" width="20"></div>
            </div>
            
            <div style="flex: 1; display: flex; justify-content: center; padding: 0 15px;">
                <div style="background: linear-gradient(90deg, {home_color} 0%, rgba(255,255,255,0.02) 50%, {away_color} 100%); padding: 6px 16px; border-radius: 6px; border: 1px solid #1e293b; display: flex; gap: 12px; align-items: center;">
                    <span style="color: {COLOR_HOME}; font-weight: 800; font-size: 1.1rem; font-family: monospace;">{row['home_score']}</span>
                    <span style="color: #475569;">-</span>
                    <span style="color: {COLOR_AWAY}; font-weight: 800; font-size: 1.1rem; font-family: monospace;">{row['away_score']}</span>
                </div>
            </div>
            
            <div style="flex: 2; display: flex; align-items: center; justify-content: flex-start; gap: 15px;">
                <div style="width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; background: #1e293b; border-radius: 50%;"><img src="{away_logo_url}" width="20"></div>
                <div style="text-align: left;">
                    <div style="color: #f8fafc; font-weight: 600; font-size: 0.9rem;">{row['away_team']}</div>
                    <div style="color: #64748b; font-size: 0.55rem; font-weight: 800; letter-spacing: 1px;">AWAY</div>
                </div>
            </div>
            
            <div style="flex: 1.5; display: flex; flex-direction: column; align-items: flex-end; justify-content: center;">
                <span style="color: #94a3b8; font-size: 0.65rem; font-weight: 600; font-family: monospace; letter-spacing: 1px;">{formatted_date}</span>
            </div>
        </div>
        """
        
        # Grid układ do przycisku na prawej stronie
        col_card, col_space, col_btn = st.columns([8.5, 0.2, 1.3])
        with col_card:
            st.markdown(card_html, unsafe_allow_html=True)
        with col_btn:
            st.markdown("<div class='analyze-btn-container'>", unsafe_allow_html=True)
            if st.button("ANALYZE ➔", key=f"btn_{row['match_id']}", use_container_width=True):
                st.query_params["comp_id"] = str(c_id)
                st.query_params["season_id"] = str(s_id)
                st.query_params["team"] = selected_team
                st.query_params["match_id"] = str(row['match_id'])
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

else:
    # =====================================================================
    # WIDOK 2: ANALIZA MECZU (DARK MODE & PREMIUM DESIGN)
    # =====================================================================
    c_id = int(st.query_params["comp_id"])
    s_id = int(st.query_params["season_id"])
    m_id = int(st.query_params["match_id"])
    
    df_matches = load_matches_for_season(c_id, s_id)
    match = df_matches[df_matches['match_id'] == m_id].iloc[0]
    date_obj = pd.to_datetime(match['match_date'])

    home_logo = logo_dict.get(match['home_team'], default_logo)
    away_logo = logo_dict.get(match['away_team'], default_logo)

    # STICKY HEADER (NOWOCZESNY)
    header_html = f"""
    <div class="fixed-match-header">
        <div class="fixed-header-content">
            <div style="flex: 1; display: flex; justify-content: flex-start;">
                </div>
            
            <div style="flex: 2; display: flex; align-items: center; justify-content: flex-end; gap: 15px;">
                <div style="display: flex; flex-direction: column; text-align: right;">
                    <span style="color: #f8fafc; font-size: 1rem; font-weight: 600;">{match['home_team']}</span>
                    <span style="color: {COLOR_HOME}; font-size: 0.55rem; font-weight: 800; letter-spacing: 1px;">HOME</span>
                </div>
                <div style="width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1e293b; border-radius: 50%;"><img src="{home_logo}" width="22"></div>
            </div>
            
            <div style="flex: 1; display: flex; flex-direction: column; align-items: center; padding: 0 20px;">
                <div style="background: #0b0f19; padding: 4px 20px; border-radius: 6px; border: 1px solid #1e293b; margin-bottom: 6px; display: flex; align-items: center; gap: 15px;">
                    <span style="color: {COLOR_HOME}; font-size: 1.4rem; font-weight: bold; font-family: monospace;">{match['home_score']}</span>
                    <span style="color: #475569;">-</span>
                    <span style="color: {COLOR_AWAY}; font-size: 1.4rem; font-weight: bold; font-family: monospace;">{match['away_score']}</span>
                </div>
                <div style="color: #64748b; font-size: 0.55rem; letter-spacing: 1.5px; text-transform: uppercase; font-weight: bold;">
                    {date_obj.strftime('%d %b %Y')} <span style="margin: 0 5px;">|</span> M-{match['match_id']}
                </div>
            </div>

            <div style="flex: 2; display: flex; align-items: center; justify-content: flex-start; gap: 15px;">
                <div style="width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; background: #1e293b; border-radius: 50%;"><img src="{away_logo}" width="22"></div>
                <div style="display: flex; flex-direction: column; text-align: left;">
                    <span style="color: #f8fafc; font-size: 1rem; font-weight: 600;">{match['away_team']}</span>
                    <span style="color: {COLOR_AWAY}; font-size: 0.55rem; font-weight: 800; letter-spacing: 1px;">AWAY</span>
                </div>
            </div>
            
            <div style="flex: 1;"></div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

    # Niestandardowe umieszczenie przycisku powrotu w lewym górnym rogu pod headerem
    st.markdown("<div class='back-btn-container'>", unsafe_allow_html=True)
    if st.button("← Back to Match List", type="primary"):
        st.query_params.clear()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

    with st.spinner("Extracting spatial & event data..."):
        df_events = load_match_events(m_id)
        lineups = load_match_lineups(m_id)

    home_lineup = lineups[match['home_team']]
    away_lineup = lineups[match['away_team']]

    # ---------------------------------------------------------------------
    # ACTION ZONES
    # ---------------------------------------------------------------------
    p_def_h, p_mid_h, p_att_h = get_action_zones_stats(df_events, match['home_team'])
    p_def_a, p_mid_a, p_att_a = get_action_zones_stats(df_events, match['away_team'])

    col_zones1, col_zones2 = st.columns(2)
    with col_zones1:
        st.markdown(get_action_zones_html(match['home_team'], p_def_h, p_mid_h, p_att_h, COLOR_HOME), unsafe_allow_html=True)
    with col_zones2:
        st.markdown(get_action_zones_html(match['away_team'], p_def_a, p_mid_a, p_att_a, COLOR_AWAY), unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # ROW 1: PASSING NETWORKS
    # ---------------------------------------------------------------------
    st.markdown(render_section_header("1", "Passing Networks (Starting XI)", "Base Structure"), unsafe_allow_html=True)
    
    col_pass1, col_pass2 = st.columns(2)
    with col_pass1:
        fig_home = draw_passing_network(df_events, match['home_team'], home_lineup, COLOR_HOME, min_passes=3)
        if fig_home:
            st.pyplot(fig_home, use_container_width=True)
            st.markdown(get_key_insights_html(df_events, match['home_team'], home_lineup, COLOR_HOME), unsafe_allow_html=True)
        else: st.warning("Insufficient passing data.")
            
    with col_pass2:
        fig_away = draw_passing_network(df_events, match['away_team'], away_lineup, COLOR_AWAY, min_passes=3)
        if fig_away:
            st.pyplot(fig_away, use_container_width=True)
            st.markdown(get_key_insights_html(df_events, match['away_team'], away_lineup, COLOR_AWAY), unsafe_allow_html=True)
        else: st.warning("Insufficient passing data.")

    # ---------------------------------------------------------------------
    # ROW 2: FINAL THIRD ENTRIES
    # ---------------------------------------------------------------------
    st.markdown(render_section_header("2", "Final Third Entries (Full Match)", "Ball Progression Left ➔ Right"), unsafe_allow_html=True)
    
    col_entry1, col_entry2 = st.columns(2)
    with col_entry1:
        fig_prog_home = draw_progressive_passes(df_events, match['home_team'], COLOR_HOME)
        if fig_prog_home: st.pyplot(fig_prog_home, use_container_width=True)
        else: st.info("No data.")
        
    with col_entry2:
        fig_prog_away = draw_progressive_passes(df_events, match['away_team'], COLOR_AWAY)
        if fig_prog_away: st.pyplot(fig_prog_away, use_container_width=True)
        else: st.info("No data.")

    st.markdown("<div class='legend-box'><span><strong>Origin Dot:</strong> Start of Pass</span><span><strong>Arrow:</strong> Destination</span><span><strong>Direction:</strong> Always Left to Right</span></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # ROW 3: VULNERABILITY MAP
    # ---------------------------------------------------------------------
    st.markdown(render_section_header("3", "Vulnerability Map (Turnovers under Pressure)", "Loss of Possession"), unsafe_allow_html=True)

    col_vuln1, col_vuln2 = st.columns(2)
    with col_vuln1:
        fig_vuln_home = draw_turnover_map(df_events, match['home_team'])
        if fig_vuln_home: st.pyplot(fig_vuln_home, use_container_width=True)
        else: st.info("No data.")
            
    with col_vuln2:
        fig_vuln_away = draw_turnover_map(df_events, match['away_team'])
        if fig_vuln_away: st.pyplot(fig_vuln_away, use_container_width=True)
        else: st.info("No data.")

    st.markdown("<div class='legend-box'><span><strong>Red Dot:</strong> Single ball loss</span><span><strong>Heatmap:</strong> High-density turnover zones</span><span><strong>Direction:</strong> Always Left to Right</span></div>", unsafe_allow_html=True)

    # ---------------------------------------------------------------------
    # ROW 4: DEFENSIVE ACTIONS & PPDA
    # ---------------------------------------------------------------------
    st.markdown(render_section_header("4", "Defensive Actions & PPDA", "Pressing Intensity"), unsafe_allow_html=True)

    col_def1, col_def2 = st.columns(2)
    
    with col_def1:
        fig_def_home = draw_defensive_actions_map(df_events, match['home_team'])
        if fig_def_home: st.pyplot(fig_def_home, use_container_width=True)
        
    with col_def2:
        fig_def_away = draw_defensive_actions_map(df_events, match['away_team'])
        if fig_def_away: st.pyplot(fig_def_away, use_container_width=True)

    st.markdown("<div class='legend-box'><span><strong>Blue Dot:</strong> Successful defensive action</span><span><strong>Heatmap:</strong> High-density pressing zones</span><span><strong>Direction:</strong> Always Left to Right</span></div>", unsafe_allow_html=True)

    # PPDA KARTY
    col_ppda1, col_ppda2 = st.columns(2)
    with col_ppda1:
        ppda_val_h = get_ppda_value(df_events, match['home_team'], match['away_team'])
        st.markdown(get_ppda_html(match['home_team'], ppda_val_h), unsafe_allow_html=True)
    with col_ppda2:
        ppda_val_a = get_ppda_value(df_events, match['away_team'], match['home_team'])
        st.markdown(get_ppda_html(match['away_team'], ppda_val_a), unsafe_allow_html=True)


    # ---------------------------------------------------------------------
    # THE TACTICAL DOSSIER
    # ---------------------------------------------------------------------
    st.markdown(render_section_header("5", "Post-Match Tactical Dossier", "Executive Scouting Output"), unsafe_allow_html=True)
    
    col_dos1, col_dos2 = st.columns(2)
    with col_dos1:
        st.markdown(get_tactical_dossier_html(df_events, match['home_team'], match['away_team'], home_lineup, COLOR_HOME, 0), unsafe_allow_html=True)
    with col_dos2:
        st.markdown(get_tactical_dossier_html(df_events, match['away_team'], match['home_team'], away_lineup, COLOR_AWAY, 1), unsafe_allow_html=True)

    st.divider()
    st.markdown("<div style='text-align: center; color: #475569; font-size: 0.65rem; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 2rem;'>Data provided by StatsBomb · Built with Streamlit</div>", unsafe_allow_html=True)