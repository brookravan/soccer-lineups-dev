# shared_logic.py
# Shared utilities for the 5v5 and 7v7 lineup generators.
# Import this module in each generator page — do not add format-specific logic here.

import matplotlib
import matplotlib.pyplot as plt
# Non-interactive backend must be set before pyplot is used
matplotlib.use('Agg')

import streamlit as st
from mplsoccer import Pitch
from matplotlib import patheffects
import random
import io

# --- POSITION ASSIGNMENT ---
# Source: both files (identical logic)
# Note: original versions read FORMATION_CONFIGS from module scope.
# formation_configs is now an explicit parameter so this function is
# format-agnostic and requires no globals.
def assign_positions(players, ranks, formation_key, formation_configs):
    """Assign players to formation slots based on position preference rankings."""
    f_cfg = formation_configs[formation_key]
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


# --- PITCH VISUALIZATION ---
# Source: both files (near-identical; only the per-period title label differs)
# Format-specific variation: each generator must supply `period_labels`, a list
# of strings with one entry per period in display order.
#   5v5 example: ["Quarter 1 - Block 1", "Quarter 1 - Block 2", ...]
#   7v7 example: ["Half 1: 0-10m", "Half 1: 10-15m", ...]
def create_plot(layout_type, lineups, participation, hp_stats, team_name, opponent,
                formation_key, formation_configs, seed, period_labels):
    """Render a grid of pitch diagrams, one per period."""
    pitch = Pitch(pitch_color='grass', line_color='white', stripe=True)
    if layout_type == 'SingleColumn':
        nr, nc, fh, gh, eh, sp = 8, 1, 28, 0.88, 0.07, 0.5
    else:
        nr, nc, fh, gh, eh, sp = 4, 2, 20, 0.82, 0.08, 0.45

    fig, axs = pitch.grid(nrows=nr, ncols=nc, figheight=fh, grid_height=gh,
                          title_height=0, endnote_height=eh, space=sp)
    fig.suptitle(f"{team_name} vs {opponent} | Seed: {seed}",
                 fontsize=22, fontweight='bold', y=0.995)
    path_eff = [patheffects.withStroke(linewidth=3, foreground="black")]
    f_cfg = formation_configs[formation_key]

    for i, ax in enumerate(axs['pitch'].flat):
        l = lineups[i]
        pitch.draw(ax=ax)
        ax.set_title(period_labels[i], fontsize=13, fontweight='bold', pad=5)
        for pos in ['GK'] + f_cfg['slots']:
            px, py = f_cfg['coords'][pos]
            color = '#f1c40f' if pos == 'GK' else '#3498db'
            pitch.scatter(px, py, s=400, c=color, edgecolors='white', ax=ax, zorder=3)
            pitch.annotate(l[pos], (px, py + 6), fontsize=9.5, ax=ax, color='white',
                           path_effects=path_eff, fontweight='bold', ha='center')

        subs_text = (f"ON: {', '.join(l['SubsOn'])}  |  OFF: {', '.join(l['SubsOff'])}"
                     f"\nBENCH: {', '.join(l['Bench'])}")
        ax.text(0.5, -0.05, subs_text, fontsize=9, ha='center', va='top',
                fontweight='bold', transform=ax.transAxes)

    ax_table = axs['endnote']
    ax_table.axis('off')
    return fig


# --- PLOT BYTES (CACHED) ---
# Source: both files (identical)
# Wraps create_plot and returns JPEG bytes for st.image / st.download_button.
@st.cache_data
def get_plot_bytes(layout_type, lineups, participation, hp_stats, team_name, opponent,
                   formation_key, formation_configs, seed, period_labels):
    """Render the pitch grid and return the result as JPEG bytes (cached)."""
    fig = create_plot(layout_type, lineups, participation, hp_stats, team_name, opponent,
                      formation_key, formation_configs, seed, period_labels)
    buf = io.BytesIO()
    fig.savefig(buf, format="jpg", dpi=100, bbox_inches='tight')
    plt.close(fig)
    return buf.getvalue()
