# websites domain
import os

from dotenv import load_dotenv

loaded_envvars = load_dotenv(override=True)
assert loaded_envvars, "Have not loaded the environment variables"
# VWA
REDDIT = os.environ.get("REDDIT", "")
SHOPPING = os.environ.get("SHOPPING", "")
WIKIPEDIA = os.environ.get("WIKIPEDIA", "")
HOMEPAGE = os.environ.get("HOMEPAGE", "")
OPENTABLE = os.environ.get("OPENTABLE", "")
CLASSIFIEDS = os.environ.get("CLASSIFIEDS", "")
CLASSIFIEDS_RESET_TOKEN = os.environ.get("CLASSIFIEDS_RESET_TOKEN", "")
REDDIT_RESET_URL = os.environ.get("REDDIT_RESET_URL", "")

# WebArena
SHOPPING_ADMIN = os.environ.get("SHOPPING_ADMIN", "")
GITLAB = os.environ.get("GITLAB", "")
MAP = os.environ.get("MAP", "")


print(
    f"Env Var checks:\n{REDDIT}\n{SHOPPING}"
)

assert (
    REDDIT
    and SHOPPING
    and WIKIPEDIA
    and HOMEPAGE
    and CLASSIFIEDS
    and CLASSIFIEDS_RESET_TOKEN
#    and REDDIT_RESET_URL
), (
    f"Please setup the URLs and tokens to each site. Current: "
    + f"Reddit: {REDDIT}\n"
    # + f"  Reddit reset url: {REDDIT_RESET_URL}"
    + f"Shopping: {SHOPPING}\n"
    + f"Wikipedia: {WIKIPEDIA}\n"
    + f"Homepage: {HOMEPAGE}\n"
    + f"Classifieds: {CLASSIFIEDS}\n"
    + f"  Classifieds reset token: {CLASSIFIEDS_RESET_TOKEN}\n"
)


ACCOUNTS = {
    "reddit": {"username": "MarvelsGrantMan136", "password": "test1234"},
    "shopping": {
        "username": "emma.lopez@gmail.com",
        "password": "Password.123",
    },
    "classifieds": {
        "username": "blake.sullivan@gmail.com",
        "password": "Password.123",
    },
    "shopping_site_admin": {"username": "admin", "password": "admin1234"},
    "shopping_admin": {"username": "admin", "password": "admin1234"},
    "gitlab": {"username": "byteblaze", "password": "hello1234"},
}

URL_MAPPINGS = {
    # VWA:
    REDDIT: "http://reddit.com",
    SHOPPING: "http://onestopmarket.com",
    WIKIPEDIA: "http://wikipedia.org",
    HOMEPAGE: "http://homepage.com",
    CLASSIFIEDS: "http://classifieds.com",
    # WebArena:
    SHOPPING_ADMIN: "http://luma.com/admin",
    GITLAB: "http://gitlab.com",
    MAP: "http://openstreetmap.org",
}
