# -*- coding: utf-8 -*-

"""
Tarbell project configuration
"""

# Google spreadsheet key
SPREADSHEET_KEY = "1ChHq-ZcB0-xuEysQu8-sAPT5QACxNv-sGoYWgz6IuHg"

# Exclude these files from publication
EXCLUDES = ["*.md", "requirements.txt"]

# Spreadsheet cache lifetime in seconds. (Default: 4)
# SPREADSHEET_CACHE_TTL = 4

# Create JSON data at ./data.json, disabled by default
CREATE_JSON = True

# Get context from a local file or URL. This file can be a CSV or Excel
# spreadsheet file. Relative, absolute, and remote (http/https) paths can be 
# used.
# CONTEXT_SOURCE_FILE = ""

# EXPERIMENTAL: Path to a credentials file to authenticate with Google Drive.
# This is useful for for automated deployment. This option may be replaced by
# command line flag or environment variable. Take care not to commit or publish
# your credentials file.
# CREDENTIALS_PATH = ""

# S3 bucket configuration
#S3_BUCKETS = {
    # Provide target -> s3 url pairs, such as:
    #     "mytarget": "mys3url.bucket.url/some/path"
    # then use tarbell publish mytarget to publish to it
    
#}

# Default template variables
DEFAULT_CONTEXT = {
    'name': 'pbcelections',
    'title': 'Know your candidates guide'
}

from flask import Blueprint, g, render_template,Flask, url_for
from jinja2 import evalcontextfilter, contextfunction, Template, Markup
from tarbell.hooks import register_hook

# @my_blueprint.route('/foo/')
# def foo():
    # site = g.current_site
#     return site.data['values']['headline']
# @eads

def build_dict(seq, key):
	return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))

def build_edu(list):
    return list.split('|')

def build_competition(dictlist,city, seat, name):
    expectedResult = [d for d in dictlist if d['city'] == city and d['seat']==seat and d['namekey']!=name ]
    return expectedResult

blueprint = Blueprint('add', __name__)

@blueprint.route('/<namekey>.html')
def person_detail(namekey):
    "Show details on a single id"
    # get context, also setting site.data
    site = g.current_site
    context = site.get_context()
    context.update({
        'PROJECT_PATH': site.path,
        'PATH': '/<namekey>.html'
    })
    info_by_name = build_dict(context['responses'], key="namekey")
    context['selected'] = info_by_name[namekey]
    context['selected']['education'] = build_edu(context['selected']['For_each_college_degree_you_have_list_the_degree_BA_PhD_the_field_of_study_and_the_college_or_university_Otherwise_please_provide_your_highest_level_of_education_and_the_school_you_attended'])
    context['selected']['competitors'] = build_competition(context['candidates'],context['selected']['In_which_municipality_are_you_running_for_office'],context['selected']['Which_seat_are_you_running_for'],context['selected']['namekey'])

    return render_template('_person.html', **context)

@blueprint.route('/')
@blueprint.route('/index.html')
def index():
    "Print the home page"
    # get context, also setting site.data
    site = g.current_site
    context = site.get_context()
    context.update({
        'PROJECT_PATH': site.path,
        'PATH': '/'
    })
    # for row in context.cities:
    #     context['cities'][row] = build_candidates(context['candidates'],row,seat)
    return render_template('index.html', **context)