INSERT INTO users (username, hashed_password, email)
VALUES (
    'test_user',
    pgp_sym_encrypt('securepassword', 'encryption_key'),
    'test@example.com'
);

SELECT username, hashed_password FROM users WHERE username = 'test_user';

SELECT username, pgp_sym_decrypt(hashed_password::bytea, 'encryption_key')
FROM users
WHERE username = 'test_user';
