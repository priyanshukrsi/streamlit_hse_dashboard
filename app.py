import streamlit as st
from page import Leading_Indicator_1, Leading_Indicator_2, Leading_Indicator_3, Leading_Indicator_4, Leading_Indicator_5

st.set_page_config(page_title="HSE Dashboard", layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "Health Safety & Environment"


st.sidebar.title("Navigation")

with st.sidebar.expander("HSE Leading Indicators"):
    if st.button("HSE Leading Indicator 1", use_container_width=True):
        st.session_state.page = "📈 HSE Leading Indicator 1"
    if st.button("HSE Leading Indicator 2", use_container_width=True):
        st.session_state.page = "HSE Leading Indicator 2"
    if st.button("HSE Leading Indicator 3", use_container_width=True):
        st.session_state.page = "HSE Leading Indicator 3"
    if st.button("HSE Leading Indicator 4", use_container_width=True):
        st.session_state.page = "HSE Leading Indicator 4"
    if st.button("HSE Leading Indicator 5", use_container_width=True):
        st.session_state.page = "HSE Leading Indicator 5"


st.title(st.session_state.page)

if st.session_state.page == "📈 HSE Leading Indicator 1":
    Leading_Indicator_1.show()

elif st.session_state.page == "HSE Leading Indicator 2":
    Leading_Indicator_2.show()

elif st.session_state.page == "HSE Leading Indicator 3":
    Leading_Indicator_3.show()

elif st.session_state.page == "HSE Leading Indicator 4":
    Leading_Indicator_4.show()

elif st.session_state.page == "HSE Leading Indicator 5":
    Leading_Indicator_5.show()