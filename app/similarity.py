from app.models import db, Users
import math

FIELD_LABELS = ["DS", "WD", "MD", "GD", "CS", "AI", "ML"]

def get_all_users(exclude_id=None):
    users = Users.query.all()
    user_list = []
    
    for user in users:
        if exclude_id is not None and user.user_id == exclude_id:
            continue
        
        user_dict = {
            "id": user.user_id,
            "fullname": user.fullname,
            "semester": user.semester,
            "gender": "L" if user.gender == "L" else "P",
            "field_of_preference": [f.strip() for f in user.field_of_preference.split(",") if f.strip()]
        }
        user_list.append(user_dict)
        
    return user_list

def normalize_user(user, min_semester, max_semester, ignore_gender=False, ignore_semester=False):
    features = []

    if not ignore_semester:
        semester_norm = (user["semester"] - min_semester) / (max_semester - min_semester)
        features.append(semester_norm)

    if not ignore_gender:
        gender_norm = 0 if user["gender"] == "L" else 1
        features.append(gender_norm)

    field_vector = [1 if field in user["field_of_preference"] else 0 for field in FIELD_LABELS]
    features.extend(field_vector)

    return features

def cosine_similarity(vec1, vec2):
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_vec1 = math.sqrt(sum(a * a for a in vec1))
    norm_vec2 = math.sqrt(sum(b * b for b in vec2))

    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0.0 

    return dot_product / (norm_vec1 * norm_vec2)