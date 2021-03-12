from hashlib import sha256

# 87e93406a19d11166fd4aff9addf299aad2221cbd45febc596a527b65269b78f = blaa

def Sha256Crack(attempt, hash):
    attemptHashed = sha256(attempt.encode('utf-8')).hexdigest()
    return attemptHashed == hash

if __name__ == '__main__':
    print(Sha256Crack('bl1aa', '87e93406a19d11166fd4aff9addf299aad2221cbd45febc596a527b65269b78f'))