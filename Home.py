import streamlit as st

st.set_page_config(
    page_title="Soccer Lineup Generator",
    page_icon="⚽",
    layout="wide"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #dce8dc;
    }
    section[data-testid="stSidebar"] {
        background-color: #1e4d35;
    }
    section[data-testid="stSidebar"] * {
        color: #f0fdf4;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    div.stButton > button:first-child {
        background-color: #166534;
        color: white;
    }
    h1 {
        color: #166534;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Soccer Lineup Generator")
st.write("""
Select a format from the sidebar to begin generating rotations:
- **5v5 Generator**: Built for youth 5v5 teams.
- **7v7 Generator**: Built for youth 7v7 teams.
""")