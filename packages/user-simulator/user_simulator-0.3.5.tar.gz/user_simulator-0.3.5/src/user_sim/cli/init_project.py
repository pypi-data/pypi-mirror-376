import os
from argparse import ArgumentParser
from user_sim.cli.cli import parse_init_project_arguments


def generate_untitled_name(path):
    i = 1
    while True:
        name = f"Untitled_project_{i}"
        full_path = os.path.join(path, name)
        if not os.path.exists(full_path):
            return name
        i += 1


def _setup_configuration():
    args = parse_init_project_arguments()
    base_path = os.path.abspath(args.path)

    if not args.name:
        project_name = generate_untitled_name(base_path)
    else:
        project_name = args.name

    path = args.path

    return project_name, path


def make_unique_dir(path):
    base_path = path
    counter = 1

    while os.path.exists(path):
        path = f"{base_path}_{counter}"
        counter += 1

    os.makedirs(path)
    return path


def init_proj():

    project_name, path = _setup_configuration()

    project_path = os.path.join(path, project_name)

    project_path = make_unique_dir(project_path)

    run_yml_content = f"""\
project_folder: {project_name}

user_profile:
technology:
connector_params:
extract:
#execution_parameters:
    # - verbose
    # - clean_cache
    # - update_cache
    # - ignore_cache
    """
    # project_path = os.path.join(path, project_name)

    folder_list = ["profiles", "rules", "types", "personalities"]
    for folder in folder_list:
        folder_path = os.path.join(project_path, folder)
        os.makedirs(folder_path)
        with open(f'{folder_path}/PlaceDataHere.txt', 'w') as f:
            pass

    run_yml_path = os.path.join(project_path, "run.yml")
    if not os.path.exists(run_yml_path):
        with open(run_yml_path, "w") as archivo:
            archivo.write(run_yml_content)

    return project_path


def main():
    final_path = init_proj()
    print(f"--- Project created at: '{final_path}' ---")


if __name__ == "__main__":
    main()
