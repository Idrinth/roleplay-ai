# Contributing

Contributions are very welcome. Even if you can't code, you can help test and create training data, so feel free to jump in!

## Setup

`docker compose up` will run a local version of the project, that is (usually) productionready. If it is not, that is a bug and should be listed as an issue asap.

### app

The app is a fastapi microservice, that handles the data retrieval and storage as well as communication with other services. Either use the dockerfile or install the requirements.txt in a venv with pip to get it up and running.

### beam-llm-hosting

These are the configurations for the [beam.cloud](https://beam.cloud) service. They contain little logic and would require installing the requirements.remote.txt and requirements.txt with pip in a venv to have full autocomplete locally.

### beam-llm-training

These are the configurations for the [beam.cloud](https://beam.cloud) model training. They contain little logic and require installing the requirements.remote.txt and requirements.txt with pip in a venv for full autocompletion.

#### data

The data folder contains yaml files for training the model. If you have any examples you can think about, please add them as a fresh file or expand an existing one following the formatting in the existing files in the folder.

### system-prompts

These markdown files dictate model behaviour both locally and remotely. Please touch and change with utmost care.

### ui

This is a npm based project. run `npm ci` to set it up or `npm install` to update dependencies. `npm run build` creates static files output or just run the dockerfile for a fully functional frontend.
