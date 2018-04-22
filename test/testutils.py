import os


def _delDir(directory):
    for the_file in os.listdir(directory):
        file_path = os.path.join(directory, the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
            #elif os.path.isdir(file_path): shutil.rmtree(file_path)
        except Exception as e:
            print(e)


def prepareFs(config):
    if 'temp' in config and not os.path.exists(config["temp"]):
        os.makedirs(config["temp"])

    if 'outcome_dir' in config and not os.path.exists(config["outcome_dir"]):
        os.makedirs(config["outcome_dir"])

    if 'inputs' in config:
        if not os.path.exists(config["inputs"]):
            os.makedirs(config["inputs"])
        else:
            _delDir(config["inputs"])
