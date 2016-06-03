import os
import requests
import requests.auth
import unicodedata as uni

from praw import Reddit

#The names corresponding to the 2-letter unicode category codes
category_names = {
	'Cc': 'Other, control',
	'Cf': 'Other, format',
	'Cn': 'Other, not assigned',
	'Co': 'Other, private use',
	'Cs': 'Other, surrogate',
	'Ll': 'Letter, lowercase',
	'Lm': 'Letter, modifier',
	'Lo': 'Letter, other',
	'Lt': 'Letter, titlecase',
	'Lu': 'Letter, uppercase',
	'Mc': 'Mark, spacing combining',
	'Me': 'Mark, enclosing',
	'Mn': 'Mark, nonspacing',
	'Nd': 'Number, decimal digit',
	'Nl': 'Number, letter',
	'No': 'Number, other',
	'Pc': 'Punctuation, connector',
	'Pd': 'Punctuation, dash',
	'Pe': 'Punctuation, close',
	'Pf': 'Punctuation, final quote',
	'Pi': 'Punctuation, initial quote',
	'Po': 'Punctuation, other',
	'Ps': 'Punctuation, open',
	'Sc': 'Symbol, currency',
	'Sk': 'Symbol, modifier',
	'Sm': 'Symbol, math',
	'So': 'Symbol, other',
	'Zl': 'Separator, line',
	'Zp': 'Separator, paragraph',
	'Zs': 'Separator, space'
}

#Returns the name of a character
def get_name(c):
	if c == '\n':
		return 'LINE FEED' #Not in unicodedata for some reason??
	else:
		return uni.name(c, 'UNKNOWN')

#Escapes a character, so it'll appear and not mess up the formatting
def escape(c):
	if c in r'\!#&()*+-./:<>[\]^_`{|}~':
		return '\\' + c #May not appear in comment due to markdown
	elif c == '\n':
		return ' ' #Messes up table formatting otherwise
	else:
		return c
	
#Returns a list of comments which contain the table of information
def make_output(str):
	TABLE_HEADING = 'Character|Name|Category\n---------|----|--------\n'
	TABLE_POSTSCRIPT = '^I ^am ^a ^bot, ^contact ^/u/sirgroovy ^to ^leave ^feedback ^or ^report ^a ^bug'
	messages = [TABLE_HEADING]
	for c in str:
		new_row = escape(c) + '|' + get_name(c) + '|' + category_names[uni.category(c)] + '\n'
		if MAX_MESSAGE_LENGTH <= len(new_row) + len(TABLE_HEADING) + \
		                         len(TABLE_POSTSCRIPT) + len(messages[-1]):
			messages[-1] += TABLE_POSTSCRIPT
			messages.append(TABLE_HEADING)
		messages[-1] += new_row
	messages[-1] += TABLE_POSTSCRIPT
	return messages
	
#Uses the given information to return a logged-in instance
def login(username, password, user_agent, id, secret, scope={'identity'}):
	reddit = Reddit(user_agent)
	client_auth = requests.auth.HTTPBasicAuth(id, secret)
	post_data = {'grant_type': 'password',
	             'username': username,
	             'password': password}
	headers = {'User-agent': user_agent}
	response = requests.post('https://www.reddit.com/api/v1/access_token',
	                         auth=client_auth, data=post_data, headers=headers)
	cred = response.json()
	reddit.set_oauth_app_info(client_id=id, client_secret=secret, redirect_uri=URI)
	reddit.set_access_credentials(scope=scope, access_token=cred['access_token'])
	return reddit

REDDIT_USERNAME = os.getenv('USERNAME')
REDDIT_PASSWORD = os.getenv('PASSWORD')
REDDIT_ID = os.getenv('REDDIT_ID')
REDDIT_SECRET = os.getenv('REDDIT_SECRET')
REDDIT_USER_AGENT = 'A bot written by /u/sirgroovy that, when summoned, tabulates \
                     information about each character of a comment or submission'
MAX_MESSAGE_LENGTH = 10000
URI = 'http://127.0.0.1:65010/authorize_callback'

reddit = login(REDDIT_USERNAME, REDDIT_PASSWORD, REDDIT_USER_AGENT,
               REDDIT_ID, REDDIT_SECRET, {'identity', 'privatemessages', 'submit'})

for mention in reddit.get_mentions():
	already_responded = False
	for reply in mention.replies:
		if reply.author.name == REDDIT_USERNAME:
			already_responded = True
			break
			
	if already_responded:
		#If we find that already responded to this username mention, we can
		#just exit out of the script
		break
	
	if mention.is_root:
		if mention.submission.is_self:
			source_text = mention.submission.selftext
		else:
			source_text = mention.submission.title
	else:
		source_comment = reddit.get_info(thing_id=mention.parent_id)
		if source_comment.author.name == REDDIT_USERNAME:
			mention.reply("I think you already know quite well what that says.")
			continue
		else:
			source_text = source_comment.body
	
	comments = make_output(source_text)
	
	reply_to = mention
	while comments:
		reply_to = reply_to.reply(comments[0])
		comments.pop(0)
