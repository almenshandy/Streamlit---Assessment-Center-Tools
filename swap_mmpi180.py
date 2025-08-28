import streamlit as st
import PyPDF2
import io
import zipfile

SEARCH_TEXT_MMPI = "LAPORAN TES PSIKOMETRIK MMPI 180 DIAGNOSTIK"
SEARCH_TEXT_BASIC_SCALES = "BASIC SCALES"

def swap_pdf_bytes(pdf_bytes, search_text_mmpi, search_text_basic_scales):
    reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
    total_pages = len(reader.pages)
    
    writer = PyPDF2.PdfWriter()
    mmpi_index = None
    basic_scales_index = None
    
    # Cari halaman yang mengandung teks MMPI
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if search_text_mmpi in text:
            mmpi_index = i
            break
    
    if mmpi_index is None:
        return None, f"SKIP: Teks '{search_text_mmpi}' tidak ditemukan dalam {total_pages} halaman"
    
    # Cari halaman yang mengandung teks BASIC SCALES (hanya jika total 3 atau 4 halaman)
    if total_pages in (3, 4):
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if search_text_basic_scales in text and i != mmpi_index:
                basic_scales_index = i
                break
    
    # Debug info
    debug_info = f"Total halaman: {total_pages}, Halaman MMPI ditemukan di index: {mmpi_index}"
    if total_pages in (3, 4) and basic_scales_index is not None:
        debug_info += f", Halaman BASIC SCALES ditemukan di index: {basic_scales_index}"
    elif total_pages in (3, 4):
        debug_info += f", Halaman BASIC SCALES tidak ditemukan"
    
    # Strategi: buat list halaman dengan urutan yang benar
    pages_to_add = []
    
    # 1. Tambahkan halaman MMPI sebagai halaman pertama
    pages_to_add.append(reader.pages[mmpi_index])
    
    # 2. Atur halaman berdasarkan jumlah halaman
    if total_pages == 3 and basic_scales_index is not None:
        # Urutan untuk 3 halaman: MMPI (1), BASIC SCALES (2), sisa (3)
        remaining_indices = [i for i in range(total_pages) if i != mmpi_index and i != basic_scales_index]
        if len(remaining_indices) != 1:
            debug_info += f" | ERROR: Jumlah halaman sisa tidak valid: {len(remaining_indices)}"
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            return output, debug_info
        
        # Tambahkan halaman kedua (BASIC SCALES)
        pages_to_add.append(reader.pages[basic_scales_index])
        # Tambahkan halaman ketiga (sisa)
        pages_to_add.append(reader.pages[remaining_indices[0]])
    elif total_pages == 4 and basic_scales_index is not None:
        # Urutan untuk 4 halaman: MMPI (1), sisa (2), BASIC SCALES (3), sisa (4)
        remaining_indices = [i for i in range(total_pages) if i != mmpi_index and i != basic_scales_index]
        if len(remaining_indices) != 2:
            debug_info += f" | ERROR: Jumlah halaman sisa tidak valid: {len(remaining_indices)}"
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            return output, debug_info
        
        # Tambahkan halaman kedua (sisa 1)
        pages_to_add.append(reader.pages[remaining_indices[0]])
        # Tambahkan halaman ketiga (BASIC SCALES)
        pages_to_add.append(reader.pages[basic_scales_index])
        # Tambahkan halaman keempat (sisa 2)
        pages_to_add.append(reader.pages[remaining_indices[1]])
    else:
        # Jika bukan 3 atau 4 halaman, atau BASIC SCALES tidak ditemukan, tambahkan sisa halaman secara berurutan
        for i in range(total_pages):
            if i != mmpi_index:
                pages_to_add.append(reader.pages[i])
    
    # 3. Tulis semua halaman ke writer
    for page in pages_to_add:
        writer.add_page(page)
    
    # Verifikasi: halaman hasil harus sama dengan total halaman asli
    result_page_count = len(pages_to_add)
    if result_page_count != total_pages:
        debug_info += f" | ERROR: Jumlah halaman hasil tidak sama dengan asli! Asli: {total_pages}, Hasil: {result_page_count}"
    else:
        debug_info += f" | SUCCESS: Halaman MMPI dipindahkan dari posisi {mmpi_index+1} ke posisi 1 ({total_pages} halaman ✓)"
        if total_pages == 3 and basic_scales_index is not None:
            debug_info += f", Halaman BASIC SCALES dipindahkan ke posisi 2"
        elif total_pages == 4 and basic_scales_index is not None:
            debug_info += f", Halaman BASIC SCALES dipindahkan ke posisi 3"
    
    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output, debug_info

def swap_mmpi180():
    # st.title("Pindahkan Halaman PDF MMPI-180 ke Halaman Pertama dan BASIC SCALES Sesuai Jumlah Halaman")
    
    st.info("""
    Aplikasi ini akan:
    1. **Memindahkan** halaman yang mengandung teks "LAPORAN TES PSIKOMETRIK MMPI 180 DIAGNOSTIK" ke halaman pertama.
    2. **Jika file memiliki tepat 3 halaman**, memindahkan halaman yang mengandung teks "BASIC SCALES" ke halaman kedua.
    3. **Jika file memiliki tepat 4 halaman**, memindahkan halaman yang mengandung teks "BASIC SCALES" ke halaman ketiga.
    
    ⚠️ **Proses semua PDF selama teks MMPI ditemukan**, tanpa batasan jumlah halaman untuk pemindahan MMPI.
    File tanpa teks MMPI akan di-skip. Pemindahan BASIC SCALES hanya dilakukan untuk file 3 atau 4 halaman.
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
                result = swap_pdf_bytes(uploaded_file.read(), SEARCH_TEXT_MMPI, SEARCH_TEXT_BASIC_SCALES)
                
                if result[0] is not None:  # Berhasil diproses
                    swapped_pdf, debug_info = result
                    zipf.writestr(f"{uploaded_file.name}", swapped_pdf.read())
                    processed_count += 1
                    debug_logs.append(f"✅ {uploaded_file.name}: {debug_info}")
                else:
                    # File di-skip (teks MMPI tidak ditemukan)
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
            file_name="hasil_pindah_mmpi180.zip",
            mime="application/zip"
        )

# Jalankan aplikasi
if __name__ == "__main__":
    swap_mmpi180()