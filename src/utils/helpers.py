import streamlit as st

# Mark route as not optimized when parameters change
def mark_route_as_not_optimized():
    st.session_state.route_optimized = False