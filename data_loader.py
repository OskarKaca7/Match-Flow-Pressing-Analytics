from statsbombpy import sb
import streamlit as st

@st.cache_data
def load_all_competitions():
    return sb.competitions()

@st.cache_data
def load_matches_for_season(competition_id, season_id):
    return sb.matches(competition_id=competition_id, season_id=season_id)

@st.cache_data
def load_match_events(match_id):
    return sb.events(match_id=match_id)

@st.cache_data
def load_match_lineups(match_id):
    return sb.lineups(match_id=match_id)