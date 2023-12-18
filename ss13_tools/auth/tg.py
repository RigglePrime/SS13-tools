"""
Auth module

Provides methods to authenticate against raw logs
"""
from __future__ import annotations

# Grrr globals but right now I don't care, refactor later
# Maybe if another station needs to add their own auth

import time
import os
import getpass
import platform
import locale
import pickle
import struct
from datetime import timedelta
from typing import Optional

from colorama import Fore, Style
from Crypto.Hash import SHA256
from Crypto.Cipher import AES
import requests as req
from requests.exceptions import ReadTimeout
from pyperclip import copy, paste, PyperclipException

from ..constants import USER_AGENT, __version__
from .constants import PASSPORT_FILE_LOCATION, PASSPORT_FILE_NAME, PASSPORT_FILE_HEADER, AUTH_TEST_URL, \
                       TOKEN_URL, PASSPORT_URL


PASSPORT: Passport = None


class Passport():
    """Passport class"""

    rawlogs_passport: str = ""
    expires_at: float = 0
    current_server_time: float = 0
    local_time_delta: float = 0

    def __init__(self, token: str) -> None:
        if not token:
            return
        # Request a new passport to be issued
        passport_response = req.get(PASSPORT_URL,
                                    headers={"User-Agent": USER_AGENT, "Authorization": f"Bearer {token}"},
                                    timeout=10)
        if not passport_response.ok:
            return

        # Shush I'm lazy I will do it this way for now
        passport_response = passport_response.json()
        if (err := passport_response.get("error")):
            print(err)
            return
        self.rawlogs_passport = passport_response["rawlogs_passport"]
        self.expires_at = float(passport_response["expires_at"])
        self.current_server_time = float(passport_response["current_server_time"])
        self.local_time_delta = time.time() - self.current_server_time

    def seconds_left(self) -> float:
        """The number of seconds this token has left before impending death. Now including fractions!"""
        return self.expires_at - time.time() + self.local_time_delta

    def test(self) -> bool:
        """Tests the passport for validity"""
        return bool(self.rawlogs_passport) and\
            self.expires_at > time.time() + self.local_time_delta and\
            req.get(AUTH_TEST_URL,
                    headers={"User-Agent": USER_AGENT, "Authorization": f"Bearer {self.rawlogs_passport}"},
                    timeout=10).ok

    def __getstate__(self):
        return (__version__, self.__dict__)

    def __setstate__(self, state: tuple):
        if state[0] != __version__:
            return
        self.__dict__ = state[1]

    def save_to_file(self, path: str = PASSPORT_FILE_LOCATION + PASSPORT_FILE_NAME) -> None:
        """Saves the passport to a file"""
        with open(path, 'ab+') as file:
            file.seek(0, 0)  # Append puts us at the end of the file
            header = file.read(len(PASSPORT_FILE_HEADER))  # Try read the header
            if file.tell() and header and header != PASSPORT_FILE_HEADER:
                raise FileExistsError(f"The file at {path} already exists and is not a passport file")

            cipher = AES.new(generate_key(), AES.MODE_GCM)
            passport_pickle = pickle.dumps(self)
            passport_pickle, mac = cipher.encrypt_and_digest(passport_pickle)

            file.seek(0, 0)
            file.truncate()
            file.write(PASSPORT_FILE_HEADER)
            file.write(struct.pack("<B", len(cipher.nonce)))
            file.write(cipher.nonce)
            file.write(struct.pack("<I", len(passport_pickle)))
            file.write(passport_pickle)
            file.write(struct.pack("<B", len(mac)))
            file.write(mac)

    @staticmethod
    def load_from_file(path: str = PASSPORT_FILE_LOCATION + PASSPORT_FILE_NAME) -> Optional[Passport]:
        """Reads a passport from a file"""
        with open(path, 'rb') as file:
            header = file.read(len(PASSPORT_FILE_HEADER))  # Try read the header
            # file.tell tells us if we moved in the file at all, check header if it's empty, and then validate it
            if file.tell() and header and header != PASSPORT_FILE_HEADER:
                raise FileNotFoundError(f"The file at {path} is not a passport file")

            nonce_len = struct.unpack('<B', file.read(1))[0]  # Yes, yes, <B and B are the same, shush
            nonce = file.read(nonce_len)
            cipher = AES.new(generate_key(), AES.MODE_GCM, nonce=nonce)
            pickle_len = struct.unpack('<I', file.read(4))[0]
            passport_file = file.read(pickle_len)
            mac_len = struct.unpack('<B', file.read(1))[0]
            mac = file.read(mac_len)
            try:
                passport_file = cipher.decrypt_and_verify(passport_file, mac)
            except ValueError:  # Wuh oh, mac doesn't match! Someone tampered with our file!
                return None  # NEVER load a pickle you don't trust
            return pickle.loads(passport_file)


def generate_key() -> bytes:
    """
    Generates the 256-bit encryption/decryption key.
    This is NOT meant to be safe, and is NOT a replacement
    for a safe, user-defined password, just safe enough so
    our user doesn't accidentally share their passport.
    Or if their files get leaked, the passport is protected.

    Passports are by their very nature short lived. Because
    saving it is insecure, tokens aren't stored next to them.
    (tokens have a longer lifespan)

    Hopefully if someone asks our user for all of this info
    they will get extremely suspicious. What I made is probably
    safer than most users' passwords anyway.
    """
    bits, linkage = platform.architecture()
    loc, encoding = locale.getlocale()
    key: str = platform.node() + getpass.getuser() + bits + linkage + time.tzname[0] + loc + encoding
    sha = SHA256.new()
    sha.update(key.encode())
    return sha.digest()


def save_passport() -> None:
    """Saves the provided passport"""
    PASSPORT.save_to_file()


def load_passport() -> None:
    """Loads the passport into the auth module"""
    global PASSPORT  # pylint: disable=global-statement
    passport_file_path = PASSPORT_FILE_LOCATION + PASSPORT_FILE_NAME
    try:
        PASSPORT = Passport.load_from_file(path=passport_file_path)
    except FileNotFoundError:
        pass
    # I'd love to catch a specific exception but struct.unpact just says... error
    except Exception:  # pylint: disable=broad-exception-caught
        print(f"The passport file at {passport_file_path} is malformed, trying to remove")
        try:
            os.remove(passport_file_path)
        except Exception:  # pylint: disable=broad-exception-caught
            print("The file could not be removed.")


def create_from_token(token: str, override_old: bool = False) -> Optional[Passport]:
    """Creates a new passport from a token. Tests the token before setting it, retuning if the token is valid or not

    If override_old is not true, the new token won't be used if the old one is still valid"""
    if is_authenticated() and not override_old:
        return True
    global PASSPORT  # pylint: disable=global-statement
    new_passport = Passport(token=token)
    if not new_passport.test():
        return None
    PASSPORT = new_passport
    return new_passport


def interactive():  # noqa: C901
    """Interactively authenticate. Calls functions to load and test the passport before asking the user"""
    global PASSPORT  # pylint: disable=global-statement
    print("Authenticating...", end='')
    if is_authenticated():
        print(Fore.GREEN, "passport valid", Fore.RESET)
        valid_for = timedelta(seconds=seconds_left())
        print(f"The token has {valid_for} left.")
        return True
    print(Fore.RED, "not authenticated!", Fore.RESET)
    copied = ""
    token = ""
    try:
        # Copy and paste can throw, make sure they don't crash everything
        token = paste()
        copy(TOKEN_URL)
        copied = f"{Fore.CYAN}Link copied to clipboard!{Fore.RESET} If you leave the field {Fore.CYAN}empty{Fore.RESET}, " +\
                 f"the program will {Fore.CYAN}auto-paste{Fore.RESET} for you. "
    except PyperclipException:
        pass
    print(f"Please go to {Style.BRIGHT}{TOKEN_URL}{Style.NORMAL} and obtain a token. {copied}The token will NOT be saved " +
          f"in this software, so please store it somewhere safe.\nWith it, anyone could access raw logs, {Fore.CYAN}" +
          f"treat it as you would treat a password{Fore.RESET}! {Fore.RED}If you accidentally leak this, change your " +
          f"password immediately{Fore.RESET} to invalidate it.")
    print(f"If you are having trouble copy-pasting the link, select it with your mouse and {Fore.CYAN}right click" +
          f"{Fore.RESET}. That should copy it.")
    print("Right clicking will also paste the contents of your clipboard if nothing is selected.")
    while True:
        if not verify_token_format(token):
            token = input("Token: ").strip()
        if not token:
            try:
                token = paste()
            except PyperclipException:
                print("Could not paste from clipboard, please paste the token manually.")
                continue
        if not verify_token_format(token):
            print("What you pasted does not appear to be the token. Copy only what comes after '=>'")
            continue
        try:
            new_passport = Passport(token=token)
            if new_passport.test():
                valid_for = timedelta(seconds=new_passport.seconds_left())
                print(f"{Fore.GREEN}Authenticated.{Fore.RESET} Valid for {valid_for} from now")
                PASSPORT = new_passport
                save_passport()
                return True
        except ReadTimeout:
            print("Read timeout")
        print(f"{Fore.RED}Something went wrong, please try again.{Fore.RESET}")


def verify_token_format(token: str) -> bool:
    """Checks if the string is in token format"""
    return token.endswith(".fin") and token.count('.') == 3


# This gets called a lot, I should probably change how test works some day, but right now it's fine
def is_authenticated() -> bool:
    """Checks if we're authenticated. If a passport file exists and is invalid, it will be deleted"""
    return bool(PASSPORT) and PASSPORT.test()


def seconds_left() -> float:
    """Returns the TTL in seconds"""
    return PASSPORT.seconds_left()


def get_auth_headers():
    """Returns all headers needed to authorize. Does not check validity."""
    if not PASSPORT:
        return None
    return {"Authorization": f"Bearer {PASSPORT.rawlogs_passport}"}
