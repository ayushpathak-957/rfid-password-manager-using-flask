import random
import os
from drive_sync import sync_password_file

PASSWORD_FILE = "password.txt"


def generate_password(length, types):
    password = ""

    while len(password) < length:
        t = random.choice(types)
        if t == "lower":
            password += chr(random.randint(97, 122))
        elif t == "upper":
            password += chr(random.randint(65, 90))
        elif t == "number":
            password += str(random.randint(0, 9))
        elif t == "special":
            password += random.choice("!@#$%*")

    return password


def read_passwords():
    data = []
    if not os.path.exists(PASSWORD_FILE):
        return data

    with open(PASSWORD_FILE) as f:
        for line in f:
            if ":" in line:
                k, v = line.strip().split(" : ")
                data.append((k, v))
    return data


def save_password(label, password):
    with open(PASSWORD_FILE, "a") as f:
        f.write(f"{label} : {password}\n")
        f.flush()
        os.fsync(f.fileno())

    sync_password_file()


def update_password(index, new_password):
    data = read_passwords()
    key = data[index][0]
    data[index] = (key, new_password)

    with open(PASSWORD_FILE, "w") as f:
        for k, v in data:
            f.write(f"{k} : {v}\n")

    sync_password_file()
