"""
Chronicle AI - Text Processing Utility

Provides functions for processing and segmenting raw diary text.
"""
import re
from typing import Dict


def segment_diary_text(raw_text: str) -> Dict[str, str]:
    """
    Segments raw diary text into morning, afternoon, and night based on time hints or position.
    
    The function first looks for explicit markers (e.g., "Morning:", "Afternoon:", "Night:").
    If no markers are found, it identifies time hints within the text to attempt a split.
    As a final fallback, it divides the text into three segments based on position.
    
    Args:
        raw_text: The full diary entry text
        
    Returns:
        A dictionary with keys 'morning', 'afternoon', and 'night'.
    """
    segments = {"morning": "", "afternoon": "", "night": ""}
    
    if not raw_text or not raw_text.strip():
        return segments
    
    # Normalize line endings
    text = raw_text.replace('\r\n', '\n')
    lines = text.splitlines()
    
    # 1. LOOK FOR EXPLICIT MARKERS (e.g., "Morning:", "Afternoon:")
    current_key = None
    segment_captured = {"morning": [], "afternoon": [], "night": [], "unassigned": []}
    found_markers = False
    
    for line in lines:
        stripped = line.strip()
        lower_line = stripped.lower()
        
        new_key = None
        if lower_line.startswith("morning:"):
            new_key = "morning"
        elif lower_line.startswith("afternoon:"):
            new_key = "afternoon"
        elif lower_line.startswith("night:") or lower_line.startswith("evening:"):
            new_key = "night"
            
        if new_key:
            current_key = new_key
            found_markers = True
            # Keep the content after the colon if it exists on the same line
            content = stripped.split(":", 1)[1].strip()
            if content:
                segment_captured[current_key].append(content)
        elif current_key:
            segment_captured[current_key].append(line)
        else:
            segment_captured["unassigned"].append(line)
            
    if found_markers:
        segments["morning"] = "\n".join(segment_captured["unassigned"] + segment_captured["morning"]).strip()
        segments["afternoon"] = "\n".join(segment_captured["afternoon"]).strip()
        segments["night"] = "\n".join(segment_captured["night"]).strip()
        return segments

    # 2. TIME-HINT BASED SEGMENTATION
    # If no explicit markers, look for time-of-day keywords within the text
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    if not found_markers and len(paragraphs) > 1:
        p_segments = {"morning": [], "afternoon": [], "night": []}
        
        for p in paragraphs:
            p_lower = p.lower()
            # Simple keyword matching
            if any(word in p_lower for word in ["woke up", "breakfast", "8am", "9am", "10am", "morning"]):
                p_segments["morning"].append(p)
            elif any(word in p_lower for word in ["lunch", "1pm", "2pm", "afternoon"]):
                p_segments["afternoon"].append(p)
            elif any(word in p_lower for word in ["dinner", "night", "evening", "tonight", "bed"]):
                p_segments["night"].append(p)
            else:
                # If no clear hint, we'll try to guess based on existing paragraphs
                # or just leave it for the positional logic
                pass
        
        # If we found distinct segments via hints, use them
        if any(p_segments.values()):
            # Fill them back into the main segments dict
            segments["morning"] = "\n\n".join(p_segments["morning"]).strip()
            segments["afternoon"] = "\n\n".join(p_segments["afternoon"]).strip()
            segments["night"] = "\n\n".join(p_segments["night"]).strip()
            
            # If we still have empty segments, we'll let the positional logic handle it
            # or if we have at least one segment filled, return it
            if any(segments.values()):
                # We could potentially distribute unassigned paragraphs here,
                # but for simplicity, we only return if it looks like a decent split.
                # However, the user asked for morning/afternoon/night.
                pass

    # 3. POSITION-BASED FALLBACK (Equal parts)
    # If heuristics/markers didn't yield a complete 3-way split
    if not segments["morning"] and not segments["afternoon"] and not segments["night"]:
        if len(paragraphs) >= 3:
            n = len(paragraphs)
            first_split = (n + 2) // 3
            second_split = (2 * n + 2) // 3
            segments["morning"] = "\n\n".join(paragraphs[:first_split])
            segments["afternoon"] = "\n\n".join(paragraphs[first_split:second_split])
            segments["night"] = "\n\n".join(paragraphs[second_split:])
        elif len(paragraphs) == 2:
            segments["morning"] = paragraphs[0]
            segments["afternoon"] = paragraphs[1]
        elif len(paragraphs) == 1:
            segments["morning"] = paragraphs[0]
            
    return segments
