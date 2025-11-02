import os, sys

# Make sure /srv/chat is importable
BASE = os.path.dirname(__file__)
if BASE not in sys.path:
    sys.path.insert(0, BASE)

# Import the FINAL full app (the one that logs
# "🔐 HODLXXI OAuth2/OIDC System Initialized" and defines /oauth/* etc)
from app.app import app

if __name__ == "__main__":
    app.run()
# Gunicorn will look for variable "app" in this module,
# so no extra work needed. If something expects `application`, expose both:
application = app
