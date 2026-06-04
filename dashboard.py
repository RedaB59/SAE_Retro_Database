import json
import urllib.request
import psycopg2
import psycopg2.extras
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="DVF – Dashboard immobilier",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PARAMS = dict(
    host="vps-c63213e3.vps.ovh.net",
    port=5432,
    dbname="projet_sae_dvf",
    user="reda_belarbi",
    password="eB3JGPbhmtkhmrTytcsBwHNsurkgdUWT",
    sslmode="require",
)

COLORS = px.colors.qualitative.Set2


def run_query(sql: str, params=None) -> pd.DataFrame:
    with psycopg2.connect(**DB_PARAMS) as conn:
        conn.autocommit = True
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql, params)
            df = pd.DataFrame(cur.fetchall())
            for col in df.columns:
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass
            return df


@st.cache_resource
def load_geojson():
    url = "https://raw.githubusercontent.com/gregoiredavid/france-geojson/master/departements-version-simplifiee.geojson"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode())


@st.cache_data(ttl=600)
def load_refs():
    types = run_query("""
        SELECT id_type_mutation, libelle_type_mutation
        FROM "Datawarehouse"."type_mutation" WHERE est_courant = true
        ORDER BY libelle_type_mutation
    """)
    deps = run_query("""
        SELECT DISTINCT code_dep, lib_departement
        FROM "Datawarehouse"."localisation"
        WHERE est_courant = true AND code_dep IS NOT NULL
        ORDER BY code_dep
    """)
    bounds = run_query("""
        SELECT MIN(id_date)::date AS date_min, MAX(id_date)::date AS date_max,
               MIN(valeur_fonciere) AS val_min,
               PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY valeur_fonciere) AS val_p99
        FROM "Datawarehouse"."fact_mutation"
        WHERE est_courant = true AND valeur_fonciere > 0
    """)
    return types, deps, bounds


try:
    types_df, deps_df, bounds_df = load_refs()
    geojson = load_geojson()
except Exception as e:
    st.error(f"Erreur de connexion : {e}")
    st.stop()


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🔍 Filtres")

date_min = pd.to_datetime(bounds_df["date_min"].iloc[0]).date()
date_max = pd.to_datetime(bounds_df["date_max"].iloc[0]).date()
date_sel = st.sidebar.date_input("Période", value=(date_min, date_max),
                                  min_value=date_min, max_value=date_max)
d1 = date_sel[0] if isinstance(date_sel, (list, tuple)) and len(date_sel) >= 1 else date_min
d2 = date_sel[1] if isinstance(date_sel, (list, tuple)) and len(date_sel) == 2 else date_max

all_types = types_df["libelle_type_mutation"].tolist()
sel_types = st.sidebar.multiselect("Type de mutation", all_types, default=all_types)
if not sel_types:
    sel_types = all_types

all_deps = sorted(deps_df["code_dep"].dropna().tolist())
sel_deps = st.sidebar.multiselect("Département(s)", all_deps, placeholder="Tous")
dep_filter = sel_deps if sel_deps else all_deps


@st.cache_data(ttl=300)
def load_communes(dep_tuple):
    return run_query("""
        SELECT DISTINCT lib_com
        FROM "Datawarehouse"."localisation"
        WHERE est_courant = true AND lib_com IS NOT NULL AND code_dep = ANY(%s)
        ORDER BY lib_com
    """, (list(dep_tuple),))


communes_df = load_communes(tuple(dep_filter))
all_communes = communes_df["lib_com"].tolist() if not communes_df.empty else []
sel_communes = st.sidebar.multiselect("Commune(s)", all_communes, placeholder="Toutes")
com_filter = sel_communes if sel_communes else None

val_min_db = max(0, int(bounds_df["val_min"].iloc[0] or 0))
val_max_db = int(bounds_df["val_p99"].iloc[0] or 2_000_000)
v1, v2 = st.sidebar.slider("Valeur foncière (€)", val_min_db, val_max_db,
                             (val_min_db, val_max_db), step=5_000)

st.sidebar.markdown("---")
st.sidebar.caption("Source : DVF – Demandes de Valeurs Foncières")


# ── Construction WHERE / JOINS / params ───────────────────────────────────────
def build_filter():
    com_clause = "AND loc.lib_com = ANY(%s)" if com_filter else ""
    where = f"""
        fm.est_courant = true
        AND fm.id_date BETWEEN %s AND %s
        AND tm.libelle_type_mutation = ANY(%s)
        AND (loc.code_dep = ANY(%s) OR loc.code_dep IS NULL)
        {com_clause}
        AND fm.valeur_fonciere BETWEEN %s AND %s
    """
    joins = """
        FROM "Datawarehouse"."fact_mutation" fm
        JOIN "Datawarehouse"."type_mutation" tm
            ON tm.id_type_mutation = fm.id_type_mutation AND tm.est_courant = true
        LEFT JOIN "Datawarehouse"."localisation" loc
            ON loc.id_localisation = fm.id_location AND loc.est_courant = true
    """
    params = [str(d1), str(d2), list(sel_types), list(dep_filter)]
    if com_filter:
        params.append(list(com_filter))
    params.extend([v1, v2])
    return where, joins, tuple(params)


WHERE, JOINS, FPARAMS = build_filter()
FKEY = (str(d1), str(d2), tuple(sel_types), tuple(dep_filter),
        tuple(com_filter) if com_filter else (), v1, v2)


# ── KPIs ──────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=120)
def load_kpis(key, where, joins, params):
    return run_query(f"""
        SELECT COUNT(*)                                                             AS nb,
               SUM(fm.valeur_fonciere)                                             AS vol,
               AVG(fm.valeur_fonciere)                                             AS val_moy,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY fm.valeur_fonciere)    AS val_med,
               COUNT(DISTINCT loc.lib_com)                                         AS nb_communes,
               AVG(fm.valeur_fonciere / NULLIF(fm.avg_surface_bat, 0))            AS prix_m2
        {joins} WHERE {where}
    """, params)


try:
    kpis = load_kpis(FKEY, WHERE, JOINS, FPARAMS)
except Exception as e:
    st.error(f"Erreur KPIs : {e}")
    st.stop()

st.title("🏠 DVF – Tableau de bord des mutations immobilières")
st.caption(f"Données filtrées · {d1} → {d2}")

c1, c2, c3, c4, c5, c6 = st.columns(6)
nb = int(kpis["nb"].iloc[0])
vol = float(kpis["vol"].iloc[0] or 0)
val_moy = float(kpis["val_moy"].iloc[0] or 0)
val_med = float(kpis["val_med"].iloc[0] or 0)
nb_com = int(kpis["nb_communes"].iloc[0])
raw_m2 = kpis["prix_m2"].iloc[0]
prix_m2 = float(raw_m2) if raw_m2 is not None and not pd.isna(raw_m2) else None

c1.metric("Mutations", f"{nb:,}")
c2.metric("Volume total", f"{vol/1e9:.2f} Md€")
c3.metric("Valeur moyenne", f"{val_moy/1e3:.0f} k€")
c4.metric("Valeur médiane", f"{val_med/1e3:.0f} k€")
c5.metric("Communes", f"{nb_com:,}")
c6.metric("Prix moyen/m²", f"{prix_m2:,.0f} €" if prix_m2 else "N/A")
st.divider()


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📈 Temporel", "🗺️ Carte", "🏘️ Géographique",
    "💰 Prix au m²", "🏷️ Par type", "📊 Distributions", "🕓 SCD2",
])


# ═══════════════════════════════════════════════════════
# TAB 1 – Temporel
# ═══════════════════════════════════════════════════════
with tab1:
    gran = st.radio("Granularité", ["Mois", "Trimestre", "Année"], horizontal=True)
    trunc = {"Mois": "month", "Trimestre": "quarter", "Année": "year"}[gran]

    @st.cache_data(ttl=120)
    def load_temporal(key, trunc, where, joins, params):
        return run_query(f"""
            SELECT DATE_TRUNC('{trunc}', fm.id_date)::date AS periode,
                   COUNT(*)                                AS nb,
                   ROUND(AVG(fm.valeur_fonciere))          AS val_moy,
                   ROUND(SUM(fm.valeur_fonciere))          AS val_tot
            {joins} WHERE {where}
            GROUP BY periode ORDER BY periode
        """, params)

    with st.spinner("Chargement…"):
        try:
            agg = load_temporal(FKEY, trunc, WHERE, JOINS, FPARAMS)
        except Exception as e:
            st.error(str(e)); st.stop()

    fmt = "%Y-%m" if gran == "Mois" else "%Y-T%q" if gran == "Trimestre" else "%Y"
    agg["periode"] = pd.to_datetime(agg["periode"]).dt.strftime(fmt)

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(agg, x="periode", y="nb", title="Nombre de mutations",
                     labels={"nb": "Mutations", "periode": ""},
                     color_discrete_sequence=["#4C72B0"])
        fig.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.line(agg, x="periode", y="val_moy", markers=True,
                      title="Valeur foncière moyenne (€)",
                      labels={"val_moy": "Valeur moy. (€)", "periode": ""},
                      color_discrete_sequence=["#DD8452"])
        fig.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig, use_container_width=True)

    fig = px.area(agg, x="periode", y="val_tot", title="Volume total (€)",
                  labels={"val_tot": "Volume (€)", "periode": ""},
                  color_discrete_sequence=["#55A868"])
    fig.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig, use_container_width=True)

    @st.cache_data(ttl=120)
    def load_heatmap(key, where, joins, params):
        return run_query(f"""
            SELECT EXTRACT(year  FROM fm.id_date)::int AS annee,
                   EXTRACT(month FROM fm.id_date)::int AS mois_num,
                   COUNT(*)                            AS nb
            {joins} WHERE {where}
            GROUP BY annee, mois_num ORDER BY annee, mois_num
        """, params)

    hm = load_heatmap(FKEY, WHERE, JOINS, FPARAMS)
    if not hm.empty and hm["annee"].nunique() > 1:
        pivot = hm.pivot(index="annee", columns="mois_num", values="nb").fillna(0)
        noms = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
        pivot.columns = [noms[m - 1] for m in pivot.columns]
        fig = px.imshow(pivot, title="Heatmap : mutations par mois × année",
                        color_continuous_scale="Blues", aspect="auto", text_auto=True,
                        labels={"x": "Mois", "y": "Année", "color": "Nb mutations"})
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 2 – Carte choroplèthe
# ═══════════════════════════════════════════════════════
with tab2:
    metric_map = st.radio(
        "Métrique",
        ["Nombre de mutations", "Valeur moyenne (€)", "Volume total (€)", "Prix moyen/m² (€)"],
        horizontal=True,
    )

    @st.cache_data(ttl=120)
    def load_carte(key, where, joins, params):
        return run_query(f"""
            SELECT loc.code_dep, loc.lib_departement,
                   COUNT(*)                                                          AS nb,
                   ROUND(AVG(fm.valeur_fonciere))                                    AS val_moy,
                   ROUND(SUM(fm.valeur_fonciere))                                    AS vol,
                   ROUND(AVG(fm.valeur_fonciere / NULLIF(fm.avg_surface_bat, 0)))   AS prix_m2
            {joins} WHERE {where} AND loc.code_dep IS NOT NULL
            GROUP BY loc.code_dep, loc.lib_departement
        """, params)

    with st.spinner("Chargement de la carte…"):
        try:
            carte_df = load_carte(FKEY, WHERE, JOINS, FPARAMS)
        except Exception as e:
            st.error(str(e)); st.stop()

    col_cfg = {
        "Nombre de mutations":  ("nb",       "Mutations",    "Blues"),
        "Valeur moyenne (€)":   ("val_moy",  "Val. moy. (€)", "Oranges"),
        "Volume total (€)":     ("vol",      "Volume (€)",   "Greens"),
        "Prix moyen/m² (€)":    ("prix_m2",  "Prix/m² (€)",  "Reds"),
    }
    col_z, lbl_z, scale = col_cfg[metric_map]

    if not carte_df.empty:
        fig = px.choropleth(
            carte_df,
            geojson=geojson,
            locations="code_dep",
            featureidkey="properties.code",
            color=col_z,
            hover_name="lib_departement",
            hover_data={"code_dep": False, "nb": True, "val_moy": True, "prix_m2": True},
            color_continuous_scale=scale,
            title=f"Carte par département – {metric_map}",
            labels={col_z: lbl_z, "nb": "Mutations", "val_moy": "Val. moy. (€)", "prix_m2": "Prix/m² (€)"},
        )
        fig.update_geos(fitbounds="locations", visible=False)
        fig.update_layout(height=600, margin={"r": 0, "t": 40, "l": 0, "b": 0})
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            carte_df.sort_values(col_z, ascending=False).reset_index(drop=True),
            use_container_width=True,
        )
    else:
        st.info("Aucune donnée géographique pour les filtres sélectionnés.")


# ═══════════════════════════════════════════════════════
# TAB 3 – Géographique
# ═══════════════════════════════════════════════════════
with tab3:
    top_n = st.slider("Nombre de résultats", 5, 30, 15)
    metric = st.radio("Métrique", ["Nombre de mutations", "Valeur moyenne", "Volume total"], horizontal=True)
    col_map2 = {
        "Nombre de mutations": ("nb",      "Mutations"),
        "Valeur moyenne":      ("val_moy", "Val. moy. (€)"),
        "Volume total":        ("vol",     "Volume (€)"),
    }
    col_y, lbl_y = col_map2[metric]

    @st.cache_data(ttl=120)
    def load_geo(key, where, joins, params):
        deps = run_query(f"""
            SELECT loc.code_dep, loc.lib_departement,
                   COUNT(*) AS nb, ROUND(AVG(fm.valeur_fonciere)) AS val_moy,
                   ROUND(SUM(fm.valeur_fonciere)) AS vol
            {joins} WHERE {where} AND loc.code_dep IS NOT NULL
            GROUP BY loc.code_dep, loc.lib_departement
        """, params)
        coms = run_query(f"""
            SELECT loc.lib_com, loc.code_dep,
                   COUNT(*) AS nb, ROUND(AVG(fm.valeur_fonciere)) AS val_moy,
                   ROUND(SUM(fm.valeur_fonciere)) AS vol
            {joins} WHERE {where} AND loc.lib_com IS NOT NULL
            GROUP BY loc.lib_com, loc.code_dep
        """, params)
        return deps, coms

    with st.spinner("Chargement…"):
        try:
            agg_dep, agg_com = load_geo(FKEY, WHERE, JOINS, FPARAMS)
        except Exception as e:
            st.error(str(e)); st.stop()

    c1, c2 = st.columns(2)
    with c1:
        top = agg_dep.nlargest(top_n, col_y).sort_values(col_y)
        fig = px.bar(top, x=col_y, y="lib_departement", orientation="h",
                     title=f"Top {top_n} départements – {metric}",
                     labels={col_y: lbl_y, "lib_departement": ""},
                     color=col_y, color_continuous_scale="Blues")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        top = agg_com.nlargest(top_n, col_y).sort_values(col_y)
        fig = px.bar(top, x=col_y, y="lib_com", orientation="h",
                     title=f"Top {top_n} communes – {metric}",
                     labels={col_y: lbl_y, "lib_com": ""},
                     color=col_y, color_continuous_scale="Oranges")
        st.plotly_chart(fig, use_container_width=True)

    if not agg_dep.empty and not agg_com.empty:
        fig = px.treemap(agg_com, path=["code_dep", "lib_com"], values="nb", color="val_moy",
                         color_continuous_scale="RdYlGn",
                         title="Treemap département → commune (couleur = valeur moy.)",
                         labels={"nb": "Mutations", "val_moy": "Val. moy. (€)"})
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 4 – Prix au m²
# ═══════════════════════════════════════════════════════
with tab4:
    @st.cache_data(ttl=120)
    def load_prix_m2(key, where, joins, params):
        evol = run_query(f"""
            SELECT DATE_TRUNC('month', fm.id_date)::date AS mois,
                   tm.libelle_type_mutation,
                   ROUND(AVG(fm.valeur_fonciere / NULLIF(fm.avg_surface_bat, 0))) AS prix_m2
            {joins} WHERE {where} AND fm.avg_surface_bat > 0
            GROUP BY mois, tm.libelle_type_mutation ORDER BY mois
        """, params)
        dep = run_query(f"""
            SELECT loc.code_dep, loc.lib_departement,
                   ROUND(AVG(fm.valeur_fonciere / NULLIF(fm.avg_surface_bat, 0))) AS prix_m2,
                   COUNT(*) AS nb
            {joins} WHERE {where} AND fm.avg_surface_bat > 0 AND loc.code_dep IS NOT NULL
            GROUP BY loc.code_dep, loc.lib_departement ORDER BY prix_m2 DESC NULLS LAST
        """, params)
        scatter = run_query(f"""
            SELECT fm.avg_surface_bat                  AS surface,
                   fm.valeur_fonciere                  AS valeur,
                   tm.libelle_type_mutation            AS type_mutation
            {joins} WHERE {where}
                   AND fm.avg_surface_bat BETWEEN 10 AND 500
                   AND fm.valeur_fonciere BETWEEN 10000 AND 2000000
            LIMIT 5000
        """, params)
        return evol, dep, scatter

    with st.spinner("Chargement prix au m²…"):
        try:
            evol_m2, dep_m2, scatter_df = load_prix_m2(FKEY, WHERE, JOINS, FPARAMS)
        except Exception as e:
            st.error(str(e)); st.stop()

    if not evol_m2.empty:
        evol_m2["mois"] = pd.to_datetime(evol_m2["mois"]).dt.strftime("%Y-%m")
        fig = px.line(evol_m2, x="mois", y="prix_m2", color="libelle_type_mutation",
                      title="Évolution du prix moyen au m² (€/m²)",
                      labels={"prix_m2": "Prix/m² (€)", "mois": "", "libelle_type_mutation": "Type"},
                      markers=True, color_discrete_sequence=COLORS)
        fig.update_layout(xaxis_tickangle=-40)
        st.plotly_chart(fig, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        if not dep_m2.empty:
            top15 = dep_m2.head(15).sort_values("prix_m2")
            fig = px.bar(top15, x="prix_m2", y="lib_departement", orientation="h",
                         title="15 départements les plus chers (€/m²)",
                         labels={"prix_m2": "Prix/m² (€)", "lib_departement": ""},
                         color="prix_m2", color_continuous_scale="Reds")
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        if not dep_m2.empty and len(dep_m2) > 5:
            bottom15 = dep_m2.dropna(subset=["prix_m2"]).tail(15).sort_values("prix_m2")
            fig = px.bar(bottom15, x="prix_m2", y="lib_departement", orientation="h",
                         title="15 départements les moins chers (€/m²)",
                         labels={"prix_m2": "Prix/m² (€)", "lib_departement": ""},
                         color="prix_m2", color_continuous_scale="Greens")
            st.plotly_chart(fig, use_container_width=True)

    if not scatter_df.empty:
        fig = px.scatter(scatter_df, x="surface", y="valeur", color="type_mutation",
                         title="Surface bâtiment vs Valeur foncière (échantillon 5 000 mutations)",
                         labels={"surface": "Surface bâtiment (m²)", "valeur": "Valeur (€)",
                                 "type_mutation": "Type"},
                         opacity=0.4, color_discrete_sequence=COLORS)
        st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 5 – Par type
# ═══════════════════════════════════════════════════════
with tab5:
    @st.cache_data(ttl=120)
    def load_type(key, where, joins, params):
        agg = run_query(f"""
            SELECT tm.libelle_type_mutation,
                   COUNT(*) AS nb, ROUND(AVG(fm.valeur_fonciere)) AS val_moy,
                   ROUND(SUM(fm.valeur_fonciere)) AS vol
            {joins} WHERE {where}
            GROUP BY tm.libelle_type_mutation ORDER BY nb DESC
        """, params)
        evo = run_query(f"""
            SELECT DATE_TRUNC('month', fm.id_date)::date AS mois,
                   tm.libelle_type_mutation, COUNT(*) AS nb
            {joins} WHERE {where}
            GROUP BY mois, tm.libelle_type_mutation ORDER BY mois
        """, params)
        return agg, evo

    with st.spinner("Chargement…"):
        try:
            agg_type, evo_type = load_type(FKEY, WHERE, JOINS, FPARAMS)
        except Exception as e:
            st.error(str(e)); st.stop()

    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(agg_type, values="nb", names="libelle_type_mutation",
                     title="Répartition par type (nombre)", hole=0.4,
                     color_discrete_sequence=COLORS)
        fig.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(agg_type, x="libelle_type_mutation", y="val_moy",
                     title="Valeur foncière moyenne par type",
                     labels={"val_moy": "Valeur moy. (€)", "libelle_type_mutation": ""},
                     color="libelle_type_mutation", color_discrete_sequence=COLORS)
        fig.update_layout(showlegend=False, xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    evo_type["mois"] = pd.to_datetime(evo_type["mois"]).dt.strftime("%Y-%m")
    fig = px.area(evo_type, x="mois", y="nb", color="libelle_type_mutation",
                  title="Évolution mensuelle par type",
                  labels={"nb": "Mutations", "mois": "", "libelle_type_mutation": "Type"},
                  color_discrete_sequence=COLORS)
    fig.update_layout(xaxis_tickangle=-40)
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 6 – Distributions
# ═══════════════════════════════════════════════════════
with tab6:
    @st.cache_data(ttl=120)
    def load_distrib(key, v1, v2, where, joins, params):
        hist = run_query(f"""
            SELECT width_bucket(fm.valeur_fonciere, %s, %s, 60) AS bucket,
                   COUNT(*) AS nb,
                   MIN(fm.valeur_fonciere) AS val_min,
                   MAX(fm.valeur_fonciere) AS val_max
            {joins} WHERE {where}
            GROUP BY bucket ORDER BY bucket
        """, (v1, v2) + params)
        box = run_query(f"""
            SELECT tm.libelle_type_mutation,
                   PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY fm.valeur_fonciere) AS q1,
                   PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY fm.valeur_fonciere) AS med,
                   PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY fm.valeur_fonciere) AS q3
            {joins} WHERE {where}
            GROUP BY tm.libelle_type_mutation
        """, params)
        surf = run_query(f"""
            SELECT tm.libelle_type_mutation,
                   ROUND(AVG(fm.avg_surface_bat))     AS surf_bat,
                   ROUND(AVG(fm.avg_surface_terrain)) AS surf_terrain
            {joins} WHERE {where} AND fm.avg_surface_bat > 0
            GROUP BY tm.libelle_type_mutation
        """, params)
        parc = run_query(f"""
            SELECT fm.nb_parcelle,
                   COUNT(*) AS nb,
                   ROUND(AVG(fm.valeur_fonciere)) AS val_moy
            {joins} WHERE {where} AND fm.nb_parcelle BETWEEN 1 AND 10
            GROUP BY fm.nb_parcelle ORDER BY fm.nb_parcelle
        """, params)
        return hist, box, surf, parc

    with st.spinner("Chargement…"):
        try:
            hist_df, box_df, surf_df, parc_df = load_distrib(FKEY, v1, v2, WHERE, JOINS, FPARAMS)
        except Exception as e:
            st.error(str(e)); st.stop()

    c1, c2 = st.columns(2)
    with c1:
        if not hist_df.empty:
            hist_df["centre"] = (hist_df["val_min"] + hist_df["val_max"]) / 2
            fig = px.bar(hist_df, x="centre", y="nb",
                         title="Distribution des valeurs foncières",
                         labels={"centre": "Valeur (€)", "nb": "Nb mutations"},
                         color_discrete_sequence=["#4C72B0"])
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        if not box_df.empty:
            fig = px.bar(box_df, x="libelle_type_mutation", y=["q1", "med", "q3"],
                         barmode="group",
                         title="Quartiles de valeur foncière par type",
                         labels={"value": "Valeur (€)", "libelle_type_mutation": "",
                                 "variable": "Quartile"},
                         color_discrete_sequence=COLORS)
            fig.update_layout(xaxis_tickangle=-20)
            st.plotly_chart(fig, use_container_width=True)

    if not surf_df.empty:
        fig = px.bar(surf_df, x="libelle_type_mutation",
                     y=["surf_bat", "surf_terrain"], barmode="group",
                     title="Surface moyenne bâtiment vs terrain par type (m²)",
                     labels={"value": "Surface (m²)", "libelle_type_mutation": "",
                             "variable": "Surface"},
                     color_discrete_sequence=COLORS)
        fig.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)

    if not parc_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            fig = px.bar(parc_df, x="nb_parcelle", y="nb",
                         title="Mutations par nombre de parcelles",
                         labels={"nb": "Mutations", "nb_parcelle": "Nb parcelles"},
                         color_discrete_sequence=["#55A868"])
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.line(parc_df, x="nb_parcelle", y="val_moy", markers=True,
                          title="Valeur moyenne selon nb de parcelles",
                          labels={"val_moy": "Valeur moy. (€)", "nb_parcelle": "Nb parcelles"},
                          color_discrete_sequence=["#DD8452"])
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════
# TAB 7 – Historique SCD2
# ═══════════════════════════════════════════════════════
with tab7:
    st.markdown("**Mutations avec plusieurs versions historiques (SCD2)**")

    @st.cache_data(ttl=60)
    def load_scd2():
        return run_query("""
            SELECT fm.id_mutation, fm.valeur_fonciere, fm.est_courant,
                   fm.date_debut::timestamp AS date_debut,
                   fm.date_fin::timestamp   AS date_fin,
                   tm.libelle_type_mutation, loc.lib_com, loc.code_dep
            FROM "Datawarehouse"."fact_mutation" fm
            JOIN "Datawarehouse"."type_mutation" tm
                ON tm.id_type_mutation = fm.id_type_mutation AND tm.est_courant = true
            LEFT JOIN "Datawarehouse"."localisation" loc
                ON loc.id_localisation = fm.id_location AND loc.est_courant = true
            WHERE fm.id_mutation IN (
                SELECT id_mutation FROM "Datawarehouse"."fact_mutation"
                GROUP BY id_mutation HAVING COUNT(*) > 1
            )
            ORDER BY fm.id_mutation, fm.date_debut
        """)

    with st.spinner("Chargement…"):
        try:
            df_scd = load_scd2()
        except Exception as e:
            st.error(str(e)); st.stop()

    if df_scd.empty:
        st.info("Aucune mutation multi-versions pour l'instant.")
    else:
        df_scd["date_debut"] = pd.to_datetime(df_scd["date_debut"])
        df_scd["date_fin_viz"] = pd.to_datetime(df_scd["date_fin"]).clip(
            upper=pd.Timestamp("2030-01-01"))
        df_scd["statut"] = df_scd["est_courant"].map(
            {True: "✅ Courant", False: "📁 Historique"})

        st.metric("Mutations avec historique", df_scd["id_mutation"].nunique())

        fig = px.timeline(df_scd, x_start="date_debut", x_end="date_fin_viz",
                          y="id_mutation", color="statut",
                          hover_data=["valeur_fonciere", "lib_com", "libelle_type_mutation"],
                          title="Timeline SCD2 par mutation",
                          color_discrete_map={"✅ Courant": "#2ecc71", "📁 Historique": "#95a5a6"})
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)

        fig = px.line(df_scd.sort_values("date_debut"),
                      x="date_debut", y="valeur_fonciere", color="id_mutation", markers=True,
                      title="Évolution de la valeur foncière par mutation",
                      labels={"date_debut": "Date version", "valeur_fonciere": "Valeur (€)"})
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            df_scd[["id_mutation", "valeur_fonciere", "statut", "date_debut", "date_fin",
                    "lib_com", "libelle_type_mutation"]]
            .sort_values(["id_mutation", "date_debut"]).reset_index(drop=True),
            use_container_width=True,
        )
