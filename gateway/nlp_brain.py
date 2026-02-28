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

        # Extract Multiple Grids and Durations (e.g., region 1 for 1 min and region 2 for 2 hours)
        extracted_grids = []
        grid_pattern = r'(grid|zone|block|region)\s*(\d+)(?:\s+(?:for\s+)?(\d+)\s*(min|minute|minutes|hour|hours|h))?'
        for match in re.finditer(grid_pattern, text):
            g_id = int(match.group(2))
            dur_val = match.group(3)
            dur_unit = match.group(4)
            dur = None
            if dur_val and dur_unit:
                val = int(dur_val)
                if 'hour' in dur_unit or 'h' == dur_unit:
                    dur = val * 60
                else:
                    dur = val
            extracted_grids.append({"grid": g_id, "duration": dur})

        # Backward compatibility for single duration somewhere else in text
        dur_match = re.search(r'(\d+)\s*(min|minute|minutes|hour|hours|h)', text)
        if dur_match:
            val = int(dur_match.group(1))
            unit = dur_match.group(2)
            if 'hour' in unit or 'h' == unit:
                global_dur = val * 60
            else:
                global_dur = val
            for g in extracted_grids:
                if g["duration"] is None:
                    g["duration"] = global_dur

        if extracted_grids:
            extracted_grid = extracted_grids[0]["grid"]
            extracted_duration = extracted_grids[0]["duration"]
            
        return {
            "action": extracted_action,
            "material": extracted_material,
            "quantity": extracted_quantity,
            "grid": extracted_grid,
            "duration": extracted_duration,
            "grids": extracted_grids,
            "raw": text
        }

if __name__ == "__main__":
    nlp = NLPBrain()
    print(nlp.process_text("Added 10kg of Potash to the south grid"))
    print(nlp.process_text("Sprayed 2 liters of pesticide"))
    print(nlp.process_text("Used 5 bags of Urea"))
