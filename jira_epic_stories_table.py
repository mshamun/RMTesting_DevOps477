import functools
import pprint
from jira import JIRA
from tabulate import tabulate
import os
import sys
import warnings
import pandas as pd

warnings.filterwarnings('ignore',message='Unverified HTTPS request')

jira_base_url = os.environ.get("JIRA_CLOUD_URL")
username = os.environ.get("JIRA_USER_LOCAL")
apikey = os.environ.get("JIRA_TOKEN_LOCAL")

parent_epic_ticket = sys.argv[1]

class issue_fields(dict):
 
  # __init__ function
  def __init__(self):
    self = dict()
 
  # Function to add key:value
  def add(self, key, value):
    self[key] = value
 
 
 
def rgetattr(obj, attr, *args):
    def __getattr(obj, attr):
        return getattr(obj, attr, *args)
    return functools.reduce(__getattr, [obj] + attr.split('.'))

def get_field_data(field, name):
    return rgetattr(field, name, 'Not Populated')

def get_validation_fields(issue):
    migr_fields = issue.fields
    field_dict = {
        'services_list': get_field_data(migr_fields, 'customfield_10426'),
        'QA_Tester': get_field_data(migr_fields, 'customfield_10425.displayName')
    }
    valid_ticket = True
    jira_validation_results = {}
    for k, v in field_dict.items():
        if v is None:
            jira_validation_results[k] = 'Not Populated'
            valid_ticket = False
        # print(f'k: {k} v: {v}')
        fieldname = k
        attr = v
        if isinstance(attr, str):
            jira_validation_results[fieldname] = attr
        if isinstance(attr, list):
            count = 0
            keys = []
            for item in attr:
                fname = fieldname + '_' + str(count) + '_key'
                keys.append(item.key)
                jira_validation_results[fname] = item.key
                fname = fieldname + '_' + str(count) + '_url'
                jira_validation_results[fname] = item.self
                count = count + 1  
            jira_validation_results[fieldname] = ', '.join(keys)
    jira_validation_results['valid_ticket'] = valid_ticket
    return jira_validation_results
jira = JIRA(options={'server':jira_base_url, 'verify':False}, basic_auth=(username, apikey))

jira.search_issues('parentEpic={}'.format(parent_epic_ticket))

epic_stories=[]
for issue in jira.search_issues('parentEpic={}'.format(parent_epic_ticket)):
    epic_stories.append(issue.key)

epic_stories_details=[]
for story in epic_stories:
    migr_issue = jira.issue(story)
    story_default_details=issue_fields()
    story_default_details.add("JIRA ID",migr_issue.key)
    story_default_details.add("Summary",migr_issue.fields.summary)
    story_default_details.add("Status",migr_issue.fields.status)
    story_default_details.add("Assignee",migr_issue.fields.assignee)
    validation_results = get_validation_fields(migr_issue)
    validation_results.update(story_default_details)
    epic_stories_details.append(validation_results)

story_details_table=pd.DataFrame.from_dict(epic_stories_details)
story_details_jira_table=tabulate(story_details_table, headers=['S.No','Service_list','QA_Tester','Valid_ticket','JIRA_ID','Summary','Status','Assignee'],tablefmt="jira")
jira.add_comment(issue=parent_epic_ticket,body=story_details_jira_table)
