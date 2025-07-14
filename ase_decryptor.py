#!/usr/bin/env python3
import sys, json
import swatch
import configparser

def decrypt(input_ase, output_json):
    items = swatch.parse(input_ase)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(items)} swatches/palettes to {output_json}")

if __name__ == '__main__':

    config = configparser.ConfigParser()
    config.read('config.ini')
    swatch_file = config['Settings']['swatch_file']
    json_file = config['Settings']['json_file']

    decrypt(swatch_file, json_file)
