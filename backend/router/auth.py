## Setup Libraries
from datetime import timedelta, datetime, timezone

from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, HTTPException, status, APIRouter, Response
from fastapi.responses import RedirectResponse # If you plan to use server-side redirects


from sqlalchemy.orm import Session

from ..auth.auth_handler import (
    authenticate_user, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token,
    get_user, get_password_hash,
    generate_password_reset_token, save_password_reset_token,
    get_password_reset_token, mark_token_as_used,
    update_user_password,
    # NEW IMPORTS FOR EMAIL VERIFICATION
    generate_six_digit_otp, save_pending_user_registration,
    get_pending_user_by_phone_num, delete_pending_user, send_signup_otp
)
from ..databse import get_db
from ..schemas import Token, UserCreate, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, VerifyOTPRequest, LoginOTPRequest, VerifyLoginOTPRequest
from ..models import User, PendingUser




router = APIRouter()


@router.post("/register", response_model=dict, status_code=status.HTTP_202_ACCEPTED)
async def register_user_initiate(user_data: UserCreate, db: Session = Depends(get_db)):


    db_user_phone_num = get_user(db, user_data.phone_num)
    if db_user_phone_num:
        raise HTTPException(status_code=400, detail="User already registered.")
    
    now = datetime.now(timezone.utc)

    existing_pending_phone_num_user = get_pending_user_by_phone_num(db, user_data.phone_num) # This already checks expiry
    if existing_pending_phone_num_user:
        if existing_pending_phone_num_user.otp_expires_at > now:
            raise HTTPException(status_code=400, detail="A verification code has already been sent to this number. Please check your inbox or wait for it to expire.")
        else:
            # OTP expired, delete old pending record to allow new one
            delete_pending_user(db, existing_pending_phone_num_user)
            db.commit() # Commit after deletion



    hashed_password = get_password_hash(user_data.password)

    # 4. Generate OTP
    otp = generate_six_digit_otp()

    # 5. Save pending user data with OTP
    save_pending_user_registration(db, user_data.phone_num, hashed_password, otp)

    # 6. Send OTP to email
    #await send_verification_otp_email(user_data.phone_num, otp)
    await send_signup_otp(user_data.phone_num, otp)

    return {"message": "A 6-digit verification code has been sent to your email. Please verify to complete registration."}
