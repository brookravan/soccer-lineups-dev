import streamlit as st

st.set_page_config(
    page_title="Soccer Lineup Master",
    page_icon="⚽",
    layout="wide"
)

st.title("Welcome to the Soccer Lineup Generator")
st.write("""
Select a format from the sidebar to begin generating rotations:
- **5v5 Generator**: Optimized for small-sided indoor or recreational play.
- **7v7 Generator**: Advanced rotation logic for 7v7 league play.
""")