from PIL import Image
import random
from aes import *
import os
import numpy as np

def valid_img(cover_path):
    try:
        with Image.open(cover_path) as img:
            img.verify()
            format = img.format
        return format.upper() == "PNG"
    except Exception:
        return False

def find_peak(hist):
    u = int(np.argmax(hist))
    zero_bins = np.where(hist == 0)[0]
    if zero_bins.size:
        z = zero_bins[np.argmin(np.abs(zero_bins - u))]
    else:
        z = int(np.argmin(hist))
    return u, z

def hist_extract(stego_path, key):
    try:
        if not os.path.exists(stego_path):
            raise FileNotFoundError(f"Stego image {stego_path} not found.")
        if not valid_img(stego_path):
            raise ValueError(f"{stego_path} is not a valid PNG image file.")
        
        print("Loading and analyzing stego image...")
        
        with Image.open(stego_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
        
            arr = np.array(img, dtype=np.uint8)
        height, width, channels = arr.shape
        flat = {ch: arr[..., i].flatten() for i, ch in enumerate(('R','G','B'))}
        
        print(f"Image dimensions: {width}x{height}")
        
        peaks, zeros, shifts = {}, {}, {}
        total_capacity = 0
        
        for ch in ('R','G','B'):
            hist, faltu = np.histogram(flat[ch], bins=256, range=(0,255))
            u, z = find_peak(hist)
            peaks[ch], zeros[ch] = u, z
            shifts[ch] = 1 if z > u else -1
            total_capacity += hist[u]
            
            print(f"Channel {ch}: Peak={u}, Zero={z}, Capacity={hist[u]} bits")
        
        print(f"Total extraction capacity: {total_capacity} bits")
        
        total_bits = 152 * 8
        bits_pr_ch = total_bits // 3
        remainder = total_bits % 3
        
        seed = to_seed(key)
        rng = random.Random(seed)
        
        print("Extracting bits from each channel...")
        extracted_bits = []
        
        for i, ch in enumerate(('R','G','B')):
            extra = 1 if i < remainder else 0
            channel_bits_count = bits_pr_ch + extra
            
            positions = list(range(flat[ch].size))
            rng.shuffle(positions)
            
            u = peaks[ch]
            shift = shifts[ch]
            channel_bits = []
            
            for pos in positions:
                if len(channel_bits) >= channel_bits_count:
                    break
                
                pixel_value = flat[ch][pos]
                
                if pixel_value == u:
                    channel_bits.append('0')
                elif pixel_value == u + shift:
                    channel_bits.append('1')
            
            print(f"Successfully extracted {len(channel_bits)} bits from channel {ch}")
            extracted_bits.extend(channel_bits)
        
        print(f"Total bits extracted: {len(extracted_bits)}")
        
        bit_string = ''.join(extracted_bits[:total_bits])
        byte_data = bytearray()
        
        for i in range(0, len(bit_string), 8):
            byte_chunk = bit_string[i:i+8]
            if len(byte_chunk) == 8:
                byte_data.append(int(byte_chunk, 2))
        
        print(f"Converted to {len(byte_data)} bytes")
        
        starting = b'HISTOSTART'
        ending = b'HISTO_END!'
        
        if not byte_data.startswith(starting):
            raise ValueError("Start marker not found - wrong key or corrupted data")
        
        if not byte_data.endswith(ending):
            raise ValueError("End marker not found - extraction incomplete")
        
        print("Markers validated successfully")
        
        encrypted_payload = bytes(byte_data[10:-10])
        
        # Decrypt
        decrypted_data = decryption(encrypted_payload, key)
        message = decrypted_data.decode('utf-8').rstrip()
        
        print("Decryption successful")
        print("message : ",message)
        return message
        
    except Exception as e:
        raise ValueError(f"Extraction failed: {str(e)}")