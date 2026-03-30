import matplotlib
import matplotlib.pyplot as plt
# Set non-interactive backend BEFORE importing pyplot or using it
matplotlib.use('Agg')

import streamlit as st
from mplsoccer import Pitch
from matplotlib import patheffects
import random
import io
import json
import os
from datetime import datetime

FORMATION_CONFIGS = {
    "1-2-1": {
        "slots": ['DEF', 'LMID', 'RMID', 'FWD'],
        "slot_types": {'DEF': 0, 'LMID': 1, 'RMID': 1, 'FWD': 2},
        "coords": {'GK': (8, 40), 'DEF': (42, 40), 'LMID': (62, 18), 'RMID': (62, 62), 'FWD': (86, 40)}
    },
    "2-2-0": {
        "slots": ['LDEF', 'RDEF', 'LMID', 'RMID'],
        "slot_types": {'LDEF': 0, 'RDEF': 0, 'LMID': 1, 'RMID': 1},
        "coords": {'GK': (8, 40), 'LDEF': (42, 20), 'RDEF': (42, 60), 'LMID': (75, 20), 'RMID': (75, 60)}
    }
}

st.set_page_config(page_title="Soccer Lineup Generator", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background-color: #f8fafc;
    }
    section[data-testid="stSidebar"] {
        background-color: #f1f5f9;
    }
    div.stButton > button:first-child {
        background-color: #166534;
        color: white;
        border: none;
    }
    thead tr th {
        background-color: #166534 !important;
        color: white !important;
    }
    .stDownloadButton > button {
        background-color: #ffffff;
        border: 1px solid #166534 !important;
        color: #166534 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- APP STATE INITIALIZATION ---
if 'seed' not in st.session_state:
    st.session_state.seed = random.randint(1000, 9999)
if 'manual_swaps_5v5' not in st.session_state:
    st.session_state.manual_swaps_5v5 = []

# --- SIDEBAR CONFIGURATION ---
st.sidebar.header("Team Configuration")

# --- CONFIGURATION PERSISTENCE ---
st.sidebar.header("Configuration Portability")
uploaded_config = st.sidebar.file_uploader("Upload saved config (.json)", type="json")
if uploaded_config is not None:
    if st.sidebar.button("Apply Loaded Configuration"):
        config_data = json.load(uploaded_config)
        for key, value in config_data.items():
            st.session_state[key] = value
        # Pre-calculate roster from the loaded/existing roster_raw to handle attendance checkboxes
        current_roster_raw = st.session_state.get('roster_raw', "")
        temp_roster = [p.strip() for p in current_roster_raw.split(",") if p.strip()]
        if "attending" in config_data:
            for p in temp_roster:
                st.session_state[f'attend_{p}'] = p in config_data["attending"]
        st.success("Configuration applied!")

roster_raw = st.sidebar.text_area("Roster (comma separated)", st.session_state.get('roster_raw', "Player 1, Player 2, Player 3, Player 4, Player 5, Player 6, Player 7, Player 8"), key='roster_raw')
roster = [p.strip() for p in roster_raw.split(",") if p.strip()]

if st.sidebar.button("Generate New Random Rotation"):
    st.session_state.seed = random.randint(1000, 9999)
    st.session_state.manual_swaps_5v5 = []

team_name = st.sidebar.text_input("Team Name", st.session_state.get('team_name', "Your Team"), key='team_name')
opponent = st.sidebar.text_input("Opponent", st.session_state.get('opponent', "Opponent"), key='opponent')
formation_choice = st.sidebar.selectbox("Formation", list(FORMATION_CONFIGS.keys()), key='formation_choice')

attending = []
st.sidebar.subheader("Attending Players")
for p in roster:
    if st.sidebar.checkbox(f"{p}", value=st.session_state.get(f'attend_{p}', True), key=f'attend_{p}'):
        attending.append(p)

quarterly_gks = []
if len(attending) > 0:
    for q in range(1, 5):
        saved_gk = st.session_state.get(f"gk_q{q}")
        gk_idx = attending.index(saved_gk) if saved_gk in attending else (q-1)%len(attending)
        gk = st.sidebar.selectbox(f"Q{q} Goalkeeper", attending, index=gk_idx, key=f"gk_q{q}")
        quarterly_gks.append(gk)
else:
    st.error("Please select at least one attending player to continue.")
    st.stop()

st.sidebar.subheader("Lineup Constraints")
split_pairs = []
with st.sidebar.expander("Split Pairs (Keep Apart)"):
    for i in range(1, 3):
        col1, col2 = st.columns(2)
        s_p1 = col1.selectbox(f"Pair {i} A", ["None"] + roster, 
                              index=(roster.index(st.session_state.get(f"s{i}a")) + 1) if st.session_state.get(f"s{i}a") in roster else 0, key=f"s{i}a")
        s_p2 = col2.selectbox(f"Pair {i} B", ["None"] + roster, 
                              index=(roster.index(st.session_state.get(f"s{i}b")) + 1) if st.session_state.get(f"s{i}b") in roster else 0, key=f"s{i}b")
        if s_p1 != "None" and s_p2 != "None":
            split_pairs.append([s_p1, s_p2])

synergy_pairs = []
with st.sidebar.expander("Synergy Pairs (Keep Together)"):
    for i in range(1, 3):
        col1, col2 = st.columns(2)
        syn_p1 = col1.selectbox(f"Pair {i} A", ["None"] + roster, 
                                index=(roster.index(st.session_state.get(f"syn{i}a")) + 1) if st.session_state.get(f"syn{i}a") in roster else 0, key=f"syn{i}a")
        syn_p2 = col2.selectbox(f"Pair {i} B", ["None"] + roster, 
                                index=(roster.index(st.session_state.get(f"syn{i}b")) + 1) if st.session_state.get(f"syn{i}b") in roster else 0, key=f"syn{i}b")
        if syn_p1 != "None" and syn_p2 != "None":
            synergy_pairs.append([syn_p1, syn_p2])

st.sidebar.subheader("Player Rankings")
st.sidebar.caption("DEF | MID | FWD (1=High, 3=Low)")
default_ranks = {
    "Player 1": "312", "Player 2": "321", "Player 3": "132", "Player 4": "123",
    "Player 5": "312", "Player 6": "312", "Player 7": "321", "Player 8": "213"
}
player_ranks = {}
rank_options = ["123", "132", "213", "231", "312", "321"]
for p in roster:
    saved_rank = st.session_state.get(f"rank_{p}", default_ranks.get(p, "312"))
    rank_idx = rank_options.index(saved_rank) if saved_rank in rank_options else 0
    rank = st.sidebar.selectbox(f"Rank for {p}", options=rank_options, index=rank_idx, key=f"rank_{p}")
    player_ranks[p] = rank

# --- SAVE CONFIG BUTTON ---
config_to_save = {"team_name": team_name, "opponent": opponent, "formation_choice": formation_choice, "roster_raw": roster_raw, "attending": attending}
for p in roster: config_to_save[f"rank_{p}"] = player_ranks[p]
for q in range(1, 5): config_to_save[f"gk_q{q}"] = quarterly_gks[q-1]
for i in range(1, 3):
    config_to_save[f"s{i}a"] = st.session_state[f"s{i}a"]
    config_to_save[f"s{i}b"] = st.session_state[f"s{i}b"]
    config_to_save[f"syn{i}a"] = st.session_state[f"syn{i}a"]
    config_to_save[f"syn{i}b"] = st.session_state[f"syn{i}b"]

st.sidebar.download_button("Download Current Config", data=json.dumps(config_to_save, indent=4), 
                           file_name=f"{team_name}_config.json", mime="application/json")

user_seed = st.sidebar.text_input("Seed (leave blank for random)", "")

current_seed = int(user_seed) if user_seed.isdigit() else st.session_state.seed
random.seed(current_seed)

# --- LOGIC (REUSED FROM YOUR SCRIPT) ---
def assign_positions(players, ranks, formation_key):
    f_cfg = FORMATION_CONFIGS[formation_key]
    slots, slot_types = f_cfg['slots'], f_cfg['slot_types']
    assignment = {s: None for s in slots}
    rem_players = list(players)
    random.shuffle(rem_players)
    for level in ['1', '2', '3']:
        for slot in slots:
            if assignment[slot] is None:
                idx = slot_types[slot]
                for p in rem_players:
                    if p in ranks and ranks[p][idx] == level:
                        assignment[slot] = p
                        rem_players.remove(p)
                        break
    for slot in slots:
        if assignment[slot] is None and rem_players:
            assignment[slot] = rem_players.pop(0)
    return assignment

@st.cache_data
def generate_rotation(attending, quarterly_gks, player_ranks, split_pairs, synergy_pairs, formation_key, seed):
    random.seed(seed)
    lineups = []
    con_played = {p: 0 for p in attending}
    sat_last = {p: False for p in attending}
    total_played = {p: 0 for p in attending}
    hp_played = {p: 0 for p in attending}
    
    for q in range(4):
        gk = quarterly_gks[q]
        for b in range(2):
            is_hp = (b == 0)
            candidates = [p for p in attending if p != gk]
            candidates.sort(key=lambda p: (not sat_last[p], total_played[p], con_played[p] >= 2))
            selected = []
            for p in candidates:
                if len(selected) < 4 and p not in selected:
                    can_play = (con_played[p] < 2 or sat_last[p])
                    split_clash = False
                    for pair in split_pairs:
                        if p in pair:
                            partner = pair[0] if p == pair[1] else pair[1]
                            if partner in selected: split_clash = True
                    
                    if can_play and not split_clash: 
                        selected.append(p)
                        # Synergy check
                        for pair in synergy_pairs:
                            if p in pair and len(selected) < 4:
                                partner = pair[0] if p == pair[1] else pair[1]
                                if partner in candidates and partner not in selected:
                                    p_can_play = (con_played[partner] < 2 or sat_last[partner])
                                    p_split_clash = False
                                    for s_pair in split_pairs:
                                        if partner in s_pair:
                                            s_partner = s_pair[0] if partner == s_pair[1] else s_pair[1]
                                            if s_partner in selected: p_split_clash = True
                                    if p_can_play and not p_split_clash:
                                        selected.append(partner)

            if len(selected) < 4:
                for p in candidates:
                    if p not in selected and len(selected) < 4: selected.append(p)
            assigned = assign_positions(selected, player_ranks, formation_key)
            assigned['GK'] = gk
            active = set(selected) | {gk}
            assigned['Bench'] = sorted([p for p in attending if p not in active])
            lineups.append(assigned)
            for p in attending:
                if p in active:
                    total_played[p] += 1
                    if is_hp: hp_played[p] += 1
                    con_played[p] = 1 if p == gk else con_played[p] + 1
                    sat_last[p] = False
                else:
                    con_played[p] = 0
                    sat_last[p] = True
    return lineups

# --- EXECUTION & SWAPS ---
lineups = generate_rotation(attending, quarterly_gks, player_ranks, split_pairs, synergy_pairs, formation_choice, current_seed)

st.header(f"Lineup for {team_name} vs {opponent} (Seed: {current_seed})")

with st.expander("Manual Swaps"):
    col1, col2, col3, col4 = st.columns(4)
    with col1: q_swap = st.selectbox("Quarter", [1,2,3,4])
    with col2: b_swap = st.selectbox("Block", [1,2])
    with col3: p1 = st.selectbox("Player 1", attending, key="p1")
    with col4: p2 = st.selectbox("Player 2", attending, key="p2")
    
    if st.button("Swap Players"):
        st.session_state.manual_swaps_5v5.append({'q': q_swap, 'b': b_swap, 'p1': p1, 'p2': p2})

    if st.button("Reset All Swaps"):
        st.session_state.manual_swaps_5v5 = []

# Apply manual swaps
for swap in st.session_state.manual_swaps_5v5:
    idx = (swap['q']-1)*2 + (swap['b']-1)
    l = lineups[idx]
    pos_fields = ['GK'] + FORMATION_CONFIGS[formation_choice]['slots']
    p1_pos = next((f for f in pos_fields if l[f] == swap['p1']), 'Bench' if swap['p1'] in l['Bench'] else None)
    p2_pos = next((f for f in pos_fields if l[f] == swap['p2']), 'Bench' if swap['p2'] in l['Bench'] else None)
    
    if p1_pos and p2_pos:
        if p1_pos == 'Bench':
            l[p2_pos] = swap['p1']
            l['Bench'].remove(swap['p1'])
            l['Bench'].append(swap['p2'])
        elif p2_pos == 'Bench':
            l[p1_pos] = swap['p2']
            l['Bench'].remove(swap['p2'])
            l['Bench'].append(swap['p1'])
        else:
            l[p1_pos], l[p2_pos] = l[p2_pos], l[p1_pos]
        l['Bench'].sort()

# Post-Swap Metadata Refresh
participation, hp_stats = {p: 0 for p in attending}, {p: 0 for p in attending}
pos_fields = ['GK'] + FORMATION_CONFIGS[formation_choice]['slots']
for i, l in enumerate(lineups):
    active = {l[k] for k in pos_fields}
    if i == 0:
        l['SubsOn'], l['SubsOff'] = sorted(list(active)), []
    else:
        prev_active = {lineups[i-1][k] for k in pos_fields}
        l['SubsOn'] = sorted([p for p in active if p not in prev_active])
        l['SubsOff'] = sorted([p for p in prev_active if p not in active])
    if i % 2 == 0:
        for p in active: hp_stats[p] += 1
        # Goalkeeper counts as 1 period for the entire quarter (2 blocks)
        participation[l['GK']] += 1

    # Field players count as 1 period per block
    for slot in FORMATION_CONFIGS[formation_choice]['slots']:
        participation[l[slot]] += 1

# --- PLOTTING FUNCTION ---
def create_plot(layout_type, lineups, participation, hp_stats, team_name, opponent, formation_key, seed):
    pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
    if layout_type == 'SingleColumn':
        nr, nc, fh, gh, eh, sp = 8, 1, 28, 0.88, 0.07, 0.5
    else:
        nr, nc, fh, gh, eh, sp = 4, 2, 20, 0.82, 0.08, 0.45

    fig, axs = pitch.grid(nrows=nr, ncols=nc, figheight=fh, grid_height=gh, title_height=0, endnote_height=eh, space=sp)
    fig.suptitle(f"{team_name} vs {opponent} | Seed: {current_seed}", fontsize=22, fontweight='bold', y=0.995)
    path_eff = [patheffects.withStroke(linewidth=3, foreground="black")]
    f_cfg = FORMATION_CONFIGS[formation_key]

    for i, ax in enumerate(axs['pitch'].flat):
        q, b = (i // 2) + 1, (i % 2) + 1
        l = lineups[i]
        pitch.draw(ax=ax)
        ax.set_title(f"Quarter {q} - Block {b}", fontsize=13, fontweight='bold', pad=5)
        for pos in ['GK'] + f_cfg['slots']:
            px, py = f_cfg['coords'][pos]
            color = '#f1c40f' if pos == 'GK' else '#3498db'
            pitch.scatter(px, py, s=400, c=color, edgecolors='white', ax=ax, zorder=3)
            pitch.annotate(l[pos], (px, py + 6), fontsize=9.5, ax=ax, color='white', path_effects=path_eff, fontweight='bold', ha='center')
        
        subs_text = f"ON: {', '.join(l['SubsOn'])}  |  OFF: {', '.join(l['SubsOff'])}\nBENCH: {', '.join(l['Bench'])}"
        ax.text(0.5, -0.05, subs_text, fontsize=9, ha='center', va='top', fontweight='bold', transform=ax.transAxes)

    # Create summary table in endnote
    ax_table = axs['endnote']
    ax_table.axis('off')
    return fig

@st.cache_data
def get_plot_bytes(layout_type, lineups, participation, hp_stats, team_name, opponent, formation_key, seed):
    fig = create_plot(layout_type, lineups, participation, hp_stats, team_name, opponent, formation_key, seed)
    buf = io.BytesIO()
    fig.savefig(buf, format="jpg", dpi=100, bbox_inches='tight')
    plt.close(fig)
    return buf.getvalue()

# --- DISPLAY & DOWNLOAD ---
tab1, tab2 = st.tabs(["Printable View", "Single Column View"])

with tab1:
    img_bytes1 = get_plot_bytes('Printable', lineups, participation, hp_stats, team_name, opponent, formation_choice, current_seed)
    st.image(img_bytes1)
    st.download_button(
        label="Download Printable JPG",
        data=img_bytes1,
        file_name=f"{team_name}_{opponent}_Printable.jpg",
        mime="image/jpeg"
    )

with tab2:
    img_bytes2 = get_plot_bytes('SingleColumn', lineups, participation, hp_stats, team_name, opponent, formation_choice, current_seed)
    st.image(img_bytes2)
    st.download_button(
        label="Download Single Column JPG",
        data=img_bytes2,
        file_name=f"{team_name}_{opponent}_Single.jpg",
        mime="image/jpeg"
    )

st.divider()
st.subheader("Player Participation Summary")
st.caption("Total periods played based on the current rotation (Field players count per block; GKs count as 1 per quarter).")

# Prepare and sort data for the table
summary_data = [{"Player": p, "Periods Played": participation[p]} for p in attending]
summary_data.sort(key=lambda x: x["Periods Played"], reverse=True)

col_l, col_m, col_r = st.columns([1, 2, 1])
with col_m:
    st.table(summary_data)

# Subtle footer to track version/sync time
last_sync = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime("%Y-%m-%d %H:%M:%S")
st.markdown(
    f"<div style='opacity: 0.3; text-align: center; font-size: 0.8em; margin-top: 50px;'>"
    f"Last synchronized: {last_sync}</div>",
    unsafe_allow_html=True
)