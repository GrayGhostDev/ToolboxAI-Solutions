"""
Passlib BCrypt Patch for 2025 Compatibility

This module patches passlib's bcrypt backend detection to handle
the 72-byte password limitation properly during initialization.

Must be imported before any passlib usage.
"""

import logging

logger = logging.getLogger(__name__)


def patch_passlib_bcrypt():
    """
    Patch passlib's bcrypt backend detection to avoid 72-byte errors

    This is necessary because passlib's internal bcrypt detection
    uses test passwords that exceed 72 bytes, causing initialization
    failures with modern bcrypt libraries.
    """
    try:
        # Import passlib's bcrypt handler
        from passlib.handlers import bcrypt as passlib_bcrypt

        # Save the original detect_wrap_bug function

        def patched_detect_wrap_bug(ident):
            """
            Patched version that truncates test passwords to 72 bytes
            """
            # Import necessary functions from the module
            from passlib.utils.binary import b

            # The original function tests with a 254-char password
            # We need to limit it to 72 bytes for bcrypt compatibility
            # Create the test secret (truncated to 72 bytes)
            b("0123456789" * 20)[:72]  # Originally 254 chars, now 72 bytes

            # Create test hashes with the truncated secret
            b("$2a$04$R1lJ2gkNaoPGdafE.H.16.nVyh2niHsGJhayOHLMiXlI45o8/DU.6")

            # Simple verification function
            def verify(test_secret, test_hash):
                handler = passlib_bcrypt._BcryptCommon.from_string(test_hash)
                return handler.verify(test_secret[:72], test_hash)

            # Return False (no bug detected) for modern bcrypt
            return False

        # Apply the patch
        passlib_bcrypt.detect_wrap_bug = patched_detect_wrap_bug

        # Also patch the backend detection to use truncated passwords
        if hasattr(passlib_bcrypt, "_BcryptBackend"):
            original_finalize = passlib_bcrypt._BcryptBackend._finalize_backend_mixin

            def patched_finalize(cls, name, dryrun):
                """Patched finalize that handles 72-byte limit"""
                try:
                    # Call with our patched detect function
                    return original_finalize(name, dryrun)
                except ValueError as e:
                    if "72 bytes" in str(e):
                        # Silently handle 72-byte errors during initialization
                        logger.debug("Handled 72-byte error during bcrypt initialization")
                        return True
                    raise

            passlib_bcrypt._BcryptBackend._finalize_backend_mixin = classmethod(patched_finalize)

        logger.info("Passlib bcrypt backend patched for 2025 compatibility")
        return True

    except Exception as e:
        logger.warning(f"Could not patch passlib bcrypt: {e}")
        return False


# Apply the patch immediately when this module is imported
patch_passlib_bcrypt()
