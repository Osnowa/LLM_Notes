from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
import bcrypt
from environs import Env

env = Env()
env.read_env()

SECRET_KEY = env.str("SECRET_KEY")  # "соль" для шифрования
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # время жизни токена в минутах    

# --- Пароли ---

def hash_password(password: str) -> str:
    """Хешируем пароль перед сохранением в БД"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли введённый пароль с хешем из БД"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


# --- JWT ---

def create_access_token(data: dict) -> str:
    '''Создаем JWT токен, содержащий payload (словарь) с данными пользователя, которые мы хотим сохранить и проверить'''
    to_encode = data.copy()             # копируем, чтобы не испортить оригинал

    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) 
    to_encode["exp"] = expire           # добавляем время жизни # JWT сам проверит это поле при декодировании

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM) # возвращает токен

def decode_access_token(token: str) -> dict | None:
    """
    Расшифровывает токен → возвращает payload (словарь).
    Если токен невалидный или истёк — возвращает None.
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None