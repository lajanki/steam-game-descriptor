# Flask CLI commands for manual maintenance tasks


import json

from flask import Flask
from flask.cli import AppGroup

from app import generate_description, setup_gcs_models
from app.tools import nltk_pos_tag_download, get_model_stats


app = Flask(__name__)
app.config.from_prefixed_env()

task_cli = AppGroup("task")
app.cli.add_command(task_cli)

@task_cli.command("create-pos-map", help="Create a mapping of nltk POS tags to their descriptions. Requires nltk library setup.")
def create_pos_map():
    nltk_pos_tag_download.create_pos_tag_mapping()

@task_cli.command("show-model-stats", help="Show the current model stats.")
def show_model_stats():
    get_model_stats.show_current_model_stats()

@task_cli.command("demo", help="Generate a sample game description in JSON format.")
def show_demo():
    generator = generate_description.DescriptionGenerator(app.config)
    print(json.dumps(generator(), indent=4))

@task_cli.command("train", help="Train new models and store to remote bucket.")
def setup_gcs_models_():
    setup_gcs_models.setup()
