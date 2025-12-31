import streamlit as st
import google.generativeai as genai
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import time
from xhtml2pdf import pisa
from io import BytesIO
from streamlit_lottie import st_lottie
import requests

# 1. SETUP & CONFIGURATION
load_dotenv()
st.set_page_config(page_title="Modul Cerdas", page_icon="📖", layout="wide")

# Link Donasi
DONATE_LINK = "https://saweria.co/usernamekamu" 

# Fungsi Load Animasi
def load_lottieurl(url: str):
    try:
        r = requests.get(url)
        if r.status_code != 200: return None
        return r.json()
    except:
        return None

# Load Aset (Animasi lebih clean/professional)
lottie_robot = load_lottieurl("https://lottie.host/5a07c584-6f3f-48db-9556-993f3503928e/wF8w8O9ZlW.json") 
lottie_success = load_lottieurl("https://lottie.host/9c334346-6d60-44a6-98a9-448255959080/c8Z3Y7d5x9.json")

# --- KONEKSI DATABASE & AI (DIAGNOSA MODE) ---
try:
    # 1. Ambil Kunci (Prioritas: Streamlit Secrets > Environment Variable)
    # Kita pakai .get() biar gak error kalau kuncinya gak ada
    if st.secrets:
        # Hapus tanda kutip ganda jika user tidak sengaja memasukkannya di dalam string
        SUPA_URL = st.secrets.get("SUPABASE_URL", "").replace('"', '').strip()
        SUPA_KEY = st.secrets.get("SUPABASE_KEY", "").replace('"', '').strip()
        GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", "").replace('"', '').strip()
    else:
        # Fallback ke laptop lokal
        load_dotenv()
        SUPA_URL = os.getenv("SUPABASE_URL", "").strip()
        SUPA_KEY = os.getenv("SUPABASE_KEY", "").strip()
        GEMINI_KEY = os.getenv("GEMINI_API_KEY", "").strip()

    # 2. Cek Apakah Kunci Kosong? (Ini yang sering bikin gagal)
    missing_keys = []
    if not SUPA_URL: missing_keys.append("SUPABASE_URL")
    if not SUPA_KEY: missing_keys.append("SUPABASE_KEY")
    if not GEMINI_KEY: missing_keys.append("GEMINI_API_KEY")

    if missing_keys:
        st.error(f"❌ Gawat! Kunci rahasia berikut belum terbaca: {', '.join(missing_keys)}")
        st.info("Cek lagi di Settings > Secrets di Streamlit Cloud ya.")
        st.stop()

    # 3. Tes Koneksi
    supabase: Client = create_client(SUPA_URL, SUPA_KEY)
    genai.configure(api_key=GEMINI_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 4. Tes Panggilan Ringan (Ping)
    # Kita coba akses dummy biar tau valid atau nggak
    # (Opsional: Kalau ini error, berarti URL/Key valid tapi akses ditolak)
    
except Exception as e:
    st.error("❌ Terjadi Error saat Inisialisasi:")
    st.code(str(e)) # Tampilkan pesan error aslinya biar jelas
    st.stop()

# --- FUNGSI GENERATE PDF ---
def convert_html_to_pdf(source_html):
    result_file = BytesIO()
    # CSS PDF (Tetap Times New Roman Resmi)
    pdf_style = """
    <style>
        @page { size: A4; margin: 2.5cm; }
        body { font-family: 'Times New Roman', Times, serif; font-size: 12pt; color: #000; line-height: 1.5; }
        h2 { text-align: center; text-transform: uppercase; margin-bottom: 20px; font-size: 14pt; font-weight: bold; }
        h3 { font-size: 12pt; font-weight: bold; margin-top: 15px; }
        p { text-align: justify; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-bottom: 15px; table-layout: fixed; }
        th, td { border: 1px solid #000; padding: 6px; vertical-align: top; word-wrap: break-word; font-size: 12pt !important; }
        th { background-color: #f0f0f0; text-align: center; font-weight: bold; }
        tr { page-break-inside: avoid; }
    </style>
    """
    full_html = f"<html><body>{pdf_style}{source_html}</body></html>"
    pisa_status = pisa.CreatePDF(full_html, dest=result_file)
    if pisa_status.err: return None
    return result_file.getvalue()

# --- DATABASE LOGIC (CP) ---
def get_cp_text(fase, elemen):
    cp_fase_f = {
        "Menyimak – Berbicara": """Pada akhir Fase F, peserta didik menggunakan bahasa Inggris untuk berkomunikasi dengan guru, teman sebaya dan orang lain dalam berbagai macam situasi dan tujuan. Mereka menggunakan dan merespon pertanyaan terbuka dan menggunakan strategi untuk memulai, mempertahankan dan menyimpulkan percakapan dan diskusi. Mereka memahami dan mengidentifikasi ide utama dan detail relevan dari diskusi atau presentasi mengenai berbagai macam topik. Mereka menggunakan bahasa Inggris untuk menyampaikan opini terhadap isu sosial dan untuk membahas minat, perilaku dan nilai-nilai lintas konteks budaya yang dekat dengan kehidupan pemuda. Mereka memberikan dan mempertahankan pendapatnya, membuat perbandingan dan mengevaluasi perspektifnya. Mereka menggunakan strategi koreksi dan perbaikan diri, dan menggunakan elemen non-verbal seperti bahasa tubuh, kecepatan bicara dan nada suara untuk dapat dipahami dalam sebagian besar konteks.""",
        "Membaca – Memirsa": """Pada akhir Fase F, peserta didik membaca dan merespon berbagai macam teks seperti narasi, deskripsi, eksposisi, prosedur, argumentasi, dan diskusi secara mandiri. Mereka membaca untuk mempelajari sesuatu dan membaca untuk kesenangan. Mereka mencari, membuat sintesis dan mengevaluasi detil spesifik dan inti dari berbagai macam jenis teks. Teks ini dapat berbentuk cetak atau digital, termasuk di antaranya teks visual, multimodal atau interaktif. Mereka menunjukkan pemahaman terhadap ide pokok, isu-isu atau pengembangan plot dalam berbagai macam teks. Mereka mengidentifikasi tujuan penulis dan melakukan inferensi untuk memahami informasi tersirat dalam teks.""",
        "Menulis – Mempresentasikan": """Pada akhir Fase F, peserta didik menulis berbagai jenis teks fiksi dan non-fiksi, melalui aktivitas yang dipandu, menunjukkan kesadaran peserta didik terhadap tujuan dan target pembaca. Mereka membuat perencanaan, menulis, mengulas dan menulis ulang berbagai jenis tipe teks dengan menunjukkan strategi koreksi diri, termasuk tanda baca dan huruf besar. Mereka menyampaikan ide menggunakan kosakata dan kata kerja umum dalam tulisannya. Mereka menyajikan informasi menggunakan berbagai mode presentasi untuk menyesuaikan dengan pembaca/pemirsa dan untuk mencapai tujuan yang berbeda-beda, dalam bentuk cetak dan digital."""
    }
    if fase == "F" and elemen in cp_fase_f:
        return cp_fase_f[elemen]
    else:
        return "GENERATE_BY_AI"

# 2. UI/UX "CLEAN AESTHETIC" STYLE
st.markdown("""
<style>
    /* FONT UTAMA */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Plus Jakarta Sans', sans-serif; 
        color: #0f172a; /* Warna Teks Gelap (Slate 900) */
    }
    
    /* BACKGROUND */
    .stApp { 
        background-color: #f8fafc; /* Slate 50 */
    }
    
    /* CONTAINER KOTAK PUTIH ELEGAN */
    div.stContainer { 
        background-color: #ffffff; 
        border: 1px solid #e2e8f0; 
        border-radius: 12px; 
        padding: 30px; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
        margin-bottom: 24px;
    }
    
    /* JUDUL HALAMAN */
    h1 { 
        color: #1e293b; 
        font-weight: 800; 
        letter-spacing: -1px;
        font-size: 3rem !important;
    }
    h2 { color: #334155; font-weight: 700; }
    h3 { color: #475569; font-weight: 600; }
    
    /* INPUT FIELDS (RAPI & JELAS) */
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { 
        border-radius: 8px; 
        border: 1px solid #cbd5e1; 
        background-color: #ffffff;
        color: #1e293b;
        padding: 10px 12px;
        transition: all 0.2s;
    }
    .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus-within { 
        border-color: #2563eb; /* Biru Profesional */
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); 
    }
    
    /* TOMBOL UTAMA (SOLID BLUE) */
    .stButton button { 
        background-color: #2563eb; 
        color: white; 
        border: none; 
        border-radius: 8px; 
        padding: 0.8rem 2rem; 
        font-weight: 600; 
        font-size: 16px; 
        width: 100%; 
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        transition: all 0.2s; 
    }
    .stButton button:hover { 
        background-color: #1d4ed8; 
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transform: translateY(-1px);
    }
    
    /* SIDEBAR */
    section[data-testid="stSidebar"] { 
        background-color: #ffffff; 
        border-right: 1px solid #f1f5f9; 
    }
    
    /* TABS */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        padding: 8px 16px;
        background-color: transparent;
        border: none;
        color: #64748b;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #eff6ff;
        color: #2563eb;
        font-weight: 700;
    }

</style>
""", unsafe_allow_html=True)

# 3. SESSION STATE
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ""

# --- HALAMAN AUTH ---
def login_page():
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        with st.container():
            st.markdown("<h2 style='text-align: center; color: #1e293b;'>Modul Cerdas</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #1e293b;'>Created by Feri Ramadhan</p>", unsafe_allow_html=True)
            
            tab_login, tab_signup = st.tabs(["Masuk Akun", "Daftar Baru"])
            
            with tab_login:
                with st.form("login_form"):
                    email = st.text_input("Email", placeholder="Email")
                    password = st.text_input("Password", type="password", placeholder="Password")
                    st.markdown("<br>", unsafe_allow_html=True)
                    submitted = st.form_submit_button("Masuk", use_container_width=True)
                    if submitted:
                        try:
                            response = supabase.table('users').select("*").eq('email', email).eq('password', password).execute()
                            if len(response.data) > 0:
                                st.session_state['logged_in'] = True
                                st.session_state['user_email'] = email
                                st.success("Login Berhasil!")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("Email/Password salah.")
                        except Exception as e:
                                st.error(str(e))
            
            with tab_signup:
                with st.form("signup_form"):
                    new_email = st.text_input("Email Baru", placeholder="New Email")
                    new_pass = st.text_input("Password Baru", type="password", placeholder="New Password")
                    confirm_pass = st.text_input("Ulangi Password", type="password", placeholder="Confirm Password")
                    st.markdown("<br>", unsafe_allow_html=True)
                    btn_register = st.form_submit_button("Daftar Sekarang", use_container_width=True)
                    if btn_register:
                        if new_pass != confirm_pass:
                            st.warning("Password tidak sama.")
                        elif not new_email or not new_pass:
                            st.warning("Isi semua data.")
                        else:
                            try:
                                check = supabase.table('users').select("*").eq('email', new_email).execute()
                                if len(check.data) > 0:
                                    st.error("Email sudah dipakai.")
                                else:
                                    supabase.table('users').insert({"email": new_email, "password": new_pass}).execute()
                                    st.success("Akun dibuat! Silakan login.")
                            except Exception as e:
                                st.error(str(e))

# --- MAIN APP ---
def main_app():
    # SIDEBAR CLEAN
    with st.sidebar:
        st.markdown("### Modul Cerdas")
        st.markdown(f"<p style='font-size:14px; color:#64748b;'>Signed in as:<br><b>{st.session_state['user_email']}</b></p>", unsafe_allow_html=True)
        st.markdown("---")
        if st.button("Log Out", use_container_width=True):
            st.session_state['logged_in'] = False
            st.rerun()
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f'<a href="{DONATE_LINK}" target="_blank" style="display:block;text-align:center;background:#10b981;color:white;padding:10px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:600;">☕ Dukung Developer</a>', unsafe_allow_html=True)

    # HERO SECTION
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("# Generate Modul Ajar")
        st.markdown("<p style='font-size: 18px; color: #475569;'>Buat modul ajar Kurikulum Merdeka yang rapi, terstruktur, dan siap cetak (PDF) dalam hitungan detik dengan AI.</p>", unsafe_allow_html=True)
    with col2:
        if lottie_robot:
            st_lottie(lottie_robot, height=180, key="hero")

    st.markdown("<br>", unsafe_allow_html=True)

    # INPUT SECTION
    with st.container():
        st.markdown("### 📝 Informasi Umum")
        c1, c2 = st.columns(2)
        with c1:
            penyusun = st.text_input("Nama Penyusun", placeholder="Nama Lengkap dengan Gelar")
            instansi = st.text_input("Instansi / Sekolah", placeholder="Nama Sekolah")
        with c2:
            jenjang = st.selectbox("Jenjang Sekolah", ["SD/MI", "SMP/MTS", "SMA/MA"])
            if jenjang == "SD/MI": opsi_kelas = [1, 2, 3, 4, 5, 6]
            elif jenjang == "SMP/MTS": opsi_kelas = [7, 8, 9]
            else: opsi_kelas = [10, 11, 12]
            kelas = st.selectbox("Kelas", opsi_kelas)
            fase = ""
            if kelas in [1, 2]: fase = "A"
            elif kelas in [3, 4]: fase = "B"
            elif kelas in [5, 6]: fase = "C"
            elif kelas in [7, 8, 9]: fase = "D"
            elif kelas == 10: fase = "E"
            elif kelas in [11, 12]: fase = "F"
            st.caption(f"Fase Terdeteksi: **Fase {fase}**")

    with st.container():
        st.markdown("### 🎯 Detail Pembelajaran")
        c3, c4 = st.columns(2)
        with c3:
            topik = st.text_input("Topik / Materi", placeholder="Contoh: Narrative Text")
            semester = st.selectbox("Semester", ["Ganjil", "Genap"])
            alokasi = st.text_input("Alokasi Waktu", "2 x 45 Menit")
        with c4:
            elemen_pilih = st.selectbox("Elemen CP", ["Menyimak – Berbicara", "Membaca – Memirsa", "Menulis – Mempresentasikan"])
            metode = st.selectbox("Metode Pembelajaran", ["Jigsaw", "Think-Pair-Share (TPS)", "Number Heads Together (NHT)", "Role Play", "Gallery Walk", "Two Stay Two Stray (TSTS)", "Talking Chips"])
            ppp_map = {
                "Jigsaw": "Gotong Royong & Mandiri",
                "Think-Pair-Share (TPS)": "Bernalar Kritis & Kreatif",
                "Number Heads Together (NHT)": "Gotong Royong & Bernalar Kritis",
                "Role Play": "Kreatif & Kebinekaan Global",
                "Gallery Walk": "Gotong Royong & Bernalar Kritis",
                "Two Stay Two Stray (TSTS)": "Gotong Royong & Komunikasi Efektif",
                "Talking Chips": "Gotong Royong & Menghargai Orang Lain"
            }
            ppp_value = ppp_map.get(metode, "Mandiri & Kreatif")
            st.info(f"**Profil Pelajar Pancasila:** {ppp_value}")

    st.markdown("<br>", unsafe_allow_html=True)
    generate_btn = st.button("✨ Buat Modul Ajar (PDF)", type="primary", use_container_width=True)

    if generate_btn:
        if not topik or not penyusun:
            st.toast("⚠️ Mohon lengkapi Nama & Topik.")
        else:
            cp_content = get_cp_text(fase, elemen_pilih)
            if cp_content == "GENERATE_BY_AI":
                prompt_cp = f"Buatkan CP yang sesuai untuk Fase {fase}, Elemen {elemen_pilih}."
            else:
                prompt_cp = f"Gunakan TEKS CP INI (JANGAN UBAH): {cp_content}"

            result_container = st.container()

            # PROMPT
            prompt = f"""
            Bertindaklah sebagai Guru Inggris Profesional. Buat Modul Ajar Lengkap.
            **DATA:**
            Penyusun: {penyusun} | Sekolah: {instansi} | Jenjang: {jenjang} | Kelas: {kelas} | Fase: {fase}
            Topik: {topik} | Metode: {metode} | Profil Pancasila: {ppp_value} | Elemen: {elemen_pilih}

            **INSTRUKSI FORMATTING (PDF FRIENDLY):**
            1. JANGAN GUNAKAN MARKDOWN (Bintang/Pagar). Gunakan HTML.
            2. Gunakan tag HTML `<i>` miring, `<b>` tebal.
            3. Gunakan tag <table>, <tr>, <th>, <td> untuk SEMUA tabel.
            4. Gunakan <ul> dan <li> untuk poin-poin.
            5. Gunakan <h2> dan <h3> untuk judul.
            
            **STRUKTUR ISI MODUL:**
            <h2>MODUL AJAR: {topik.upper()}</h2>
            <hr>
            <h3>I. INFORMASI UMUM</h3>
            <p><strong>A. IDENTITAS MODUL</strong></p>
            <table>
                <tr><th width="30%">Informasi</th><th>Keterangan</th></tr>
                <tr><td>Penyusun</td><td>{penyusun}</td></tr>
                <tr><td>Instansi</td><td>{instansi}</td></tr>
                <tr><td>Jenjang / Kelas</td><td>{jenjang} / {kelas} (Fase {fase})</td></tr>
                <tr><td>Alokasi Waktu</td><td>{alokasi}</td></tr>
                <tr><td>Mata Pelajaran</td><td>Bahasa Inggris</td></tr>
                <tr><td>Elemen</td><td>{elemen_pilih}</td></tr>
            </table>

            <p><strong>B. KOMPETENSI AWAL</strong></p>
            <p>(1 Paragraf singkat)</p>

            <p><strong>C. PROFIL PELAJAR PANCASILA</strong></p>
            <p>{ppp_value}</p>

            <p><strong>D. SARANA DAN PRASARANA</strong></p>
            <ul><li>Laptop/Smartphone</li><li>Jaringan Internet</li><li>Materi {topik}</li></ul>

            <p><strong>E. MODEL PEMBELAJARAN</strong></p>
            <p>Tatap Muka dengan metode <strong>{metode}</strong>.</p>

            <h3>II. KOMPONEN INTI</h3>
            <p><strong>A. TUJUAN PEMBELAJARAN</strong></p>
            <p>1. <strong>Capaian Pembelajaran (CP):</strong> {prompt_cp}</p>
            <p>2. <strong>Tujuan Pembelajaran (TP):</strong> (Poin ABCD)</p>

            <p><strong>B. PEMAHAMAN BERMAKNA</strong></p>
            <p>(Manfaat mempelajari topik ini)</p>

            <p><strong>C. KEGIATAN PEMBELAJARAN</strong></p>
            <table>
                <tr><th width="15%">Tahap</th><th width="70%">Deskripsi Kegiatan</th><th width="15%">Waktu</th></tr>
                <tr>
                    <td><strong>Pendahuluan</strong></td>
                    <td><ul><li>Salam & Doa</li><li>Apersepsi: Guru menampilkan gambar <i>(misal: "{topik}")</i></li><li>Pertanyaan Pemantik</li></ul></td>
                    <td>10'</td>
                </tr>
                <tr>
                    <td><strong>Inti</strong></td>
                    <td>(Rincikan langkah {metode} disini. Gunakan tag <i> untuk bahasa inggris. Gunakan <ul><li> untuk poin.)</td>
                    <td>70'</td>
                </tr>
                <tr>
                    <td><strong>Penutup</strong></td>
                    <td><ul><li>Refleksi</li><li>Kesimpulan</li><li>Doa</li></ul></td>
                    <td>10'</td>
                </tr>
            </table>

            <h3>III. LAMPIRAN</h3>
            <p><strong>A. ASESMEN / PENILAIAN</strong></p>
            
            <p><strong>1. Penilaian Sikap</strong></p>
            <table>
                <tr><th width="20%">Aspek</th><th width="20%">Skor 4 (Sangat Baik)</th><th width="20%">Skor 3 (Baik)</th><th width="20%">Skor 2 (Cukup)</th><th width="20%">Skor 1 (Kurang)</th></tr>
                <tr>
                    <td>{ppp_value.split('&')[0]}</td>
                    <td>Sangat aktif...</td>
                    <td>Aktif...</td>
                    <td>Cukup aktif...</td>
                    <td>Kurang aktif...</td>
                </tr>
            </table>

            <p><strong>2. Penilaian Keterampilan</strong></p>
            <table>
                <tr><th width="30%">Aspek</th><th width="70%">Indikator (Skor 4-1)</th></tr>
                <tr>
                    <td>Konten</td>
                    <td>(Deskripsi indikator penilaian)</td>
                </tr>
            </table>

            <p><strong>B. LEMBAR KERJA PESERTA DIDIK (LKPD)</strong></p>
            <p><strong>Activity 1: {topik} Exploration</strong></p>
            <table>
                <tr><th width="10%">No</th><th width="50%">Question / Instruction</th><th width="40%">Answer Space</th></tr>
                <tr><td>1</td><td>(Buatkan pertanyaan pemahaman terkait {topik})</td><td>...</td></tr>
                <tr><td>2</td><td>(Buatkan pertanyaan analisis)</td><td>...</td></tr>
            </table>

            <p><strong>C. GLOSARIUM</strong></p>
            <ul><li>(Istilah 1)</li><li>(Istilah 2)</li></ul>

            <p><strong>D. DAFTAR PUSTAKA</strong></p>
            <ul>
                <li>Kementerian Pendidikan dan Kebudayaan. (2025). <em>Buku Guru Bahasa Inggris Fase {fase}</em>. Jakarta: Kemendikbud.</li>
                <li>Sumber internet relevan tentang {topik}.</li>
            </ul>
            """

            try:
                # EFEK MENGETIK
                with st.spinner("🤖 AI sedang menyusun modul..."):
                    response = model.generate_content(prompt, stream=True)
                
                output_placeholder = result_container.empty()
                full_text = ""
                
                for chunk in response:
                    full_text += chunk.text
                    clean_text = full_text.replace("```html", "").replace("```", "")
                    output_placeholder.markdown(clean_text + "▌", unsafe_allow_html=True)
                
                final_html = full_text.replace("```html", "").replace("```", "")
                output_placeholder.markdown(final_html, unsafe_allow_html=True)
                
                st.balloons()
                st.success("Selesai! Modul Anda siap.")

                # TOMBOL DOWNLOAD
                st.markdown("### 📥 Download File")
                pdf_bytes = convert_html_to_pdf(final_html)
                if pdf_bytes:
                    st.download_button(
                        label="📄 Unduh PDF (A4 - Resmi)",
                        data=pdf_bytes,
                        file_name=f"Modul_{topik.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.error("Gagal membuat PDF.")
                
            except Exception as e:
                st.error(f"Error AI: {e}")

if st.session_state['logged_in']:
    main_app()
else:
    login_page()