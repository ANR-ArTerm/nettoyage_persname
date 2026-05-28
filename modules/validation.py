from modules.list_and_dics import VERIF_LIST

def normalize_validation(value):
    validation = str(value or "").strip()
    if validation.endswith(".0"):
        validation = validation[:-2]
    return validation if validation in VERIF_LIST else "0"


def normalize_validation_series(series):
    validation = series.fillna("").astype(str).str.strip()
    validation = validation.str.replace(r"\.0$", "", regex=True)
    return validation.where(validation.isin(VERIF_LIST), "0")
