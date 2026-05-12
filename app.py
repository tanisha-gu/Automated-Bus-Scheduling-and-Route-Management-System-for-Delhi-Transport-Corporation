from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import json, uuid, random
from datetime import datetime, timedelta
from scheduler import LinkedDutyScheduler, UnlinkedDutyScheduler
from route_manager import RouteManager

app = Flask(__name__)
CORS(app)

# In-memory data stores
buses_db = {}
crews_db = {}
duties_db = {}
routes_db = {}
scheduler_linked = LinkedDutyScheduler()
scheduler_unlinked = UnlinkedDutyScheduler()
route_manager = RouteManager()

def seed_data():
    """Seed initial demo data"""
    # Buses
    depots = ["Rohini Depot", "Dwarka Depot", "Okhla Depot", "Sarojini Depot", "Kashmere Gate Depot"]
    bus_types = ["Standard", "Low-Floor AC", "Electric", "Mini"]
    for i in range(1, 31):
        bid = f"DTC-{1000+i}"
        buses_db[bid] = {
            "id": bid, "number": bid,
            "type": random.choice(bus_types),
            "depot": random.choice(depots),
            "status": random.choice(["Available", "Available", "Available", "In Service", "Maintenance"]),
            "capacity": random.choice([45, 50, 55, 60]),
            "fuel_type": random.choice(["Diesel", "CNG", "Electric"]),
        }

    # Crew
    first = ["Rajesh","Amit","Suresh","Vinod","Mohan","Pradeep","Sanjay","Deepak","Ravi","Arun",
             "Manoj","Vijay","Sandeep","Rakesh","Naveen","Pankaj","Dinesh","Ramesh","Ajay","Vikas"]
    last = ["Kumar","Singh","Sharma","Gupta","Yadav","Verma","Mishra","Jha","Tiwari","Chauhan"]
    for i in range(1, 41):
        cid = f"CREW-{200+i}"
        crews_db[cid] = {
            "id": cid,
            "name": f"{random.choice(first)} {random.choice(last)}",
            "role": random.choice(["Driver", "Driver", "Driver", "Conductor"]),
            "depot": random.choice(depots),
            "shift": random.choice(["Morning", "Afternoon", "Night"]),
            "status": random.choice(["Available", "Available", "On Duty", "On Rest"]),
            "license": f"DL{random.randint(10000,99999)}",
            "experience_years": random.randint(1, 20),
        }

    # Routes
    route_data = [
        {"id":"R-001","name":"Rohini Sec-7 → ISBT Kashmere Gate","color":"#E74C3C",
         "stops":["Rohini Sec-7","Rohini Sec-5","Pitampura","Netaji Subhash Place","Ashok Vihar","Model Town","GTB Nagar","Vishwavidyalaya","Civil Lines","ISBT Kashmere Gate"],
         "distance_km":28,"frequency_min":8,"peak_buses":6,"daily_trips":85},
        {"id":"R-002","name":"Dwarka Sec-21 → Connaught Place","color":"#2ECC71",
         "stops":["Dwarka Sec-21","Dwarka Sec-14","Dwarka Mor","Uttam Nagar","Tilak Nagar","Subhash Nagar","Rajouri Garden","Mayapuri","Dhaula Kuan","Connaught Place"],
         "distance_km":35,"frequency_min":10,"peak_buses":7,"daily_trips":72},
        {"id":"R-003","name":"Badarpur → Kashmere Gate","color":"#3498DB",
         "stops":["Badarpur","Sarita Vihar","Jasola","Okhla","Kalkaji","Nehru Place","Lajpat Nagar","INA","Dhaula Kuan","Connaught Place","Minto Road","Kashmere Gate"],
         "distance_km":42,"frequency_min":12,"peak_buses":8,"daily_trips":65},
        {"id":"R-004","name":"Noida City Center → Inderlok","color":"#9B59B6",
         "stops":["Noida City Center","Akshardham","Preet Vihar","Anand Vihar","Dilshad Garden","Jhilmil","Shastri Park","Kashmere Gate","Inderlok"],
         "distance_km":30,"frequency_min":15,"peak_buses":5,"daily_trips":58},
        {"id":"R-005","name":"Gurgaon Terminal → AIIMS","color":"#F39C12",
         "stops":["Gurgaon Terminal","Iffco Chowk","Cyber City","MG Road","Sikanderpur","Dhaula Kuan","RML Hospital","Connaught Place","AIIMS"],
         "distance_km":25,"frequency_min":10,"peak_buses":5,"daily_trips":70},
    ]
    for r in route_data:
        routes_db[r["id"]] = r

seed_data()

# ─── BUS ENDPOINTS ───────────────────────────────────────────────
@app.route("/api/buses", methods=["GET"])
def get_buses():
    status = request.args.get("status")
    buses = list(buses_db.values())
    if status:
        buses = [b for b in buses if b["status"] == status]
    return jsonify({"buses": buses, "total": len(buses)})

@app.route("/api/buses/<bus_id>", methods=["GET"])
def get_bus(bus_id):
    bus = buses_db.get(bus_id)
    if not bus:
        return jsonify({"error": "Bus not found"}), 404
    return jsonify(bus)

@app.route("/api/buses/<bus_id>", methods=["PUT"])
def update_bus(bus_id):
    bus = buses_db.get(bus_id)
    if not bus:
        return jsonify({"error": "Bus not found"}), 404
    data = request.get_json()
    bus.update(data)
    return jsonify(bus)

# ─── CREW ENDPOINTS ───────────────────────────────────────────────
@app.route("/api/crews", methods=["GET"])
def get_crews():
    status = request.args.get("status")
    role = request.args.get("role")
    crews = list(crews_db.values())
    if status:
        crews = [c for c in crews if c["status"] == status]
    if role:
        crews = [c for c in crews if c["role"] == role]
    return jsonify({"crews": crews, "total": len(crews)})

@app.route("/api/crews/<crew_id>", methods=["GET"])
def get_crew(crew_id):
    crew = crews_db.get(crew_id)
    if not crew:
        return jsonify({"error": "Crew not found"}), 404
    return jsonify(crew)

# ─── SCHEDULING ENDPOINTS ─────────────────────────────────────────
@app.route("/api/schedule/linked", methods=["POST"])
def create_linked_schedule():
    data = request.get_json()
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    shift = data.get("shift", "Morning")
    available_buses = [b for b in buses_db.values() if b["status"] in ["Available", "In Service"]]
    available_crews = [c for c in crews_db.values()
                       if c["status"] in ["Available"] and c["role"] == "Driver"]
    result = scheduler_linked.generate_schedule(
        available_buses[:15], available_crews[:15], date, shift, routes_db
    )
    for duty in result["duties"]:
        did = f"LD-{uuid.uuid4().hex[:6].upper()}"
        duty["id"] = did
        duties_db[did] = duty
    return jsonify(result)

@app.route("/api/schedule/unlinked", methods=["POST"])
def create_unlinked_schedule():
    data = request.get_json()
    date = data.get("date", datetime.now().strftime("%Y-%m-%d"))
    available_buses = [b for b in buses_db.values() if b["status"] in ["Available", "In Service"]]
    available_crews = [c for c in crews_db.values() if c["status"] in ["Available"]]
    result = scheduler_unlinked.generate_schedule(
        available_buses[:12], available_crews[:20], date, routes_db
    )
    for duty in result["duties"]:
        did = f"UL-{uuid.uuid4().hex[:6].upper()}"
        duty["id"] = did
        duties_db[did] = duty
    return jsonify(result)

@app.route("/api/duties", methods=["GET"])
def get_duties():
    duty_type = request.args.get("type")
    duties = list(duties_db.values())
    if duty_type:
        duties = [d for d in duties if d.get("type") == duty_type]
    return jsonify({"duties": duties, "total": len(duties)})

@app.route("/api/duties/<duty_id>", methods=["GET"])
def get_duty(duty_id):
    duty = duties_db.get(duty_id)
    if not duty:
        return jsonify({"error": "Duty not found"}), 404
    return jsonify(duty)

# ─── ROUTE ENDPOINTS ─────────────────────────────────────────────
@app.route("/api/routes", methods=["GET"])
def get_routes():
    return jsonify({"routes": list(routes_db.values()), "total": len(routes_db)})

@app.route("/api/routes/<route_id>", methods=["GET"])
def get_route(route_id):
    route = routes_db.get(route_id)
    if not route:
        return jsonify({"error": "Route not found"}), 404
    return jsonify(route)

@app.route("/api/routes", methods=["POST"])
def create_route():
    data = request.get_json()
    rid = f"R-{len(routes_db)+1:03d}"
    new_route = {
        "id": rid,
        "name": data.get("name", f"New Route {rid}"),
        "color": data.get("color", "#1ABC9C"),
        "stops": data.get("stops", []),
        "distance_km": data.get("distance_km", 0),
        "frequency_min": data.get("frequency_min", 15),
        "peak_buses": data.get("peak_buses", 3),
        "daily_trips": data.get("daily_trips", 40),
        "is_new": True,
    }
    overlaps = route_manager.find_overlaps(new_route, list(routes_db.values()))
    new_route["overlaps"] = overlaps
    routes_db[rid] = new_route
    return jsonify({"route": new_route, "overlaps": overlaps}), 201

@app.route("/api/routes/overlap", methods=["POST"])
def check_overlap():
    data = request.get_json()
    candidate = data.get("route", {})
    overlaps = route_manager.find_overlaps(candidate, list(routes_db.values()))
    return jsonify({"overlaps": overlaps})

@app.route("/api/routes/<route_id>", methods=["DELETE"])
def delete_route(route_id):
    if route_id not in routes_db:
        return jsonify({"error": "Route not found"}), 404
    del routes_db[route_id]
    return jsonify({"message": "Route deleted"})

# ─── DASHBOARD STATS ─────────────────────────────────────────────
@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    buses = list(buses_db.values())
    crews = list(crews_db.values())
    duties = list(duties_db.values())
    routes = list(routes_db.values())
    return jsonify({
        "buses": {
            "total": len(buses),
            "available": sum(1 for b in buses if b["status"] == "Available"),
            "in_service": sum(1 for b in buses if b["status"] == "In Service"),
            "maintenance": sum(1 for b in buses if b["status"] == "Maintenance"),
        },
        "crews": {
            "total": len(crews),
            "available": sum(1 for c in crews if c["status"] == "Available"),
            "on_duty": sum(1 for c in crews if c["status"] == "On Duty"),
            "on_rest": sum(1 for c in crews if c["status"] == "On Rest"),
        },
        "duties": {
            "total": len(duties),
            "linked": sum(1 for d in duties if d.get("type") == "linked"),
            "unlinked": sum(1 for d in duties if d.get("type") == "unlinked"),
        },
        "routes": {
            "total": len(routes),
            "total_distance": sum(r.get("distance_km", 0) for r in routes),
            "total_daily_trips": sum(r.get("daily_trips", 0) for r in routes),
        }
    })

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
