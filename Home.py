import streamlit as st

st.set_page_config(
    page_title="Soccer Lineup Generator",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f1f5f9;
    }
    section[data-testid="stSidebar"] {
        background-color: #064e3b;
    }
    section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {
        color: white !important;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    div.stButton > button:first-child {
        background-color: #15803d;
        color: white;
        border: 2px solid #14532d;
        font-weight: bold;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    div.stButton > button:first-child:hover {
        background-color: #166534;
        border-color: #15803d;
    }
    h1 {
        color: #15803d;
        font-weight: 800;
        text-transform: uppercase;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Soccer Lineup Generator")
st.write("""
Select a format from the sidebar to begin generating rotations:
- **5v5 Generator**: Built for youth 5v5 teams.
- **7v7 Generator**: Built for youth 7v7 teams.
""")