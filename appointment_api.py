
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import random

app = Flask(__name__)
CORS(app)

# ✅ Supabase config
url = "https://cdbavugbuicjjgqeehyb.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkYmF2dWdidWljampncWVlaHliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MjQzMTQsImV4cCI6MjA4OTQwMDMxNH0.OQC_Qq-DoygyX__6b9s3NSP8WED_V1kpxze1EkXTl-AY"
supabase = create_client(url, key)


# ================= APPOINTMENT =================
@app.route("/appointment", methods=["POST"])
def appointment():

    name = request.form.get("name")
    mobile = request.form.get("mobile")
    date = request.form.get("date")
    time_slot = request.form.get("time")
    department = request.form.get("department")

    import random
    uhid = random.randint(100000,999999)

    try:
        response = supabase.table("opd_live").insert({
            "name": name,
            "uhid": uhid,
            "mobile": mobile,
            "date": date,
            "time": time_slot,
            "department": department,
            "source": "ONLINE"
        }).execute()

        print("✅ INSERT RESPONSE:", response)

        return jsonify({"status": "success", "data": str(response)})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"status": "error", "message": str(e)})


@app.route("/test")
def test():
    try:
        response = supabase.table("opd_live").insert({
            "name": "TEST",
            "uhid": 111111,
            "mobile": "9999999999",
            "date": "2026-03-18",
            "time": "10:00 AM",
            "department": "Test",
            "source": "ONLINE"
        }).execute()

        return str(response)

    except Exception as e:
        return str(e)
# ================= SLOTS =================
@app.route("/slots", methods=["GET"])
def get_slots():

    date = request.args.get("date")

    all_slots = [
        "10:00 AM","10:30 AM",
        "11:00 AM","11:30 AM","12:00 PM",
        "06:00 PM","07:30 PM","08:00 PM","08:30 PM"
    ]

    slot_limit = 5
    available_slots = []

    for slot in all_slots:

        result = supabase.table("opd_live") \
            .select("*") \
            .eq("date", date) \
            .eq("time", slot) \
            .execute()

        count = len(result.data)

        if count < slot_limit:
            available_slots.append({"time": slot, "available": True})
        else:
            available_slots.append({"time": slot, "available": False})

    return jsonify(available_slots)


@app.route("/test")
def test():
    return "API WORKING"

# ================= RUN =================
if __name__ == "__main__":

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import random

app = Flask(__name__)
CORS(app)

# ✅ Supabase config
url = "https://cdbavugbuicjjgqeehyb.supabase.co"
key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkYmF2dWdidWljampncWVlaHliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MjQzMTQsImV4cCI6MjA4OTQwMDMxNH0.OQC_Qq-DoygyX__6b9s3NSP8WED_V1kpxze1EkXTl-AY"
supabase = create_client(url, key)


# ================= APPOINTMENT =================
@app.route("/appointment", methods=["POST"])
def appointment():

    name = request.form.get("name")
    mobile = request.form.get("mobile")
    date = request.form.get("date")
    time_slot = request.form.get("time")
    department = request.form.get("department")

    import random
    uhid = random.randint(100000,999999)

    try:
        response = supabase.table("opd_live").insert({
            "name": name,
            "uhid": uhid,
            "mobile": mobile,
            "date": date,
            "time": time_slot,
            "department": department,
            "source": "ONLINE"
        }).execute()

        print("✅ INSERT RESPONSE:", response)

        return jsonify({"status": "success", "data": str(response)})

    except Exception as e:
        print("❌ ERROR:", str(e))
        return jsonify({"status": "error", "message": str(e)})


@app.route("/test")
def test():
    try:
        response = supabase.table("opd_live").insert({
            "name": "TEST",
            "uhid": 111111,
            "mobile": "9999999999",
            "date": "2026-03-18",
            "time": "10:00 AM",
            "department": "Test",
            "source": "ONLINE"
        }).execute()

        return str(response)

    except Exception as e:
        return str(e)
# ================= SLOTS =================
@app.route("/slots", methods=["GET"])
def get_slots():

    date = request.args.get("date")

    all_slots = [
        "10:00 AM","10:30 AM",
        "11:00 AM","11:30 AM","12:00 PM",
        "06:00 PM","07:30 PM","08:00 PM","08:30 PM"
    ]

    slot_limit = 5
    available_slots = []

    for slot in all_slots:

        result = supabase.table("opd_live") \
            .select("*") \
            .eq("date", date) \
            .eq("time", slot) \
            .execute()

        count = len(result.data)

        if count < slot_limit:
            available_slots.append({"time": slot, "available": True})
        else:
            available_slots.append({"time": slot, "available": False})

    return jsonify(available_slots)


@app.route("/test")
def test():
    return "API WORKING"

# ================= RUN =================
if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))