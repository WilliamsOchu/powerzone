## Setup Libraries
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


## Specify the User Data to work with
class PendingUser(Base):
    __tablename__ = "pending_users"
    id = Column(Integer, primary_key=True, index=True)
    phone_num = Column(String, unique=True, index=True) # Should be unique for pending users
    hashed_password = Column(String)                    # The hashed password
    otp = Column(String)                                # The 6-digit OTP
    otp_expires_at = Column(DateTime(timezone=True))    # When the OTP expires
    attempt_reg_time = Column(DateTime(timezone=True))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    phone_num = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    registered_time = Column(DateTime(timezone=True))
    reset_tokens = relationship("PasswordResetToken", back_populates="user")



class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True) # The actual OTP/unique string
    user_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime(timezone=True))
    is_used = Column(Boolean, default=False) # To ensure tokens are single-use
    user = relationship("User", back_populates="reset_tokens")


