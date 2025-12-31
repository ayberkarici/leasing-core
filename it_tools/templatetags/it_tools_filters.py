from django import template
import re

register = template.Library()


@register.filter
def extract_day_from_filename(filename):
    """
    Dosya isminden tarih yapısını bulup sadece gün kısmını döndürür.
    Öncelik: Son tire (-) sonrası son sayıyı alır (EventExport_2025-12-16 -> 16)
    Fallback: Farklı tarih formatlarını dener
    """
    if not filename:
        return ''
    
    # Önce son tire (-) sonrası son kısmı kontrol et
    # EventExport_2025-12-16.txt formatı için
    if '-' in filename:
        parts = filename.split('-')
        last_part = parts[-1]
        # Son kısımdan sadece sayıları al (uzantıyı temizle)
        day_match = re.match(r'(\d+)', last_part)
        if day_match:
            return day_match.group(1)
    
    # Fallback: Farklı tarih formatlarını dene
    patterns = [
        r'(\d{4})(\d{2})(\d{2})',  # YYYYMMDD format: 20250131
        r'(\d{4})_(\d{2})_(\d{2})',  # YYYY_MM_DD format: 2025_01_31
        r'(\d{2})(\d{2})(\d{4})',  # DDMMYYYY format: 31012025
        r'(\d{2})\.(\d{2})\.(\d{4})',  # DD.MM.YYYY format: 31.01.2025
    ]
    
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            groups = match.groups()
            # YYYYMMDD formatı
            if len(groups[0]) == 4:
                return groups[2]  # Gün son grup
            # DDMMYYYY formatı
            else:
                return groups[0]  # Gün ilk grup
    
    return filename  # Tarih bulunamazsa dosya ismini olduğu gibi döndür
