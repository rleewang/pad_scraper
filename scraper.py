from lxml import html
from lxml.etree import tostring
import requests
import re
import sys
from monster import Monster

print("Retrieving monsters from padx")
pad_url = "http://www.puzzledragonx.com/en/"
page = requests.get("http://www.puzzledragonx.com/en/monsterbook.asp")
tree = html.fromstring(page.content)

hrefs = tree.xpath('//td[@class="index"]/div[@class="indexframe"]/a')

monster_urls = {}
for href in hrefs:
	monster_id = int(re.search('[0-9]+', href.attrib['href']).group(0))
	monster_urls[monster_id] = pad_url + href.attrib['href']

### loop over every monster link
print("Parsing monster information")

monster_image_urls = []
max = 1
monsters = []
for mon_id in range(126,127):
	page = requests.get(monster_urls[mon_id])
	tree = html.fromstring(page.content)

	monster = Monster()

	### Get monster information from tables
	monster.id = mon_id
	monster.image = pad_url + tree.xpath('//div[@id="monster"]/a')[0].attrib['href']
	monster.avatar = pad_url + tree.xpath('//div[@id="content"]/div[@class="avatar"]/img')[0].attrib['src']

	### Table 1 info
	monster.en_name = tree.xpath('//div[@id="content"]/div[@class="name"]//text()')[0]
	monster.jp_name = tree.xpath('//div[@id="content"]//td[@class="data jap"]/text()')[0]
	monster.type = tree.xpath('//div[@id="content"]//td[@class="ptitle" and text()="Type:"]/../td[@class="data"]/a/text()')
	monster.element = tree.xpath('//div[@id="content"]//td[@class="ptitle" and text()="Element:"]/../td[@class="data"]/a/text()')
	monster.rarity = int(tree.xpath('count(//div[@id="content"]/div[@class="stars"]/img)'))
	monster.cost = int(tree.xpath('//div[@id="content"]//td[@class="ptitle" and text()="Cost:"]/../td[@class="data"]/a/text()')[0])
	monster.monsterpoints = int(tree.xpath('//div[@id="content"]//span[@title="Monster Point"]/../../td[@class="data"]/text()')[0])
	monster.expcurve = int(tree.xpath('//div[@id="compareprofile"]/table[@id="tablestat"]//td[contains(.,"Growth Curve")]/a/text()')[0].replace(',',''))
	monster.maxexp = int(re.search('[0-9]+',tree.xpath('//div[@id="compareprofile"]/table[@id="tablestat"]//td[contains(.,"Exp to max")]/text()')[0].replace(',','')).group(0))

	### Table 3 info
	monster.minlvl = int(tree.xpath('//div[@id="comparechart"]//td[text()="Level"]/following-sibling::td/text()')[0])
	monster.maxlvl = int(tree.xpath('//div[@id="comparechart"]//td[text()="Level"]/following-sibling::td/following-sibling::td/text()')[0])
	monster.basehp = int(tree.xpath('//div[@id="comparechart"]//td[text()="HP"]/following-sibling::td/text()')[0])
	monster.maxhp = int(tree.xpath('//div[@id="comparechart"]//td[text()="HP"]/following-sibling::td/following-sibling::td/text()')[0])
	monster.baseatk = int(tree.xpath('//div[@id="comparechart"]//td[text()="ATK"]/following-sibling::td/text()')[0])
	monster.maxatk = int(tree.xpath('//div[@id="comparechart"]//td[text()="ATK"]/following-sibling::td/following-sibling::td/text()')[0])
	monster.basercv = int(tree.xpath('//div[@id="comparechart"]//td[text()="RCV"]/following-sibling::td/text()')[0])
	monster.maxrcv = int(tree.xpath('//div[@id="comparechart"]//td[text()="RCV"]/following-sibling::td/following-sibling::td/text()')[0])
	### Weighted stats are HP/10 + ATK/5 + RCV/3
	monster.minweighted = monster.basehp/10 + monster.baseatk/5 + monster.basercv/3
	monster.maxweighted = monster.maxhp/10 + monster.maxatk/5 + monster.maxrcv/3

	### Table 4 info
	monster.active_skill = tree.xpath('//div[@id="content"]//td[@class="title value-normal nowrap" and text()="Active Skill:"]/following-sibling::td/a/span/text()')[0]
	monster.active_skill_description = tree.xpath('//div[@id="content"]//td[@class="title" and text()="Effects:"]/following-sibling::td/text()')[0]
	monster.active_skill_cooldown = tree.xpath('//div[@id="content"]//td[@class="title" and text()="Cool Down:"]/following-sibling::td/text()')[0]
	monster.same_active_skill = [re.search('[0-9]+', x.attrib['href']).group(0) for x in tree.xpath('//div[@id="content"]//td[@class="title" and text()="Same Skill:"]/following-sibling::td/a')]
	monster.leader_skill = tree.xpath('//div[@id="content"]//td[@class="title value-normal nowrap" and text()="Leader Skill:"]/following-sibling::td/a/span/text()')[0]
	monster.leader_skill_description = tree.xpath('//div[@id="content"]//td[@class="title" and text()="Effects:"]/following-sibling::td/text()')[1]
	monster.awakenings = [re.search('^(.*?)(?=\r\n)', x.attrib['title']).group(0) for x in tree.xpath('//div[@id="content"]//td[@class="awoken1"]/a/img')]

	### Grab evolutions
	### Grab the evolution and material rows
	evolution_rows = tree.xpath('//span[@id="evolve"]/following-sibling::table//td[@class="evolve" or @class="awokenevolve"]/..')
	material_rows = tree.xpath('//span[@id="evolve"]/following-sibling::table//td[@class="require" or @class="finalevolve nowrap" or @class="finalawokenevolve nowrap"]/..')

	print(str(evolution_rows))
	print(str(material_rows))

	evolution_tuples = []

	### Work through the first row to determine the base form for all subsequent evolution rows
	evo_row = evolution_rows[0]
	mat_row = material_rows[0]
	evolutions = evo_row.xpath('./td[@class="evolve" or @class="awokenevolve"]/div/div/text()')
	materials = [[re.search('[0-9]+', y.attrib['href']).group(0) for y in x.xpath('./a')] for x in mat_row.xpath('./td[@class="require" or @class="finalevolve nowrap" or @class="finalawokenevolve nowrap"]')]

	print(str(evolutions))
	print(str(materials))

	### Create tuples for each evolution pair in the first row and save the last evolution to be used as the base for the subsequent rows
	base = ""
	for i in range(len(evolutions)):
		if i == len(evolutions) - 1:
			base = evolutions[i]
		else:
			evolution_tuples.append((evolutions[i], materials[i], evolutions[i+1]))

	print(str(evolution_tuples))

	### Work through all subsequent rows using the previously determined base form for the first evolution pair in each row
	# for evo_row, mat_row in evolution_rows[1:], material_rows[1:]:
	# 	evolutions = evo_row


	# monster.info()
