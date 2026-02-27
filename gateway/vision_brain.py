import random
import time

class VisionBrain:
    """
    Vision AI Engine for Agri-Brain.
    Processes crop images to detect diseases (e.g., Rust, Blight, Pests).
    Powered by AMD Ryzen for local high-speed inference.
    """
    def __init__(self):
        self.supported_crops = ["Tomato", "Pepper", "Pomegranate", "Chilli"]
        self.detection_threshold = 0.75
        
    def analyze_leaf(self, image_metadata):
        """
        Simulates local image processing on AMD Gateway.
        In production, this would use OpenCV + TensorFlow/PyTorch.
        """
        print(f"[Vision AI] Processing image from camera: {image_metadata.get('camera_id')}...")
        time.sleep(1.5) # Simulate inference time
        
        # Simulated Detection Results
        diseases = ["Healthy", "Early Blight", "Late Blight", "Rust", "Leaf Miner"]
        result_disease = random.choice(diseases)
        confidence = random.uniform(0.6, 0.99)
        
        status = "HEALTHY" if result_disease == "Healthy" else "WARNING"
        if confidence < self.detection_threshold and status == "WARNING":
            status = "UNCERTAIN"
            
        return {
            "crop": image_metadata.get("crop", "Unknown"),
            "diagnosis": result_disease,
            "confidence": round(confidence, 2),
            "status": status,
            "recommendation": self._get_recommendation(result_disease),
            "timestamp": time.time()
        }
    
    def _get_recommendation(self, disease):
        recommendations = {
            "Healthy": "No action needed. Continue current schedule.",
            "Early Blight": "Remove infected leaves. Apply copper-based fungicide.",
            "Late Blight": "Critical! Isolate affected area. Apply defensive spray immediately.",
            "Rust": "Improve airflow. Apply sulfur-based organic spray.",
            "Leaf Miner": "Introduce parasitic wasps or use neem oil."
        }
        return recommendations.get(disease, "Consult Agri-Brain Gemini Advisor.")

if __name__ == "__main__":
    vision = VisionBrain()
    sample_img = {"camera_id": "Field_South_01", "crop": "Tomato"}
    print(vision.analyze_leaf(sample_img))
