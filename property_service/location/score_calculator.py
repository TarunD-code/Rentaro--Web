from typing import List, Dict, Any

class ScoreCalculator:
    """
    Implements a normalized convenience score logic independent of the map provider.
    Categories expected: metro, hospital, grocery, office
    """
    
    @staticmethod
    def calculate(pois: List[Dict[str, Any]]) -> Dict[str, Any]:
        score_additions = 0.0
        details = []
        
        # Track best available distances
        best = {
            "metro": float('inf'),
            "hospital": float('inf'),
            "grocery": float('inf'),
            "office": float('inf')
        }
        
        for p in pois:
            cat = p.get("category")
            if cat in best and p["distance"] < best[cat]:
                best[cat] = p["distance"]
                
        # Applying scoring logic from hybrid strategy spec
        if best["metro"] <= 1000:
            score_additions += 3
            details.append({"mode": "Metro", "time": f"< 10 mins", "distance": f"{int(best['metro'])} m"})
        
        if best["hospital"] <= 2000:
            score_additions += 2
            details.append({"mode": "Hospital", "time": "Nearby", "distance": f"{int(best['hospital'])} m"})
            
        if best["grocery"] <= 500:
            score_additions += 1
            details.append({"mode": "Grocery", "time": "Walking", "distance": f"{int(best['grocery'])} m"})
            
        if best["office"] <= 3000:
            score_additions += 2
            details.append({"mode": "Offices", "time": "Commutable", "distance": f"{int(best['office']/1000.0)} km"})

        # Normalization to 1-10 (base score 2 + max 8)
        final_score = 2 + score_additions
        
        # Basic mapping of number to category
        return {
            "score": round(final_score, 1),
            "max": 10.0,
            "details": details,
            "raw_pois": pois
        }
