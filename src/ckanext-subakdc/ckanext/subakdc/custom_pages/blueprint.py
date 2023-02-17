import logging

from flask import Blueprint

from ckan.logic import NotAuthorized
import ckan.plugins.toolkit as tk

log = logging.getLogger(__name__)

custom_pages_blueprint = Blueprint("custom_pages", __name__)

def submit_dataset_view():
    try:
        tk.check_access('package_create', {"user": tk.g.user})
        return tk.redirect_to("dataset.new")
    except NotAuthorized:
        pass
        
    return tk.render("custom_pages/submit_dataset.html")

custom_pages_blueprint.add_url_rule(
    "/submit-dataset",
    "submit_dataset",
    submit_dataset_view,
)

custom_pages_blueprint.add_url_rule(
    "/request-a-dataset",
    "request_dataset",
    lambda: tk.redirect_to("https://airtable.com/shrakRbosU1b6QjLZ")
)

custom_pages_blueprint.add_url_rule(
    "/climate-data-research",
    "climate_data_research",
    lambda: tk.render('custom_pages/climate_data_research.html')
)

def get_blueprints():
    return [custom_pages_blueprint]
