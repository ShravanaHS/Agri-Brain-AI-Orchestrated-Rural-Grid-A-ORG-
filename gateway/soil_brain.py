import time

class SoilBrain:
    """
    Soil Health Mapping Engine.
    Analyzes multi-sensor data (pH, NPK, Moisture) to generate health insights.
    """
    def __init__(self):
        self.ideal_ph_range = (6.0, 7.5)
        
    def analyze_soil(self, grid_id, ph_value, moisture):
        """
        Calculates a soil health score for a specific grid.
        """
        health_score = 100.0
        insights = []
        
        # pH Logic
        if ph_value < self.ideal_ph_range[0]:
            diff = self.ideal_ph_range[0] - ph_value
            health_score -= diff * 15
            insights.append("Soil is too ACIDIC. Add Lime/Calcium carbonate.")
        elif ph_value > self.ideal_ph_range[1]:
            diff = ph_value - self.ideal_ph_range[1]
            health_score -= diff * 15
            insights.append("Soil is too ALKALINE. Add Sulfur or Organic Matter.")
        else:
            insights.append("pH balance is OPTIMAL.")
            
        # Moisture Interaction
        if moisture < 20.0 and ph_value > 7.5:
             insights.append("CAUTION: High Alkalinity + Low Moisture creates salt stress.")
             
        health_score = max(0.0, min(100.0, health_score))
        
        return {
            "grid_id": grid_id,
            "ph": ph_value,
            "moisture": moisture,
            "health_score": round(health_score, 2),
            "insights": insights,
            "status": "OPTIMAL" if health_score > 80 else "NEEDS_ATTENTION" if health_score > 50 else "CRITICAL",
            "timestamp": time.time()
        }

if __name__ == "__main__":
    soil = SoilBrain()
    print(soil.analyze_soil(1, 5.2, 35.0)) # Acidic
    print(soil.analyze_soil(5, 7.2, 45.0)) # Optimal
