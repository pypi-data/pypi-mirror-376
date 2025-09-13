from pathlib import Path
from os.path import dirname, abspath
from os import listdir
from shutil import copyfile


def absolute_path(file):
    file = Path(file).resolve()
    direction = dirname(file)
    return direction

def copy(file_whole_name: str, project_absolute_path: str):
    flag = True

    if file_whole_name in listdir(absolute_path(project_absolute_path)):
        flag = False

    if flag:
        copyfile(
            src=absolute_path(__file__) + '\\' + file_whole_name,
            dst=project_absolute_path + '\\' + file_whole_name
        )

def check(project_absolute_path: str):
    file_list = listdir(absolute_path(__file__))
    resource_list = []

    for f in file_list:
        if '.py' not in f and '.' in f:
            resource_list.append(f)

    for src in resource_list:
        copy(src, project_absolute_path)

