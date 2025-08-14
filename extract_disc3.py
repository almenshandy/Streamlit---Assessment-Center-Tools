import pdfplumber
import re
import pandas as pd
import streamlit as st
import tempfile
import os

def extract_nomor_tes_from_uploaded(files):
    results = []
    pattern = r'Nomor\s*:\s*([^|]+)\|'
    for uploaded_file in files:
        # Simpan file ke temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name
        try:
            with pdfplumber.open(tmp_path) as pdf:
                total_pages = len(pdf.pages)
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        for match in matches:
                            cleaned_match = match.strip()
                            if cleaned_match:
                                results.append({
                                    'File': uploaded_file.name,
                                    'Nomor Tes': cleaned_match,
                                    'Halaman': page_num,
                                    'Jumlah Halaman': total_pages
                                })
        except Exception as e:
            st.warning(f"Error memproses {uploaded_file.name}: {e}")
        finally:
            os.unlink(tmp_path)
    return results

def extract_disc3_streamlit():
    st.header("Daftar Nomor Tes dari PDF (DISC3)")
    uploaded_files = st.file_uploader(
        "Upload satu atau beberapa file PDF", 
        type=["pdf"], 
        accept_multiple_files=True
    )
    if uploaded_files:
        if st.button("Tampilkan Nomor Tes"):
            with st.spinner("Memproses file PDF..."):
                results = extract_nomor_tes_from_uploaded(uploaded_files)
                df = pd.DataFrame(results)
                if not df.empty:
                    st.success(f"Berhasil mengekstrak {len(df)} nomor tes dari PDF.")
                    st.dataframe(
                        df,
                        column_config={
                            "File": st.column_config.TextColumn("Nama File"),
                            "Nomor Tes": st.column_config.TextColumn("Nomor Tes"),
                            "Halaman": st.column_config.NumberColumn("Halaman"),
                            "Jumlah Halaman": st.column_config.NumberColumn("Jumlah Halaman"),
                        },
                        use_container_width=True
                    )
                else:
                    st.warning("Tidak ada nomor tes yang ditemukan di file PDF.")