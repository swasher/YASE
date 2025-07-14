#!/usr/bin/env python3
import sys, json
import swatch
import configparser

def encrypt(input_json, output_ase):
    with open(input_json, 'r', encoding='utf-8') as f:
        items = json.load(f)
    swatch.write(items, output_ase)
    print(f"✅ Wrote {len(items)} items to {output_ase}")

if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    swatch_file = config['Settings']['swatch_file']
    json_file = config['Settings']['json_file']

    encrypt(json_file, swatch_file)
