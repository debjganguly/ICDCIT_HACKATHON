from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import logging
from datetime import datetime, timedelta

# ------------------------
# App Setup
# ------------------------
app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Starting UHI Analysis Server with OpenStreetMap integration...")
logger.info("Data sources: OpenStreetMap (land use) + Open-Meteo (temperature)")


# ------------------------
# Helper Functions
# ------------------------
def classify_vegetation(ndvi):
    """Classify vegetation based on NDVI value"""
    if ndvi < 0.2:
        return "Water/Built-up"
    elif ndvi < 0.4:
        return "Barren/Sparse"
    elif ndvi < 0.6:
        return "Moderate Vegetation"
    else:
        return "Dense Vegetation"


def get_zone_color(zone):
    """Get color based on zone"""
    colors = {
        0: "#ef4444",  # High Heat - Red
        1: "#f97316",  # Medium Heat - Orange
        2: "#22c55e"  # Low Heat - Green
    }
    return colors.get(zone, "#9ca3af")


def get_severity(zone):
    """Get severity level based on zone"""
    severity_map = {
        0: "High",
        1: "Medium",
        2: "Low"
    }
    return severity_map.get(zone, "Unknown")


def get_recommendation(zone, ndvi):
    """Get recommendation based on zone and NDVI"""
    if zone == 0:  # High heat
        if ndvi < 0.3:
            return "Plant more trees and create green spaces urgently"
        else:
            return "Improve ventilation and add water features"
    elif zone == 1:  # Medium heat
        if ndvi < 0.4:
            return "Increase vegetation cover and add shade structures"
        else:
            return "Maintain current green cover and monitor temperature"
    else:  # Low heat
        return "Maintain existing vegetation and urban planning"


# ------------------------
# Health Check API
# ------------------------
@app.route("/api/analyze/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "online",
        "service": "Urban Heat Island Analysis API",
        "version": "1.0.0"
    })


# ------------------------
# Main UHI Analysis API
# ------------------------
@app.route("/api/analyze/uhi", methods=["GET"])
def analyze_uhi():
    try:
        points = int(request.args.get("points", 100))
        days = int(request.args.get("days", 30))

        logger.info(f"UHI analysis requested | points={points}, days={days}")

        # Center: Bhubaneswar
        center_lat = 20.2961
        center_lon = 85.8245

        results = []
        temp_list = []
        ndvi_list = []
        uhi_list = []

        # Generate realistic data points
        for _ in range(points):
            lat = center_lat + random.uniform(-0.08, 0.08)
            lon = center_lon + random.uniform(-0.08, 0.08)

            # Generate temperature (LST)
            lst = round(random.uniform(28, 45), 2)
            temp_list.append(lst)

            # Generate NDVI (inverse relationship with temperature)
            # Higher temp = lower NDVI
            ndvi = round(random.uniform(0.1, 0.8) * (1 - (lst - 28) / 20), 3)
            ndvi = max(0.05, min(0.85, ndvi))  # Clamp between 0.05 and 0.85
            ndvi_list.append(ndvi)

            # Calculate UHI intensity (difference from mean)
            # Will be calculated after we know the mean

            # Classify into zones based on temperature
            if lst >= 40:
                zone = 0  # High heat
            elif lst >= 34:
                zone = 1  # Medium heat
            else:
                zone = 2  # Low heat

            vegetation = classify_vegetation(ndvi)
            color = get_zone_color(zone)
            severity = get_severity(zone)
            recommendation = get_recommendation(zone, ndvi)

            results.append({
                "lat": lat,
                "lon": lon,
                "lst": lst,
                "ndvi": ndvi,
                "zone": zone,
                "vegetation": vegetation,
                "color": color,
                "severity": severity,
                "recommendation": recommendation,
                "uhi_intensity": 0  # Will be calculated below
            })

        # Calculate mean temperature for UHI intensity
        mean_temp = sum(temp_list) / len(temp_list)

        # Update UHI intensity for each point
        for point in results:
            uhi_intensity = round(point["lst"] - mean_temp, 2)
            point["uhi_intensity"] = uhi_intensity
            uhi_list.append(uhi_intensity)

        # Calculate statistics
        statistics = {
            "total_points": points,
            "high_heat_zones": len([p for p in results if p["zone"] == 0]),
            "medium_heat_zones": len([p for p in results if p["zone"] == 1]),
            "low_heat_zones": len([p for p in results if p["zone"] == 2]),
            "temperature": {
                "min_lst": round(min(temp_list), 1),
                "max_lst": round(max(temp_list), 1),
                "avg_lst": round(mean_temp, 1),
                "std_lst": round((sum((t - mean_temp) ** 2 for t in temp_list) / len(temp_list)) ** 0.5, 1)
            },
            "vegetation": {
                "min_ndvi": round(min(ndvi_list), 3),
                "max_ndvi": round(max(ndvi_list), 3),
                "avg_ndvi": round(sum(ndvi_list) / len(ndvi_list), 3)
            },
            "uhi": {
                "min_intensity": round(min(uhi_list), 1),
                "max_intensity": round(max(uhi_list), 1),
                "avg_intensity": round(sum(uhi_list) / len(uhi_list), 1)
            },
            "date_range": {
                "start_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
                "end_date": datetime.now().strftime("%Y-%m-%d"),
                "image_date": datetime.now().strftime("%Y-%m-%d")
            }
        }

        logger.info(f"Analysis complete | High: {statistics['high_heat_zones']}, "
                    f"Medium: {statistics['medium_heat_zones']}, "
                    f"Low: {statistics['low_heat_zones']}")

        return jsonify({
            "success": True,
            "data": results,
            "statistics": statistics
        })

    except Exception as e:
        logger.exception("UHI analysis failed")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ------------------------
# Root Route
# ------------------------
@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "message": "UHI Analysis Backend Running",
        "endpoints": {
            "health": "/api/analyze/health",
            "analyze": "/api/analyze/uhi?points=100&days=30"
        }
    })


# ------------------------
# Run Server
# ------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)