import hashlib

from typing import Dict

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey  

from .key import XKeyPair, EdKeyPair 

class OmemoBundle:
    def __init__(
                self,
                device_id: int,
                indentity_key: EdKeyPair,
                signed_prekey: XKeyPair,
                onetime_prekeys: Dict[str, XKeyPair],
            ):
        self._device_id = device_id
        self._indentity_key = indentity_key
        self._signed_prekey = signed_prekey
        self._onetime_prekeys = onetime_prekeys

    def get_device_id(self):
        return self._device_id

    def get_indentity(self) -> EdKeyPair:
        return self._indentity_key

    def get_prekey(self) -> XKeyPair:
        return self._signed_prekey

    def get_onetime_prekeys(self) -> Dict[str, XKeyPair]:
        return self._onetime_prekeys
    
    def get_onetime_prekey(self, id: str) -> XKeyPair:
        try:
            return self._onetime_prekeys[id]
        except KeyError:
            raise Exception("There is no PreKey with this ID.")

    def get_prekey_signature(self, encoding="utf-8") -> bytes | str:
        return self._indentity_key.sign_public_key(
                public_key=self._signed_prekey.get_public_key(),
                encoding=encoding
        )
    
    def get_indentity_fingerprint(self) -> bytes:
        public_bytes = self._indentity_key.get_public_key_bytes()
        return OmemoBundle.public_key_to_fingerprint(public_bytes)  

    def get_indentity_hex_fingerprint(self) -> str:
        public_bytes = self._indentity_key.get_public_key_bytes()
        return OmemoBundle.public_key_to_hex_fingerprint(public_bytes)


    @staticmethod
    def public_key_to_fingerprint(public_key_bytes: bytes):
        hash_obj = hashlib.sha256()
        hash_obj.update(public_key_bytes)
        return hash_obj.digest() 

    @staticmethod
    def public_key_to_hex_fingerprint(public_key_bytes: bytes):
        return OmemoBundle.public_key_to_fingerprint(public_key_bytes).hex()

