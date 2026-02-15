"""
Örnek kullanıcı oluştur - Veritabanı sıfırlandığında giriş yapabilmek için.
API başlangıcında otomatik çalışır. Manuel: cd backend && python -m app.seed_user
"""
from sqlalchemy import select

from app.core.db_sync import get_sync_session
from app.core.security import get_password_hash
from app.models import User

DEFAULT_EMAIL = "deneme@gmail.com"
DEFAULT_PASSWORD = "deneme"


def seed_default_user():
    """Örnek kullanıcı yoksa oluştur; varsa şifreyi güncelle (hash uyumsuzluğu önlemi)."""
    with get_sync_session() as session:
        result = session.execute(select(User).where(User.email == DEFAULT_EMAIL))
        existing = result.scalars().first()
        fresh_hash = get_password_hash(DEFAULT_PASSWORD)
        if existing:
            existing.hashed_password = fresh_hash
            session.commit()
            print(f"[MemeVault] Örnek hesap güncellendi: {DEFAULT_EMAIL} / {DEFAULT_PASSWORD}")
            return
        user = User(
            email=DEFAULT_EMAIL,
            hashed_password=fresh_hash,
        )
        session.add(user)
        session.commit()
        print(f"[MemeVault] Örnek kullanıcı oluşturuldu: {DEFAULT_EMAIL} / {DEFAULT_PASSWORD}")


if __name__ == "__main__":
    seed_default_user()
