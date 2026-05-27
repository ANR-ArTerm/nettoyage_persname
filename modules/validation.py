VERIF_LIST = {
    "0": "🔴 Notice non consultée",
    "1": "👤 Nom vérifié",
    "2": "✏️ Notice à revoir",
    "3": "✅ Notice terminée",
}


def normalize_validation(value):
    validation = str(value or "").strip()
    if validation.endswith(".0"):
        validation = validation[:-2]
    return validation if validation in VERIF_LIST else "0"


def normalize_validation_series(series):
    validation = series.fillna("").astype(str).str.strip()
    validation = validation.str.replace(r"\.0$", "", regex=True)
    return validation.where(validation.isin(VERIF_LIST), "0")
