from libs.crypto.aes256 import AESCipher


def test_encrypt():
    expected_key = AESCipher('salt_key').key
    assert AESCipher('salt_key').key == expected_key
    assert AESCipher('salt_key').key == expected_key
    assert AESCipher('salt_key').key == expected_key

    plaintext = 'plaintext'
    cipher_text = AESCipher('salt_key').encrypt(plaintext)
    assert AESCipher('salt_key').decrypt(cipher_text) == plaintext
