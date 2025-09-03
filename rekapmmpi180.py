import streamlit as st
import PyPDF2
import re
import pandas as pd
from io import BytesIO

def extract_text_from_pdf(uploaded_file):
    """
    Mengekstrak teks dari file PDF yang diupload
    """
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

def extract_text_between_validitas_and_internal(text):
    """
    Mengekstrak teks setelah "I. Validitas / Akurasi" dan sebelum "II. Internal Pribadi"
    """
    try:
        # Mencari posisi "I. Validitas / Akurasi"
        validitas_pattern = r"I\.\s*Validitas\s*/\s*Akurasi"
        validitas_match = re.search(validitas_pattern, text, re.IGNORECASE)
        
        if not validitas_match:
            return "I. Validitas / Akurasi tidak ditemukan dalam dokumen"
        
        # Mengambil teks setelah "I. Validitas / Akurasi"
        text_after_validitas = text[validitas_match.end():]
        
        # Mencari posisi "II. Internal Pribadi"
        internal_pattern = r"II\.\s*Internal\s*Pribadi"
        internal_match = re.search(internal_pattern, text_after_validitas, re.IGNORECASE)
        
        if internal_match:
            # Ambil teks antara keduanya
            extracted_text = text_after_validitas[:internal_match.start()].strip()
            return extracted_text
        else:
            # Jika tidak ada "II. Internal Pribadi", ambil sampai akhir
            return text_after_validitas.strip()
            
    except Exception as e:
        return f"Error dalam ekstraksi teks dari bagian validitas: {str(e)}"

def extract_text_after_kesimpulan(text):
    """
    Mengekstrak teks setelah "2." dan sebelum "3." yang berada setelah "VI. Kesimpulan"
    Jika tidak ditemukan, cari di bagian antara "I. Validitas / Akurasi" dan "II. Internal Pribadi"
    """
    try:
        # Mencari posisi "VI. Kesimpulan"
        kesimpulan_pattern = r"VI\.\s*Kesimpulan"
        kesimpulan_match = re.search(kesimpulan_pattern, text, re.IGNORECASE)
        
        if kesimpulan_match:
            # Mengambil teks setelah "VI. Kesimpulan"
            text_after_kesimpulan = text[kesimpulan_match.end():]
            
            # Mencari pola "2." dan "3."
            pattern_2 = r"2\.\s*(.*?)(?=3\.|$)"
            match = re.search(pattern_2, text_after_kesimpulan, re.DOTALL | re.IGNORECASE)
            
            if match:
                extracted_text = match.group(1).strip()
                return extracted_text
        
        # Jika tidak ditemukan di bagian kesimpulan, cari di bagian validitas
        validitas_text = extract_text_between_validitas_and_internal(text)
        if validitas_text and "tidak ditemukan" not in validitas_text and "Error" not in validitas_text:
            return validitas_text
        
        return "Teks tidak ditemukan di bagian kesimpulan maupun bagian validitas"
            
    except Exception as e:
        return f"Error dalam ekstraksi teks: {str(e)}"

def classify_condition(extracted_text):
    """
    Mengklasifikasi kondisi berdasarkan teks yang diekstrak
    """
    if not extracted_text or "Error" in extracted_text or "tidak ditemukan" in extracted_text:
        return "-"
    
    text_lower = extracted_text.lower()
    
    # Cek kondisi akurasi dan konsistensi terlebih dahulu
    if "hasil tes ini tidak konsisten, tidak akurat" in text_lower:
        return "Tidak Konsisten & Tidak Akurat"
    elif "hasil tes ini konsisten, tetapi tidak akurat  dan tidak dapat dipercaya, " in text_lower:
        return "Tidak Akurat"
    
    # Cek kondisi stres
    elif "tidak mengalami stres" in text_lower:
        return "Tidak Stres"
    elif "stres berat" in text_lower or "mengalami stres berat" in text_lower:
        return "Stres Berat"
    elif "stress ringan" in text_lower or "mengalami stres ringan" in text_lower:
        return "Stres Ringan"
    elif "stres sedang" in text_lower or "mengalami stres sedang" in text_lower:
        return "Stres Sedang"
    else:
        return "-"

def rekap_mmpi180():
    st.title("Ekstraksi Teks MMPI-180 PDF")
    st.write("Upload file PDF (bisa banyak file sekaligus) untuk mengekstrak teks setelah '2.' dan sebelum '3.' dari bagian VI. Kesimpulan")
    
    uploaded_files = st.file_uploader("Pilih file PDF", type="pdf", accept_multiple_files=True)
    
    if uploaded_files:
        st.write(f"{len(uploaded_files)} file berhasil diupload!")
        
        # Container untuk hasil ekstraksi
        results = []
        
        # Progress bar
        progress_bar = st.progress(0)
        
        # Proses setiap file
        for i, uploaded_file in enumerate(uploaded_files):
            # st.subheader(f"Memproses: {uploaded_file.name}")
            
            # Update progress bar
            progress_bar.progress((i + 1) / len(uploaded_files))
            
            # Ekstrak teks dari PDF
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            if pdf_text:
                # Ekstrak teks spesifik
                extracted_text = extract_text_after_kesimpulan(pdf_text)
                
                # Klasifikasi kondisi
                kondisi = classify_condition(extracted_text)
                
                # Simpan hasil
                results.append({
                    "Nama File": uploaded_file.name,
                    "Teks Terekstrak": extracted_text,
                    "Kondisi": kondisi,
                    "Status": "Berhasil" if "Error" not in extracted_text and "tidak ditemukan" not in extracted_text else "Error"
                })
                
                # Tampilkan hasil per file
                # st.text_area(f"Hasil ekstraksi {uploaded_file.name}:", extracted_text, height=150, key=f"result_{i}")
            else:
                results.append({
                    "Nama File": uploaded_file.name,
                    "Teks Terekstrak": "Error: Tidak dapat membaca PDF",
                    "Kondisi": "-",
                    "Status": "Error"
                })
        
        # Tampilkan ringkasan hasil
        st.subheader("Ringkasan Hasil Ekstraksi")
        df_results = pd.DataFrame(results)
        st.dataframe(df_results)
        
        # Tombol download hasil sebagai CSV
        csv = df_results.to_csv(index=False)
        st.download_button(
            label="Download Hasil sebagai CSV",
            data=csv,
            file_name="hasil_ekstraksi_mmpi180.csv",
            mime="text/csv"
        )
        
        # Statistik
        total_files = len(results)
        success_files = len([r for r in results if r["Status"] == "Berhasil"])
        error_files = total_files - success_files
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total File", total_files)
        with col2:
            st.metric("Berhasil", success_files)
        with col3:
            st.metric("Error", error_files)
        
        # Opsi untuk menampilkan seluruh teks PDF (untuk debugging)
        if st.checkbox("Tampilkan seluruh teks PDF semua file"):
            for i, uploaded_file in enumerate(uploaded_files):
                pdf_text = extract_text_from_pdf(uploaded_file)
                if pdf_text:
                    st.subheader(f"Seluruh Teks PDF - {uploaded_file.name}:")
                    st.text_area(f"Full text {uploaded_file.name}:", pdf_text, height=300, key=f"full_text_{i}")

if __name__ == "__main__":
    rekap_mmpi180()