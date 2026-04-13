import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from scipy.optimize import minimize

st.set_page_config(page_title="Coulomb Simulator", layout="wide")

st.markdown("""
    <style>
    html, body, [class*="css"] {
        font-family: 'Consolas', 'Courier New', monospace; 
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    header {background-color: transparent !important;}
    
    .stButton>button {
        border-radius: 8px;
        border: 1px solid #4CAF50;
        transition: 0.3s;
        width: 100%;
    }
    .stButton>button:hover {
        border: 1px solid #81C784;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.5);
    }
    `x
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-size: 18px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

if 'daftar_muatan' not in st.session_state:
    st.session_state.daftar_muatan = []

def hitung_medan_total(tx, ty, tz, muatan_list):
    k = 8.99e9
    Ex, Ey, Ez = 0.0, 0.0, 0.0
    for m in muatan_list:
        dx = tx - m['x']
        dy = ty - m['y']
        dz = tz - m['z']
        r3 = (dx**2 + dy**2 + dz**2)**1.5 
        if r3 > 0:
            Ex += k * m['q'] * dx / r3
            Ey += k * m['q'] * dy / r3
            Ez += k * m['q'] * dz / r3
    magnitudo = np.sqrt(Ex**2 + Ey**2 + Ez**2)
    return Ex, Ey, Ez, magnitudo

def fungsi_objektif(posisi, tx, ty, tz, muatan_list, q_penyeimbang):
    Ex_lama, Ey_lama, Ez_lama, _ = hitung_medan_total(tx, ty, tz, muatan_list)
    k = 8.99e9
    dx = tx - posisi[0]
    dy = ty - posisi[1]
    dz = tz - posisi[2]
    r3 = (dx**2 + dy**2 + dz**2)**1.5
    
    if r3 < 1e-6:
        return 1e9
        
    Ex_baru = k * q_penyeimbang * dx / r3
    Ey_baru = k * q_penyeimbang * dy / r3
    Ez_baru = k * q_penyeimbang * dz / r3
    
    E_total = np.sqrt((Ex_lama + Ex_baru)**2 + (Ey_lama + Ey_baru)**2 + (Ez_lama + Ez_baru)**2)
    return E_total

st.sidebar.header("Panel Kendali")

st.sidebar.subheader("1. Konfigurasi Muatan")
col1, col2, col3 = st.sidebar.columns(3)
x = col1.number_input("X", value=0.0, step=0.1)
y = col2.number_input("Y", value=0.0, step=0.1)
z = col3.number_input("Z", value=0.0, step=0.1)
q = st.sidebar.number_input("Muatan (Coulomb)", value=1e-9, format="%.2e", help="Gunakan format saintifik (contoh: 1e-9 untuk nanoCoulomb)")

if st.sidebar.button("Tambah Muatan"):
    st.session_state.daftar_muatan.append({'x': x, 'y': y, 'z': z, 'q': q})
    st.sidebar.success(f"Muatan ditambahkan di ({x}, {y}, {z})!")

if st.sidebar.button("Bersihkan Seluruh Ruang"):
    st.session_state.daftar_muatan = []
    st.rerun()

if len(st.session_state.daftar_muatan) > 0:
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Daftar Muatan Aktif (Buka untuk edit):**")
    for i, m in enumerate(st.session_state.daftar_muatan):
        with st.sidebar.expander(f"[{i+1}] {m['q']:.1e} C di ({m['x']:.1f}, {m['y']:.1f}, {m['z']:.1f})"):
            cx, cy, cz = st.columns(3)
            # Nilai otomatis terupdate secara real-time saat angka diubah
            m['x'] = cx.number_input("X", value=float(m['x']), step=0.5, key=f"edit_x_{i}")
            m['y'] = cy.number_input("Y", value=float(m['y']), step=0.5, key=f"edit_y_{i}")
            m['z'] = cz.number_input("Z", value=float(m['z']), step=0.5, key=f"edit_z_{i}")
            m['q'] = st.number_input("Muatan (C)", value=float(m['q']), format="%.2e", key=f"edit_q_{i}")
            
            if st.button("Hapus Muatan Ini", key=f"del_{i}"):
                st.session_state.daftar_muatan.pop(i)
                st.rerun()

st.sidebar.markdown("---")

st.sidebar.subheader("2. Titik Target Pengujian")
t_x = st.sidebar.number_input("Target X", value=2.0, step=0.5)
t_y = st.sidebar.number_input("Target Y", value=2.0, step=0.5)
t_z = st.sidebar.number_input("Target Z", value=2.0, step=0.5)

st.sidebar.markdown("---")

with st.sidebar.expander("Buka Inverse Problem Solver"):
    st.caption("Cari koordinat optimal untuk muatan penyeimbang agar E = 0 di Titik Target.")
    q_opt = st.number_input("Muatan Penyeimbang", value=1e-9, format="%.2e")

    if st.button("Cari Posisi Optimal"):
        if len(st.session_state.daftar_muatan) == 0:
            st.error("Masukkan minimal 1 muatan awal!")
        else:
            with st.spinner("Menjalankan optimasi..."):
                tebakan_awal = [t_x + 1, t_y + 1, t_z + 1] 
                hasil = minimize(fungsi_objektif, tebakan_awal, 
                                 args=(t_x, t_y, t_z, st.session_state.daftar_muatan, q_opt), 
                                 method='Nelder-Mead')
                
                if hasil.success:
                    opt_x, opt_y, opt_z = hasil.x
                    st.session_state.daftar_muatan.append({'x': opt_x, 'y': opt_y, 'z': opt_z, 'q': q_opt})
                    st.success(f"Posisi optimal: ({opt_x:.2f}, {opt_y:.2f}, {opt_z:.2f})")
                else:
                    st.error("Gagal konvergen.")

# Kalkulasi Real-time
Ex, Ey, Ez, Emag = hitung_medan_total(t_x, t_y, t_z, st.session_state.daftar_muatan)

st.title("Coulomb Simulator")
st.markdown("**Visualizer Medan Elektrostatis & Simulator Optimasi**")

# Tambahan Identitas Kelompok
st.caption("Dikembangkan oleh: **Kelompok 8 | Teknik Elektro UNPAD 2024**")
st.markdown("<br>", unsafe_allow_html=True) 

tab1, tab2 = st.tabs(["Ruang Simulasi 3D", "Log & Analisis Data"])

with tab1:
    st.info(f"**Intensitas Medan Listrik Total di Target ({t_x}, {t_y}, {t_z}):** {Emag:,.4f} V/m")
    
    fig = go.Figure()

    if len(st.session_state.daftar_muatan) > 0:
        qx = [m['x'] for m in st.session_state.daftar_muatan]
        qy = [m['y'] for m in st.session_state.daftar_muatan]
        qz = [m['z'] for m in st.session_state.daftar_muatan]
        q_val = [m['q'] for m in st.session_state.daftar_muatan]
        
        warna = ['red' if val > 0 else 'blue' for val in q_val]
        teks_hover = [f"Muatan {i+1}<br>Q: {q_val[i]:.2e} Coulomb<br>Posisi: ({qx[i]}, {qy[i]}, {qz[i]})" for i in range(len(qx))]
        
        fig.add_trace(go.Scatter3d(
            x=qx, y=qy, z=qz, mode='markers',
            marker=dict(size=12, color=warna, opacity=0.9),
            name='Muatan',
            text=teks_hover,
            hoverinfo='text'
        ))
    
    fig.add_trace(go.Scatter3d(
        x=[t_x], y=[t_y], z=[t_z], mode='markers',
        marker=dict(size=6, color='black', symbol='diamond'),
        name='Titik Target',
        text=[f"Target Uji<br>Posisi: ({t_x}, {t_y}, {t_z})<br>Medan Listrik: {Emag:,.2f} V/m"],
        hoverinfo='text'
    ))

    if Emag > 1e-4:
        fig.add_trace(go.Cone(
            x=[t_x], y=[t_y], z=[t_z],
            u=[Ex], v=[Ey], w=[Ez],
            sizemode="absolute", sizeref=1.5, showscale=True,
            colorscale='Electric',
            cmin=0,
            cmax=5000,
            colorbar=dict(title="E (V/m)", x=0.85, thickness=15),
            name='Vektor Medan',
            hoverinfo='skip',
            lighting=dict(ambient=0.6, diffuse=0.9, roughness=0.1, specular=2.0, fresnel=0.2)
        ))

    fig.update_layout(
        uirevision='kunci_kamera_tetap',
        scene=dict(xaxis_title='X', yaxis_title='Y', zaxis_title='Z'), 
        margin=dict(l=0, r=0, b=0, t=0), 
        height=600,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Detail Analisis Titik Target")
    
    col_status, col_vektor = st.columns(2)
    
    with col_status:
        st.markdown("### Status Keamanan")
        if Emag < 0.1:
            st.success("Aman (Nol Medan / Ternetralisir)")
        elif Emag < 1000:
            st.info("Aman (Medan Lemah)")
        elif Emag < 5000:
            st.warning("Peringatan (Medan Sedang)")
        else:
            st.error("BAHAYA (Medan Ekstrem)")
            
    with col_vektor:
        st.markdown("### Komponen Vektor Detail")
        st.code(f"Sumbu X : {Ex:,.4f} V/m\nSumbu Y : {Ey:,.4f} V/m\nSumbu Z : {Ez:,.4f} V/m\nTotal E : {Emag:,.4f} V/m", language="text")
        
        log_text = f"ANALISIS MEDAN ELEKTROSTATIS\n----------------------------\nKoordinat Target : ({t_x}, {t_y}, {t_z})\nTotal Muatan Aktif: {len(st.session_state.daftar_muatan)}\n\nHASIL KALKULASI:\nEx = {Ex} V/m\nEy = {Ey} V/m\nEz = {Ez} V/m\nMedan Total (E) = {Emag} V/m"
        st.download_button(label="Unduh Laporan Log", data=log_text, file_name="log_medan.txt", mime="text/plain")