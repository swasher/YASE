import os, sys, json
import swatch
import configparser

def decrypt(input_ase, output_json):
    items = swatch.parse(input_ase)
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(items, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(items)} swatches/palettes to {output_json}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(f"Использование: {sys.argv[0]} <файл.ase>")
        sys.exit(1)

    swatch_file = sys.argv[1]
    json_file = os.path.splitext(swatch_file)[0] + '.json'

    try:
        decrypt(swatch_file, json_file)
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден '{swatch_file}'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}", file=sys.stderr)
        sys.exit(1)
