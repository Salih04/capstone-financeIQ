import json
import time
import urllib.request
from datetime import datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Asymmetric algorithms used by Supabase "JWT Signing Keys". HS256 is handled
# separately via the shared secret — never accept HS256 through the JWKS path
# (prevents alg-confusion attacks).
_ASYMMETRIC_ALGS = {"RS256", "RS384", "RS512", "ES256", "ES384", "ES512"}

# In-memory JWKS cache: url -> (jwks_dict, fetched_at_monotonic).
_JWKS_CACHE: dict[str, tuple[dict, float]] = {}
_JWKS_TTL_SECONDS = 600.0  # 10 min


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def _http_get_json(url: str) -> dict:
    """Fetch JSON over HTTPS. Isolated seam so tests can mock JWKS without network."""
    with urllib.request.urlopen(url, timeout=5) as resp:  # noqa: S310 - https JWKS URL
        return json.loads(resp.read().decode("utf-8"))


def _get_jwks(url: str, *, force: bool = False) -> dict:
    now = time.monotonic()
    cached = _JWKS_CACHE.get(url)
    if cached and not force and (now - cached[1]) < _JWKS_TTL_SECONDS:
        return cached[0]
    jwks = _http_get_json(url)
    _JWKS_CACHE[url] = (jwks, now)
    return jwks


def _verify_kwargs() -> dict:
    """Common claim-validation options. exp/nbf/iat always verified; aud/iss only
    when configured (so local/test tokens without an issuer still work)."""
    kwargs: dict = {}
    options = {"verify_aud": False}
    if settings.SUPABASE_JWT_AUDIENCE:
        kwargs["audience"] = settings.SUPABASE_JWT_AUDIENCE
        options["verify_aud"] = True
    issuer = settings.supabase_issuer()
    if issuer:
        kwargs["issuer"] = issuer
    kwargs["options"] = options
    return kwargs


def _decode_with_jwks(token: str, kid: str | None, alg: str) -> dict:
    url = settings.supabase_jwks_url()
    if not url:
        raise JWTError("Supabase JWKS not configured (set SUPABASE_URL or SUPABASE_JWKS_URL)")
    jwks = _get_jwks(url)
    key = _select_jwk(jwks, kid)
    if key is None:
        # kid may be from a rotated key not in the cached set — refresh once.
        jwks = _get_jwks(url, force=True)
        key = _select_jwk(jwks, kid)
    if key is None:
        raise JWTError("No matching JWKS key for token kid")
    return jwt.decode(token, key, algorithms=[alg], **_verify_kwargs())


def _select_jwk(jwks: dict, kid: str | None) -> dict | None:
    keys = (jwks or {}).get("keys") or []
    if kid:
        for k in keys:
            if k.get("kid") == kid:
                return k
        return None
    return keys[0] if len(keys) == 1 else None


def decode_supabase_token(token: str) -> dict:
    """Verify a Supabase access token's signature and claims.

    - Asymmetric (RS256/ES256, new "JWT Signing Keys") → verified via JWKS.
    - HS256 (legacy shared secret) → verified with SUPABASE_JWT_SECRET.

    Raises JWTError if no correct verifier is configured or verification fails —
    callers translate this to a safe 401 (never leaks why). Email/claims are only
    returned after the signature verifies.
    """
    header = jwt.get_unverified_header(token)  # raises JWTError on malformed token
    alg = header.get("alg")
    kid = header.get("kid")

    if alg in _ASYMMETRIC_ALGS:
        return _decode_with_jwks(token, kid, alg)

    if alg == "HS256":
        if not settings.SUPABASE_JWT_SECRET:
            raise JWTError("SUPABASE_JWT_SECRET is not configured")
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            **_verify_kwargs(),
        )

    raise JWTError(f"Unsupported token alg: {alg!r}")
