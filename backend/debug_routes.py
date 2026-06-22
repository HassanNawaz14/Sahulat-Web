"""Debug route inclusion."""
import sys
sys.path.insert(0, '.')

from app.main import app

print(f"Total routes in app.routes: {len(app.routes)}")
for r in app.routes:
    t = type(r).__name__
    if hasattr(r, 'methods'):
        print(f"  {t}: {r.methods} {r.path}")
    elif hasattr(r, 'router'):
        print(f"  {t}: included router with {len(r.router.routes)} routes")
        for sr in r.router.routes:
            print(f"    -> {sr.methods} {sr.path}")
    else:
        print(f"  {t}: {getattr(r, 'path', 'N/A')}")
