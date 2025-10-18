import pathlib
from passlib.context import CryptContext
pwd_context =CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash(password: str):
    return pwd_context.hash(password)

def verify(plain_password, hashed_password):
    return pwd_context.verify(plain_password,hashed_password)

def del_file(path):
    pathlib.Path(path).unlink(missing_ok=False)
    print("file delected")