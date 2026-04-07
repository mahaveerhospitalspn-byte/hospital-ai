import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import random

app = Flask(__name__)
CORS(app)

SUPABASE_URL = "https://cdbavugbuicjjgqeehyb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNkYmF2dWdidWljampncWVlaHliIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MjQzMTQsImV4cCI6MjA4OTQwMDMxNH0.OQC_Qq-DoygyX__6b9s3NSP8WED_V1kpxze1EkXTl-AY"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@app.route("/appointment", methods=["POST"])
def appointment():
    name       = request.form.get("name")
    mobile     = request.form.get("mobile")
    date       = request.form.get("date")
    time_slot  = request.form.get("time")
    department = request.form.get("department")
    uhid       = random.randint(100000, 999999)

    try:
        response = supabase.table("opd_live").insert({
            "name": name, "uhid": uhid, "mobile": mobile,
            "date": date, "time": time_slot,
            "department": department, "source": "ONLINE"
        }).execute()
        return jsonify({"status": "success", "data": str(response)})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/slots", methods=["GET"])
def get_slots():
    date = request.args.get("date")
    all_slots = [
        "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM", "12:00 PM",
        "06:00 PM", "07:30 PM", "08:00 PM", "08:30 PM"
    ]
    slot_limit = 5
    available_slots = []
    for slot in all_slots:
        result = supabase.table("opd_live").select("*").eq("date", date).eq("time", slot).execute()
        available_slots.append({"time": slot, "available": len(result.data) < slot_limit})
    return jsonify(available_slots)


@app.route("/test")
def test():
    return "API WORKING"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
