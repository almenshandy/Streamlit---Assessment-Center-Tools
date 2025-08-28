import streamlit as st
import PyPDF2
import io
import zipfile

SEARCH_TEXT = "LAPORAN TES PSIKOMETRIK MMPI-2"

def swap_pdf_bytes(pdf_bytes, search_text):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    
    # VALIDASI: Hanya proses file dengan tepat 4 halaman
    if total_pages != 4:
        return None, f"SKIP: File memiliki {total_pages} halaman (hanya file 4 halaman yang diproses)"
    
    writer = PyPDF2.PdfWriter()
    target_index = None
    
    # Cari halaman yang mengandung teks target
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if search_text in text:
            target_index = i
            break
    
    if target_index is None:
        return None, f"SKIP: Teks '{search_text}' tidak ditemukan dalam 4 halaman"
    
    # Debug info
    debug_info = f"Total halaman: {total_pages} ✓, Halaman target ditemukan di index: {target_index}"
    
    # Strategi baru: buat list halaman dengan urutan yang benar
    pages_to_add = []
    
    # 1. Tambahkan halaman target sebagai halaman pertama
    pages_to_add.append(reader.pages[target_index])
    
    # 2. Tambahkan semua halaman lain secara berurutan, SKIP halaman target
    for i in range(total_pages):
        if i != target_index:  # HANYA skip halaman target
            pages_to_add.append(reader.pages[i])
    
    # 3. Tulis semua halaman ke writer
    for page in pages_to_add:
        writer.add_page(page)
    
    # Verifikasi: halaman hasil harus tepat 4 halaman
    result_page_count = len(pages_to_add)
    if result_page_count != 4:
        debug_info += f" | ERROR: Jumlah halaman hasil tidak 4! Hasil: {result_page_count}"
    else:
        debug_info += f" | SUCCESS: Halaman dipindahkan dari posisi {target_index+1} ke posisi 1 (4 halaman ✓)"
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output, debug_info

def swap_mmpi567():
    st.title("Pindahkan Halaman PDF MMPI-2 ke Halaman Pertama")
    
    st.info("""
    Aplikasi ini akan **memindahkan** (bukan menyalin) halaman yang mengandung 
    teks "LAPORAN TES PSIKOMETRIK MMPI-2" ke halaman pertama dalam PDF.
    
    ⚠️ **HANYA file PDF dengan tepat 4 halaman yang akan diproses.**
    File dengan jumlah halaman lain akan di-skip.
    """)
    
    uploaded_files = st.file_uploader(
        "Upload beberapa file PDF", type="pdf", accept_multiple_files=True
    )
    
    if uploaded_files:
        processed_count = 0
        skipped_count = 0
        
        # Container untuk menampilkan log debug
        debug_container = st.empty()
        debug_logs = []
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zipf:
            for uploaded_file in uploaded_files:
                result = swap_pdf_bytes(uploaded_file.read(), SEARCH_TEXT)
                
                if result[0] is not None:  # Berhasil diproses
                    swapped_pdf, debug_info = result
                    zipf.writestr(f"{uploaded_file.name}", swapped_pdf.read())
                    processed_count += 1
                    debug_logs.append(f"✅ {uploaded_file.name}: {debug_info}")
                else:
                    # File di-skip (bukan 4 halaman atau teks tidak ditemukan)
                    _, debug_info = result
                    zipf.writestr(f"{uploaded_file.name}", uploaded_file.getvalue())
                    skipped_count += 1
                    debug_logs.append(f"⏭️ {uploaded_file.name}: {debug_info}")
        
        # Tampilkan debug logs
        with debug_container.container():
            st.subheader("Log Pemrosesan:")
            for log in debug_logs:
                if "SUCCESS" in log:
                    st.success(log)
                elif "ERROR" in log:
                    st.error(log)
                elif "SKIP" in log:
                    st.warning(log)
                else:
                    st.info(log)
        
        zip_buffer.seek(0)
        
        # Tampilkan status pemrosesan
        col1, col2 = st.columns(2)
        with col1:
            if processed_count > 0:
                st.success(f"✅ {processed_count} file berhasil diproses")
        with col2:
            if skipped_count > 0:
                st.info(f"⏭️ {skipped_count} file di-skip")
        
        st.download_button(
            label="Download Semua Hasil (ZIP)",
            data=zip_buffer,
            file_name="hasil_pindah_mmpi2.zip",
            mime="application/zip"
        )

# Jalankan aplikasi
if __name__ == "__main__":
    swap_mmpi567()