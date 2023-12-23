from pydantic import EmailStr, constr, validator

from .helpers import BaseModel


class LoginModel(BaseModel):
    email: EmailStr
    password: constr(min_length=5, strip_whitespace=True)


class SignupModel(BaseModel):
    email: EmailStr
    password: constr(min_length=5, strip_whitespace=True)
    confirm_password: constr(min_length=5, strip_whitespace=True)

    @validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, values):
        if "password" in values and v != values["password"]:
            raise ValueError("passwords do not match")
        return v
