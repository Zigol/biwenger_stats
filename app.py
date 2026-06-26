import streamlit as st
import pandas as pd

st.set_page_config(page_title="Estadísticas Fantasy League", page_icon="⚽", layout="wide")

# ═══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
#
# Cada liga tiene DOS URLs de Google Sheets publicadas como CSV:
#   - stats:  Participante, Puntos, Goles, Asistencias
#   - best:   Participante, POR, DEF, MED, DEL  (columnas de posición)
#
# Para publicar una pestaña:
#   Archivo -> Compartir -> Publicar en web -> Hoja -> CSV -> Publicar
# ═══════════════════════════════════════════════════════════════
LEAGUES = {
    "La Liga": {
        "stats": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4n7ctgiUJws_wA06LJvd0unWdULuw8nIfs7CvRlMqDzhzsJKqgnlUHns_mN_u3l7JTeOmJ3N-GxpB/pub?gid=0&single=true&output=csv",
        "best": "https://docs.google.com/spreadsheets/d/e/2PACX-1vT4n7ctgiUJws_wA06LJvd0unWdULuw8nIfs7CvRlMqDzhzsJKqgnlUHns_mN_u3l7JTeOmJ3N-GxpB/pub?gid=241912853&single=true&output=csv",
    },
    # "Mundial de Clubes": {
    #     "stats": "PON_AQUI_TU_URL",
    #     "best": "PON_AQUI_TU_URL",
    # },
}
# ═══════════════════════════════════════════════════════════════


def cargar_ligas():
    stats = {}
    best = {}
    for nombre, fuentes in LEAGUES.items():
        try:
            s = pd.read_csv(fuentes["stats"])
            s.columns = [c.strip() for c in s.columns]
            s["Liga"] = nombre
            stats[nombre] = s
        except Exception as e:
            st.error(f"No se pudo cargar stats de {nombre}: {e}")
            stats[nombre] = pd.DataFrame()

        try:
            b = pd.read_csv(fuentes["best"])
            b.columns = [c.strip() for c in b.columns]
            b["Liga"] = nombre
            best[nombre] = b
        except Exception as e:
            st.error(f"No se pudo cargar mejores de {nombre}: {e}")
            best[nombre] = pd.DataFrame()

    return stats, best


@st.cache_data(ttl=3600)
def obtener_datos():
    return cargar_ligas()


stats_data, best_data = obtener_datos()
disponibles = [n for n in LEAGUES if not stats_data.get(n, pd.DataFrame()).empty]

st.title("Estadísticas de la Fantasy League")
st.markdown("Seguimiento de nuestras ligas.")

if not disponibles:
    st.warning(
        "No hay datos cargados. Revisa los archivos CSV o "
        "actualiza LEAGUES en app.py con las URLs de Google Sheets."
    )
    st.stop()

def _mostrar_mejores(df):
    cols_pos = [c for c in df.columns if c not in ("Participante", "Liga")]
    col_config = {"Participante": st.column_config.TextColumn("Participante")}
    for p in cols_pos:
        col_config[p] = st.column_config.TextColumn(p)
    st.dataframe(
        df[["Participante"] + cols_pos],
        column_config=col_config,
        use_container_width=True,
        hide_index=True,
    )


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
    st.caption("Agrega ligas nuevas en LEAGUES al inicio de `app.py`.")

# ── Preparación de datos ─────────────────────────────────────

if vista == "Todas (Acumulado)":
    dfs_stats = [stats_data[n] for n in disponibles]
    stats_df = (
        pd.concat(dfs_stats, ignore_index=True)
        .groupby("Participante", as_index=False)[["Puntos", "Goles", "Asistencias"]]
        .sum()
        .sort_values("Puntos", ascending=False)
        .reset_index(drop=True)
    )
else:
    stats_df = (
        stats_data[vista].copy()
        .sort_values("Puntos", ascending=False)
        .reset_index(drop=True)
    )

# ── Métricas de resumen ──────────────────────────────────────

c1, c2, c3, c4 = st.columns(4)
c1.metric("Participantes", len(stats_df))
c2.metric("Puntos Totales", int(stats_df["Puntos"].sum()))
c3.metric("Goles Totales", int(stats_df["Goles"].sum()))
c4.metric("Asistencias Totales", int(stats_df["Asistencias"].sum()))

# ── Tabla de clasificación ───────────────────────────────────

st.subheader("Clasificación")

col_config = {
    "Participante": st.column_config.TextColumn("Participante", width="medium"),
    "Puntos": st.column_config.NumberColumn("Pts", format="%d"),
    "Goles": st.column_config.NumberColumn("G", format="%d"),
    "Asistencias": st.column_config.NumberColumn("A", format="%d"),
}

st.dataframe(
    stats_df[["Participante", "Puntos", "Goles", "Asistencias"]],
    column_config=col_config,
    use_container_width=True,
    hide_index=True,
)

# ── Gráfico de puntos ────────────────────────────────────────

st.subheader("Puntos por Participante")
st.bar_chart(stats_df.set_index("Participante")["Puntos"])

# ── Mejores jugadores por posición ───────────────────────────

if vista == "Todas (Acumulado)":
    st.subheader("Mejores Jugadores por Liga")
    for liga in disponibles:
        bdf = best_data.get(liga)
        if bdf is not None and not bdf.empty:
            with st.expander(liga):
                _mostrar_mejores(bdf)
else:
    bdf = best_data.get(vista)
    if bdf is not None and not bdf.empty:
        st.subheader("Mejores Jugadores por Posición")
        _mostrar_mejores(bdf)

# ── Gráficos extras ──────────────────────────────────────────

st.subheader("Goles y Asistencias por Participante")
c1, c2 = st.columns(2)
with c1:
    st.caption("Goles")
    st.bar_chart(stats_df.set_index("Participante")["Goles"])
with c2:
    st.caption("Asistencias")
    st.bar_chart(stats_df.set_index("Participante")["Asistencias"])
