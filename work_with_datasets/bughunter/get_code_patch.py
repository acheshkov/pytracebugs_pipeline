import json
import argparse


def red_file(file_name, beg, end):
    with open(file_name) as f:
        data = f.read().split('\n')[beg - 1:end]
        return '\n'.join(data)


def main(input_file, output_file):
    with open(input_file) as f:
        data = json.loads(f.read())[0]
        export_data = f"{data['project_name']}\n"
        line = '=' * 10
        for path in data['patches']:
            bug = path['bug']
            fix = path['fix']

            export_data += f"{line} {bug['file_path'].split('/')[-1]} / {fix['method']['name']} {line}\n"
            export_data += red_file(bug['file_path'], bug["method"]["beg"], bug["method"]["end"])
            export_data += f"{line} fix {line}\n"
            export_data += red_file(fix['file_path'], fix["method"]["beg"], fix["method"]["end"])
            export_data += f"{line} end {line}\n"
        print(export_data)
        with open(output_file, "w") as save_file:
            save_file.write(export_data)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate dataset')
    parser.add_argument(
        'input_file', type=str, help='Имя файла JSON с bug-fix грануляциия метод'
    )
    parser.add_argument(
        'output_file', type=str, help='Имя файла для сохранения экспорта кода'
    )
    args = parser.parse_args()
    main(args.input_file, args.output_file)
