import keypass as kp

content = {
    "username": "keypass",
    "password": "wenhom.wang@gmail.com"
}
# kp.save(content, "tests/account_nsys.key", from_system=False)

account = kp.load("tests/account_nsys.key", from_system=False)
assert account["username"] == content["username"]
assert account["password"] == content["password"]
