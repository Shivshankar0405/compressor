import os
import fitz  # PyMuPDF
from PIL import Image
import io
import shutil

def compress_file(input_path, target_size_bytes):
    ext = os.path.splitext(input_path)[1].lower()
    
    # We will output to a temp file
    output_path = input_path + "_compressed" + ext
    
    if ext in ['.pdf']:
        success = compress_pdf(input_path, output_path, target_size_bytes)
    elif ext in ['.jpg', '.jpeg', '.png', '.webp']:
        success = compress_image(input_path, output_path, target_size_bytes)
    else:
        raise ValueError("Unsupported file format. Please upload PDF, JPG, PNG, or WEBP.")
        
    if not success:
        return None
        
    # Apply padding to reach exactly the target size
    pad_to_exact_size(output_path, target_size_bytes)
    
    return output_path

def pad_to_exact_size(file_path, target_size_bytes):
    current_size = os.path.getsize(file_path)
    if current_size < target_size_bytes:
        bytes_to_add = target_size_bytes - current_size
        with open(file_path, 'ab') as f:
            f.write(b'\x00' * bytes_to_add)

def compress_image(input_path, output_path, target_size):
    # Initial copy to check size
    shutil.copy2(input_path, output_path)
    if os.path.getsize(output_path) <= target_size:
        return True # Already smaller or equal, padding will handle the rest
        
    try:
        img = Image.open(input_path)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        # Binary search for JPEG quality
        min_q = 1
        max_q = 100
        best_q = 1
        
        for _ in range(8): # 8 iterations is enough for binary search 1-100
            mid_q = (min_q + max_q) // 2
            img.save(output_path, format="JPEG", quality=mid_q, optimize=True)
            size = os.path.getsize(output_path)
            
            if size > target_size:
                max_q = mid_q - 1
            else:
                best_q = mid_q
                min_q = mid_q + 1
                
        # Final save with best quality found
        img.save(output_path, format="JPEG", quality=best_q, optimize=True)
        
        # If still too big, scale it down
        current_size = os.path.getsize(output_path)
        if current_size > target_size:
            scale_factor = (target_size / current_size) ** 0.5
            new_width = int(img.width * scale_factor * 0.9) # 0.9 safety margin
            new_height = int(img.height * scale_factor * 0.9)
            if new_width > 0 and new_height > 0:
                img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                img_resized.save(output_path, format="JPEG", quality=best_q, optimize=True)
                
        # If it's still bigger, just force scale it drastically
        while os.path.getsize(output_path) > target_size:
            img = Image.open(output_path)
            new_width = max(1, int(img.width * 0.8))
            new_height = max(1, int(img.height * 0.8))
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            img_resized.save(output_path, format="JPEG", quality=10, optimize=True)
            
        return True
    except Exception as e:
        print(f"Error compressing image: {e}")
        return False

def compress_pdf(input_path, output_path, target_size):
    # Initial check
    shutil.copy2(input_path, output_path)
    if os.path.getsize(output_path) <= target_size:
        return True
        
    try:
        doc = fitz.open(input_path)
        
        dpi_min = 36
        dpi_max = 150
        best_dpi = 36
        
        for _ in range(6):
            mid_dpi = (dpi_min + dpi_max) // 2
            
            out_pdf = fitz.open()
            for page in doc:
                pix = page.get_pixmap(dpi=mid_dpi)
                img_data = pix.tobytes("jpeg")
                
                imgdoc = fitz.open("jpeg", img_data)
                pdfbytes = imgdoc.convert_to_pdf()
                imgdoc.close()
                
                imgpdf = fitz.open("pdf", pdfbytes)
                out_pdf.insert_pdf(imgpdf)
                imgpdf.close()
                
            out_pdf.save(output_path, garbage=4, deflate=True)
            out_pdf.close()
            
            size = os.path.getsize(output_path)
            if size > target_size:
                dpi_max = mid_dpi - 1
            else:
                best_dpi = mid_dpi
                dpi_min = mid_dpi + 1
        
        # Save one last time with the best dpi found
        out_pdf = fitz.open()
        for page in doc:
            pix = page.get_pixmap(dpi=best_dpi)
            img_data = pix.tobytes("jpeg")
            
            imgdoc = fitz.open("jpeg", img_data)
            pdfbytes = imgdoc.convert_to_pdf()
            imgdoc.close()
            
            imgpdf = fitz.open("pdf", pdfbytes)
            out_pdf.insert_pdf(imgpdf)
            imgpdf.close()
            
        out_pdf.save(output_path, garbage=4, deflate=True)
        out_pdf.close()
        
        while os.path.getsize(output_path) > target_size:
            best_dpi = int(best_dpi * 0.8)
            if best_dpi < 10:
                best_dpi = 10
            
            out_pdf = fitz.open()
            for page in doc:
                pix = page.get_pixmap(dpi=best_dpi)
                img_data = pix.tobytes("jpeg") 
                imgdoc = fitz.open("jpeg", img_data)
                pdfbytes = imgdoc.convert_to_pdf()
                imgdoc.close()
                imgpdf = fitz.open("pdf", pdfbytes)
                out_pdf.insert_pdf(imgpdf)
                imgpdf.close()
            out_pdf.save(output_path, garbage=4, deflate=True)
            out_pdf.close()
            
            if best_dpi <= 10:
                break
                
        doc.close()
        return True
    except Exception as e:
        print(f"Error compressing PDF: {e}")
        return False
