import os
import numpy as np
from PIL import Image, ImageDraw

def generate_vibrant_icons():
    source_path = r"C:\Users\YUVARAJ\.gemini\antigravity-ide\brain\df568210-1dfa-4dd5-b65a-149be5d49029\.user_uploaded\media_1791281056660.jpg"
    orig = Image.open(source_path).convert("RGB")
    w, h = orig.size  # 1024, 1024
    orig_arr = np.array(orig)

    cream_color = (250, 246, 234)

    # 1. Supersampled squircle alpha mask (4x)
    scale = 4
    mask_squircle_hi = Image.new("L", (w * scale, h * scale), 0)
    draw_sq = ImageDraw.Draw(mask_squircle_hi)
    # Inset by 6px inside card boundaries [60, 55, 958, 945] -> [66, 61, 952, 939]
    x0, y0, x1, y1 = 66 * scale, 61 * scale, 952 * scale, 939 * scale
    radius = 205 * scale
    draw_sq.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=255)
    alpha_squircle = mask_squircle_hi.resize((w, h), Image.Resampling.LANCZOS)
    alpha_sq_arr = np.array(alpha_squircle)

    # 2. Supersampled circle alpha mask (4x)
    mask_circle_hi = Image.new("L", (w * scale, h * scale), 0)
    draw_circ = ImageDraw.Draw(mask_circle_hi)
    cx, cy = 509 * scale, 500 * scale
    r_circ = 438 * scale
    draw_circ.ellipse([cx - r_circ, cy - r_circ, cx + r_circ, cy + r_circ], fill=255)
    alpha_circle = mask_circle_hi.resize((w, h), Image.Resampling.LANCZOS)
    alpha_circ_arr = np.array(alpha_circle)

    # 3. Clean RGB canvas:
    # PRESERVE 100% of the original vibrant image inside the card (red magnifying glass, dark text, pins, etc.)
    # ONLY pixels outside the card (and the 1-2px anti-aliased edge) are set to cream color.
    clean_rgb_arr = np.full_like(orig_arr, cream_color)
    clean_rgb_arr[alpha_sq_arr >= 250] = orig_arr[alpha_sq_arr >= 250]
    clean_rgb_img = Image.fromarray(clean_rgb_arr)

    # Verify colors preserved
    reds = (clean_rgb_arr[:, :, 0] > 140) & (clean_rgb_arr[:, :, 1] < 60) & (clean_rgb_arr[:, :, 2] < 60)
    print(f"Verified {np.sum(reds)} red pixels preserved in full saturation!")

    # Helper function to resize RGB and Alpha separately to avoid any dark fringe or blending artifact
    def make_resized_rgba(rgb_img, alpha_img, target_size):
        r_rgb = rgb_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        r_a = alpha_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
        return Image.merge("RGBA", (*r_rgb.split(), r_a))

    # Helper function for adaptive foreground
    def make_adaptive_foreground(size):
        # Canvas: size x size
        # Badge scaled to 80% so the artwork is comfortably inside the 72dp safe circle
        badge_size = int(round(size * 0.80))
        offset = (size - badge_size) // 2

        r_rgb = clean_rgb_img.resize((badge_size, badge_size), Image.Resampling.LANCZOS)
        r_a = alpha_squircle.resize((badge_size, badge_size), Image.Resampling.LANCZOS)
        badge_rgba = Image.merge("RGBA", (*r_rgb.split(), r_a))

        fg_canvas = Image.new("RGBA", (size, size), (*cream_color, 0))
        fg_canvas.paste(badge_rgba, (offset, offset), badge_rgba)
        return fg_canvas

    # Mipmap configurations
    mipmap_configs = {
        "mipmap-mdpi": {"legacy": 48, "adaptive": 108},
        "mipmap-hdpi": {"legacy": 72, "adaptive": 162},
        "mipmap-xhdpi": {"legacy": 96, "adaptive": 216},
        "mipmap-xxhdpi": {"legacy": 144, "adaptive": 324},
        "mipmap-xxxhdpi": {"legacy": 192, "adaptive": 432},
    }

    base_res = r"c:\Users\YUVARAJ\OneDrive\Desktop\Client Finder\mobile\android\app\src\main\res"

    for folder, sizes in mipmap_configs.items():
        folder_path = os.path.join(base_res, folder)
        os.makedirs(folder_path, exist_ok=True)
        leg_sz = sizes["legacy"]
        adap_sz = sizes["adaptive"]

        # 1. ic_launcher.webp (vibrant squircle badge)
        leg_icon = make_resized_rgba(clean_rgb_img, alpha_squircle, leg_sz)
        leg_icon.save(os.path.join(folder_path, "ic_launcher.webp"), "WEBP", lossless=True, exact=True)

        # 2. ic_launcher_round.webp (vibrant circular badge)
        # For circle, also preserve orig inside circle
        clean_circ_rgb = np.full_like(orig_arr, cream_color)
        clean_circ_rgb[alpha_circ_arr >= 250] = orig_arr[alpha_circ_arr >= 250]
        round_icon = make_resized_rgba(Image.fromarray(clean_circ_rgb), alpha_circle, leg_sz)
        round_icon.save(os.path.join(folder_path, "ic_launcher_round.webp"), "WEBP", lossless=True, exact=True)

        # 3. ic_launcher_background.webp (solid cream 108dp canvas)
        bg = Image.new("RGB", (adap_sz, adap_sz), cream_color)
        bg.save(os.path.join(folder_path, "ic_launcher_background.webp"), "WEBP", lossless=True, exact=True)

        # 4. ic_launcher_foreground.webp (vibrant artwork in 108dp canvas)
        fg = make_adaptive_foreground(adap_sz)
        fg.save(os.path.join(folder_path, "ic_launcher_foreground.webp"), "WEBP", lossless=True, exact=True)

        print(f"Updated {folder}: legacy={leg_sz}px, adaptive={adap_sz}px")

    # Update mobile/assets
    assets_dir = r"c:\Users\YUVARAJ\OneDrive\Desktop\Client Finder\mobile\assets"
    os.makedirs(assets_dir, exist_ok=True)

    # icon.png (1024x1024 squircle)
    icon_1024 = make_resized_rgba(clean_rgb_img, alpha_squircle, 1024)
    icon_1024.save(os.path.join(assets_dir, "icon.png"), "PNG")

    # android-icon-foreground.png (1024x1024)
    fg_1024 = make_adaptive_foreground(1024)
    fg_1024.save(os.path.join(assets_dir, "android-icon-foreground.png"), "PNG")

    # android-icon-background.png (1024x1024)
    bg_1024 = Image.new("RGBA", (1024, 1024), (*cream_color, 255))
    bg_1024.save(os.path.join(assets_dir, "android-icon-background.png"), "PNG")

    # app-logo.png (512x512)
    logo_512 = make_resized_rgba(clean_rgb_img, alpha_squircle, 512)
    logo_512.save(os.path.join(assets_dir, "app-logo.png"), "PNG")

    # splash-icon.png (512x512)
    splash_512 = make_resized_rgba(clean_rgb_img, alpha_squircle, 512)
    splash_512.save(os.path.join(assets_dir, "splash-icon.png"), "PNG")

    # favicon.png (48x48)
    fav_48 = make_resized_rgba(clean_rgb_img, alpha_squircle, 48)
    fav_48.save(os.path.join(assets_dir, "favicon.png"), "PNG")

    print("All vibrant icons generated and saved successfully!")

if __name__ == "__main__":
    generate_vibrant_icons()
