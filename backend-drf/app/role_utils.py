from .models import AdminUser, CoachStudent, CoachUser, GeneralUser, User


def normalize_role(role: str) -> str:
    return str(role)


def ensure_role_profile(user: User, role: str) -> None:
    role_value = normalize_role(role)
    if role_value == User.ROLE_ADMIN:
        AdminUser.objects.get_or_create(user=user)
    elif role_value == User.ROLE_COACH:
        CoachUser.objects.get_or_create(user=user)
    else:
        GeneralUser.objects.get_or_create(user=user)


def delete_role_profiles(user: User) -> None:
    admin_profile = AdminUser.objects.filter(user=user).first()
    if admin_profile:
        admin_profile.delete()

    coach_profile = CoachUser.objects.filter(user=user).first()
    if coach_profile:
        CoachStudent.objects.filter(coach=coach_profile).delete()
        coach_profile.delete()

    general_profile = GeneralUser.objects.filter(user=user).first()
    if general_profile:
        CoachStudent.objects.filter(student=general_profile).delete()
        general_profile.delete()


def sync_user_role(user: User, role: str) -> None:
    role_value = normalize_role(role)
    if user.role == role_value:
        ensure_role_profile(user, role_value)
        return
    delete_role_profiles(user)
    user.role = role_value
    user.save(update_fields=["role"])
    ensure_role_profile(user, role_value)
