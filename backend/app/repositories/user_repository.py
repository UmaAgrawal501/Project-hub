from uuid import UUID

from sqlalchemy.orm import Session

from app.models import User, Workspace


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, user_id: UUID) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).one_or_none()

    def create(self, *, user_id: UUID, email: str, display_name: str) -> User:
        user = User(id=user_id, email=email.lower(), display_name=display_name)
        self.db.add(user)
        self.db.flush()
        return user

    def update_display_name(self, user: User, display_name: str) -> User:
        user.display_name = display_name
        self.db.add(user)
        self.db.flush()
        return user


class WorkspaceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_owner(self, owner_user_id: UUID) -> Workspace | None:
        return (
            self.db.query(Workspace)
            .filter(Workspace.owner_user_id == owner_user_id)
            .one_or_none()
        )

    def create(self, *, owner_user_id: UUID, name: str = "Personal") -> Workspace:
        workspace = Workspace(owner_user_id=owner_user_id, name=name)
        self.db.add(workspace)
        self.db.flush()
        return workspace
