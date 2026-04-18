import streamlit as st
import random
import json
import os
from datetime import datetime

import streamlit.components.v1 as components

from shared_logic import assign_positions, get_plot_bytes

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

st.sidebar.subheader("Game Structure")
quarter_duration = st.sidebar.number_input("Quarter duration (min)", min_value=1, max_value=30, step=1, value=12, key='quarter_duration')
subs_per_quarter = st.sidebar.number_input("Subs per quarter", min_value=1, max_value=4, step=1, value=2, key='subs_per_quarter')
block_secs = int((quarter_duration / subs_per_quarter) * 60)

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

user_seed = st.sidebar.text_input("Seed (leave blank for random)", "")
current_seed = int(user_seed) if user_seed.isdigit() else st.session_state.seed
random.seed(current_seed)

# --- SAVE CONFIG BUTTON ---
config_to_save = {"team_name": team_name, "opponent": opponent, "formation_choice": formation_choice, "roster_raw": roster_raw, "attending": attending}
for p in roster: config_to_save[f"rank_{p}"] = player_ranks[p]
for q in range(1, 5): config_to_save[f"gk_q{q}"] = quarterly_gks[q-1]
for i in range(1, 3):
    config_to_save[f"s{i}a"] = st.session_state[f"s{i}a"]
    config_to_save[f"s{i}b"] = st.session_state[f"s{i}b"]
    config_to_save[f"syn{i}a"] = st.session_state[f"syn{i}a"]
    config_to_save[f"syn{i}b"] = st.session_state[f"syn{i}b"]
config_to_save["seed"] = current_seed
config_to_save["user_seed"] = str(current_seed)
config_to_save["quarter_duration"] = quarter_duration
config_to_save["subs_per_quarter"] = subs_per_quarter
# manual_swaps_5v5 is added at download time (main body) so it captures the current run's swaps

@st.cache_data
def generate_rotation(attending, quarterly_gks, player_ranks, split_pairs, synergy_pairs, formation_key, seed, subs_per_quarter):
    random.seed(seed)
    lineups = []
    con_played = {p: 0 for p in attending}
    sat_last = {p: False for p in attending}
    total_played = {p: 0 for p in attending}
    hp_played = {p: 0 for p in attending}
    # Mirrors the display participation table: GK counts once per quarter (not per block),
    # field players count once per block. Used as the sort key so the selection algorithm
    # prioritizes players who are genuinely behind on visible participation credit.
    part_score = {p: 0 for p in attending}
    
    # Tracks which slot types (0=DEF, 1=MID, 2=FWD) each player has been assigned so far
    positions_played = {p: set() for p in attending}

    for q in range(4):
        gk = quarterly_gks[q]
        for b in range(subs_per_quarter):
            is_hp = (b == 0)
            candidates = [p for p in attending if p != gk]
            # Primary sort: fewest participation credits first (mirrors the display table).
            # sat_last is a tiebreaker so recently-rested players break ties fairly.
            candidates.sort(key=lambda p: (part_score[p], not sat_last[p], con_played[p] >= 2))
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
            assigned = assign_positions(selected, player_ranks, formation_key, FORMATION_CONFIGS, positions_played)
            assigned['GK'] = gk
            active = set(selected) | {gk}
            assigned['Bench'] = sorted([p for p in attending if p not in active])
            lineups.append(assigned)
            # Update position variety tracking for field players
            for slot in FORMATION_CONFIGS[formation_key]['slots']:
                p = assigned[slot]
                if p:
                    positions_played[p].add(FORMATION_CONFIGS[formation_key]['slot_types'][slot])
            for p in attending:
                if p in active:
                    total_played[p] += 1
                    if is_hp: hp_played[p] += 1
                    con_played[p] = 1 if p == gk else con_played[p] + 1
                    sat_last[p] = False
                    # GK earns 1 credit for the whole quarter (first block only);
                    # field players earn 1 credit per block.
                    if p == gk:
                        if is_hp: part_score[p] += 1
                    else:
                        part_score[p] += 1
                else:
                    con_played[p] = 0
                    sat_last[p] = True
    return lineups

# --- EXECUTION & SWAPS ---
lineups = generate_rotation(attending, quarterly_gks, player_ranks, split_pairs, synergy_pairs, formation_choice, current_seed, subs_per_quarter)

st.header(f"Lineup for {team_name} vs {opponent} (Seed: {current_seed})")

with st.expander("⏱ Game Timer", expanded=False):
    # Build BLOCKS array dynamically from game structure settings
    _blocks_entries = ",\n        ".join(
        "{label:'Quarter " + str(q+1) + " \u2013 Block " + str(b+1) + "', dur:" + str(block_secs) + "}"
        for q in range(4) for b in range(subs_per_quarter)
    )
    components.html("""
    <div style="font-family:-apple-system,sans-serif;background:#f8fafc;border:1px solid #cbd5e1;border-radius:8px;padding:16px 20px;max-width:480px;margin:0 auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
            <span id="blk-label" style="font-weight:700;font-size:1.05em;color:#166534;"></span>
            <span id="blk-counter" style="color:#94a3b8;font-size:0.85em;"></span>
        </div>
        <div id="time-disp" style="font-size:3.4em;font-weight:700;text-align:center;color:#0f172a;letter-spacing:3px;margin:4px 0 10px;"></div>
        <div style="background:#e2e8f0;border-radius:4px;height:6px;margin-bottom:14px;overflow:hidden;">
            <div id="prog-bar" style="background:#166534;height:6px;width:100%;border-radius:4px;"></div>
        </div>
        <div style="display:flex;gap:8px;justify-content:center;">
            <button onclick="prevBlock()" style="padding:7px 14px;border:1px solid #166534;color:#166534;background:#fff;border-radius:5px;cursor:pointer;font-size:0.9em;">&#9664; Prev</button>
            <button id="start-btn" onclick="toggleTimer()" style="padding:7px 20px;background:#166534;color:#fff;border:none;border-radius:5px;cursor:pointer;font-size:0.9em;min-width:95px;">&#9654; Start</button>
            <button onclick="resetBlock()" style="padding:7px 14px;border:1px solid #166534;color:#166534;background:#fff;border-radius:5px;cursor:pointer;font-size:0.9em;">&#8635; Reset</button>
            <button onclick="nextBlock()" style="padding:7px 14px;border:1px solid #166534;color:#166534;background:#fff;border-radius:5px;cursor:pointer;font-size:0.9em;">Next &#9654;</button>
        </div>
        <div id="status-msg" style="text-align:center;margin-top:10px;font-size:0.82em;min-height:18px;color:#94a3b8;"></div>
    </div>
    <script>
    const STORAGE_KEY = 'soccerTimer_5v5';
    const BLOCKS = [
        """ + _blocks_entries + """
    ];

    let curBlock = 0;
    let isRunning = false;
    let secsLeft = BLOCKS[0].dur; // seconds remaining at last pause
    let startedAt = null;          // Date.now() when timer was last started
    let ticker = null;

    function getTimeLeft() {
        if (isRunning && startedAt !== null) {
            return Math.max(0, secsLeft - (Date.now() - startedAt) / 1000);
        }
        return secsLeft;
    }

    function fmt(s) {
        s = Math.ceil(s);
        return String(Math.floor(s / 60)).padStart(2,'0') + ':' + String(s % 60).padStart(2,'0');
    }

    function updateDisplay() {
        const tl = getTimeLeft();
        document.getElementById('blk-label').textContent = BLOCKS[curBlock].label;
        document.getElementById('blk-counter').textContent = 'Block ' + (curBlock+1) + ' of ' + BLOCKS.length;
        document.getElementById('time-disp').textContent = fmt(tl);
        document.getElementById('prog-bar').style.width = ((tl / BLOCKS[curBlock].dur) * 100) + '%';
        document.getElementById('start-btn').textContent = isRunning ? '\u23F8 Pause' : '\u25B6 Start';
        const msg = document.getElementById('status-msg');
        if (tl <= 0) {
            msg.textContent = '\u23F1 Time\u2019s up \u2014 make your subs and hit Next';
            msg.style.color = '#dc2626';
        } else {
            msg.textContent = '';
            msg.style.color = '#94a3b8';
        }
    }

    function playBeep() {
        try {
            const ctx = new (window.AudioContext || window.webkitAudioContext)();
            [0, 0.3, 0.6].forEach(t => {
                const osc = ctx.createOscillator();
                const gain = ctx.createGain();
                osc.connect(gain); gain.connect(ctx.destination);
                osc.frequency.value = 880;
                gain.gain.setValueAtTime(0.5, ctx.currentTime + t);
                gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + t + 0.25);
                osc.start(ctx.currentTime + t);
                osc.stop(ctx.currentTime + t + 0.25);
            });
        } catch(e) {}
    }

    function saveState() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify({curBlock, isRunning, secsLeft, startedAt}));
    }

    function loadState() {
        try {
            const s = JSON.parse(localStorage.getItem(STORAGE_KEY));
            if (!s) return;
            curBlock  = s.curBlock  ?? 0;
            isRunning = s.isRunning ?? false;
            secsLeft  = s.secsLeft  ?? BLOCKS[0].dur;
            startedAt = s.startedAt ?? null;
            // If it was running, check whether time has already expired
            if (isRunning && startedAt !== null && getTimeLeft() <= 0) {
                isRunning = false; secsLeft = 0; startedAt = null;
            }
        } catch(e) {}
    }

    function tick() {
        const tl = getTimeLeft();
        updateDisplay();
        if (tl <= 0) {
            clearInterval(ticker); ticker = null;
            isRunning = false; secsLeft = 0; startedAt = null;
            saveState(); playBeep(); updateDisplay();
        }
    }

    function toggleTimer() {
        if (isRunning) {
            secsLeft = getTimeLeft(); startedAt = null; isRunning = false;
            clearInterval(ticker); ticker = null;
        } else {
            if (secsLeft <= 0) secsLeft = BLOCKS[curBlock].dur;
            startedAt = Date.now(); isRunning = true;
            ticker = setInterval(tick, 250);
        }
        saveState(); updateDisplay();
    }

    function resetBlock() {
        clearInterval(ticker); ticker = null;
        isRunning = false; secsLeft = BLOCKS[curBlock].dur; startedAt = null;
        saveState(); updateDisplay();
    }

    function nextBlock() {
        if (curBlock < BLOCKS.length - 1) {
            clearInterval(ticker); ticker = null;
            isRunning = false; curBlock++; secsLeft = BLOCKS[curBlock].dur; startedAt = null;
            saveState(); updateDisplay();
        }
    }

    function prevBlock() {
        if (curBlock > 0) {
            clearInterval(ticker); ticker = null;
            isRunning = false; curBlock--; secsLeft = BLOCKS[curBlock].dur; startedAt = null;
            saveState(); updateDisplay();
        }
    }

    loadState();
    if (isRunning && startedAt !== null) { ticker = setInterval(tick, 250); }
    updateDisplay();
    </script>
    """, height=230)

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

# --- DISPLAY & DOWNLOAD ---
period_labels = [f"Quarter {q+1} - Block {b+1}" for q in range(4) for b in range(subs_per_quarter)]
tab1, tab2 = st.tabs(["Printable View", "Single Column View"])

with tab1:
    img_bytes1 = get_plot_bytes('Printable', lineups, participation, hp_stats, team_name, opponent, formation_choice, FORMATION_CONFIGS, current_seed, period_labels)
    st.image(img_bytes1)
    st.download_button(
        label="Download Printable JPG",
        data=img_bytes1,
        file_name=f"{team_name}_{opponent}_Printable.jpg",
        mime="image/jpeg"
    )

with tab2:
    img_bytes2 = get_plot_bytes('SingleColumn', lineups, participation, hp_stats, team_name, opponent, formation_choice, FORMATION_CONFIGS, current_seed, period_labels)
    st.image(img_bytes2)
    st.download_button(
        label="Download Single Column JPG",
        data=img_bytes2,
        file_name=f"{team_name}_{opponent}_Single.jpg",
        mime="image/jpeg"
    )

st.divider()
# Download button placed here (after swap section) so it captures swaps added in this run
config_to_save["manual_swaps_5v5"] = st.session_state.get('manual_swaps_5v5', [])
st.download_button("Download Current Config", data=json.dumps(config_to_save, indent=4),
                   file_name=f"{team_name}_config.json", mime="application/json")

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