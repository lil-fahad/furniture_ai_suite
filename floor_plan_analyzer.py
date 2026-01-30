"""Floor plan analysis module for interior design.

This module provides functionality to analyze floor plans, detect rooms,
and provide furniture placement recommendations.
"""
import cv2
import numpy as np
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Tuple, Optional, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FloorPlanAnalyzer:
    """Analyze floor plans and extract room information.
    
    This class processes floor plan images to detect rooms, walls, doors,
    and other architectural elements.
    """
    
    def __init__(self, min_room_area: int = 5000):
        """Initialize the floor plan analyzer.
        
        Args:
            min_room_area: Minimum area in pixels to consider as a room
        """
        self.min_room_area = min_room_area
        logger.info(f"FloorPlanAnalyzer initialized with min_room_area={min_room_area}")
    
    def load_image(self, image_path: str) -> np.ndarray:
        """Load a floor plan image.
        
        Args:
            image_path: Path to the floor plan image
            
        Returns:
            Loaded image as numpy array
            
        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image cannot be loaded
        """
        if not Path(image_path).exists():
            raise FileNotFoundError(f"Floor plan not found: {image_path}")
        
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        logger.info(f"Loaded floor plan: {image_path}, shape: {img.shape}")
        return img
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess floor plan image for analysis.
        
        Args:
            image: Input floor plan image
            
        Returns:
            Preprocessed binary image
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Apply adaptive thresholding for better wall detection
        binary = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11, 2
        )
        
        logger.debug("Floor plan preprocessing completed")
        return binary
    
    def detect_walls(self, binary_image: np.ndarray) -> List[np.ndarray]:
        """Detect walls in the floor plan.
        
        Args:
            binary_image: Preprocessed binary image
            
        Returns:
            List of wall contours
        """
        # Use morphological operations to enhance walls
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        morph = cv2.morphologyEx(binary_image, cv2.MORPH_CLOSE, kernel)
        
        # Find contours (walls)
        contours, _ = cv2.findContours(
            morph,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        logger.info(f"Detected {len(contours)} wall contours")
        return contours
    
    def detect_rooms(self, binary_image: np.ndarray) -> List[Dict[str, Any]]:
        """Detect individual rooms in the floor plan.
        
        Args:
            binary_image: Preprocessed binary image
            
        Returns:
            List of room dictionaries with properties
        """
        # Invert for room detection
        inverted = cv2.bitwise_not(binary_image)
        
        # Find connected components (rooms)
        contours, _ = cv2.findContours(
            inverted,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )
        
        rooms = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            
            # Filter small areas
            if area < self.min_room_area:
                continue
            
            # Get bounding box
            x, y, w, h = cv2.boundingRect(contour)
            
            # Calculate centroid
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = x + w // 2, y + h // 2
            
            # Estimate room type based on dimensions
            aspect_ratio = max(w, h) / min(w, h)
            room_type = self._estimate_room_type(area, aspect_ratio)
            
            room = {
                "id": i,
                "type": room_type,
                "area_pixels": int(area),
                "bounding_box": {"x": int(x), "y": int(y), "width": int(w), "height": int(h)},
                "centroid": {"x": int(cx), "y": int(cy)},
                "aspect_ratio": float(aspect_ratio),
                "contour": contour
            }
            rooms.append(room)
        
        logger.info(f"Detected {len(rooms)} rooms")
        return rooms
    
    def _estimate_room_type(self, area: float, aspect_ratio: float) -> str:
        """Estimate room type based on dimensions.
        
        Args:
            area: Room area in pixels
            aspect_ratio: Width to height ratio
            
        Returns:
            Estimated room type
        """
        # Simple heuristics - can be improved with ML
        if area > 100000:
            if aspect_ratio > 2.0:
                return "living_room"
            else:
                return "master_bedroom"
        elif area > 50000:
            if aspect_ratio > 1.5:
                return "dining_room"
            else:
                return "bedroom"
        elif area > 20000:
            if aspect_ratio < 1.2:
                return "bathroom"
            else:
                return "kitchen"
        else:
            return "storage_or_hallway"
    
    def detect_doors_windows(self, binary_image: np.ndarray) -> Dict[str, List[Dict[str, int]]]:
        """Detect doors and windows in the floor plan.
        
        Args:
            binary_image: Preprocessed binary image
            
        Returns:
            Dictionary with 'doors' and 'windows' lists
        """
        # Use Hough Line Transform to detect lines
        edges = cv2.Canny(binary_image, 50, 150)
        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi/180,
            threshold=50,
            minLineLength=20,
            maxLineGap=10
        )
        
        doors = []
        windows = []
        
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                length = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
                
                # Simple heuristic: shorter lines might be doors/windows
                if 30 < length < 100:
                    element = {
                        "x1": int(x1), "y1": int(y1),
                        "x2": int(x2), "y2": int(y2),
                        "length": float(length)
                    }
                    # More sophisticated detection would classify these
                    if length < 60:
                        windows.append(element)
                    else:
                        doors.append(element)
        
        logger.info(f"Detected {len(doors)} doors and {len(windows)} windows")
        return {"doors": doors, "windows": windows}
    
    def analyze_floor_plan(
        self,
        image_path: str,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Complete floor plan analysis pipeline.
        
        Args:
            image_path: Path to floor plan image
            output_path: Optional path to save annotated image
            
        Returns:
            Dictionary with complete analysis results
        """
        logger.info(f"Starting floor plan analysis for {image_path}")
        
        # Load and preprocess
        image = self.load_image(image_path)
        binary = self.preprocess(image)
        
        # Detect elements
        walls = self.detect_walls(binary)
        rooms = self.detect_rooms(binary)
        openings = self.detect_doors_windows(binary)
        
        # Calculate total area
        total_area = sum(room["area_pixels"] for room in rooms)
        
        # Create visualization if output path provided
        if output_path:
            self._visualize_analysis(image, rooms, openings, output_path)
        
        results = {
            "total_rooms": len(rooms),
            "total_area_pixels": int(total_area),
            "rooms": [
                {
                    "id": r["id"],
                    "type": r["type"],
                    "area_pixels": r["area_pixels"],
                    "bounding_box": r["bounding_box"],
                    "centroid": r["centroid"],
                    "aspect_ratio": r["aspect_ratio"]
                }
                for r in rooms
            ],
            "doors": openings["doors"],
            "windows": openings["windows"],
            "wall_count": len(walls)
        }
        
        logger.info("Floor plan analysis completed")
        return results
    
    def _visualize_analysis(
        self,
        image: np.ndarray,
        rooms: List[Dict[str, Any]],
        openings: Dict[str, List[Dict[str, int]]],
        output_path: str
    ) -> None:
        """Create visualization of the analysis.
        
        Args:
            image: Original floor plan image
            rooms: Detected rooms
            openings: Detected doors and windows
            output_path: Path to save visualization
        """
        # Create a copy for annotation
        annotated = image.copy()
        
        # Draw room contours and labels
        for room in rooms:
            # Draw contour
            cv2.drawContours(annotated, [room["contour"]], -1, (0, 255, 0), 2)
            
            # Draw centroid
            cx, cy = room["centroid"]["x"], room["centroid"]["y"]
            cv2.circle(annotated, (cx, cy), 5, (255, 0, 0), -1)
            
            # Add label
            label = f"{room['type']} ({room['id']})"
            cv2.putText(
                annotated, label, (cx - 50, cy - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2
            )
        
        # Draw doors (red)
        for door in openings["doors"]:
            cv2.line(
                annotated,
                (door["x1"], door["y1"]),
                (door["x2"], door["y2"]),
                (0, 0, 255), 3
            )
        
        # Draw windows (blue)
        for window in openings["windows"]:
            cv2.line(
                annotated,
                (window["x1"], window["y1"]),
                (window["x2"], window["y2"]),
                (255, 0, 0), 3
            )
        
        # Save
        cv2.imwrite(output_path, annotated)
        logger.info(f"Visualization saved to {output_path}")
    
    def recommend_furniture(self, room: Dict[str, Any]) -> List[Dict[str, str]]:
        """Recommend furniture for a detected room.
        
        Args:
            room: Room dictionary from detection
            
        Returns:
            List of furniture recommendations
        """
        room_type = room["type"]
        area = room["area_pixels"]
        
        # Furniture recommendations based on room type
        recommendations = {
            "bedroom": [
                {"item": "bed", "priority": "essential"},
                {"item": "nightstand", "priority": "recommended"},
                {"item": "wardrobe", "priority": "essential"},
                {"item": "dresser", "priority": "optional"},
                {"item": "chair", "priority": "optional"}
            ],
            "master_bedroom": [
                {"item": "king_bed", "priority": "essential"},
                {"item": "nightstands_pair", "priority": "essential"},
                {"item": "wardrobe", "priority": "essential"},
                {"item": "dresser", "priority": "recommended"},
                {"item": "seating_area", "priority": "optional"}
            ],
            "living_room": [
                {"item": "sofa", "priority": "essential"},
                {"item": "coffee_table", "priority": "essential"},
                {"item": "tv_stand", "priority": "recommended"},
                {"item": "armchair", "priority": "optional"},
                {"item": "bookshelf", "priority": "optional"}
            ],
            "dining_room": [
                {"item": "dining_table", "priority": "essential"},
                {"item": "dining_chairs", "priority": "essential"},
                {"item": "buffet", "priority": "optional"},
                {"item": "china_cabinet", "priority": "optional"}
            ],
            "kitchen": [
                {"item": "dining_table_small", "priority": "recommended"},
                {"item": "bar_stools", "priority": "optional"},
                {"item": "kitchen_island", "priority": "optional"}
            ],
            "bathroom": [
                {"item": "vanity", "priority": "essential"},
                {"item": "storage_cabinet", "priority": "recommended"},
                {"item": "towel_rack", "priority": "essential"}
            ]
        }
        
        base_recommendations = recommendations.get(
            room_type,
            [{"item": "general_storage", "priority": "recommended"}]
        )
        
        # Adjust based on room size
        if area < 30000:
            # Small room - filter to essentials only
            return [r for r in base_recommendations if r["priority"] == "essential"]
        elif area < 60000:
            # Medium room - essentials + recommended
            return [r for r in base_recommendations if r["priority"] in ["essential", "recommended"]]
        else:
            # Large room - all recommendations
            return base_recommendations


def analyze_floor_plan_bytes(
    image_bytes: bytes,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze floor plan from raw bytes.
    
    Args:
        image_bytes: Floor plan image as bytes
        output_path: Optional path to save annotated image
        
    Returns:
        Analysis results dictionary
        
    Raises:
        ValueError: If image cannot be decoded
    """
    # Convert bytes to image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Could not decode image from bytes")
    
    # Save temporarily using cross-platform temp file
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
        temp_path = tmp.name
        cv2.imwrite(temp_path, image)
    
    try:
        # Analyze
        analyzer = FloorPlanAnalyzer()
        
        # Get preprocessed image for room detection
        binary = analyzer.preprocess(image)
        detected_rooms = analyzer.detect_rooms(binary)
        
        # Run full analysis
        results = analyzer.analyze_floor_plan(temp_path, output_path)
        
        # Add furniture recommendations for each room
        for room in results["rooms"]:
            # Find matching room from detected_rooms
            matching_room = None
            for r in detected_rooms:
                if r["id"] == room["id"]:
                    matching_room = r
                    break
            
            if matching_room:
                room["furniture_recommendations"] = analyzer.recommend_furniture(matching_room)
        
        return results
    
    finally:
        # Clean up temp file
        try:
            Path(temp_path).unlink()
        except Exception:
            pass
