import re

class NLPBrain:
    """
    Local NLP Engine for Agri-Brain.
    Parses natural language commands into structured farm data.
    """
    def __init__(self):
        # Patterns for extraction
        self.actions = ["added", "removed", "sprayed", "applied", "purchased", "used", "irrigate", "water"]
        self.materials = ["potash", "polash", "urea", "npm", "water", "fertilizer", "pesticide", "seeds"]
        
    def process_text(self, text):
        text = text.lower()
        
        extracted_action = "GENERAL"
        extracted_material = "UNKNOWN"
        extracted_quantity = "N/A"
        extracted_grid = None
        extracted_duration = None
        
        # Extract Action
        for action in self.actions:
            if action in text:
                extracted_action = action.upper()
                break
                
        # Extract Material
        for material in self.materials:
            if material in text:
                extracted_material = material.upper()
                break
                
        # Extract Quantity (e.g., 5kg, 10L)
        qty_match = re.search(r'(\d+\s*(kg|l|liters|bags|grams|g|units))', text)
        if qty_match:
            extracted_quantity = qty_match.group(0).upper()

        # Extract Grid ID (e.g., grid 1, zone 2)
        grid_match = re.search(r'(grid|zone|block)\s*(\d+)', text)
        if grid_match:
            extracted_grid = int(grid_match.group(2))

        # Extract Duration (e.g., 30 minutes, 1 hour)
        dur_match = re.search(r'(\d+)\s*(min|minute|minutes|hour|hours|h)', text)
        if dur_match:
            val = int(dur_match.group(1))
            unit = dur_match.group(2)
            if 'hour' in unit or 'h' == unit:
                extracted_duration = val * 60
            else:
                extracted_duration = val
            
        return {
            "action": extracted_action,
            "material": extracted_material,
            "quantity": extracted_quantity,
            "grid": extracted_grid,
            "duration": extracted_duration,
            "raw": text
        }

if __name__ == "__main__":
    nlp = NLPBrain()
    print(nlp.process_text("Added 10kg of Potash to the south grid"))
    print(nlp.process_text("Sprayed 2 liters of pesticide"))
    print(nlp.process_text("Used 5 bags of Urea"))
