"""Build Excel (.xlsx) exports for the admin: registered users and predictions."""
from io import BytesIO
from typing import List

import pandas as pd

from app.models.prediction import Prediction
from app.models.user import User


def registered_users_xlsx(users: List[User], totals: dict[int, int] | None = None) -> bytes:
    rows = [
        {
            "User ID": u.id,
            "Name": u.name,
            "Email": u.email,
            "Mobile": u.mobile,
            "College": u.college,
            "City": u.city,
            "State": u.state,
            "Registration Date": u.registration_date.strftime("%Y-%m-%d %H:%M") if u.registration_date else "",
            "Approval Status": u.status.value if hasattr(u.status, "value") else str(u.status),
            "Last Login": u.last_login.strftime("%Y-%m-%d %H:%M") if u.last_login else "",
            "Prediction Count": (totals or {}).get(u.id, u.prediction_count),
        }
        for u in users
    ]
    return _to_xlsx(pd.DataFrame(rows), "Registered Users")


def predictions_xlsx(preds: List[Prediction]) -> bytes:
    rows = [
        {
            "ID": p.id,
            "User ID": p.user_id,
            "Student Name": p.student_name,
            "Mode": p.mode,
            "Score": p.score,
            "AIR": p.air,
            "Gender": p.gender,
            "Category": p.category,
            "Degrees": ", ".join(p.degrees_list),
            "Results": len(p.results),
            "Downloads": p.downloads,
            "Date": p.created_at.strftime("%Y-%m-%d %H:%M") if p.created_at else "",
        }
        for p in preds
    ]
    return _to_xlsx(pd.DataFrame(rows), "Predictions")


def _to_xlsx(df: pd.DataFrame, sheet: str) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet)
    return buf.getvalue()
