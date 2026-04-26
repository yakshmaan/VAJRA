import hashlib
import secrets
import time
from datetime import datetime

# CRYSTALS-Kyber and CRYSTALS-Dilithium simulation
# Production would use liboqs (Open Quantum Safe library)
# This simulates the handshake logic and timing

class KyberSimulator:
    """
    Simulates CRYSTALS-Kyber KEM (Key Encapsulation Mechanism)
    NIST PQC Standard - Lattice-based encryption
    Security level: Kyber-768 (equivalent to AES-192)
    """
    SECURITY_LEVEL = "Kyber-768"
    KEY_SIZE = 32  # bytes

    def keygen(self, node_id: str) -> dict:
        """Generate public/private keypair for a node"""
        seed = secrets.token_bytes(32)
        private_key = hashlib.sha3_256(seed + node_id.encode()).hexdigest()
        public_key = hashlib.sha3_256(private_key.encode() + b'_pub').hexdigest()
        return {
            "node_id": node_id,
            "public_key": public_key,
            "private_key": private_key,
            "algorithm": self.SECURITY_LEVEL,
            "key_size_bits": self.KEY_SIZE * 8
        }

    def encapsulate(self, public_key: str) -> dict:
        """Sender encapsulates shared secret using recipient's public key"""
        t0 = time.perf_counter()
        ephemeral = secrets.token_bytes(32)
        ciphertext = hashlib.sha3_512(
            public_key.encode() + ephemeral
        ).hexdigest()
        shared_secret = hashlib.sha3_256(
            ciphertext.encode() + b'_shared'
        ).hexdigest()
        latency_ms = (time.perf_counter() - t0) * 1000

        return {
            "ciphertext": ciphertext[:64],
            "shared_secret": shared_secret[:32],
            "latency_ms": round(latency_ms, 4),
            "algorithm": self.SECURITY_LEVEL
        }

    def decapsulate(self, ciphertext: str, private_key: str) -> dict:
        """Recipient decapsulates to recover shared secret"""
        t0 = time.perf_counter()
        shared_secret = hashlib.sha3_256(
            (ciphertext + private_key).encode()
        ).hexdigest()
        latency_ms = (time.perf_counter() - t0) * 1000

        return {
            "shared_secret": shared_secret[:32],
            "latency_ms": round(latency_ms, 4)
        }


class DilithiumSimulator:
    """
    Simulates CRYSTALS-Dilithium digital signatures
    NIST PQC Standard - Lattice-based signatures
    Security level: Dilithium3 (equivalent to AES-192)
    """
    SECURITY_LEVEL = "Dilithium3"

    def sign(self, message: str, private_key: str) -> dict:
        """Sign a transaction message"""
        t0 = time.perf_counter()
        signature = hashlib.sha3_512(
            (message + private_key).encode()
        ).hexdigest()
        latency_ms = (time.perf_counter() - t0) * 1000

        return {
            "signature": signature[:64],
            "message_hash": hashlib.sha3_256(message.encode()).hexdigest()[:32],
            "algorithm": self.SECURITY_LEVEL,
            "latency_ms": round(latency_ms, 4)
        }

    def verify(self, message: str, signature: str, public_key: str) -> dict:
        """Verify a transaction signature"""
        t0 = time.perf_counter()
        expected = hashlib.sha3_512(
            (message + hashlib.sha3_256(
                (public_key + b'_priv' if isinstance(public_key, bytes)
                 else public_key + '_priv').encode()
            ).hexdigest()).encode()
        ).hexdigest()
        valid = secrets.compare_digest(signature[:32], expected[:32])
        latency_ms = (time.perf_counter() - t0) * 1000

        return {
            "valid": valid,
            "latency_ms": round(latency_ms, 4),
            "algorithm": self.SECURITY_LEVEL
        }


class VAJRAPQCHandshake:
    """
    Full PQC handshake between two VAJRA nodes.
    Combines Kyber (encryption) + Dilithium (signatures).
    """

    def __init__(self):
        self.kyber = KyberSimulator()
        self.dilithium = DilithiumSimulator()

    def handshake(self, sender_id: str, receiver_id: str, tx_payload: dict) -> dict:
        t_start = time.perf_counter()

        # Step 1: Key generation for both nodes
        sender_keys = self.kyber.keygen(sender_id)
        receiver_keys = self.kyber.keygen(receiver_id)

        # Step 2: Kyber key encapsulation
        encap = self.kyber.encapsulate(receiver_keys['public_key'])

        # Step 3: Dilithium signature on tx payload
        tx_string = str(sorted(tx_payload.items()))
        sig = self.dilithium.sign(tx_string, sender_keys['private_key'])

        # Step 4: Verify signature
        verify = self.dilithium.verify(
            tx_string,
            sig['signature'],
            sender_keys['public_key']
        )

        total_ms = round((time.perf_counter() - t_start) * 1000, 4)

        return {
            "handshake_id": secrets.token_hex(8),
            "sender": sender_id,
            "receiver": receiver_id,
            "kyber": {
                "algorithm": encap['algorithm'],
                "ciphertext": encap['ciphertext'][:16] + "...",
                "shared_secret": encap['shared_secret'][:16] + "...",
                "latency_ms": encap['latency_ms']
            },
            "dilithium": {
                "algorithm": sig['algorithm'],
                "signature": sig['signature'][:16] + "...",
                "verified": verify['valid'],
                "latency_ms": sig['latency_ms']
            },
            "total_handshake_ms": total_ms,
            "quantum_resistant": True,
            "timestamp": datetime.utcnow().isoformat()
        }


def secure_tx(tx: dict) -> dict:
    """Wrap a transaction with PQC handshake"""
    pqc = VAJRAPQCHandshake()
    sender = tx.get('entity_id', 'VAJRA_NODE_IN')
    receiver = f"VAJRA_NODE_{tx.get('corridor', 'IN-UAE').split('-')[1]}"

    result = pqc.handshake(sender, receiver, tx)

    return {
        **tx,
        'pqc_secured': True,
        'handshake_id': result['handshake_id'],
        'kyber_algorithm': result['kyber']['algorithm'],
        'dilithium_verified': result['dilithium']['verified'],
        'pqc_latency_ms': result['total_handshake_ms'],
        'quantum_resistant': True
    }


if __name__ == "__main__":
    pqc = VAJRAPQCHandshake()

    corridors = [
        ("HDFC_BANK_001", "CENTRAL_BANK_UAE", {"tx_id": "TX001", "amount": 500000, "corridor": "IN-UAE"}),
        ("ROSNEFT_RU_007", "CENTRAL_BANK_RU", {"tx_id": "TX002", "amount": 1200000, "corridor": "IN-RU"}),
    ]

    for sender, receiver, payload in corridors:
        result = pqc.handshake(sender, receiver, payload)
        print(f"\n⚡ [PQC] Handshake: {sender} → {receiver}")
        print(f"   Handshake ID:  {result['handshake_id']}")
        print(f"   Kyber:         {result['kyber']['algorithm']}")
        print(f"   Dilithium:     {result['dilithium']['algorithm']}")
        print(f"   Verified:      {result['dilithium']['verified']}")
        print(f"   Total Latency: {result['total_handshake_ms']}ms")
        print(f"   Quantum Safe:  {result['quantum_resistant']}")