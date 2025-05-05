import bcrypt

hashed = bcrypt.hashpw(b"21072004", bcrypt.gensalt())
print(hashed.decode())  # Вставь результат ниже
