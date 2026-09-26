import hashlib
import hmac

class EdgeSecurity:
    """
    Edge Gateway Security & Signature Validator.
    Ensures outbound telemetry to VERDICT is cryptographically signed and read-only.
    """
    @staticmethod
    def sign_payload(payload: str, secret_key: str) -> str:
        return hmac.new(secret_key.encode(), payload.encode(), hashlib.sha256).hexdigest()

    @staticmethod
    def verify_signature(payload: str, signature: str, secret_key: str) -> bool:
        expected = EdgeSecurity.sign_payload(payload, secret_key)
        return hmac.compare_digest(expected, signature)
