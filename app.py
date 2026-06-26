import streamlit as st
import pandas as pd

st.set_page_config(page_title="Estadísticas Fantasy League", page_icon="⚽", layout="wide")

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
#
# Cada liga apunta a un archivo CSV local o a una URL publicada
# de Google Sheets.
#
# Para publicar una pestaña de Google Sheets como CSV:
#   Archivo -> Compartir -> Publicar en web -> Hoja (elige la pestaña) -> CSV
#
# El CSV debe tener estas columnas:
#   Participante, Jugador, Posicion, Puntos, Goles, Asistencias
#
# Posiciones válidas: GK, DEF, MID, FWD
# ═══════════════════════════════════════════════════════════════
LEAGUES = {
    "La Liga": "data/la_liga.csv",
    "Mundial de Clubes": "data/cwc.csv",
}
# ═══════════════════════════════════════════════════════════════

POSICIONES = ["GK", "DEF", "MID", "FWD"]
COLORES = {"GK": "#FFD700", "DEF": "#4CAF50", "MID": "#2196F3", "FWD": "#FF5722"}


def cargar_datos():
    ligas = {}
    for nombre, fuente in LEAGUES.items():
        try:
            df = pd.read_csv(fuente)
            df.columns = [c.strip() for c in df.columns]
            df["Liga"] = nombre
            ligas[nombre] = df
        except Exception as e:
            st.error(f"No se pudo cargar {nombre} desde {fuente}: {e}")
            ligas[nombre] = pd.DataFrame()
    return ligas


@st.cache_data(ttl=3600)
def obtener_datos():
    return cargar_datos()


datos = obtener_datos()
disponibles = [n for n in LEAGUES if not datos.get(n, pd.DataFrame()).empty]

st.title("Estadísticas de la Fantasy League")
st.markdown("Seguimiento de nuestras ligas.")

if not disponibles:
    st.warning(
        "No hay datos cargados. Revisa que los CSV existan o "
        "actualiza el diccionario LEAGUES en app.py con las URLs de Google Sheets."
    )
    st.stop()

# ── Sidebar ──────────────────────────────────────────────────

with st.sidebar:
    st.header("Vista")
    vista = st.radio(
        "Liga",
        ["Todas (Acumulado)"] + disponibles,
        index=0,
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("Agrega nuevas ligas en el diccionario LEAGUES al inicio de `app.py`.")

# ── Preparación de datos ─────────────────────────────────────

if vista == "Todas (Acumulado)":
    dfs = [datos[n] for n in disponibles]
    combinado = pd.concat(dfs, ignore_index=True)
    jugadores_df = (
        combinado.groupby(["Participante", "Jugador", "Posicion"], as_index=False)[
            ["Puntos", "Goles", "Asistencias"]
        ]
        .sum()
        .sort_values("Puntos", ascending=False)
        .reset_index(drop=True)
    )
else:
    jugadores_df = datos[vista].copy().sort_values("Puntos", ascending=False).reset_index(drop=True)

# Totales por participante
participantes_df = (
    jugadores_df.groupby("Participante", as_index=False)[
        ["Puntos", "Goles", "Asistencias"]
    ]
    .sum()
    .sort_values("Puntos", ascending=False)
    .reset_index(drop=True)
)

# ── Métricas de resumen ──────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric("Participantes", len(participantes_df))
c2.metric("Puntos Totales", int(participantes_df["Puntos"].sum()))
c3.metric("Goles Totales", int(participantes_df["Goles"].sum()))
c4.metric("Asistencias Totales", int(participantes_df["Asistencias"].sum()))

# ── Tabla de clasificación ───────────────────────────────────

st.subheader("Clasificación")

col_config = {
    "Participante": st.column_config.TextColumn("Participante", width="medium"),
    "Puntos": st.column_config.NumberColumn("Pts", format="%d"),
    "Goles": st.column_config.NumberColumn("G", format="%d"),
    "Asistencias": st.column_config.NumberColumn("A", format="%d"),
}

st.dataframe(
    participantes_df[["Participante", "Puntos", "Goles", "Asistencias"]],
    column_config=col_config,
    use_container_width=True,
    hide_index=True,
)

# ── Mejor jugador por posición para cada participante ───────

st.subheader("Mejor Jugador por Posición")

mejores = jugadores_df.loc[
    jugadores_df.groupby(["Participante", "Posicion"])["Puntos"].idxmax()
].copy()

POSICIONES_EXISTENTES = [p for p in POSICIONES if p in mejores["Posicion"].values]

if not mejores.empty:
    mejores["Mostrar"] = mejores.apply(
        lambda r: f"{r['Jugador']} ({int(r['Puntos'])} pts)", axis=1
    )
    pivot = mejores.pivot(
        index="Participante", columns="Posicion", values="Mostrar"
    )
    pivot = pivot.reindex(columns=POSICIONES_EXISTENTES, fill_value="—")

    col_config_mvp = {}
    for pos in POSICIONES_EXISTENTES:
        col_config_mvp[pos] = st.column_config.TextColumn(pos, width="medium")

    st.dataframe(
        pivot,
        column_config=col_config_mvp,
        use_container_width=True,
    )
else:
    st.caption("Sin datos para mostrar.")

# ── Desglose por posición ────────────────────────────────────

st.subheader("Puntos por Posición")
resumen_pos = (
    jugadores_df.groupby("Posicion")["Puntos"]
    .sum()
    .reindex(POSICIONES, fill_value=0)
)
st.bar_chart(resumen_pos, color="#8884d8")

# ── Gráficos por participante ────────────────────────────────

st.subheader("Gráficos")
c1, c2 = st.columns(2)
with c1:
    st.caption("Puntos por Participante")
    st.bar_chart(participantes_df.set_index("Participante")["Puntos"])
with c2:
    st.caption("Goles por Participante")
    st.bar_chart(participantes_df.set_index("Participante")["Goles"])

st.caption("Asistencias por Participante")
st.bar_chart(participantes_df.set_index("Participante")["Asistencias"])
