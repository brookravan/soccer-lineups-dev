import streamlit as st

st.set_page_config(
    page_title="Soccer Lineup Generator",
    page_icon="⚽",
    layout="wide"
)


st.title("Soccer Lineup Generator")
st.write("""
Select a format from the sidebar to begin generating rotations:
- **5v5 Generator**: Built for youth 5v5 teams.
- **7v7 Generator**: Built for youth 7v7 teams.
""")