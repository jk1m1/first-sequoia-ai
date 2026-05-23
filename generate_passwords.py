"""
Run this script to generate hashed passwords for config.yaml.

Usage:
    python generate_passwords.py

Then copy the printed hashes into config.yaml under each user's 'password' field.
"""

import streamlit_authenticator as stauth

# ---- SET YOUR DESIRED PASSWORDS HERE ----
passwords = [
    "FirstSequoiaFinancial",    # will become eric's hash
    "FirstSequoiaFinancial",  # will become intern's hash
]
# -----------------------------------------

hashed = stauth.Hasher(passwords).generate()

print("\n=== Paste these hashes into config.yaml ===\n")
print(f"eric   →  {hashed[0]}")
print(f"intern →  {hashed[1]}")
print("\nDone. Keep your plaintext passwords private — delete them from this file after use.\n")
