from pathlib import Path
import pymupdf4llm
import fitz
import re
import math
from typing import Optional

from .pdf import get_page_important_object_coordinates, get_split_coordinates

def detect_rotation_needed(page):
    """
    Detect rotation needed based on weighted text directions.
    More coherent version with clear angle->rotation mapping.
    """
    text_dict = page.get_text("dict")
    
    if not text_dict['blocks']:
        return 0
    
    # Collect direction vectors with text length weighting
    direction_weights = []
    for block in text_dict['blocks']:
        if block['type'] == 0:  # Text block
            for line in block['lines']:
                if 'dir' in line:
                    dir_x, dir_y = line['dir']
                    angle = math.degrees(math.atan2(dir_y, dir_x))
                    
                    # Weight by amount of text in this line
                    text_length = sum(len(span.get('text', '')) for span in line['spans'])
                    if text_length > 0:  # Only count lines with actual text
                        direction_weights.append((angle, text_length))
    
    if not direction_weights:
        return 0
    
    # Group angles by what they represent (current text orientation)
    orientation_weights = {
        'horizontal': 0,        # Text is already horizontal (0°)
        'vertical_up': 0,       # Text goes upward (90°) 
        'vertical_down': 0,     # Text goes downward (-90°)
        'upside_down': 0        # Text is upside down (180°)
    }
    
    for angle, weight in direction_weights:
        # Normalize angle to -180 to 180
        normalized = ((angle + 180) % 360) - 180
        
        if -15 <= normalized <= 15:
            orientation_weights['horizontal'] += weight
        elif 75 <= normalized <= 105:
            orientation_weights['vertical_up'] += weight
        elif -105 <= normalized <= -75:
            orientation_weights['vertical_down'] += weight
        elif abs(normalized) >= 165:  # 165 to 180 or -165 to -180
            orientation_weights['upside_down'] += weight
    
    # print(f"Text orientation weights:")
    # for orientation, weight in orientation_weights.items():
    #     print(f"  {orientation}: {weight} characters")
    
    # Find dominant orientation
    dominant_orientation = max(orientation_weights.keys(), 
                             key=lambda k: orientation_weights[k])
    dominant_weight = orientation_weights[dominant_orientation]
    total_weight = sum(orientation_weights.values())
    
    if total_weight == 0:
        return 0
    
    # Only rotate if the dominant orientation is significantly stronger
    # and it's not already horizontal
    dominance_ratio = dominant_weight / total_weight
    # print(f"Dominant orientation: {dominant_orientation} ({dominance_ratio:.2f})")
    
    if dominant_orientation == 'horizontal':
        return 0  # Already good
    elif dominance_ratio > 0.6:  # 60% of text in one non-horizontal orientation
        # Map current text orientation to needed rotation
        rotation_map = {
            'vertical_up': -90,      # Text goes up → rotate -90° to make horizontal
            'vertical_down': 90,     # Text goes down → rotate 90° to make horizontal  
            'upside_down': 180       # Text upside down → rotate 180°
        }
        return rotation_map[dominant_orientation]
    else:
        # print("Mixed orientations - keeping original")
        return 0


def process_split_to_markdown(split_path):
    """
    Process a single PDF split and convert it to markdown,
    removing any trailing newlines.
    """
    doc = fitz.open(split_path)
    page = doc[0]
    rotation_needed = detect_rotation_needed(page)
    if rotation_needed != 0:
        page.set_rotation(rotation_needed)
    split_markdown = pymupdf4llm.to_markdown(
        doc, 
        write_images=False, 
        table_strategy='lines_strict', 
        margins=(0,0,0,0), 
        show_progress=False,
        force_text=True,
    )
    doc.close()
    # Remove the "-----" at the end of the split (if it exists)
    split_markdown = split_markdown.rstrip('-\n')
    # print("--------------------------------")
    # print(split_markdown)
    # print("--------------------------------")
    return split_markdown
    
def create_json_object(accumulated_result: Optional[dict], input_pdf_path: str, text: str) -> dict:
    """
    Process a PDF section and accumulate results across multiple calls.
    
    Args:
        accumulated_result (Optional[dict]): Previous result to accumulate with. None for first call.
        input_pdf_path (str): Path in format "split_sections/{name}_page{number}_{section}.pdf"
        text (str): The text content to be assigned to the appropriate section
        
    Returns:
        dict: Updated accumulated result with the new section
    """
    # Initialize result structure if this is the first call
    if accumulated_result is None:
        accumulated_result = {
            "pdf_with_lines": None,
            "pages": {}  # Using dict for accumulation, will convert to list at the end
        }
    
    # Convert to Path object and get just the filename
    path = Path(input_pdf_path)
    filename = path.name

    # Extract components from the input path using regex
    pattern = r"(.+)_page(\d+)_(header|main|footer)\.pdf"
    match = re.match(pattern, filename)
    
    if not match:
        raise ValueError("Invalid filename format")
    
    name, page_number, section = match.groups()
    page_number = int(page_number)
    # Set the pdf_with_lines path if not already set
    if accumulated_result["pdf_with_lines"] is None:
        accumulated_result["pdf_with_lines"] = f"{name}_final_boundaries.pdf"
    
    # Initialize the page dictionary if it doesn't exist
    if page_number not in accumulated_result["pages"]:
        accumulated_result["pages"][page_number] = {
            "number": page_number,
            "header": None,
            "body": None,
            "footer": None
        }
    
    # Update the appropriate section
    if section == "header":
        accumulated_result["pages"][page_number]["header"] = text
    elif section == "main":
        accumulated_result["pages"][page_number]["body"] = text
    elif section == "footer":
        accumulated_result["pages"][page_number]["footer"] = text
    return accumulated_result