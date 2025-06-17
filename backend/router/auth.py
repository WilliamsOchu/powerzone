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
    get_pending_user_by_phone_num, delete_pending_user, 
    send_signup_otp, send_password_reset_token
)
from ..databse import get_db
from ..schemas import Token, UserCreate, UserResponse, ForgotPasswordRequest, ResetPasswordRequest, VerifyOTPRequest #LoginOTPRequest, VerifyLoginOTPRequest
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


@router.post("/verify_signup", response_model=UserResponse)
async def verify_signup_otp(otp_request: VerifyOTPRequest, db: Session = Depends(get_db)):
    """
    Verifies the 6-digit OTP sent to the user's phone and completes registration.
    """
    # 1. Get the pending user data using the email (which also checks for expiry)
    pending_user = get_pending_user_by_phone_num(db, otp_request.phone_num)

    if not pending_user:
        # This covers cases where email doesn't exist in pending, or OTP has already expired
        raise HTTPException(status_code=400, detail="No pending registration found for this email or OTP has expired. Please try registering again.")

    # 2. Validate the OTP
    if pending_user.otp != otp_request.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP. Please check the code sent to your email.")

    # 3. Double-check OTP expiry (good for robustness, though get_pending_user_by_email already filters)
    now = datetime.now(timezone.utc)
    if pending_user.otp_expires_at <= now:
        delete_pending_user(db, pending_user) # Clean up expired token
        db.commit()
        raise HTTPException(status_code=400, detail="OTP has expired. Please initiate registration again to get a new code.")

    # 4. Create the actual user in the User table
    registered_time = datetime.now(timezone.utc)
    new_user = User(
        phone_num=pending_user.phone_num,
        hashed_password=pending_user.hashed_password,
        registered_time=registered_time
    )
    db.add(new_user)
    db.commit() # Commit the new user creation

    # 5. Delete the pending user record as registration is complete
    delete_pending_user(db, pending_user)
    db.commit() # Commit the deletion of the pending user

    db.refresh(new_user) # Refresh to get the auto-generated ID etc.
    return new_user # Return the newly created user's data


@router.post("/login", response_model=Token) # Removed response_model=Token for this step
async def request_login(
    form_data: OAuth2PasswordRequestForm = Depends(), # Still accepts standard form data
    db: Session = Depends(get_db)
) -> Token:
    """
    Authenticates user credentials.
    """
    # 1. Authenticate user credentials
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 4. Generate and return the access token
    access_token_expires = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES))
    access_token = create_access_token(
        data={"sub": user.phone_num}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key="access_token",
        httponly=True,
        samesite="lax",
        secure=True # Set to True in production with HTTPS
    )
    return {"message": "Logged out successfully. Please clear your token and redirect."}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Initiates the password reset process.
    Generates a password reset token and sends it to the user's phone number
    """
    user = get_user(db, request.phone_num)
    if not user:
        # For security, always return a generic success message
        # even if the email doesn't exist to prevent user enumeration.
        return {"message": "If an account with that number exists, a password reset email has been sent."}

    # Generate a unique, secure token
    reset_token = generate_password_reset_token()
    
    # Save the token to the database, linked to the user
    save_password_reset_token(db, user.id, reset_token)

    # --- Choose between OTP or Reset Link ---
    # Set this to True for OTP (user types in code) or False for a direct link (user clicks link)
    #send_as_otp = True

    #if send_as_otp:
        # Send the raw token as an OTP in the email
    #    await send_password_reset_email(request.email, reset_token, is_otp=True)
    #else:
        # Construct the full reset link for the user to click
        # IMPORTANT: Replace "http://localhost:3000" with your actual frontend's base URL
        # The frontend should have a route like /reset-password that expects a 'token' query param
    #    reset_link = f"http://localhost:3000/reset-password?token={reset_token}&email={request.email}"
    await send_password_reset_token(request.phone_num, reset_token)

    return {"message": "If an account with that number exists, a password reset OTP has been sent."}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Resets the user's password using the provided token and new password.
    """
    # 1. Verify user by phone first
    user = get_user(db, request.phone_num)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone or token." # Generic message for security
        )

    # 2. Retrieve and validate the token from the database
    # Check if the token exists, is not expired, and has not been used yet.
    db_token = get_password_reset_token(db, request.token)
    
    if not db_token or db_token.user_id != user.id:
        # If token is invalid, expired, or doesn't belong to the email provided
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token."
        )
    
    # Ensure the token hasn't been used already
    if db_token.is_used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has already been used."
        )

    # 3. Update the user's password
    update_user_password(db, user, request.new_password)

    # 4. Mark the token as used to prevent replay attacks
    mark_token_as_used(db, db_token)
    
    db.commit() # Commit all changes (password update and token status)
    db.refresh(user) # Refresh the user object after commit

    return {"message": "Password has been successfully reset."}
