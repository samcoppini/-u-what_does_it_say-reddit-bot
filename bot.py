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
	if c in r'\!#&()*+-./:<>[\]^_`{}~':
		return '\\' + c #May not appear in comment due to markdown
	elif c == '\n':
		return ' ' #Messes up table formatting otherwise
	elif c == '|':
		return '&#124;' # Reddit doesn't escape vertical lines in tables properly
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

REDDIT_USERNAME = os.getenv('USERNAME')
REDDIT_PASSWORD = os.getenv('PASSWORD')
REDDIT_ID = os.getenv('REDDIT_ID')
REDDIT_SECRET = os.getenv('REDDIT_SECRET')
REDDIT_USER_AGENT = 'A bot written by /u/sirgroovy that, when summoned, tabulates \
                     information about each character of a comment or submission'
MAX_MESSAGE_LENGTH = 10000
URI = 'http://127.0.0.1:65010/authorize_callback'

reddit = Reddit(client_id=REDDIT_ID,
                client_secret=REDDIT_SECRET,
                user_agent=REDDIT_USER_AGENT,
                username=REDDIT_USERNAME,
                password=REDDIT_PASSWORD)

for mention in reddit.inbox.mentions():
	if mention.author.name == "AutoModerator":
		# Prevent abuse from /r/doctorbutts, a subreddit that set their automod
		# to automatically summon /u/what_does_it_say in response to every
		# single comment on that subreddit
		continue

	# Retrieve replies for the comment
	mention.refresh()

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
		if mention.submission.is_self and len(mention.submission.selftext) > 0:
			source_text = mention.submission.selftext
		else:
			source_text = mention.submission.title
	else:
		source_text = mention.parent().body

	comments = make_output(source_text)

	reply_to = mention
	while comments:
		reply_to = reply_to.reply(comments[0])
		comments.pop(0)
