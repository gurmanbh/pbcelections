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
from flask_frozen import Freezer
from jinja2 import evalcontextfilter, contextfunction, Template, Markup
from tarbell.hooks import register_hook

def build_dict(seq, key):
	return dict((d[key], dict(d, index=index)) for (index, d) in enumerate(seq))

def build_edu(list):
    return list.split('|')

def build_social(links):
    linklist = links.split('|')
    linkobjs = []
    for link in linklist:
        obj = {}
        obj['link']=link.strip()
        if 'facebook' in link:
            obj['type'] = 'facebook-square'
        elif 'twitter' in link:
            obj['type'] = 'twitter-square'
        else:
            obj['type'] = 'globe'
        linkobjs.append(obj.copy())
    return linkobjs


def build_competition(dictlist,city, seat, name):
    expectedResult = [d for d in dictlist if d['city'] == city and d['seat']==seat and d['namekey']!=name ]
    return expectedResult

def build_questions(list,city):
    masterdict = {}
    for item in list:
        city = item["city"]
        if city not in masterdict:
            masterdict[city] = []
        masterdict[city].append(item.copy())
    return masterdict

def buildcityseatlist(list):
    masterdict = {}
    for item in list:
        city = item["city"]
        namekey = item["namekey"]
        seat = item["seat"]
        if city not in masterdict:
            masterdict[city] = {}
        if seat not in masterdict[city]:
            masterdict[city][seat] = []
        temp = {}
        temp["status"] = item["status"]
        temp["name"] = item["name"]
        temp["cleanname"] = item["cleanname"]
        temp["city"] = item["city"]
        temp["namekey"] = item["namekey"]
        masterdict[city][seat].append(temp.copy())
    return masterdict

def getraces(selected):
    obj = []
    if 'List_elected_offices_you_have_held_and_date_ranges_for_each_office' in selected:
        wonraces = selected['List_elected_offices_you_have_held_and_date_ranges_for_each_office'].split('|')
        for race in wonraces:
            check = {}
            if "(" in race:
                check['race'] = race.split(' (')[0]
                if "-" in race:
                    check['startyear'] = race.split(' (')[1].split('-')[0].strip()
                    check['endyear'] = check['orderyear'] = race.split(' (')[1].split('-')[1].replace (")", "").strip()
                else:
                    check['startyear'] = race.split(' (')[1].replace (")", "").strip()
                    check['endyear'] = check['orderyear'] = check['startyear']
            check['type'] = 'won'
            check['racestring'] = race
            obj.append(check.copy())
    if 'List_positions_and_years_you_unsuccessfully_ran_for_office' in selected:
        lostraces = selected['List_positions_and_years_you_unsuccessfully_ran_for_office'].split('|')
        for race in lostraces:
            check = {}
            if "(" in race:
                check['race'] = race.split(' (')[0]
                check['startyear'] = race.split(' (')[1].replace (")", "").strip()
                check['endyear'] = check['startyear']
                check['orderyear'] = check['endyear']
            check['type'] = 'lost'
            check['racestring'] = race
            obj.append(check.copy())
    # sort by the order year
    newlist = sorted(obj, key=lambda k: k['orderyear'])
    # return the reversed list
    return newlist[::-1]

blueprint = Blueprint('add', __name__)

@blueprint.route('/candidate/<namekey>.html')
def persondetail(namekey):
    "Show details on a single id"
    # get context, also setting site.data
    site = g.current_site
    context = site.get_context()
    context.update({
        'PROJECT_PATH': site.path,
        'PATH': '/candidate/<namekey>.html',
        'ROOT_URL': 'http://apps.mypalmbeachpost.com/kyc',
    })
    info_by_name = build_dict(context['responses'], key="namekey")
    context['info_by_name'] = info_by_name
    context['question_types'] = build_dict(context['questionlist'], key="question")
    status_by_name = build_dict(context['candidates'], key="namekey")
    context['selectedstatus'] = status_by_name[namekey]
    if context['selectedstatus']['status'] == 'received':
        context['selected'] = info_by_name[namekey]
        context['selected']['previousraces'] = getraces(context['selected'])
        if 'For_each_college_degree_you_have_list_the_degree_BA_PhD_the_field_of_study_and_the_college_or_university_Otherwise_please_provide_your_highest_level_of_education_and_the_school_you_attended' in context['selected']:
            context['selected']['education'] = build_edu(context['selected']['For_each_college_degree_you_have_list_the_degree_BA_PhD_the_field_of_study_and_the_college_or_university_Otherwise_please_provide_your_highest_level_of_education_and_the_school_you_attended'])
        else:
            context['selected']['education']=[]
        if 'List_municipal_committees_youve_been_appointed_to_and_currently_serve_on' in context['selected']:
            context['selected']['otherpolex'] = build_edu(context['selected']['List_municipal_committees_youve_been_appointed_to_and_currently_serve_on'])
        else:
            context['selected']['otherpolex']=[]
        if 'Any_social_or_website_addresses_youd_like_to_share' in context['selected']:
            context['selected']['social'] = build_social(context['selected']['Any_social_or_website_addresses_youd_like_to_share'])
    if context['selectedstatus']['status'] == 'pending':
        context['selected'] = {}
    context['selected']['questionlist'] = build_questions(context['questionlist'],context['selectedstatus']['city'])[context['selectedstatus']['city']]
    context['selected']['competitors'] = build_competition(context['candidates'],context['selectedstatus']['city'],context['selectedstatus']['seat'],context['selectedstatus']['namekey'])
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
        'PATH': '/',
        'ROOT_URL': 'http://apps.mypalmbeachpost.com/kyc'
    })
    context['cityseatlist'] = buildcityseatlist(context['candidates'])
    return render_template('index.html', **context)