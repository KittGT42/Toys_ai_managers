import json
import math


def split_json_file(input_file, output_prefix):
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunk_size = math.ceil(len(data) / 9)
    for i in range(9):
        start = i * chunk_size
        end = (i + 1) * chunk_size
        chunk = data[start:end]

        with open(f'chanks_toys_data/{output_prefix}_{i + 1}.json', 'w', encoding='utf-8') as f:
            json.dump(chunk, f, ensure_ascii=False, indent=2)


# Використання
split_json_file('bontoi_product_data.json', 'feed_part')