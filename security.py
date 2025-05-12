from passlib.context import CryptContext
import bcrypt

# Create a CryptContext instance for password hashing
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    """
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    return pwd_context.verify(plain_password, hashed_password)