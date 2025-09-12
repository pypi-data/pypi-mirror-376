# ==================== IMPORTS ====================
import cv2
import numpy as np
import json
import os
import re
import base64
import time
import shutil
import textwrap
from io import BytesIO
from PIL import Image
from getpass import getpass
from typing import List, Tuple, Dict, Any, Optional

# Imports for Google Colab
from google.colab import files
from google.colab.patches import cv2_imshow
from google.colab import output
from IPython.display import display, Image as IPImage, clear_output, HTML

# Imports for Stage 3 (LLM)
try:
    import google.generativeai as genai
except ImportError:
    print("Warning: 'google-generativeai' not found. Stage 3 will not be available.")
    print("Please run: !pip install -q google-generativeai")

# ==================== UTILITY FUNCTIONS ====================
def cleanup_pipeline():
    """Removes all generated files and folders from the pipeline."""
    print("🧹 Cleaning up pipeline artifacts...")
    items_to_remove = [
        'uploads', 
        'bounded_images', 
        'final_outputs', 
        'coords.json'
    ]
    for item in items_to_remove:
        try:
            if os.path.exists(item):
                if os.path.isdir(item):
                    shutil.rmtree(item)
                    print(f"  - Removed directory: {item}/")
                else:
                    os.remove(item)
                    print(f"  - Removed file: {item}")
        except Exception as e:
            print(f"  - Error removing {item}: {e}")
    print("✅ Cleanup complete.")

def pretty_print_page_with_image(json_path: str):
    """
    Pretty prints the content of a final JSON file and displays its 
    corresponding annotated image.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{json_path}' not found.")
        return

    row_id = os.path.splitext(os.path.basename(json_path))[0]
    print("=" * 100)
    print(f"📄 DOCUMENT PREVIEW: {row_id}")
    print("=" * 100)

    header = data.get("Page header", "") or "(none)"
    page_text = data.get("Page text", "") or "(none)"
    footer = data.get("Page footer", "") or "(none)"
    
    print(f"📋 HEADER:\n---\n{textwrap.fill(header, 100)}\n")
    print(f"📖 PAGE TEXT:\n---\n{textwrap.fill(page_text, 100)}")
    print(f"\n📝 FOOTER:\n---\n{textwrap.fill(footer, 100)}\n")

    table_bbox = data.get("table_bbox", [])
    image_bbox = data.get("image_bbox", [])
    
    print("🟥 TABLE BBOX ([ymin, xmin, ymax, xmax]):")
    print("---" if table_bbox else "(none)")
    if table_bbox:
        for i, bbox in enumerate(table_bbox, 1): print(f"  Table {i}: {bbox}")
        
    print("\n🟩 IMAGE BBOX ([ymin, xmin, ymax, xmax]):")
    print("---" if image_bbox else "(none)")
    if image_bbox:
        for i, bbox in enumerate(image_bbox, 1): print(f"  Image {i}: {bbox}")

    img_path = os.path.join('bounded_images', f"{row_id}.jpg")
    if os.path.exists(img_path):
        print(f"\n📸 CORRESPONDING ANNOTATED IMAGE:")
        cv2_imshow(cv2.imread(img_path))
    else:
        print(f"\n⚠️ Annotated image not found at: {img_path}")
    print("=" * 100)

def show_comparison_view(json_path: str):
    """
    Renders a side-by-side HTML view of the original page image and the
    reconstructed page content from its final JSON file.
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: File '{json_path}' not found.")
        return

    row_id = os.path.splitext(os.path.basename(json_path))[0]
    img_path = os.path.join('bounded_images', f"{row_id}.jpg")

    if not os.path.exists(img_path):
        print(f"❌ Error: Image file not found at '{img_path}'")
        return

    image = cv2.imread(img_path)
    _, buffer = cv2.imencode('.jpg', image)
    base64_image = base64.b64encode(buffer).decode('utf-8')

    header = data.get("Page header", "")
    page_text = data.get("Page text", "").replace('\n', '<br>')
    footer = data.get("Page footer", "")

    html_content = f"""
    <div style="display: flex; gap: 20px; font-family: sans-serif;">
        <div style="flex: 1; border: 1px solid #ddd; padding: 10px;">
            <h3 style="text-align: center;">Annotated Page Image</h3>
            <img src="data:image/jpeg;base64,{base64_image}" style="width: 100%;">
        </div>
        <div style="flex: 1; border: 1px solid #ddd; padding: 10px;">
            <h3 style="text-align: center;">Reconstructed Page Preview</h3>
            <div style="background: #f5f5f5; padding: 10px; margin-bottom: 10px; border-radius: 4px;"><b>Header:</b> {header}</div>
            <div style="line-height: 1.6;">{page_text}</div>
            <div style="background: #f5f5f5; padding: 10px; margin-top: 10px; border-radius: 4px; font-size: 0.9em;"><b>Footer:</b> {footer}</div>
        </div>
    </div>
    """
    display(HTML(html_content))
    
# ==================== HELPER & EDITOR FUNCTIONS ====================

def xywh_to_yminmax(box: tuple) -> List[int]:
    """Converts (x, y, w, h) to [ymin, xmin, ymax, xmax]."""
    x, y, w, h = box
    return [y, x, y + h, x + w]

def yminmax_to_xywh(box: list) -> List[int]:
    """Converts [ymin, xmin, ymax, xmax] to [x, y, w, h]."""
    ymin, xmin, ymax, xmax = box
    return [xmin, ymin, xmax - xmin, ymax - ymin]

def detect_tables(image: np.ndarray) -> List[List[int]]:
    """Detects tables in an image. Returns xywh format."""
    boxes = []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    binary = cv2.adaptiveThreshold(~gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, -2)
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
    h_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, h_kernel, iterations=2)
    v_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, v_kernel, iterations=2)
    mask = cv2.add(h_lines, v_lines)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for c in contours:
        if cv2.contourArea(c) > 2000:
            x, y, w, h = cv2.boundingRect(c)
            if w > 50 and h > 50:
                boxes.append([x, y, w, h])
    return boxes

def detect_image_regions(image: np.ndarray, min_area_percentage=1.5) -> List[List[int]]:
    """Detects image regions. Returns xywh format."""
    h, w, _ = image.shape
    min_area = (min_area_percentage / 100) * (h * w)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edged = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 100, 200)
    contours, _ = cv2.findContours(cv2.dilate(edged, None, iterations=2), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        if cv2.contourArea(c) > min_area:
            x, y, w_box, h_box = cv2.boundingRect(c)
            if 0.2 < (w_box / float(h_box) if h_box > 0 else 0) < 5.0 and w_box > 80 and h_box > 80:
                boxes.append([x, y, w_box, h_box])
    return boxes

def create_annotated_image(
    image: np.ndarray, 
    table_boxes: List[List[int]], 
    image_boxes: List[List[int]]
) -> np.ndarray:
    """Creates annotated image with table and image bounding boxes."""
    annotated_img = image.copy()
    
    # Draw table boxes (red)
    for i, box in enumerate(table_boxes):
        x, y, w, h = box
        cv2.rectangle(annotated_img, (x, y), (x + w, y + h), (0, 0, 255), 3)
        cv2.putText(annotated_img, f"Table {i+1}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    
    # Draw image boxes (green)
    for i, box in enumerate(image_boxes):
        x, y, w, h = box
        cv2.rectangle(annotated_img, (x, y), (x + w, y + h), (0, 255, 0), 3)
        cv2.putText(annotated_img, f"Image {i+1}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    
    return annotated_img

def create_context_image(
    image: np.ndarray,
    context_table_boxes: List[Tuple[List[int], int]],  # (box, original_index)
    context_image_boxes: List[Tuple[List[int], int]]   # (box, original_index)
) -> np.ndarray:
    """Creates image with context boxes (all boxes except the one being edited)."""
    context_img = image.copy()
    
    # Draw context table boxes (red)
    for box, original_idx in context_table_boxes:
        x, y, w, h = box
        cv2.rectangle(context_img, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.putText(context_img, f"Table {original_idx + 1}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    
    # Draw context image boxes (green)
    for box, original_idx in context_image_boxes:
        x, y, w, h = box
        cv2.rectangle(context_img, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(context_img, f"Image {original_idx + 1}", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    return context_img

def interactive_editor(img: np.ndarray, initial_box: List[int], editor_title: str) -> List[int]:
    """Launches the HTML/JS editor for editing a single bounding box."""
    _, buffer = cv2.imencode('.png', img)
    img_str = base64.b64encode(buffer).decode('utf-8')
    img_data_url = f'data:image/png;base64,{img_str}'
    
    # Convert single box to list format for the editor
    initial_boxes = [initial_box] if initial_box else []
    boxes_json = json.dumps(initial_boxes)
    
    html_template = f"""
    <div style="border: 2px solid #ccc; padding: 10px; display: inline-block;">
        <h3 style="font-family: sans-serif;">{editor_title}</h3>
        <p style="font-family: sans-serif; margin-top: 0;">
            <b>Click and drag to draw a box.</b> | <b>Click an existing box to delete.</b>
        </p>
        <canvas id="editor-canvas" style="cursor: crosshair; border: 1px solid black;"></canvas>
        <br>
        <button id="done-button" style="margin-top: 10px; font-size: 16px; padding: 8px 16px;">✅ Submit Box</button>
        <div id="status" style="margin-top: 10px; font-family: sans-serif; font-size: 14px;"></div>
    </div>
    <script>
        const canvas = document.getElementById('editor-canvas');
        const ctx = canvas.getContext('2d');
        const doneButton = document.getElementById('done-button');
        const status = document.getElementById('status');
        const img = new Image();
        
        window.finished = false;
        window.finalBoxes = [];
        let boxes = JSON.parse('{boxes_json}');
        let isDrawing = false;
        let startX, startY;
        
        function updateStatus(message) {{ status.textContent = message; }}
        
        img.onload = function() {{
            canvas.width = img.width;
            canvas.height = img.height;
            redraw();
            updateStatus('Image loaded. Ready for editing.');
        }};
        img.src = '{img_data_url}';
        
        function redraw() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.drawImage(img, 0, 0);
            ctx.strokeStyle = 'blue';
            ctx.lineWidth = 2;
            boxes.forEach(([x, y, w, h]) => {{ ctx.strokeRect(x, y, w, h); }});
            updateStatus(`Current boxes: ${{boxes.length}}`);
        }}
        
        canvas.addEventListener('mousedown', (e) => {{
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            let boxClicked = -1;
            for (let i = boxes.length - 1; i >= 0; i--) {{
                const [x, y, w, h] = boxes[i];
                if (mouseX >= x && mouseX <= x + w && mouseY >= y && mouseY <= y + h) {{
                    boxClicked = i;
                    break;
                }}
            }}
            if (boxClicked !== -1) {{
                boxes.splice(boxClicked, 1);
                redraw();
                updateStatus('Box deleted.');
            }} else {{
                isDrawing = true;
                startX = mouseX;
                startY = mouseY;
                updateStatus('Drawing new box...');
            }}
        }});
        
        canvas.addEventListener('mousemove', (e) => {{
            if (!isDrawing) return;
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            redraw();
            ctx.strokeStyle = 'red';
            ctx.strokeRect(startX, startY, mouseX - startX, mouseY - startY);
        }});
        
        canvas.addEventListener('mouseup', (e) => {{
            if (!isDrawing) return;
            isDrawing = false;
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            const x = Math.min(startX, mouseX);
            const y = Math.min(startY, mouseY);
            const w = Math.abs(mouseX - startX);
            const h = Math.abs(mouseY - startY);
            if (w > 5 && h > 5) {{
                boxes.push([Math.round(x), Math.round(y), Math.round(w), Math.round(h)]);
            }}
            redraw();
        }});
        
        doneButton.addEventListener('click', () => {{
            doneButton.textContent = '⏳ Submitting...';
            doneButton.disabled = true;
            canvas.style.cursor = 'default';
            window.finalBoxes = boxes;
            window.finished = true;
            updateStatus('✅ Submitted! Python is now processing...');
        }});
    </script>
    """
    
    display(HTML(html_template))
    print(f"\n✍️ Edit the {editor_title.lower()} above. Click 'Submit' when done.")
    print("Waiting for manual correction... ⏳")
    
    final_boxes = None
    for _ in range(600):  # Wait for up to 5 minutes
        try:
            is_done = output.eval_js('window.finished')
            if is_done:
                final_boxes = output.eval_js('window.finalBoxes')
                break
        except Exception:
            pass
        time.sleep(0.5)
    
    clear_output(wait=True)
    if final_boxes is not None and len(final_boxes) > 0:
        print("✅ Manual corrections received!")
        return final_boxes[0]  # Return the first (and should be only) box
    else:
        print("⚠️ No box submitted. Using original box." if initial_box else "⚠️ No box submitted. Box will be removed.")
        return initial_box if initial_box else None

# ==================== STAGE 1: UPLOAD, DETECT, & EDIT ====================

def stage_1():
    """
    Handles document upload, detection, and interactive editing (single pass, no loop).
    """
    print("=" * 60 + "\nSTAGE 1: UPLOAD, DETECT, AND EDIT\n" + "=" * 60)

    # Create directories
    for folder in ['uploads', 'bounded_images']:
        os.makedirs(folder, exist_ok=True)

    # Upload file
    print("\n📤 Please upload your document image...")
    uploaded = files.upload()
    if not uploaded:
        print("❌ No files uploaded.")
        return

    # Initial setup
    filename = list(uploaded.keys())[0]
    filepath = os.path.join('uploads', filename)
    with open(filepath, 'wb') as f:
        f.write(uploaded[filename])
    
    row_id = input(f"➡️ Enter a unique Row ID for '{filename}' (e.g., ID_1): ").strip() or os.path.splitext(filename)[0]
    original_img = cv2.imread(filepath)
    
    # Resize for consistent display
    MAX_WIDTH = 1200
    original_h, original_w, _ = original_img.shape
    scale = MAX_WIDTH / original_w if original_w > MAX_WIDTH else 1.0
    display_w = int(original_w * scale)
    display_h = int(original_h * scale)
    display_img = cv2.resize(original_img, (display_w, display_h), interpolation=cv2.INTER_AREA)

    print("\n" + "=" * 50 + f"\nProcessing: {filename} (Row ID: {row_id})\n" + "=" * 50)
    print("🤖 Running automatic detection...")
    
    # Detect on original image, then scale for display
    table_coords_xywh = detect_tables(original_img)
    image_coords_xywh = detect_image_regions(original_img)
    
    # Scale coordinates for display
    table_coords_display = [[int(x * scale), int(y * scale), int(w * scale), int(h * scale)] 
                           for x, y, w, h in table_coords_xywh]
    image_coords_display = [[int(x * scale), int(y * scale), int(w * scale), int(h * scale)] 
                           for x, y, w, h in image_coords_xywh]
    
    print(f"✅ Found {len(table_coords_xywh)} tables and {len(image_coords_xywh)} images.")

    # Show initial detection results
    current_annotated_img = create_annotated_image(display_img, table_coords_display, image_coords_display)
    print("\n📸 Detection Results (Original vs Annotated):")
    side_by_side = np.hstack((display_img, current_annotated_img))
    cv2_imshow(side_by_side)

    # Ask if user wants to edit anything
    prompt = "\n❓ Are you satisfied with these detections?\n"
    
    if table_coords_display:
        if len(table_coords_display) == 1:
            prompt += "  - To edit the table, type 'table'\n"
        else:
            prompt += f"  - To edit tables, type 'table 1' to 'table {len(table_coords_display)}'\n"
            
    if image_coords_display:
        if len(image_coords_display) == 1:
            prompt += "  - To edit the image, type 'image'\n"
        else:
            prompt += f"  - To edit images, type 'image 1' to 'image {len(image_coords_display)}'\n"
            
    prompt += "  - Type 'yes' to approve all and finish\nYour choice: "
    
    choice = input(prompt).strip().lower()

    if choice == 'yes':
        print("✅ All annotations approved.")
    else:
        # Parse and handle editing request
        try:
            if choice in ['table', 'image']:
                # Single box case
                if choice == 'table' and len(table_coords_display) == 1:
                    box_type = 'table'
                    box_index = 0
                elif choice == 'image' and len(image_coords_display) == 1:
                    box_type = 'image'
                    box_index = 0
                else:
                    print(f"❌ Multiple {choice}s detected. Please specify which one (e.g., '{choice} 1').")
                    return
            else:
                # Parse "table 1", "image 2", etc.
                parts = choice.split()
                if len(parts) != 2:
                    print("❌ Invalid format. Please specify which item to edit.")
                    return
                    
                box_type = parts[0]
                box_index = int(parts[1]) - 1
                
                if box_type not in ['table', 'image']:
                    print("❌ Invalid type. Use 'table' or 'image'.")
                    return
                    
                # Validate index
                if box_type == 'table':
                    if not (0 <= box_index < len(table_coords_display)):
                        print(f"❌ Table {box_index + 1} doesn't exist.")
                        return
                else:  # image
                    if not (0 <= box_index < len(image_coords_display)):
                        print(f"❌ Image {box_index + 1} doesn't exist.")
                        return
                        
        except (ValueError, IndexError):
            print("❌ Invalid input. Please enter a valid choice.")
            return

        # Perform the editing
        if box_type == 'table':
            # Get the box being edited
            box_to_edit = table_coords_display[box_index]
            
            # Create context: all images + all other tables (with original indices)
            context_table_boxes = [(box, i) for i, box in enumerate(table_coords_display) if i != box_index]
            context_image_boxes = [(box, i) for i, box in enumerate(image_coords_display)]
            
            # Create context image
            context_img = create_context_image(display_img, context_table_boxes, context_image_boxes)
            
            # Edit the specific table box
            print(f"\n✏️ Editing Table {box_index + 1}...")
            corrected_boxes = interactive_editor(context_img, [], f"Table {box_index + 1} Editor")

            # Update the specific box
            if corrected_boxes and len(corrected_boxes) > 0:
              print(f"DEBUG: corrected_boxes = {corrected_boxes}")
              print(f"DEBUG: corrected_boxes[0] = {corrected_boxes[0]}")
              print(f"DEBUG: type of corrected_boxes[0] = {type(corrected_boxes[0])}")
              table_coords_display[box_index] = corrected_boxes  # This updates display
              table_coords_xywh[box_index] = [int(v / scale) for v in corrected_boxes]  # This updates final coords
            else:
                # Remove the box if None returned
                del table_coords_display[box_index]
                del table_coords_xywh[box_index]
                
        else:  # image
            # Get the box being edited
            box_to_edit = image_coords_display[box_index]
            
            # Create context: all tables + all other images (with original indices)
            context_table_boxes = [(box, i) for i, box in enumerate(table_coords_display)]
            context_image_boxes = [(box, i) for i, box in enumerate(image_coords_display) if i != box_index]
            
            # Create context image
            context_img = create_context_image(display_img, context_table_boxes, context_image_boxes)
            
            # Edit the specific image box
            print(f"\n✏️ Editing Image {box_index + 1}...")
            corrected_box = interactive_editor(context_img, box_to_edit, f"Image {box_index + 1} Editor")
            
            # Update the specific box
            if corrected_box:
                image_coords_display[box_index] = corrected_box
                # Scale back to original coordinates
                image_coords_xywh[box_index] = [int(v / scale) for v in corrected_box]
            else:
                # Remove the box if None returned
                del image_coords_display[box_index]
                del image_coords_xywh[box_index]
        
        # Show final result: clean original vs updated result
        final_annotated = create_annotated_image(display_img, table_coords_display, image_coords_display)
        print("\n🔄 Final Result (Original Clean vs Updated):")
        comparison = np.hstack((display_img, final_annotated))
        cv2_imshow(comparison)

    # Convert to yminmax format for final output
    table_coords_yminmax = [xywh_to_yminmax(box) for box in table_coords_xywh]
    image_coords_yminmax = [xywh_to_yminmax(box) for box in image_coords_xywh]

    # Save final results
    final_coords = {
        row_id: {
            "original_filename": filename,
            "tables": [[int(v) for v in box] for box in table_coords_yminmax],
            "images": [[int(v) for v in box] for box in image_coords_yminmax]
        }
    }
    
    with open('coords.json', 'w') as f:
        json.dump(final_coords, f, indent=4)

    # Save final annotated image (on original resolution)
    final_annotated_img = create_annotated_image(original_img, table_coords_xywh, image_coords_xywh)
    bounded_path = os.path.join('bounded_images', f"{row_id}.jpg")
    cv2.imwrite(bounded_path, final_annotated_img)
    
    print("\n" + "="*60)
    print(f"💾 Saved final coordinates for '{row_id}' to: coords.json")
    print(f"✅ Saved final annotated image to: {bounded_path}")
    print("✅ STAGE 1 COMPLETE")
    print("="*60)


def stage_2(
    row_id: str,
    box_type: Optional[str] = None,
    box_index: Optional[int] = None,
    custom_coords: Optional[List[int]] = None
):
    """
    Tests and visualizes a specific bounding box region from an original image.

    This function can be used in two ways:
    1.  **By Index:** Provide `row_id`, `box_type` ('tables' or 'images'), and `box_index`.
    2.  **By Custom Coordinates:** Provide `row_id` and `custom_coords` as [ymin, xmin, ymax, xmax].
    """
    print("=" * 60)
    print("STAGE 2: COORDINATE TESTING")
    print("=" * 60)

    # --- 1. Input Validation ---
    if custom_coords is None and not (box_type and box_index is not None):
        print("❌ Error: You must provide either `custom_coords` or both `box_type` and `box_index`.")
        return
    
    if box_type and box_type not in ['tables', 'images']:
        print(f"❌ Error: `box_type` must be either 'tables' or 'images', not '{box_type}'.")
        return

    # --- 2. Load Data and Image ---
    coords_path = 'coords.json'
    uploads_dir = 'uploads'

    if not os.path.exists(coords_path):
        print(f"❌ Error: '{coords_path}' not found. Please run stage_1() first.")
        return
    
    with open(coords_path, 'r') as f:
        all_coords = json.load(f)

    if row_id not in all_coords:
        print(f"❌ Error: `row_id` '{row_id}' not found in '{coords_path}'.")
        return

    # Look up the original filename using the row_id
    original_filename = all_coords[row_id].get("original_filename")
    if not original_filename:
        print(f"❌ Error: 'original_filename' not found for '{row_id}' in coords.json.")
        return
        
    original_image_path = os.path.join(uploads_dir, original_filename)
    if not os.path.exists(original_image_path):
        print(f"❌ Error: Could not find original image at '{original_image_path}'.")
        return
        
    original_image = cv2.imread(original_image_path)
    if original_image is None:
        print(f"❌ Error: Failed to load image from '{original_image_path}'.")
        return

    # --- 3. Get Coordinates to Test ---
    coords_to_test = None
    if custom_coords:
        print(f"🧪 Testing custom coordinates for '{row_id}'...")
        if len(custom_coords) != 4:
            print("❌ Error: `custom_coords` must be a list of 4 integers: [ymin, xmin, ymax, xmax].")
            return
        coords_to_test = custom_coords
    else:
        print(f"🧪 Testing '{box_type}' at index {box_index} for '{row_id}'...")
        try:
            boxes_list = all_coords[row_id][box_type]
            coords_to_test = boxes_list[box_index]
        except IndexError:
            box_count = len(all_coords[row_id].get(box_type, []))
            print(f"❌ Error: `box_index` {box_index} is out of bounds. There are only {box_count} boxes for '{box_type}'.")
            return
        except KeyError:
             print(f"❌ Error: `box_type` '{box_type}' not found for '{row_id}'.")
             return

    # --- 4. Crop and Display ---
    if coords_to_test:
        ymin, xmin, ymax, xmax = map(int, coords_to_test)
        
        # Ensure coordinates are within image bounds
        h, w, _ = original_image.shape
        ymin, xmin = max(0, ymin), max(0, xmin)
        ymax, xmax = min(h, ymax), min(w, xmax)

        if ymin >= ymax or xmin >= xmax:
            print(f"❌ Error: The coordinates {coords_to_test} result in an empty image region.")
            return

        # Create the side-by-side view
        image_with_box = original_image.copy()
        cv2.rectangle(image_with_box, (xmin, ymin), (xmax, ymax), (255, 0, 255), 3) # Bright magenta box
        
        print(f"\n📸 Side-by-Side Preview (Original vs. Tested Coordinate):")
        cv2_imshow(np.hstack((original_image, image_with_box)))

        # Also show the zoomed-in crop for detail
        cropped_region = original_image[ymin:ymax, xmin:xmax]
        print(f"\n🖼️  Zoomed-in View of Cropped Region:")
        cv2_imshow(cropped_region)
        print("\n✅ STAGE 2 COMPLETE")

def stage_3(
    api_key: Optional[str] = None, 
    custom_system_prompt: Optional[str] = None,
    output_fields: Optional[List[str]] = None,
    exclude_fields: Optional[List[str]] = None,
    model_name: Optional[str] = None,
):
    """
    Processes annotated images through LLM with customizable JSON output.

    Args:
        api_key: Your LLM API key. If None, you will be prompted.
        custom_system_prompt: An optional custom prompt to override the default.
        output_fields: A list of strings specifying which keys to INCLUDE.
                       If None, all fields are included by default.
        exclude_fields: A list of strings specifying which keys to EXCLUDE
                        from the final output. This is applied after `output_fields`.
    """
    print("=" * 60)
    print("STAGE 3: LLM CONTENT EXTRACTION")
    print("=" * 60)

    # --- 1. Determine Final Output Fields ---
    ALL_POSSIBLE_FIELDS = ["Page header", "Page text", "Page footer", "table_bbox", "image_bbox"]
    
    # Start with the user-defined list or all fields
    if output_fields is not None:
        fields_to_include = [field for field in output_fields if field in ALL_POSSIBLE_FIELDS]
    else:
        fields_to_include = ALL_POSSIBLE_FIELDS.copy()

    # Apply exclusions if provided
    if exclude_fields is not None:
        fields_to_include = [field for field in fields_to_include if field not in exclude_fields]
        print(f"✅  Excluding fields: {exclude_fields}")

    print(f"ℹ️  Final JSON will include: {fields_to_include}")

    # Determine model
    chosen_model = model_name or "gemini-1.5-flash"
    print(f"ℹ️  Using model: {chosen_model}")

    # --- 2. Configure Model API ---
    if not api_key:
        try:
            api_key = getpass("🔑 Please enter your Model's API Key: ")
        except Exception as e:
            print(f"Could not read API key: {e}")
            return
            
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"❌ Error configuring API: {e}")
        return

    # --- 3. Define System Prompt ---
    if custom_system_prompt:
        system_prompt = custom_system_prompt
    else:
        system_prompt = r"""
        You are a specialist in Spatial Document Intelligence. Your task is to perform Layout-Aware Content Extraction.
        For each document page, you will analyze its structure, extract all content in the correct reading order, and format the output as a single, clean JSON object.

        **CRITICAL INSTRUCTIONS:**

        1. **Layout Detection & Reading Order:**
            * Accurately identify the layout: `single_column`, `two_column`, `three_column`, or `four_column`.
            * Blue vertical lines on the image are visual guides for column boundaries.
            * For multi-column layouts, extract the ENTIRE first column (leftmost) from top to bottom, THEN the ENTIRE second column, and so on. DO NOT interleave lines between columns.

        2. **Header and Footer Extraction:**
            * **Decision Rule:** Headers and footers contain metadata ABOUT the document, not THE content OF the document.
            * **HEADER (Top ~15%):** Page numbers, document titles/IDs (e.g., "NACA RM 56807"), dates, author names, journal titles. Not Figure titles or Table titles.
            * **FOOTER (Bottom ~15%):** Page numbers, footnotes, copyright notices, references.
            * **EXCLUDE from Header/Footer:** Section titles (e.g., "RESULTS AND DISCUSSION"), the first paragraph of the main text, table headers, or figure captions should be in "Page text".

        3. **Image Placeholder Insertion:**
            * Green boxes indicate pre-detected image regions. Your task is to place an `[image]` placeholder in the text where that image logically belongs.
            * Place the `[image]` placeholder at the nearest paragraph break corresponding to its vertical position in the reading order.
            * The image's caption text (e.g., "FIGURE 12. Displacement of pipeline...") must be included in the "Page text" immediately after the `[image]` placeholder, as it appears in the document.
            * The number of `[image]` placeholders MUST match the number of green boxes.

        4. **Mathematical Content (LaTeX Formatting):**
            * **MANDATORY:** All mathematical expressions MUST be in LaTeX format.
            * Use `\[ ... \]` for display equations (equations on their own line).
            * Use `\( ... \)` for inline equations (equations within a line of text).
            * **CRITICAL FOR JSON VALIDITY:** Every backslash `\` in LaTeX commands MUST be escaped with a second backslash. This is required for the output to be valid JSON.
                * **Correct:** `"\\(x = \\frac{-b \\pm \\sqrt{b^2-4ac}}{2a}\\)"`
                * **Incorrect:** `"\(x = \frac{-b \pm \sqrt{b^2-4ac}}{2a}\)"`

        5. **Table Extraction:**
            * Red boxes indicate pre-detected table regions. Your task is to extract the table content.
            * Extract all tables into clean, standard HTML `<table>` format.
            * Use `<thead>`, `<tbody>`, `<tr>`, `<th>`, and `<td>`.
            * If a header spans multiple rows or columns, explicitly use rowspan or colspan (instead of leaving empty <th> tags).
            * Ensure the number of columns in the header matches the number of data columns.
            * Place the entire `<table>...</table>` string in the "Page text" where it appears in the reading order.

        NOTE:
            **Visual Cues:**
            * **Red Boxes:** These indicate tables. Your task is to extract the table content.
            * **Green Boxes:** These indicate images. Place an `[image]` placeholder in the text where the image logically belongs. The image's caption must be included in the "Page text" right after the placeholder.


        **OUTPUT FORMAT (Strictly JSON):**
        Return ONLY a valid JSON object. Do not include any introductory text, explanations, or markdown code fences like ```json.
        
        {
          "layout_type": "single_column | two_column | three_column | four_column",
          "Page header": "Text of the page header.",
          "Page text": "All body content, including [image] placeholders, LaTeX math, and HTML tables, in correct reading order.",
          "Page footer": "Text of the page footer."
        }
        """

    # --- 4. Initialize Model and Load Data ---
    model = genai.GenerativeModel(
        model_name=chosen_model,
        system_instruction=system_prompt
    )
    
    coords_path = 'coords.json'
    bounded_images_dir = 'bounded_images'
    final_outputs_dir = 'final_outputs'
    os.makedirs(final_outputs_dir, exist_ok=True)

    try:
        with open(coords_path, 'r') as f:
            all_coords = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: '{coords_path}' not found. Please run stage_1() first.")
        return

    bounded_images = sorted([f for f in os.listdir(bounded_images_dir) if f.endswith('.jpg')])
    if not bounded_images:
        print(f"❌ Error: No images found in '{bounded_images_dir}/'. Please run stage_1() first.")
        return

    # --- 5. Main Processing Loop ---
    print(f"\n📚 Found {len(bounded_images)} annotated image(s) to process.")
    not_approved_finals = []

    for img_file in bounded_images:
        row_id = os.path.splitext(img_file)[0]
        print("\n" + "=" * 50 + f"\nProcessing: {img_file}\n" + "=" * 50)

        if row_id not in all_coords:
            print(f"⚠️ Warning: No coordinates found for '{row_id}'. Skipping.")
            continue

        try:
            img_path = os.path.join(bounded_images_dir, img_file)
            image_part = {"mime_type": "image/jpeg", "data": open(img_path, 'rb').read()}
            
            print("✨ Extracting content…")
            response = model.generate_content([image_part])
            
            gem_json_str = response.text.strip()
            if gem_json_str.startswith("```json"):
                gem_json_str = gem_json_str[7:-3].strip()
            
            gem_json = json.loads(gem_json_str)
            print("✅ Extraction results ready.")

            # Build the final JSON dynamically based on the final list of fields
            final_json = {}
            for field in fields_to_include:
                if field == "Page header":
                    final_json["Page header"] = gem_json.get("Page header", "")
                elif field == "Page text":
                    final_json["Page text"] = gem_json.get("Page text", "").replace("[image]", "📷")
                elif field == "Page footer":
                    final_json["Page footer"] = gem_json.get("Page footer", "")
                elif field == "table_bbox":
                    final_json["table_bbox"] = all_coords[row_id].get("tables", [])
                elif field == "image_bbox":
                    final_json["image_bbox"] = all_coords[row_id].get("images", [])
            
            print("\n📋 Final JSON for Approval:")
            print("-" * 40)
            print(json.dumps(final_json, indent=2))
            print("-" * 40)

            approval = input("❓ Approve this output? (Enter=Yes, n=No): ").strip().lower()
            if approval == 'n':
                not_approved_finals.append(img_file)
                print("❌ Marked as not approved. Continuing...")
            else:
                output_path = os.path.join(final_outputs_dir, f"{row_id}.json")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(final_json, f, indent=4, ensure_ascii=False)
                print(f"✅ Approved and saved to: {output_path}")

        except Exception as e:
            print(f"❌ An error occurred while processing {img_file}: {e}")
            not_approved_finals.append(img_file)
            continue
            
    # --- 6. Final Summary ---
    print("\n" + "=" * 60 + "\n✅ STAGE 3 COMPLETE")
    print(f"Total images processed: {len(bounded_images)}")
    approved_count = len(bounded_images) - len(not_approved_finals)
    print(f"  - Approved and saved: {approved_count}")
    print(f"  - Not approved/Failed: {len(not_approved_finals)}")