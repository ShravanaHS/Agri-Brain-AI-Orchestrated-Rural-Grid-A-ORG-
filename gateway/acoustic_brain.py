import random
import time

class AcousticBrain:
    """
    Acoustic AI Brain for Agri-Brain.
    Detects motor health anomalies like cavitation and bearing wear using frequency analysis simulation.
    """
    
    def __init__(self):
        self.health_history = []
        self.threshold_emergency = 40.0 # Emergency shutdown threshold
        self.threshold_warning = 70.0   # Warning threshold
        
    def analyze_frequencies(self, peak_freq, rms_amplitude, vibrations, pressure=45.0):
        """
        Simulates frequency analysis of a pump motor.
        peak_freq: Frequency in Hz (Normal range ~50-60Hz)
        rms_amplitude: Sound level (Higher can mean cavitation)
        vibrations: Vibration index (Higher can mean bearing wear)
        pressure: Pipe pressure in PSI (Low pressure = Run Dry / Pipe Leak)
        """
        health_score = 100.0
        anomalies = []
        
        # --- 1. Pressure Logic (Direct & Reliable) ---
        if pressure < 15.0:
            health_score -= 80 # Massive penalty for total pressure loss
            anomalies.append("CRITICAL_PRESSURE_LOSS")
        elif pressure < 30.0:
            health_score -= 30
            anomalies.append("LOW_PRESSURE_WARNING")

        # --- 2. Acoustic AI Logic (Advanced Maintenance) ---
        # Cavitation Detection (High frequency + High Amplitude)
        if peak_freq > 80:
            penalty = (peak_freq - 80) * 1.5
            health_score -= penalty
            if penalty > 20:
                anomalies.append("CAVITATION_DETECTED")
                
        # Dry Run Detection (Low Load Signature - Acoustic fallback)
        if rms_amplitude < 0.1:
            health_score -= 30
            anomalies.append("DRY_RUN_ACOUSTIC_SIGNATURE")
            
        # Bearing Wear (High Vibrations)
        if vibrations > 5.0:
            penalty = (vibrations - 5.0) * 10
            health_score -= penalty
            if penalty > 20:
                anomalies.append("BEARING_WEAR_DETECTED")
                
        # Ensure health score is within 0-100
        health_score = max(0.0, min(100.0, health_score))
        
        result = {
            "health_score": round(health_score, 2),
            "anomalies": anomalies,
            "status": "HEALTHY" if health_score > self.threshold_warning else "WARNING" if health_score > self.threshold_emergency else "CRITICAL",
            "timestamp": time.time(),
            "telemetry": {
                "pressure": pressure,
                "freq": peak_freq,
                "vib": vibrations
            }
        }
        
        self.health_history.append(result)
        return result

    def should_shutdown(self, result):
        """Returns True if the motor must be shut down immediately."""
        # Shutdown if status is CRITICAL or if there is a CRITICAL_PRESSURE_LOSS
        return result["status"] == "CRITICAL" or "CRITICAL_PRESSURE_LOSS" in result["anomalies"]

if __name__ == "__main__":
    # Quick Test
    brain = AcousticBrain()
    print("Normal Run:", brain.analyze_frequencies(60, 0.5, 1.2, 45.0))
    print("Pressure Loss:", brain.analyze_frequencies(60, 0.5, 1.2, 10.0))
    print("Cavitation:", brain.analyze_frequencies(120, 0.9, 2.0, 40.0))
    print("Bearing Failure:", brain.analyze_frequencies(60, 0.5, 9.5, 45.0))
