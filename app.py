import streamlit as st
from swap_mmpi2 import *
from process_disc3 import *
from extract_disc3 import *

def main():
    st.title("Assessment Center Tools")

    menu = ["Swap MMPI-2", "Split DISC3", "Extract DISC3"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Swap MMPI-2":
        swap_mmpi2()
    elif choice == "Split DISC3":
        split_disc3_streamlit()
    elif choice == "Extract DISC3":
        extract_disc3_streamlit()

if __name__ == "__main__":
    main()