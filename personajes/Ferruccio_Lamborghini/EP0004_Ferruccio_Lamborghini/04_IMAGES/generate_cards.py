import os
import math
from PIL import Image, ImageEnhance

def main():
    # Ruta del retrato de estudio limpio y real de Ferruccio
    orig_path = r"C:\Users\Jota Ochoa\.gemini\antigravity\brain\4ac4fbf9-fed9-4031-be75-e58e112fc2d0\ferruccio_studio_clean_1786311810497.jpg"
    dest_dir = r"C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos\personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini\04_IMAGES"
    
    if not os.path.exists(orig_path):
        print(f"Error: No se encuentra el retrato en {orig_path}")
        return
        
    img = Image.open(orig_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
        
    os.makedirs(dest_dir, exist_ok=True)
    
    # 1. GENERACIÓN VERTICAL (9:16, 1080x1920)
    # Hacemos un recorte de precisión en ratio 9:16 exacto (532x851)
    # Centrado horizontalmente en x=448 (centro del rostro de 896) y verticalmente en y=350
    crop_w_v, crop_h_v = 532, 851
    left_v = 448 - (crop_w_v // 2)
    top_v = 20
    right_v = left_v + crop_w_v
    bottom_v = top_v + crop_h_v
    
    crop_vertical = img.crop((left_v, top_v, right_v, bottom_v))
    # Redimensionamos a 1080x1728 (90% de la altura de 1920). Como ambos son 9:16 exactos, NO hay deformación.
    portrait_vertical = crop_vertical.resize((1080, 1728), Image.Resampling.LANCZOS)
    
    # Procesamiento cinematográfico B&W
    gray_vertical = portrait_vertical.convert('L')
    enhanced_vertical = ImageEnhance.Contrast(gray_vertical).enhance(1.30)
    enhanced_vertical = ImageEnhance.Brightness(enhanced_vertical).enhance(1.05)
    processed_vertical = enhanced_vertical.convert('RGB')
    
    # Canvas en negro absoluto
    canvas_vertical = Image.new('RGB', (1080, 1920), (2, 3, 4))
    canvas_vertical.paste(processed_vertical, (0, 0))
    
    # Desvanecimiento cosenoidal súper suave al final del 90% (de y=1300 a y=1728)
    for y in range(1300, 1728):
        factor = (y - 1300) / (1728 - 1300)
        alpha = math.cos(factor * math.pi / 2)
        
        for x in range(1080):
            orig_pixel = canvas_vertical.getpixel((x, y))
            blended = tuple(int(orig_pixel[i] * alpha + (2, 3, 4)[i] * (1 - alpha)) for i in range(3))
            canvas_vertical.putpixel((x, y), blended)
            
    # Guardamos la vertical
    canvas_vertical.save(os.path.join(dest_dir, "Character_card_vertical_no_text.png"), "PNG")
    print("Vertical card saved successfully.")
    
    # 2. GENERACIÓN HORIZONTAL (16:9, 1920x1080)
    # Recorte para horizontal en ratio 4:5 (640x800) para mostrar más anchura de hombros
    crop_w_h, crop_h_h = 640, 800
    left_h = 448 - (crop_w_h // 2)
    top_h = 20
    right_h = left_h + crop_w_h
    bottom_h = top_h + crop_h_h
    
    crop_horizontal = img.crop((left_h, top_h, right_h, bottom_h))
    
    # Escalamos para que ocupe el 90% de la altura total (972 de 1080)
    # Manteniendo la proporción 4:5 exacta (ancho = 972 * 4/5 = 777)
    target_h = 972
    target_w = int(target_h * (crop_w_h / crop_h_h))
    portrait_horizontal = crop_horizontal.resize((target_w, target_h), Image.Resampling.LANCZOS)
    
    gray_horizontal = portrait_horizontal.convert('L')
    enhanced_horizontal = ImageEnhance.Contrast(gray_horizontal).enhance(1.30)
    enhanced_horizontal = ImageEnhance.Brightness(enhanced_horizontal).enhance(1.05)
    processed_horizontal = enhanced_horizontal.convert('RGB')
    
    canvas_horizontal = Image.new('RGB', (1920, 1080), (2, 3, 4))
    
    # Colocamos al personaje a la derecha, centrado verticalmente (y = (1080 - 972) / 2 = 54)
    # x = 1920 - 777 - 100 = 1043 (deja aire a la derecha e izquierda)
    paste_x = 1920 - target_w - 50 # 1093
    paste_y = (1080 - target_h) // 2 # 54
    canvas_horizontal.paste(processed_horizontal, (paste_x, paste_y))
    
    # Desvanecimiento cosenoidal en el contorno izquierdo (de x=paste_x a x=paste_x + 300)
    for x in range(paste_x, paste_x + 300):
        factor = (x - paste_x) / 300
        alpha = math.cos((1 - factor) * math.pi / 2)
        
        for y in range(1080):
            orig_pixel = canvas_horizontal.getpixel((x, y))
            blended = tuple(int(orig_pixel[i] * alpha + (2, 3, 4)[i] * (1 - alpha)) for i in range(3))
            canvas_horizontal.putpixel((x, y), blended)
            
    # Guardamos la horizontal
    canvas_horizontal.save(os.path.join(dest_dir, "Character_card_horizontal_no_text.png"), "PNG")
    print("Horizontal card saved successfully.")

if __name__ == "__main__":
    main()
