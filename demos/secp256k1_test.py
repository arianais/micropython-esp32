import time
import secp256k1
import hashlib
from binascii import hexlify

def secp256k1_example():
    """Usage example for secp256k1 usermodule"""

    # randomize context from time to time
    # - it helps against sidechannel attacks
    # secp256k1.context_randomize(os.urandom(32))

    # some random secret key
    secret = hashlib.sha256(b"secret key").digest()

    print("Secret key:", hexlify(secret).decode())

    # Makes sense to check if secret key is valid.
    # It will be ok in most cases, only if secret > N it will be invalid
    if not secp256k1.ec_seckey_verify(secret):
        raise ValueError("Secret key is invalid")

    # computing corresponding pubkey
    pubkey = secp256k1.ec_pubkey_create(secret)

    # serialize the pubkey in compressed format
    sec = secp256k1.ec_pubkey_serialize(pubkey, secp256k1.EC_COMPRESSED)
    print("Public key:", hexlify(sec).decode())
 
    # this is how you parse the pubkey
    pubkey = secp256k1.ec_pubkey_parse(sec)

    # Signature generation:
 
    # hash of the string "hello"
    msg = hashlib.sha256(b"hello").digest()

    t1 = time.ticks_ms()
    # signing
    sig = secp256k1.ecdsa_sign(msg, secret)
    print(f"secp256k1.ecdsa_sign: {time.ticks_diff(time.ticks_ms(), t1)}ms")
 
    # serialization
    der = secp256k1.ecdsa_signature_serialize_der(sig)

    print("Signature:", hexlify(der).decode())

    # verification
    if secp256k1.ecdsa_verify(sig, msg, pubkey):
        print("Signature is valid")
    else:
        print("Invalid signature")


if __name__ == '__main__':
    import machine
    machine.freq(int(240*1e6))
    print(f"Current freq: {int(machine.freq() / 1e6)}MHz")
    pin = machine.Pin(13, machine.Pin.OUT)
    pin.value(1)

    start = time.ticks_ms()
    secp256k1_example()
    end = time.ticks_ms()
    print(f"{time.ticks_diff(end, start)}ms")
    pin.value(0)
