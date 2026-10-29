from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt
from jwt import PyJWKClient
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings
from app.core.logging import logger

# Strict allowlist of permitted cryptographic signature algorithms
ALLOWED_JWT_ALGORITHMS = ("ES256", "RS256", "HS256")

# In-memory cache for PyJWKClient instances by JWKS URL
_jwks_clients: Dict[str, PyJWKClient] = {}


def get_supabase_jwks_url() -> Optional[str]:
    """
    Resolve the JWKS endpoint URL for asymmetric ES256/RS256 verification.
    Uses explicit settings.supabase_url if configured; otherwise attempts to
    derive it from settings.database_url (e.g. Supabase hosted pooler).
    """
    if settings.supabase_url and settings.supabase_url.strip():
        return f"{settings.supabase_url.strip().rstrip('/')}/auth/v1/.well-known/jwks.json"
    if settings.database_url:
        import re
        match = re.search(r"postgres\.([a-z0-9]+):", settings.database_url)
        if match:
            return f"https://{match.group(1)}.supabase.co/auth/v1/.well-known/jwks.json"
    return None


def get_jwks_client(jwks_url: str) -> PyJWKClient:
    """
    Get or create a cached PyJWKClient configured with key caching and lifespan.
    """
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(
            jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            cache_jwk_set=True,
            lifespan=300,
        )
    return _jwks_clients[jwks_url]


def get_jwt_secret() -> str:
    """
    Retrieve the secret key used to verify and sign symmetric HS256 tokens.
    Fails closed in production if SUPABASE_JWT_SECRET is not configured.
    Never uses unrelated secrets or database credentials.
    """
    if settings.supabase_jwt_secret and settings.supabase_jwt_secret.strip():
        return settings.supabase_jwt_secret.strip()

    if settings.app_env == "production":
        raise RuntimeError(
            "Production authentication misconfigured: SUPABASE_JWT_SECRET is required when using HS256."
        )

    return settings.secret_key


def get_verification_key(token: str, alg: str) -> Any:
    """
    Resolve the cryptographic verification key corresponding to the algorithm.
    - For HS256: returns symmetric shared secret.
    - For ES256 / RS256: returns asymmetric public key from explicit config or Supabase JWKS.
    Fails closed if required keys or endpoints are unavailable.
    """
    if alg == "HS256":
        return get_jwt_secret()

    if alg in ("ES256", "RS256"):
        # 1. Use explicit public key if provided
        if settings.supabase_jwt_public_key and settings.supabase_jwt_public_key.strip():
            return settings.supabase_jwt_public_key.strip()

        # 2. Use JWKS endpoint if Supabase URL is resolved
        jwks_url = get_supabase_jwks_url()
        if jwks_url:
            client = get_jwks_client(jwks_url)
            try:
                signing_key = client.get_signing_key_from_jwt(token)
                return signing_key.key
            except jwt.exceptions.PyJWKClientError as exc:
                logger.debug("JWKS key resolution failed: %s", str(exc))
                raise ValueError(f"Invalid authentication token: {exc}") from exc
            except Exception as exc:
                logger.warning("Failed to retrieve public key from JWKS (%s): %s", jwks_url, str(exc))
                raise ValueError(
                    "Unable to retrieve public key for token verification: authentication service unreachable"
                ) from exc

        # Fail closed: No public key or JWKS URL available
        if settings.app_env == "production":
            raise RuntimeError(
                "Production authentication misconfigured: SUPABASE_URL or SUPABASE_JWT_PUBLIC_KEY is required for asymmetric JWT verification."
            )

        raise ValueError(
            "Cannot verify ES256/RS256 token: SUPABASE_URL or SUPABASE_JWT_PUBLIC_KEY is not configured."
        )

    raise ValueError(f"Unsupported algorithm '{alg}'")


def verify_token(token: str) -> Dict[str, Any]:
    """
    Cryptographically verify and decode a JWT bearer token.
    Enforces algorithm allowlist, signature validity, expiration, issuer, audience, and subject claims.
    Untrusted tokens cannot select or bypass algorithms.
    Never logs raw tokens or cryptographic keys.
    """
    # 1. Inspect unverified header strictly to guard against algorithm manipulation
    try:
        header = jwt.get_unverified_header(token)
    except Exception as exc:
        logger.debug("Failed to decode token header: %s", str(exc))
        raise ValueError(f"Malformed authentication token: {exc}") from exc

    token_alg = header.get("alg")
    if not token_alg or str(token_alg).lower() == "none":
        raise ValueError("Authentication token algorithm 'none' is strictly forbidden")

    token_alg_upper = str(token_alg).upper()
    if token_alg_upper not in ALLOWED_JWT_ALGORITHMS:
        raise ValueError(f"Authentication token algorithm '{token_alg}' is not allowlisted: {ALLOWED_JWT_ALGORITHMS}")

    permitted_algs = [a.upper() for a in settings.jwt_algorithms]
    if token_alg_upper not in permitted_algs:
        raise ValueError(
            f"Token algorithm '{token_alg}' does not match expected algorithm '{settings.jwt_algorithms}'"
        )

    # 2. Resolve matching verification key (fails closed if keys/secrets missing)
    key = get_verification_key(token, token_alg_upper)

    # 3. Cryptographic claim verification
    options = {
        "verify_signature": True,
        "verify_exp": True,
        "require": ["exp", "sub"],
    }

    kwargs: Dict[str, Any] = {
        "algorithms": [token_alg_upper],
        "options": options,
    }

    if settings.jwt_audience:
        kwargs["audience"] = settings.jwt_audience
        options["require"].append("aud")
    else:
        options["verify_aud"] = False

    if settings.jwt_issuer:
        kwargs["issuer"] = settings.jwt_issuer
        options["require"].append("iss")
    elif settings.supabase_url:
        kwargs["issuer"] = [f"{settings.supabase_url.rstrip('/')}/auth/v1", "supabase"]
        options["require"].append("iss")

    try:
        payload = jwt.decode(token, key, **kwargs)
    except ExpiredSignatureError as exc:
        logger.debug("Token verification failed: signature is expired")
        raise ValueError("Authentication token has expired") from exc
    except InvalidTokenError as exc:
        logger.debug("Token verification failed: %s", str(exc))
        raise ValueError(f"Invalid authentication token: {exc}") from exc

    if not payload.get("sub") or not str(payload["sub"]).strip():
        raise ValueError("Authentication token missing required subject claim (sub)")

    return payload


def create_access_token(
    subject: str,
    email: str,
    expires_delta_seconds: int = 3600,
    role: str = "authenticated",
    user_metadata: Optional[Dict[str, Any]] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a signed JWT for local development, testing, and persona simulation.
    Uses the exact same cryptographic structure as Supabase Auth tokens.
    """
    if settings.app_env == "production" and not settings.supabase_jwt_secret:
        raise RuntimeError("Cannot generate test token in production without SUPABASE_JWT_SECRET.")

    now = datetime.now(timezone.utc)
    payload: Dict[str, Any] = {
        "sub": str(subject),
        "email": email,
        "aud": settings.jwt_audience or "authenticated",
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_delta_seconds)).timestamp()),
    }

    if settings.jwt_issuer:
        payload["iss"] = settings.jwt_issuer
    elif settings.supabase_url:
        payload["iss"] = f"{settings.supabase_url.rstrip('/')}/auth/v1"

    if user_metadata:
        payload["user_metadata"] = user_metadata

    if extra_claims:
        payload.update(extra_claims)

    secret = get_jwt_secret()
    return jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)

