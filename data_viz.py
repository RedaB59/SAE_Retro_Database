import psycopg2
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# --- Connexion ---
conn = psycopg2.connect(
    host="vps-c63213e3.vps.ovh.net",
    port=5432,
    dbname="projet_sae_dvf",
    user="reda_belarbi",
    password="eB3JGPbhmtkhmrTytcsBwHNsurkgdUWT",
    sslmode="require",
)

sns.set_theme(style="whitegrid", palette="muted")

# ── 1. Mutations par type ────────────────────────────────────────────────────
q1 = """
SELECT tm.libelle_type_mutation, COUNT(*) AS nb_mutations
FROM   "Datawarehouse"."fact_mutation" fm
JOIN   "Datawarehouse"."type_mutation" tm
    ON tm.id_type_mutation = fm.id_type_mutation AND tm.est_courant = true
WHERE  fm.est_courant = true
GROUP  BY tm.libelle_type_mutation
ORDER  BY nb_mutations DESC
"""
df1 = pd.read_sql(q1, conn)

# ── 2. Evolution mensuelle (nb mutations + valeur foncière moyenne) ──────────
q2 = """
SELECT DATE_TRUNC('month', fm.id_date)::date AS mois,
       COUNT(*)                              AS nb_mutations,
       ROUND(AVG(fm.valeur_fonciere))        AS valeur_moyenne
FROM   "Datawarehouse"."fact_mutation" fm
WHERE  fm.est_courant = true
GROUP  BY mois
ORDER  BY mois
"""
df2 = pd.read_sql(q2, conn)
df2["mois"] = pd.to_datetime(df2["mois"])

# ── 3. Top 10 communes par valeur foncière moyenne ───────────────────────────
q3 = """
SELECT loc.lib_com                            AS commune,
       ROUND(AVG(fm.valeur_fonciere))         AS valeur_moyenne,
       COUNT(*)                               AS nb_mutations
FROM   "Datawarehouse"."fact_mutation" fm
JOIN   "Datawarehouse"."localisation"  loc
    ON loc.id_localisation = fm.id_location AND loc.est_courant = true
WHERE  fm.est_courant = true AND fm.valeur_fonciere > 0
GROUP  BY loc.lib_com
HAVING COUNT(*) >= 5
ORDER  BY valeur_moyenne DESC
LIMIT  10
"""
df3 = pd.read_sql(q3, conn)

# ── 4. Distribution des valeurs foncières (sans extrêmes) ───────────────────
q4 = """
SELECT valeur_fonciere
FROM   "Datawarehouse"."fact_mutation"
WHERE  est_courant = true
  AND  valeur_fonciere BETWEEN 1000 AND 2000000
"""
df4 = pd.read_sql(q4, conn)

# ── 5. Mutations par département ─────────────────────────────────────────────
q5 = """
SELECT loc.code_dep                  AS departement,
       COUNT(*)                      AS nb_mutations
FROM   "Datawarehouse"."fact_mutation" fm
JOIN   "Datawarehouse"."localisation"  loc
    ON loc.id_localisation = fm.id_location AND loc.est_courant = true
WHERE  fm.est_courant = true
GROUP  BY loc.code_dep
ORDER  BY nb_mutations DESC
LIMIT  15
"""
df5 = pd.read_sql(q5, conn)

conn.close()

# ── Tracé ────────────────────────────────────────────────────────────────────
fig, axes = plt.subplots(3, 2, figsize=(18, 16))
fig.suptitle("DVF – Tableau de bord des mutations immobilières", fontsize=16, fontweight="bold", y=1.01)

# -- Graphe 1 : Répartition par type --
ax = axes[0, 0]
colors = sns.color_palette("muted", len(df1))
wedges, texts, autotexts = ax.pie(
    df1["nb_mutations"],
    labels=df1["libelle_type_mutation"],
    autopct="%1.1f%%",
    colors=colors,
    startangle=90,
)
for t in autotexts:
    t.set_fontsize(9)
ax.set_title("Répartition des mutations par type", fontweight="bold")

# -- Graphe 2 : Évolution mensuelle du nombre de mutations --
ax = axes[0, 1]
ax.bar(df2["mois"], df2["nb_mutations"], color=sns.color_palette("muted")[0], width=20)
ax.set_title("Évolution mensuelle du nombre de mutations", fontweight="bold")
ax.set_xlabel("Mois")
ax.set_ylabel("Nombre de mutations")
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y-%m"))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

# -- Graphe 3 : Évolution de la valeur foncière moyenne --
ax = axes[1, 0]
ax.plot(df2["mois"], df2["valeur_moyenne"] / 1000, marker="o", color=sns.color_palette("muted")[2], linewidth=2)
ax.fill_between(df2["mois"], df2["valeur_moyenne"] / 1000, alpha=0.15, color=sns.color_palette("muted")[2])
ax.set_title("Valeur foncière moyenne par mois (k€)", fontweight="bold")
ax.set_xlabel("Mois")
ax.set_ylabel("Valeur moyenne (k€)")
ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter("%Y-%m"))
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

# -- Graphe 4 : Top 10 communes --
ax = axes[1, 1]
palette = sns.color_palette("muted", len(df3))
bars = ax.barh(df3["commune"][::-1], df3["valeur_moyenne"][::-1] / 1000, color=palette)
ax.set_title("Top 10 communes par valeur foncière moyenne", fontweight="bold")
ax.set_xlabel("Valeur moyenne (k€)")
for bar, val in zip(bars, df3["valeur_moyenne"][::-1]):
    ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
            f"{val/1000:.0f}k€", va="center", fontsize=8)

# -- Graphe 5 : Distribution des valeurs foncières --
ax = axes[2, 0]
ax.hist(df4["valeur_fonciere"] / 1000, bins=60, color=sns.color_palette("muted")[1], edgecolor="white")
ax.set_title("Distribution des valeurs foncières (1k€ – 2M€)", fontweight="bold")
ax.set_xlabel("Valeur foncière (k€)")
ax.set_ylabel("Nombre de mutations")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}k"))

# -- Graphe 6 : Top 15 départements --
ax = axes[2, 1]
sns.barplot(data=df5, x="departement", y="nb_mutations", ax=ax, palette="muted")
ax.set_title("Top 15 départements par nombre de mutations", fontweight="bold")
ax.set_xlabel("Département")
ax.set_ylabel("Nombre de mutations")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

plt.tight_layout()
plt.savefig("dashboard_dvf.png", dpi=150, bbox_inches="tight")
print("Dashboard sauvegardé : dashboard_dvf.png")
plt.show()
