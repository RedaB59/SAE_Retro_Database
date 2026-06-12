# SAE Retro Database -- Pipeline DVF

Pipeline de données complet pour l'intégration et l'analyse des **Demandes de
Valeurs Foncières (DVF)** : depuis le CSV brut (data.gouv.fr) jusqu'à un
tableau de bord interactif, en passant par une base PostgreSQL normalisée et
des transformations dbt avec historisation SCD2.

## Architecture du pipeline

| Étape | Schéma PostgreSQL | Rôle | Outil |
|---|---|---|---|
| Injection DSA | `DSA` | Normalisation du CSV en 13 tables relationnelles | Python (pandas, psycopg2) |
| Staging | `DSA` | Typage, renommage (vues) | dbt |
| Intermédiaire | `DSA` | Jointures, agrégations, hash MD5 | dbt |
| ODS | `Intermediate` | Historisation SCD2 | dbt |
| DWH Marts | `Datawarehouse` | Schéma en étoile (faits / dimensions) | dbt |
| Dashboard | -- | Visualisation interactive | Streamlit + Plotly |

## Structure du projet

```
.
├── sql/relationnel/create_table/
│   ├── principal.sql           # création des 13 tables relationnelles (DSA)
│   ├── annexe.sql
│   └── injection_data_MLD.py   # ETL : lecture CSV -> normalisation -> insertion PostgreSQL
├── Data_Retro_Belarbi_Delrive/  # projet dbt
│   ├── models/
│   │   ├── staging/             # vues : typage, renommage
│   │   ├── intermediate/        # tables intermédiaires (jointures, hash)
│   │   ├── ods/                 # historisation SCD2 (8 tables)
│   │   └── marts/                # schéma en étoile (DWH)
│   ├── macros/                  # macro scd2_close_records, generate_schema_name
│   └── tests/                   # tests de qualité SCD2
├── dashboard.py                  # tableau de bord Streamlit
├── data_viz.py                   # graphiques d'exploration
├── utils/                         # modèles Pydantic (mutation, parcelle, ...)
├── modelisation_base/             # MCD / MLD du modèle relationnel
├── data/stable_link.txt           # lien de téléchargement du CSV DVF
├── rapport_projet.tex             # rapport du projet
└── presentation.tex               # support de soutenance (Beamer)
```

## Prérequis

- Python >= 3.14 (voir `.python-version`)
- [uv](https://docs.astral.sh/uv/) pour la gestion des dépendances
- Une base PostgreSQL accessible
- [dbt-postgres](https://docs.getdbt.com/docs/core/connect-data-platform/postgres-setup)

## Installation

```bash
uv sync
```

Copier `.env.exemple` vers `.env` et renseigner les accès à la base :

```bash
cp .env.exemple .env
```

```
DBHOST=...
DBPORT=5432
DBUSER=...
DBPASSWORD=...
DBSSL=require
DBDATABASE_REL=dvf_rel
DBDATABASE_DEC=dvf_dec
```

## Pipeline

### 1. Source de données

Les données DVF géolocalisées sont publiées par la DGFiP sur `data.gouv.fr`.
Le lien de téléchargement du CSV (plusieurs millions de lignes) est dans
`data/stable_link.txt`.

### 2. Création des tables et injection (DSA)

```bash
psql -f sql/relationnel/create_table/principal.sql
python sql/relationnel/create_table/injection_data_MLD.py
```

Le script `injection_data_MLD.py` lit le CSV, le découpe en 13 tables
normalisées (mutations, parcelles, locals, lots, localisations, communes,
départements, etc.) et insère les données par lots via `execute_values`.

### 3. Transformations dbt

```bash
cd Data_Retro_Belarbi_Delrive
dbt run
dbt test
```

- **staging** : vues de typage et renommage des colonnes
- **intermediate** : tables intermédiaires (jointures, calcul de hash)
- **ods** : historisation SCD2 (`est_courant`, `date_debut`, `date_fin`)
- **marts** : schéma en étoile (`fact_mutation` + dimensions)

### 4. Dashboard

```bash
streamlit run dashboard.py
```

Tableau de bord interactif (filtres, carte choroplèthe, treemap, répartition
par type de bien, distributions des prix et surfaces) connecté au schéma
`Datawarehouse`.

## Documentation

- `rapport_projet.tex` : rapport complet du projet
- `presentation.tex` : support de soutenance (Beamer)

## Auteurs

Projet réalisé en binôme dans le cadre de la SAE -- IUT de Lille (2026)

- Reda Belarbi
- Delrive
