import os


class FileProcessor:
    #list all require files, easy to update texture type or mesh type
    required_files = {
        '_base.usd': 'mesh',
        '_texture_diff.png': 'diff',
        '_texture_MR.png': 'mr',
        '_texture_normal.png': 'normal',
    }

    def __init__(self, folder_path):
        self.folder_path = folder_path
        self.type_names = set(self.required_files.values())

    def get_assets(self):
        assets = {}
        if not os.path.isdir(self.folder_path):
            raise Exception("Specified path does not exist")

        for file_name in os.listdir(self.folder_path):
            full_path = os.path.join(self.folder_path, file_name)
            if not os.path.isfile(full_path):
                continue

            for suffix, type_name in self.required_files.items():
                if file_name.endswith(suffix):
                    name = file_name[:-len(suffix)]
                    if name not in assets:
                        assets[name] = {t: '' for t in self.type_names}
                    assets[name][type_name] = full_path
                    break
        return assets

    def validate_files(self):
        assets = self.get_assets()
        valid_prefixes = {}
        for name, files in assets.items():
            missing_files = [t for t, path in files.items() if not path and t != 'mat']
            if missing_files:
                print(f"Prefix '{name}' is missing the following files:")
                for missing in missing_files:
                    print(f" - {missing}")
            else:
                valid_prefixes[name] = files
        return valid_prefixes

def main():
    folder_path = r"D:\Asset_Pipeline_Test\Assets"
    processor = FileProcessor(folder_path)
    valid_files = processor.validate_files()

    #print sourves relation
    for prefix, files in valid_files.items():
        print(f"----- {prefix} -----")
        for key, value in files.items():
            print(f"{key:<10}: {value}")
        print()
main()
