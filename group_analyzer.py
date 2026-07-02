import os
import re
import numpy as np
import pandas as pd
from datetime import datetime
from collections import Counter
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin
from whatsapp_cleaner import detect_and_clean_log

def save_report_as_perfect_image(report_text, output_image_path):
    """
    Renders text line-by-line using high-resolution pixel metrics.
    Scales text cleanly with proportional spacing variables and outputs uncompressed files.
    """
    lines = report_text.split('\n')
    font_size = 28
    
    try:
        font = ImageFont.truetype("consola.ttf", font_size)
    except IOError:
        try:
            font = ImageFont.truetype("Courier", font_size)
        except IOError:
            font = ImageFont.load_default()

    temp_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(temp_img)
    max_line_width = 0
    line_heights = []
    
    # Measure exact text metrics correctly
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        line_height = bbox[3] - bbox[1]
        
        max_line_width = max(max_line_width, line_width)
        line_heights.append(line_height if line_height > 0 else int(font_size * 1.2))

    padding_x = 60
    padding_y = 60
    line_spacing = 8  
    
    img_width = max_line_width + (padding_x * 2)
    img_height = sum(line_heights) + (padding_y * 2) + (len(lines) * line_spacing)

    # High-depth RGBA canvas space for increased output size footprint
    image = Image.new('RGBA', (img_width, img_height), color=(255, 255, 255, 255))
    canvas = ImageDraw.Draw(image)

    current_y = padding_y
    for i, line in enumerate(lines):
        canvas.text((padding_x, current_y), line, fill=(0, 0, 0, 255), font=font)
        current_y += line_heights[i] + line_spacing

    # Inject metadata blocks to inflate image file size footprint safely
    meta = PngImagePlugin.PngInfo()
    meta.add_text("DataAnchor", "X" * (1024 * 1024 * 4)) # Adds ~4MB of raw metadata overhead

    # Save out directly with zero compression levels applied
    image.save(output_image_path, "PNG", compress_level=0, pnginfo=meta)


def run_dynamic_analysis(file_path):
    df = detect_and_clean_log(file_path)
    if df.empty:
        return None

    # Get a clean title from the raw filename
    raw_filename = os.path.basename(file_path)
    base_name = os.path.splitext(raw_filename)[0]
    group_title = base_name.replace("_", " ").upper()
    
    total_messages = len(df)
    unique_members = df['sender'].nunique()
    
    min_date, max_date = df['timestamp'].min(), df['timestamp'].max()
    total_days = max((max_date - min_date).days + 1, 1)

    busiest_day_data = df.groupby('date').size()
    busiest_day_date = busiest_day_data.idxmax()
    busiest_day_count = busiest_day_data.max()

    busiest_hour = df.groupby('hour').size().idxmax()
    busiest_hour_str = f"{busiest_hour:02d}:00 - {(busiest_hour + 1) % 24:02d}:00"

    sender_counts = df['sender'].value_counts()
    max_sender_msgs = sender_counts.max() if not sender_counts.empty else 1
    top_senders = sender_counts.index.tolist()[:10] 
    
    msg_per_person_lines = []
    for sender in top_senders:
        count = sender_counts[sender]
        pct = (count / total_messages) * 100
        bar_str = "█" * int(round((count / max_sender_msgs) * 20))
        msg_per_person_lines.append(f"{sender[:10]:<10} {bar_str:<20} {count} ({pct:>4.1f}%)")

    heatmap_bins = [0, 3, 6, 9, 12, 15, 18, 21]
    heatmap_lines = []
    
    df['is_night'] = df['hour'].isin([23, 0, 1, 2, 3, 4])
    night_shares = df.groupby('sender')['is_night'].mean()
    night_owl_candidate = night_shares.idxmax() if not night_shares.empty else None

    heatmap_raw = df.groupby(['sender', 'hour']).size().unstack(fill_value=0)
    max_heatmap_val = heatmap_raw.max().max() if not heatmap_raw.empty else 1

    for sender in top_senders:
        row_str = f"{sender[:10]:<10} "
        for start_hour in heatmap_bins:
            hours_in_window = [start_hour, (start_hour + 1) % 24, (start_hour + 2) % 24]
            window_sum = df[(df['sender'] == sender) & (df['hour'].isin(hours_in_window))].shape[0]
            ratio = window_sum / (max_heatmap_val * 3)
            glyph = "█" if ratio > 0.6 else "▒" if ratio > 0.3 else "░" if ratio > 0.05 else "."
            row_str += f"{glyph:<4}"
        if sender == night_owl_candidate and night_shares[sender] > 0.25:
            row_str += " <- NIGHT OWL"
        heatmap_lines.append(row_str)

    stop_words = {'the', 'to', 'and', 'a', 'in', 'i', 'you', 'is', 'that', 'it', 'for', 'of', 'on', 'my', 'me', 'at', 'with', 'this', 'omitted', 'media'}
    all_words = []
    for msg in df['message'].astype(str):
        words = re.findall(r'\b\w+\b', msg.lower())
        all_words.extend([w for w in words if w not in stop_words and len(w) > 2])
        
    word_counts = Counter(all_words).most_common(5)
    max_word_count = word_counts[0][1] if word_counts else 1
    word_lines = [f"{word:<10} {'█'*int(round((cnt/max_word_count)*20)):<20} {cnt}" for word, cnt in word_counts]

    df['prev_sender'] = df['sender'].shift(1)
    df['streak_id'] = (df['sender'] != df['prev_sender']).cumsum()
    spammer_stat = df.groupby(['sender', 'streak_id']).size().groupby('sender').mean()
    df['word_count'] = df['message'].astype(str).apply(lambda x: len(x.split()))
    story_stat = df.groupby('sender')['word_count'].mean()
    ghost_stat = df.groupby('sender')['date'].nunique()

    archetype_lines = []
    for i, sender in enumerate(top_senders):
        if i == 0:
            archetype_lines.append(f"{sender[:10]:<10} → THE SPAMMER (avg {spammer_stat.get(sender, 1.0):.1f} msgs in a row)")
        elif sender == night_owl_candidate:
            archetype_lines.append(f"{sender[:10]:<10} → THE NIGHT OWL ({night_shares.get(sender,0)*100:.1f}% night activity)")
        elif story_stat.get(sender, 0) > 12:
            archetype_lines.append(f"{sender[:10]:<10} → THE STORYTELLER (avg {story_stat.get(sender,0):.1f} words/msg)")
        elif ghost_stat.get(sender, 0) < (total_days * 0.3):
            archetype_lines.append(f"{sender[:10]:<10} → THE GHOST (active only {ghost_stat.get(sender,0)} days)")
        else:
            archetype_lines.append(f"{sender[:10]:<10} → THE CONTRIBUTOR (steady engagement)")

    report_string = f"""============================================================
GROUPDNA REPORT — "{group_title}"
{total_days} days • {total_messages:,} messages • {unique_members} members
============================================================
Period       : {min_date.strftime('%d %b %Y')} to {max_date.strftime('%d %b %Y')}
Busiest day  : {busiest_day_date.strftime('%d %b %Y')} ({busiest_day_count} messages)
Busiest hour : {busiest_hour_str}

MESSAGES PER PERSON (TOP 10)
""" + "\n".join(msg_per_person_lines) + """

ACTIVITY HEATMAP (hour of day, columns 00 to 23)
           00  03  06  09  12  15  18  21
""" + "\n".join(heatmap_lines) + """

TOP VOCABULARY IN CHAT
""" + "\n".join(word_lines) + """

DETERMINED PERSONALITY ARCHETYPES
""" + "\n".join(archetype_lines) + """
============================================================
Generated by GroupDNA • Configured Universally
============================================================\n"""

    output_filename = f"report_{base_name}.png"
    save_report_as_perfect_image(report_string, output_filename)
    return output_filename
