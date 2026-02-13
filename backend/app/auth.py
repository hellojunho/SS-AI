from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from . import models, schemas
from .db import get_db
from .security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _normalize_role(role: schemas.UserRole | str) -> str:
    return role.value if isinstance(role, schemas.UserRole) else role


def _ensure_role_profile(db: Session, user: models.User, role: schemas.UserRole | str) -> None:
    role_value = _normalize_role(role)
    if role_value == "admin":
        exists = db.query(models.AdminUser).filter(models.AdminUser.user_id == user.id).first()
        if not exists:
            db.add(models.AdminUser(user_id=user.id))
    elif role_value == "coach":
        exists = db.query(models.CoachUser).filter(models.CoachUser.user_id == user.id).first()
        if not exists:
            db.add(models.CoachUser(user_id=user.id))
    else:
        exists = db.query(models.GeneralUser).filter(models.GeneralUser.user_id == user.id).first()
        if not exists:
            db.add(models.GeneralUser(user_id=user.id))


def _delete_role_profiles(db: Session, user: models.User) -> None:
    admin_profile = db.query(models.AdminUser).filter(models.AdminUser.user_id == user.id).first()
    if admin_profile:
        db.delete(admin_profile)
    coach_profile = db.query(models.CoachUser).filter(models.CoachUser.user_id == user.id).first()
    if coach_profile:
        db.query(models.CoachStudent).filter(
            models.CoachStudent.coach_id == coach_profile.id
        ).delete(synchronize_session=False)
        db.delete(coach_profile)
    general_profile = db.query(models.GeneralUser).filter(models.GeneralUser.user_id == user.id).first()
    if general_profile:
        db.query(models.CoachStudent).filter(
            models.CoachStudent.student_id == general_profile.id
        ).delete(synchronize_session=False)
        db.delete(general_profile)


def _sync_user_role(db: Session, user: models.User, role: schemas.UserRole | str) -> None:
    role_value = _normalize_role(role)
    if user.role == role_value:
        _ensure_role_profile(db, user, role_value)
        return
    _delete_role_profiles(db, user)
    user.role = role_value
    _ensure_role_profile(db, user, role_value)


@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if db.query(models.User).filter(models.User.user_id == user.user_id).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    role_value = _normalize_role(user.role)
    if role_value == "admin":
        raise HTTPException(status_code=403, detail="관리자는 회원가입으로 생성할 수 없습니다.")
    new_user = models.User(
        user_id=user.user_id,
        user_name=user.user_name,
        password_hash=hash_password(user.password),
        email=user.email,
        role=role_value,
    )
    db.add(new_user)
    db.flush()
    _ensure_role_profile(db, new_user, role_value)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.user_id == payload.user_id).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="로그인 실패")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="탈퇴한 계정입니다.")
    user.last_logined = datetime.utcnow()
    db.commit()
    access_token = create_access_token(subject=str(user.id), token_version=user.token)
    refresh_token = create_refresh_token(subject=str(user.id), token_version=user.token)
    return schemas.Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=schemas.Token)
def refresh_token(payload: schemas.RefreshTokenRequest, db: Session = Depends(get_db)):
    try:
        refresh_payload = decode_refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user_id = refresh_payload.get("sub")
    token_version = refresh_payload.get("ver")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user or user.token != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="탈퇴한 계정입니다.")
    access_token = create_access_token(subject=str(user.id), token_version=user.token)
    new_refresh_token = create_refresh_token(subject=str(user.id), token_version=user.token)
    return schemas.Token(access_token=access_token, refresh_token=new_refresh_token)


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> models.User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    user_id = payload.get("sub")
    token_version = payload.get("ver")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == int(user_id)).first()
    if not user or user.token != token_version:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="탈퇴한 계정입니다.")
    return user


def require_admin(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="관리자 권한이 필요합니다.")
    return current_user


def require_coach(current_user: models.User = Depends(get_current_user)) -> models.User:
    if current_user.role != "coach":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="코치 권한이 필요합니다.")
    return current_user


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.post("/withdraw", status_code=status.HTTP_204_NO_CONTENT)
def withdraw_account(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.is_active = False
    current_user.deactivated_at = datetime.utcnow()
    current_user.token += 1
    db.commit()
    return None


@router.get("/admin/users", response_model=list[schemas.UserOut])
def admin_list_users(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return db.query(models.User).order_by(models.User.created_at.desc()).all()


@router.get("/admin/traffic", response_model=list[schemas.AdminTrafficStats])
def admin_user_traffic(
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    def add_months(base: datetime, months: int) -> datetime:
        total_month = base.month - 1 + months
        year = base.year + total_month // 12
        month = total_month % 12 + 1
        return base.replace(year=year, month=month, day=1)

    def to_utc_naive(target: datetime) -> datetime:
        return target.astimezone(timezone.utc).replace(tzinfo=None)

    def count_between(date_field, start: datetime, end: datetime) -> int:
        start_utc = to_utc_naive(start)
        end_utc = to_utc_naive(end)
        return db.query(models.User).filter(date_field.isnot(None), date_field >= start_utc, date_field < end_utc).count()

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_of_week = start_of_day - timedelta(days=start_of_day.weekday())
    start_of_month = start_of_day.replace(day=1)
    start_of_year = start_of_day.replace(month=1, day=1)
    periods = [
        ("day", start_of_day),
        ("week", start_of_week),
        ("month", start_of_month),
        ("year", start_of_year),
    ]
    results: list[schemas.AdminTrafficStats] = []
    for label, start in periods:
        buckets: list[schemas.AdminTrafficBucket] = []
        if label == "day":
            base = start - timedelta(days=11)
            for offset in range(12):
                bucket_start = base + timedelta(days=offset)
                bucket_end = bucket_start + timedelta(days=1)
                buckets.append(
                    schemas.AdminTrafficBucket(
                        label=bucket_start.strftime("%m/%d"),
                        signups=count_between(models.User.created_at, bucket_start, bucket_end),
                        logins=count_between(models.User.last_logined, bucket_start, bucket_end),
                        withdrawals=count_between(models.User.deactivated_at, bucket_start, bucket_end),
                    )
                )
        elif label == "week":
            base = start - timedelta(weeks=11)
            for offset in range(12):
                bucket_start = base + timedelta(weeks=offset)
                bucket_end = bucket_start + timedelta(weeks=1)
                buckets.append(
                    schemas.AdminTrafficBucket(
                        label=bucket_start.strftime("%m/%d"),
                        signups=count_between(models.User.created_at, bucket_start, bucket_end),
                        logins=count_between(models.User.last_logined, bucket_start, bucket_end),
                        withdrawals=count_between(models.User.deactivated_at, bucket_start, bucket_end),
                    )
                )
        elif label == "month":
            base = add_months(start, -11)
            for offset in range(12):
                bucket_start = add_months(base, offset)
                bucket_end = add_months(bucket_start, 1)
                buckets.append(
                    schemas.AdminTrafficBucket(
                        label=bucket_start.strftime("%y.%m"),
                        signups=count_between(models.User.created_at, bucket_start, bucket_end),
                        logins=count_between(models.User.last_logined, bucket_start, bucket_end),
                        withdrawals=count_between(models.User.deactivated_at, bucket_start, bucket_end),
                    )
                )
        else:
            base_year = start.year - 11
            for offset in range(12):
                bucket_start = start.replace(year=base_year + offset)
                bucket_end = bucket_start.replace(year=bucket_start.year + 1)
                buckets.append(
                    schemas.AdminTrafficBucket(
                        label=str(bucket_start.year),
                        signups=count_between(models.User.created_at, bucket_start, bucket_end),
                        logins=count_between(models.User.last_logined, bucket_start, bucket_end),
                        withdrawals=count_between(models.User.deactivated_at, bucket_start, bucket_end),
                    )
                )
        results.append(
            schemas.AdminTrafficStats(
                period=label,
                buckets=buckets,
            )
        )
    return results


@router.patch("/admin/users/{user_id}", response_model=schemas.UserOut)
def admin_update_user(
    user_id: int,
    payload: schemas.AdminUserUpdate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    if payload.email and payload.email != user.email:
        exists = (
            db.query(models.User)
            .filter(models.User.email == payload.email, models.User.id != user_id)
            .first()
        )
        if exists:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
        user.email = payload.email
    if payload.user_name is not None:
        user.user_name = payload.user_name
    if payload.role is not None:
        _sync_user_role(db, user, payload.role)
    if payload.password:
        user.password_hash = hash_password(payload.password)
        user.token += 1
    db.commit()
    db.refresh(user)
    return user


@router.post("/admin/users", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: schemas.AdminUserCreate,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if db.query(models.User).filter(models.User.user_id == payload.user_id).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 사용자입니다.")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")
    role_value = _normalize_role(payload.role)
    new_user = models.User(
        user_id=payload.user_id,
        user_name=payload.user_name,
        password_hash=hash_password(payload.password),
        email=payload.email,
        role=role_value,
    )
    db.add(new_user)
    db.flush()
    _ensure_role_profile(db, new_user, role_value)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.delete("/admin/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_user(
    user_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    db.query(models.ChatRecord).filter(models.ChatRecord.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(models.ChatSummary).filter(models.ChatSummary.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(models.QuizAnswer).filter(models.QuizAnswer.user_id == user.id).delete(
        synchronize_session=False
    )
    db.query(models.WrongQuestion).filter(
        (models.WrongQuestion.question_creator_id == user.id)
        | (models.WrongQuestion.solver_user_id == user.id)
    ).delete(synchronize_session=False)
    quizzes = db.query(models.Quiz).filter(models.Quiz.user_id == user.id).all()
    for quiz in quizzes:
        db.delete(quiz)
    _delete_role_profiles(db, user)
    db.delete(user)
    db.commit()
    return None


@router.get("/admin/users/{user_id}", response_model=schemas.UserOut)
def admin_get_user(
    user_id: int,
    current_user: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="사용자를 찾을 수 없습니다.")
    return user


@router.get("/coach/students", response_model=list[schemas.UserOut])
def coach_list_students(
    current_user: models.User = Depends(require_coach),
    db: Session = Depends(get_db),
):
    coach_profile = db.query(models.CoachUser).filter(models.CoachUser.user_id == current_user.id).first()
    if not coach_profile:
        coach_profile = models.CoachUser(user_id=current_user.id)
        db.add(coach_profile)
        db.flush()
    students = (
        db.query(models.User)
        .join(models.GeneralUser, models.GeneralUser.user_id == models.User.id)
        .join(models.CoachStudent, models.CoachStudent.student_id == models.GeneralUser.id)
        .filter(models.CoachStudent.coach_id == coach_profile.id)
        .order_by(models.User.created_at.desc())
        .all()
    )
    return students


@router.post("/coach/students", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def coach_add_student(
    payload: schemas.CoachStudentCreate,
    current_user: models.User = Depends(require_coach),
    db: Session = Depends(get_db),
):
    coach_profile = db.query(models.CoachUser).filter(models.CoachUser.user_id == current_user.id).first()
    if not coach_profile:
        coach_profile = models.CoachUser(user_id=current_user.id)
        db.add(coach_profile)
        db.flush()
    student_user = db.query(models.User).filter(models.User.user_id == payload.student_user_id).first()
    if not student_user or student_user.role != "general":
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다.")
    student_profile = db.query(models.GeneralUser).filter(models.GeneralUser.user_id == student_user.id).first()
    if not student_profile:
        student_profile = models.GeneralUser(user_id=student_user.id)
        db.add(student_profile)
        db.flush()
    exists = (
        db.query(models.CoachStudent)
        .filter(
            models.CoachStudent.coach_id == coach_profile.id,
            models.CoachStudent.student_id == student_profile.id,
        )
        .first()
    )
    if exists:
        raise HTTPException(status_code=400, detail="이미 등록된 학생입니다.")
    db.add(models.CoachStudent(coach_id=coach_profile.id, student_id=student_profile.id))
    db.commit()
    db.refresh(student_user)
    return student_user


@router.delete("/coach/students/{student_user_id}", status_code=status.HTTP_204_NO_CONTENT)
def coach_remove_student(
    student_user_id: str,
    current_user: models.User = Depends(require_coach),
    db: Session = Depends(get_db),
):
    coach_profile = db.query(models.CoachUser).filter(models.CoachUser.user_id == current_user.id).first()
    if not coach_profile:
        coach_profile = models.CoachUser(user_id=current_user.id)
        db.add(coach_profile)
        db.flush()
    student_user = db.query(models.User).filter(models.User.user_id == student_user_id).first()
    if not student_user:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다.")
    student_profile = db.query(models.GeneralUser).filter(models.GeneralUser.user_id == student_user.id).first()
    if not student_profile:
        raise HTTPException(status_code=404, detail="학생 정보를 찾을 수 없습니다.")
    deleted = (
        db.query(models.CoachStudent)
        .filter(
            models.CoachStudent.coach_id == coach_profile.id,
            models.CoachStudent.student_id == student_profile.id,
        )
        .delete(synchronize_session=False)
    )
    if not deleted:
        raise HTTPException(status_code=404, detail="등록된 학생이 아닙니다.")
    db.commit()
    return None
