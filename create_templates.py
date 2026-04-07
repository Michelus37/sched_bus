from PIL import Image
import os

# Define the panels and their corresponding screen files and regions
panels = [
    ("color_panel.png", "screens/2red_black.jpg", (780, 730, 1140, 850)),
    ("higher_lower_panel.png", "screens/3higher_lower.jpg", (780, 730, 1140, 850)),
    ("inside_outside_panel.png", "screens/4inside_outside.jpg", (780, 730, 1140, 850)),
    ("suit_panel.png", "screens/5color.jpg", (813, 748, 1107, 920)),
]

# Also create ready.png from 1rdy.jpg
ready = ("ready.png", "screens/1rdy.jpg", (860, 680, 1064, 720))

os.makedirs("templates/buttons", exist_ok=True)

for template_name, screen_file, region in panels + [ready]:
    if os.path.exists(screen_file):
        img = Image.open(screen_file)
        cropped = img.crop(region)
        cropped.save(f"templates/buttons/{template_name}")
        print(f"Created {template_name}")
    else:
        print(f"Screen file {screen_file} not found")