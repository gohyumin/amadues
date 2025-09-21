# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math
import time

def draw_clean_detection_dots(frame, detections, selected_idx=None):
    """
    Draw CLEAN dots ONLY on detected objects (no text, no borders)
    """
    if not detections:
        return frame

    # Draw dots on ALL detected objects
    for i, det in enumerate(detections):
        (cx, cy) = det["center"]
        
        if i == selected_idx:
            # Selected dot - bright green and pulsing
            dot_color = (0, 255, 0)  # Bright green
            dot_radius = 12
            
            # Pulsing effect for selected dot
            pulse_radius = int(abs(math.sin(time.time() * 4) * 3) + dot_radius)
            
            # Multi-layer selected dot for high visibility
            cv2.circle(frame, (cx, cy), pulse_radius, (255, 255, 255), 3)  # White pulse ring
            cv2.circle(frame, (cx, cy), dot_radius + 3, (0, 255, 0), 3)    # Green outer ring
            cv2.circle(frame, (cx, cy), dot_radius, (0, 255, 0), -1)       # Green filled center
            cv2.circle(frame, (cx, cy), dot_radius - 4, (255, 255, 255), -1)  # White inner
            
        else:
            # Unselected dots - small orange dots
            dot_color = (0, 165, 255)  # Orange
            dot_radius = 6
            
            # Simple clean dot
            cv2.circle(frame, (cx, cy), dot_radius, dot_color, -1)        # Orange center
            cv2.circle(frame, (cx, cy), dot_radius, (255, 255, 255), 2)   # White border

    return frame

def draw_green_selection_border(frame, detection, border_color=(0, 255, 0), thickness=6):
    """
    Draw prominent GREEN border around selected object ONLY
    """
    # Handle both "bbox" and "box" keys
    if "bbox" in detection:
        x1, y1, x2, y2 = detection["bbox"]
    elif "box" in detection:
        x1, y1, x2, y2 = detection["box"]
    else:
        return frame

    # Convert to int to avoid any float issues
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    
    # Animated pulsing border thickness
    pulse_thickness = int(abs(math.sin(time.time() * 3) * 3) + thickness)
    
    # Multi-layer green border for maximum visibility
    cv2.rectangle(frame, (x1-4, y1-4), (x2+4, y2+4), (255, 255, 255), 4)  # White outer frame
    cv2.rectangle(frame, (x1-1, y1-1), (x2+1, y2+1), border_color, pulse_thickness)  # Pulsing green border
    cv2.rectangle(frame, (x1+2, y1+2), (x2-2, y2-2), (0, 200, 0), 2)      # Inner green accent
    
    # Professional corner markers
    corner_length = 25
    corner_thickness = 6
    corner_color = (255, 255, 255)  # White corners for contrast
    
    # Draw L-shaped corner markers
    # Top-left corner
    cv2.line(frame, (x1-6, y1-6), (x1+corner_length, y1-6), corner_color, corner_thickness)
    cv2.line(frame, (x1-6, y1-6), (x1-6, y1+corner_length), corner_color, corner_thickness)
    
    # Top-right corner  
    cv2.line(frame, (x2+6, y1-6), (x2-corner_length, y1-6), corner_color, corner_thickness)
    cv2.line(frame, (x2+6, y1-6), (x2+6, y1+corner_length), corner_color, corner_thickness)
    
    # Bottom-left corner
    cv2.line(frame, (x1-6, y2+6), (x1+corner_length, y2+6), corner_color, corner_thickness)
    cv2.line(frame, (x1-6, y2+6), (x1-6, y2-corner_length), corner_color, corner_thickness)
    
    # Bottom-right corner
    cv2.line(frame, (x2+6, y2+6), (x2-corner_length, y2+6), corner_color, corner_thickness)
    cv2.line(frame, (x2+6, y2+6), (x2+6, y2-corner_length), corner_color, corner_thickness)
    
    # Selection label at the top
    label_text = "★ SELECTED ★"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.8
    label_thickness = 2
    
    # Get text dimensions
    (text_width, text_height), baseline = cv2.getTextSize(label_text, font, font_scale, label_thickness)
    
    # Position label above the object
    label_x = x1 + (x2 - x1 - text_width) // 2
    label_y = y1 - 20
    
    # Adjust if label goes off-screen
    if label_y < text_height + 10:
        label_y = y2 + text_height + 20
    
    # Draw label background
    padding = 8
    bg_x1 = label_x - padding
    bg_y1 = label_y - text_height - padding//2
    bg_x2 = label_x + text_width + padding
    bg_y2 = label_y + padding//2
    
    # Green background for label
    cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), border_color, -1)
    cv2.rectangle(frame, (bg_x1, bg_y1), (bg_x2, bg_y2), (255, 255, 255), 2)
    
    # White text on green background
    cv2.putText(frame, label_text, (label_x, label_y), font, font_scale, 
               (255, 255, 255), label_thickness, cv2.LINE_AA)
    
    return frame

def draw_dots_and_labels(frame, detections, selected_idx=None, font=0,
                        show_confidence=False, confidence_colors=False,
                        confidence_opacity=False, thresholds=None, colors=None):
    """
    Main function: Draw dots on ALL objects, GREEN BORDER on selected object only
    """
    if not detections:
        return frame
    
    # Step 1: Draw clean dots on ALL detected objects
    frame = draw_clean_detection_dots(frame, detections, selected_idx)
    
    # Step 2: Draw GREEN BORDER only on selected object
    if selected_idx is not None and 0 <= selected_idx < len(detections):
        selected_det = detections[selected_idx]
        frame = draw_green_selection_border(frame, selected_det, 
                                          border_color=(0, 255, 0), thickness=8)
    
    return frame

# Backward compatibility aliases
draw_selection_border_enhanced = draw_green_selection_border
draw_selection_border_only = draw_green_selection_border
