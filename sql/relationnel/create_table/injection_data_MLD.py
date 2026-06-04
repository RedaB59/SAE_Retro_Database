
"""
ETL : Chargement d'un fichier Excel (feuille unique) vers PostgreSQL
MCD : DVF / Mutations foncières

Tables (ordre d'insertion respectant les FK) :
  1. types_local
  2. natures_culture
  3. natures_culture_speciales
  4. parcelles
  5. mutations
  6. locals
  7. sous_parcelles
  8. lots
  9. parcelles_mutations

Prérequis :
    pip install pandas psycopg2-binary openpyxl
"""

import pandas as pd

import psycopg2
from psycopg2.extras import execute_values


# ─────────────────────────────────────────────
# 1. CONFIGURATION
# ─────────────────────────────────────────────

           

DB_CONFIG = {
    "host":     "vps-c63213e3.vps.ovh.net",
    "port":     5432,
    "dbname":   "projet_sae_dvf",          
    "user":     "reda_belarbi",          
    "password": "eB3JGPbhmtkhmrTytcsBwHNsurkgdUWT"
}

conn = psycopg2.connect(**DB_CONFIG, client_encoding="utf8")
cur = conn.cursor()

conn.rollback()
cur.execute("SELECT * FROM departements LIMIT 5")
rows = cur.fetchall()
print(rows)

cur.close()
conn.close()
# ─────────────────────────────────────────────
# 2. LECTURE DU FICHIER EXCEL
# ─────────────────────────────────────────────

print("📂 Lecture du fichier Excel...")
df = pd.read_csv("C:/Users/149331/SAE_Retro_Database/sql/relationnel/dvf.csv", dtype=str, sep=",")
df = df.where(pd.notnull(df), None)  # Remplace NaN par None (NULL en SQL)
print(f"  ✅ {len(df)} lignes lues, {len(df.columns)} colonnes")

print("🔧 Découpage en tables...")
 
# 1. departements
# CSV : code_departement → MCD : code_dep, lib_dep
df_departements = (
    df[["code_departement"]]
    .drop_duplicates()
    .dropna()
    .rename(columns={"code_departement": "code_dep"})
)
df_departements["lib_dep"] = None
 
# 2. communes
# CSV : code_commune, code_postal, nom_commune, ancien_code_commune,
#       ancien_nom_commune, code_departement
# MCD : code_com, code_postal, lib_com, ancien_code_commune,
#       ancien_libelle_commune, code_dep
df_communes = (
    df[["code_commune", "code_postal", "nom_commune",
        "ancien_code_commune", "ancien_nom_commune", "code_departement"]]
    .drop_duplicates(subset=["code_commune"])
    .dropna(subset=["code_commune"])
    .rename(columns={
        "code_commune":       "code_com",
        "nom_commune":        "lib_com",
        "ancien_nom_commune": "ancien_libelle_commune",
        "code_departement":   "code_dep",
    })
)
 
# 3. nature_mutation
# CSV : nature_mutation (str) → MCD : id_nat_mut (int), lib_nat_mut
df_nature_mutation_raw = (
    df[["nature_mutation"]]
    .drop_duplicates()
    .dropna()
    .reset_index(drop=True)
)
df_nature_mutation_raw["id_nat_mut"] = df_nature_mutation_raw.index + 1
df_nature_mutation = df_nature_mutation_raw.rename(
    columns={"nature_mutation": "lib_nat_mut"}
)[["id_nat_mut", "lib_nat_mut"]]
 
# Map lib → id pour l'utiliser dans mutations
nat_mut_map = dict(zip(df_nature_mutation["lib_nat_mut"], df_nature_mutation["id_nat_mut"]))
 
# 4. types_local
# CSV : code_type_local, type_local → MCD : id_type_loc, lib_type_loc
df_types_local = (
    df[["code_type_local", "type_local"]]
    .drop_duplicates(subset=["code_type_local"])
    .dropna(subset=["code_type_local"])
    .rename(columns={"code_type_local": "id_type_loc", "type_local": "lib_type_loc"})
)
 
# 5. natures_culture
# CSV : code_nature_culture, nature_culture → MCD : id_nat_cult, lib_nat_cult
df_natures_culture = (
    df[["code_nature_culture", "nature_culture"]]
    .drop_duplicates(subset=["code_nature_culture"])
    .dropna(subset=["code_nature_culture"])
    .rename(columns={"code_nature_culture": "id_nat_cult", "nature_culture": "lib_nat_cult"})
)
 
# 6. natures_culture_speciales
# CSV : code_nature_culture_speciale, nature_culture_speciale
# MCD : id_nat_cult_spe, lib_nat_cult_spe
df_natures_culture_speciales = (
    df[["code_nature_culture_speciale", "nature_culture_speciale"]]
    .drop_duplicates(subset=["code_nature_culture_speciale"])
    .dropna(subset=["code_nature_culture_speciale"])
    .rename(columns={
        "code_nature_culture_speciale": "id_nat_cult_spe",
        "nature_culture_speciale":      "lib_nat_cult_spe",
    })
)
 
# 7. localisations
# CSV : adresse_numero, adresse_suffixe, adresse_code_voie, adresse_nom_voie,
#       code_commune, latitude, longitude
# MCD : id_adresse (généré), code_com, adresse_code_voie, nom_voie,
#       numero, suffixe, latitude, longitude
df_loc_raw = (
    df[["adresse_numero", "adresse_suffixe", "adresse_code_voie",
        "adresse_nom_voie", "code_commune", "latitude", "longitude"]]
    .drop_duplicates()
    .dropna(subset=["adresse_code_voie", "code_commune"])
    .reset_index(drop=True)
)
df_loc_raw["id_adresse"] = (
    df_loc_raw["code_commune"].astype(str) + "_" +
    df_loc_raw["adresse_code_voie"].astype(str) + "_" +
    df_loc_raw["adresse_numero"].fillna("0").astype(str)
)
df_localisations = df_loc_raw.rename(columns={
    "code_commune":     "code_com",
    "adresse_nom_voie": "nom_voie",
    "adresse_numero":   "numero",
    "adresse_suffixe":  "suffixe",
})[["id_adresse", "code_com", "adresse_code_voie", "nom_voie",
    "numero", "suffixe", "latitude", "longitude"]]
 
# Ajouter id_adresse au df principal pour l'utiliser dans sous_parcelles
df["_id_adresse"] = (
    df["code_commune"].astype(str) + "_" +
    df["adresse_code_voie"].astype(str) + "_" +
    df["adresse_numero"].fillna("0").astype(str)
)
 
# 8. parcelles
# MCD : id_parcelle, ancien_id_parcelle, code_nature_culture, code_nature_culture_speciale
df_parcelles = (
    df[["id_parcelle", "ancien_id_parcelle",
        "code_nature_culture", "code_nature_culture_speciale"]]
    .drop_duplicates(subset=["id_parcelle"])
    .dropna(subset=["id_parcelle"])
)
 
# 9. mutations
# CSV : id_mutation, numero_disposition, date_mutation, nature_mutation
# MCD : id_mutation, numero_mutation, date_mutation, id_nature_mutation
df_mutations_raw = (
    df[["id_mutation", "numero_disposition", "date_mutation", "nature_mutation"]]
    .drop_duplicates(subset=["id_mutation"])
    .dropna(subset=["id_mutation"])
)
df_mutations_raw["id_nature_mutation"] = df_mutations_raw["nature_mutation"].map(nat_mut_map)
df_mutations = df_mutations_raw.rename(
    columns={"numero_disposition": "numero_mutation"}
)[["id_mutation", "numero_mutation", "date_mutation", "id_nature_mutation"]]
 
# 10. locals
# MCD : id_local (généré), code_type_local, id_parcelle,
#       surface_batiment, nombre_piece_principal, nb_lots
df_locals_raw = (
    df[["id_mutation", "id_parcelle", "code_type_local",
        "surface_reelle_bati", "nombre_pieces_principales", "nombre_lots"]]
    .drop_duplicates()
    .dropna(subset=["id_mutation", "id_parcelle"])
    .reset_index(drop=True)
)
df_locals_raw["id_local"] = (
    df_locals_raw["id_mutation"].astype(str) + "_" +
    df_locals_raw["id_parcelle"].astype(str) + "_" +
    df_locals_raw.index.astype(str)
)
df_locals = df_locals_raw.rename(columns={
    "surface_reelle_bati":       "surface_batiment",
    "nombre_pieces_principales": "nombre_piece_principal",
    "nombre_lots":               "nb_lots",
})[["id_local", "code_type_local", "id_parcelle",
    "surface_batiment", "nombre_piece_principal", "nb_lots"]]
 
# 11. sous_parcelles
# MCD : id_parcelle, sous_parcelle, surface_terrain, id_adresse
df_sous_parcelles = (
    df[["id_parcelle", "surface_terrain", "_id_adresse"]]
    .drop_duplicates(subset=["id_parcelle"])
    .dropna(subset=["id_parcelle"])
    .copy()
)
df_sous_parcelles["sous_parcelle"] = "0000"
df_sous_parcelles = df_sous_parcelles.rename(
    columns={"_id_adresse": "id_adresse"}
)[["id_parcelle", "sous_parcelle", "surface_terrain", "id_adresse"]]
 
# 12. lots (pivot colonnes larges → lignes)
# MCD : id_lot, id_local, lot_surface_carrez
lots_frames = []
for i in range(1, 6):
    col_num  = f"lot{i}_numero"
    col_surf = f"lot{i}_surface_carrez"
    if col_num in df.columns and col_surf in df.columns:
        tmp = df[["id_mutation", "id_parcelle", col_num, col_surf]].copy()
        tmp = tmp.dropna(subset=[col_num])
        tmp["id_local"] = (
            tmp["id_mutation"].astype(str) + "_" +
            tmp["id_parcelle"].astype(str) + "_0"
        )
        tmp = tmp.rename(columns={
            col_num:  "id_lot",
            col_surf: "lot_surface_carrez",
        })[["id_lot", "id_local", "lot_surface_carrez"]]
        lots_frames.append(tmp)
 
df_lots = (
    pd.concat(lots_frames).drop_duplicates(subset=["id_lot"])
    if lots_frames
    else pd.DataFrame(columns=["id_lot", "id_local", "lot_surface_carrez"])
)
 
# 13. parcelles_mutations
df_parcelles_mutations = (
    df[["id_mutation", "id_parcelle"]]
    .drop_duplicates()
    .dropna()
)
 
for nom, table in [
    ("departements",              df_departements),
    ("communes",                  df_communes),
    ("nature_mutation",           df_nature_mutation),
    ("types_local",               df_types_local),
    ("natures_culture",           df_natures_culture),
    ("natures_culture_speciales", df_natures_culture_speciales),
    ("localisations",             df_localisations),
    ("parcelles",                 df_parcelles),
    ("mutations",                 df_mutations),
    ("locals",                    df_locals),
    ("sous_parcelles",            df_sous_parcelles),
    ("lots",                      df_lots),
    ("parcelles_mutations",       df_parcelles_mutations),
]:
    print(f"  ✅ {nom:<30} → {len(table)} ligne(s) extraite(s)")
 
# ─────────────────────────────────────────────
# 4. INSERTION EN BASE
# ─────────────────────────────────────────────
 
def inserer(cursor, table, df, colonnes):
    donnees = [tuple(row) for row in df[colonnes].itertuples(index=False)]
    if not donnees:
        print(f"  ⚠️  {table} : aucune donnée à insérer")
        return 0
    cols = ", ".join(colonnes)
    sql = f"INSERT INTO {table} ({cols}) VALUES %s ON CONFLICT DO NOTHING"
    execute_values(cursor, sql, donnees)
    return len(donnees)
 
print("\n🚀 Connexion à PostgreSQL et insertion...")
 
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cur = conn.cursor()
 
    etapes = [
        ("departements",              df_departements,              ["code_dep", "lib_dep"]),
        ("communes",                  df_communes,                  ["code_com", "code_postal", "lib_com", "ancien_code_commune", "ancien_libelle_commune", "code_dep"]),
        ("nature_mutation",           df_nature_mutation,           ["id_nat_mut", "lib_nat_mut"]),
        ("types_local",               df_types_local,               ["id_type_loc", "lib_type_loc"]),
        ("natures_culture",           df_natures_culture,           ["id_nat_cult", "lib_nat_cult"]),
        ("natures_culture_speciales", df_natures_culture_speciales, ["id_nat_cult_spe", "lib_nat_cult_spe"]),
        ("localisations",             df_localisations,             ["id_adresse", "code_com", "adresse_code_voie", "nom_voie", "numero", "suffixe", "latitude", "longitude"]),
        ("parcelles",                 df_parcelles,                 ["id_parcelle", "ancien_id_parcelle", "code_nature_culture", "code_nature_culture_speciale"]),
        ("mutations",                 df_mutations,                 ["id_mutation", "numero_mutation", "date_mutation", "id_nature_mutation"]),
        ("locals",                    df_locals,                    ["id_local", "code_type_local", "id_parcelle", "surface_batiment", "nombre_piece_principal", "nb_lots"]),
        ("sous_parcelles",            df_sous_parcelles,            ["id_parcelle", "sous_parcelle", "surface_terrain", "id_adresse"]),
        ("lots",                      df_lots,                      ["id_lot", "id_local", "lot_surface_carrez"]),
        ("parcelles_mutations",       df_parcelles_mutations,       ["id_mutation", "id_parcelle"]),
    ]
 
    for table, df_table, colonnes in etapes:
        n = inserer(cur, table, df_table, colonnes)
        print(f"  ✅ {table:<30} → {n} ligne(s) insérée(s)")
 
    conn.commit()
    print("\n✅ Toutes les données ont été insérées avec succès !")
 
except psycopg2.Error as e:
    conn.rollback()
    print(f"\n❌ Erreur PostgreSQL : {e}")
    raise
 
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
        print("🔒 Connexion fermée.")