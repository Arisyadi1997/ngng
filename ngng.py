import sys
import subprocess
import threading
import os
import streamlit.components.v1 as components

# Install Streamlit jika belum terpasang
try:
    import streamlit as st
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit"])
    import streamlit as st

# ---- Konfigurasi Upload Besar ----
# Meningkatkan batas upload (Streamlit default: 200MB)
# Kita gunakan cara aman lewat config_file, bukan set_option
config_path = os.path.expanduser("~/.streamlit/config.toml")
os.makedirs(os.path.dirname(config_path), exist_ok=True)
with open(config_path, "w") as f:
    f.write("[server]\nmaxUploadSize = 8192\n")  # 8 GB

# ---- Fungsi FFMPEG ----
def run_ffmpeg(video_path, stream_key, is_shorts, log_callback):
    output_url = f"rtmp://a.rtmp.youtube.com/live2/{stream_key}"
    scale = "-vf scale=720:1280" if is_shorts else ""
    cmd = [
        "ffmpeg", "-re", "-stream_loop", "-1", "-i", video_path,
        "-c:v", "libx264", "-preset", "veryfast", "-b:v", "2500k",
        "-maxrate", "2500k", "-bufsize", "5000k",
        "-g", "60", "-keyint_min", "60",
        "-c:a", "aac", "-b:a", "128k",
        "-f", "flv"
    ]
    if scale:
        cmd += scale.split()
    cmd.append(output_url)

    log_callback(f"Menjalankan: {' '.join(cmd)}")
    try:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in process.stdout:
            log_callback(line.strip())
        process.wait()
    except Exception as e:
        log_callback(f"Error: {e}")
    finally:
        log_callback("Streaming selesai atau dihentikan.")

# ---- Aplikasi Streamlit ----
def main():
    st.set_page_config(page_title="YouTube Live Stream Tool", page_icon="📺", layout="wide")
    st.title("🎥 Live Streaming ke YouTube (Video Besar & Panjang)")
    st.write("Unggah video besar hingga **8GB** dan lakukan streaming langsung ke YouTube.")

    # Iklan opsional
    show_ads = st.checkbox("Tampilkan Iklan", value=False)
    if show_ads:
        components.html("""
        <div style="background:#f0f2f6;padding:20px;border-radius:10px;text-align:center">
            <p style="color:#888">Iklan Sponsor</p>
            <script type='text/javascript'
                src='//pl26562103.profitableratecpm.com/28/f9/95/28f9954a1d5bbf4924abe123c76a68d2.js'>
            </script>
        </div>
        """, height=300)

    # List video yang tersedia
    video_files = [f for f in os.listdir('.') if f.endswith(('.mp4', '.flv', '.mkv', '.mov'))]
    selected_video = st.selectbox("Pilih video dari folder saat ini:", video_files) if video_files else None

    uploaded_file = st.file_uploader("Atau upload video baru (MP4/FLV/MKV/MOV)", type=['mp4', 'flv', 'mkv', 'mov'])
    video_path = None

    if uploaded_file:
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.read())
        st.success(f"✅ {uploaded_file.name} berhasil diupload!")
        video_path = uploaded_file.name
    elif selected_video:
        video_path = selected_video

    stream_key = st.text_input("Masukkan Stream Key YouTube:", type="password")
    is_shorts = st.checkbox("Mode Shorts (720x1280)", value=False)

    log_placeholder = st.empty()
    logs = []

    def log_callback(msg):
        logs.append(msg)
        log_placeholder.text("\n".join(logs[-25:]))

    if 'ffmpeg_thread' not in st.session_state:
        st.session_state['ffmpeg_thread'] = None

    if st.button("▶️ Jalankan Streaming"):
        if not video_path or not stream_key:
            st.error("Silakan pilih video dan isi stream key terlebih dahulu.")
        else:
            st.session_state['ffmpeg_thread'] = threading.Thread(
                target=run_ffmpeg, args=(video_path, stream_key, is_shorts, log_callback), daemon=True)
            st.session_state['ffmpeg_thread'].start()
            st.success("🎬 Streaming dimulai! Pastikan koneksi internet stabil.")

    if st.button("⏹️ Hentikan Streaming"):
        os.system("pkill ffmpeg")
        st.warning("Streaming dihentikan oleh pengguna.")

    log_placeholder.text("\n".join(logs[-25:]))

if __name__ == '__main__':
    main()
