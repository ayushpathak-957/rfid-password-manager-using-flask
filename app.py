from flask import Flask, render_template, request, redirect
import threading
import time
import serial

from password_core import (
    generate_password,
    save_password,
    read_passwords,
    update_password
)

app = Flask(__name__)

# ---------- RFID STATE ----------
rfid_authenticated = False
rfid_status = "waiting"   # waiting | invalid | valid
VALID_UID = "61 2C 67 22"


# ---------- SERIAL LISTENER ----------
def serial_listener():
    global rfid_authenticated, rfid_status

    ser = serial.Serial("COM9", 115200, timeout=1)
    time.sleep(2)
    print("🔌 Serial listener running")

    while True:
        if ser.in_waiting:
            uid = ser.readline().decode(errors="ignore").strip().upper()
            print("📡 UID:", repr(uid))

            if uid == VALID_UID:
                rfid_authenticated = True
                rfid_status = "valid"
                print("✅ Valid RFID")
            else:
                rfid_authenticated = False
                rfid_status = "invalid"
                print("❌ Invalid RFID")


# ---------- ROUTES ----------
@app.route("/")
def index():
    if rfid_authenticated:
        return redirect("/dashboard")
    return render_template("scan.html", status=rfid_status)


@app.route("/dashboard")
def dashboard():
    if not rfid_authenticated:
        return redirect("/")
    return render_template("dashboard.html")


@app.route("/generate", methods=["GET", "POST"])
def generate():
    if not rfid_authenticated:
        return redirect("/")

    password = None
    success_message = None

    if request.method == "POST":
        length = int(request.form["length"])
        types = request.form.getlist("types")
        password = generate_password(length, types)

    return render_template(
        "generate.html",
        password=password,
        success_message=success_message
    )


@app.route("/save", methods=["POST"])
def save():
    if not rfid_authenticated:
        return redirect("/")

    label = request.form["label"]
    password = request.form["password"]

    save_password(label, password)

    # ⬅️ IMPORTANT: render generate.html again (NO redirect)
    return render_template(
        "generate.html",
        password=password,
        success_message="✅ File updated successfully and uploaded to the cloud."
    )


@app.route("/view")
def view():
    if not rfid_authenticated:
        return redirect("/")

    data = read_passwords()
    return render_template("view.html", data=data)


@app.route("/edit/<int:index>", methods=["GET", "POST"])
def edit(index):
    if not rfid_authenticated:
        return redirect("/")

    if request.method == "POST":
        new_password = request.form["password"]

        # update backend
        update_password(index, new_password)

        # IMPORTANT: force UI to use the NEW value
        item = (read_passwords()[index][0], new_password)

        return render_template(
            "edit.html",
            item=item,
            index=index,
            success_message="✅ Password updated successfully and uploaded to the cloud."
        )

    # GET request
    data = read_passwords()
    return render_template(
        "edit.html",
        item=data[index],
        index=index
    )




@app.route("/exit")
def exit():
    global rfid_authenticated, rfid_status
    rfid_authenticated = False
    rfid_status = "waiting"
    return redirect("/")


# ---------- START ----------
if __name__ == "__main__":
    threading.Thread(target=serial_listener, daemon=True).start()
    app.run(debug=True, use_reloader=False)
