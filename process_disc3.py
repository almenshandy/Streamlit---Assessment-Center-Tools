import os
import pdfplumber
from PyPDF2 import PdfReader, PdfWriter
import streamlit as st
import tempfile
import shutil
import zipfile
from io import BytesIO

def is_nomor_page(page_text):
    lines = page_text.split('\n')
    for line in lines:
        line = line.strip()
        if line.lower().startswith('nomor :'):
            return True
    return False

def split_pdf_streamlit(uploaded_file):
    """Split PDF from uploaded file and return list of (filename, bytes)"""
    temp_dir = tempfile.mkdtemp()
    input_path = os.path.join(temp_dir, uploaded_file.name)
    with open(input_path, "wb") as f:
        f.write(uploaded_file.read())

    pdf_reader = PdfReader(input_path)
    total_pages = len(pdf_reader.pages)
    current_writer = None
    file_count = 0
    base_name = os.path.splitext(os.path.basename(uploaded_file.name))[0]
    output_files = []

    with pdfplumber.open(input_path) as pdf:
        for page_num in range(total_pages):
            page_text = pdf.pages[page_num].extract_text() or ""
            if is_nomor_page(page_text):
                if current_writer is not None:
                    output_filename = f'{base_name}_document_{file_count}.pdf'
                    output_path = os.path.join(temp_dir, output_filename)
                    with open(output_path, 'wb') as output_file:
                        current_writer.write(output_file)
                    with open(output_path, "rb") as f:
                        output_files.append((output_filename, f.read()))
                file_count += 1
                current_writer = PdfWriter()
            if current_writer is not None:
                current_writer.add_page(pdf_reader.pages[page_num])

    if current_writer is not None and len(current_writer.pages) > 0:
        output_filename = f'{base_name}_document_{file_count}.pdf'
        output_path = os.path.join(temp_dir, output_filename)
        with open(output_path, 'wb') as output_file:
            current_writer.write(output_file)
        with open(output_path, "rb") as f:
            output_files.append((output_filename, f.read()))

    shutil.rmtree(temp_dir)
    return output_files

def split_disc3_streamlit():
    st.header("Split DISC3 PDF")
    uploaded_file = st.file_uploader("Upload PDF file", type=["pdf"])
    if uploaded_file is not None:
        with st.spinner("Memproses file..."):
            try:
                output_files = split_pdf_streamlit(uploaded_file)
                if output_files:
                    # Buat ZIP di memori
                    zip_buffer = BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for filename, file_bytes in output_files:
                            zip_file.writestr(filename, file_bytes)
                    zip_buffer.seek(0)
                    st.success(f"Berhasil memisahkan menjadi {len(output_files)} file.")
                    st.download_button(
                        label="Download Semua (DISC3-SplitFile.zip)",
                        data=zip_buffer,
                        file_name="DISC3-SplitFile.zip",
                        mime="application/zip"
                    )
                else:
                    st.warning("Tidak ada file yang dihasilkan dari PDF ini.")
            except Exception as e:
                st.error(f"Terjadi kesalahan: {str(e)}")