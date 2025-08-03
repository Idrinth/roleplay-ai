def load_dataset(callback):
    from datasets import Dataset
    import os
    import yaml

    dataset_list = []
    for fname in os.listdir("./raw-data"):
        try:
            if fname.endswith(".yml"):
                with open(f"./raw-data/{fname}", "r") as file:
                    data = yaml.load(file, yaml.SafeLoader)
                    for element in callback(data):
                        dataset_list.append(element)
        except Exception as e:
            print(f"{fname}: {e}")

    return Dataset.from_list(dataset_list)
