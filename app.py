import streamlit as st
from swap_mmpi180 import *
from swap_mmpi567 import *
from process_disc3 import *
from extract_disc3 import *

def main():
    st.title("Tools Tes Online")

    menu = ["Swap MMPI-567", "Swap MMPI-180","Split DISC3", "Extract DISC3"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Swap MMPI-567":
        swap_mmpi567()
    elif choice == "Swap MMPI-180":
        # st.write("Halaman PDF MMPI-180 masih dalam pengembangan.")
        swap_mmpi180()
    elif choice == "Split DISC3":
        split_disc3_streamlit()
    elif choice == "Split DISC3":
        split_disc3_streamlit()
    elif choice == "Extract DISC3":
        extract_disc3_streamlit()

if __name__ == "__main__":
    main()