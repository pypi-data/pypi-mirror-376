from pictex import *

# Test the transparency handling
canvas = Canvas().color("#ffffff72").font_family("Impact").font_size(150)
result = canvas.render("hey")

# Get the raw numpy array to inspect
import numpy as np
raw_array = result.to_numpy('BGRA')  # Skia's native format
rgba_array = result.to_numpy('RGBA')  # What gets passed to Pillow

print("Sample BGRA values (raw from Skia):")
print(raw_array[100:105, 100:105, :])
print("\nSample RGBA values (passed to Pillow):")
print(rgba_array[100:105, 100:105, :])

# Check if values are premultiplied
print(f"\nAlpha channel range: {rgba_array[:,:,3].min()} - {rgba_array[:,:,3].max()}")
print(f"Are RGB values potentially premultiplied? {np.any(rgba_array[:,:,:3] > rgba_array[:,:,3:4])}")