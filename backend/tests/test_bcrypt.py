"""
为何单独为加密算法编写测试？因为加密算法的测试需要确保其正确性，并且需要确保加密后的数据能够正确地被解密。
密码本不需要存储在代码库中，因此测试代码需要单独处理密码的哈希和验证。
"""



import bcrypt

def hash_password(password: str) -> str:
    """使用原生 bcrypt 哈希密码"""
    # 确保密码不超过 72 字节
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # 生成 salt 并哈希
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    return bcrypt.checkpw(password_bytes, hashed.encode('utf-8'))

def test_hash_password():
    password = "secure_password"
    hashed = hash_password(password)
    assert verify_password(password, hashed)
    print("Bcrypt test passed!")

if __name__ == "__main__":
    test_hash_password()