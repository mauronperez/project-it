import duckdb
import streamlit as st

DB_PATH = "/workspace/data/chicago_crimes.db"

st.set_page_config(page_title="Crímenes en Chicago 2026", layout="wide")
st.title("Crímenes en Chicago 2026")


@st.cache_data(ttl=60)
def query(sql: str):
    # Conexión corta: se abre y se cierra en cada consulta para no bloquear a dbt
    with duckdb.connect(DB_PATH, read_only=True) as con:
        return con.sql(sql).df()


by_month = query("select * from gold_crimes_by_month_type")
by_district = query("select * from gold_crimes_by_district")

# Filtro por tipo de delito
tipos = sorted(by_month["primary_type"].unique())
elegidos = st.multiselect("Tipo de delito", tipos, default=tipos[:5])
filtrado = by_month[by_month["primary_type"].isin(elegidos)]

col1, col2 = st.columns(2)
col1.metric("Crímenes (selección)", f"{filtrado['total_crimes'].sum():,}")
col2.metric("Arrestos (selección)", f"{int(filtrado['total_arrests'].sum()):,}")

st.subheader("Crímenes por mes")
st.line_chart(
    filtrado.pivot(index="month", columns="primary_type", values="total_crimes")
)

st.subheader("Crímenes por distrito")
st.bar_chart(by_district.set_index("district")["total_crimes"])

st.subheader("Datos")
st.dataframe(by_district, use_container_width=True)