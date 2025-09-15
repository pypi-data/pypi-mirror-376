import click, os, json, time
from rich.console import Console

console = Console()
print = console.print

class QTYPE:
	ZERO_TO_ONE = 0
	HIGHER_BETTER = 1
	LOWER_BETTER = 2

class Store:
	savepath: str
	data: dict
	first_time: bool

	def __init__(self):
		home = os.path.expanduser("~")
		savedir = os.path.join(home, '.baseline')
		if not os.path.exists(savedir): os.mkdir(savedir)

		self.savepath = os.path.join(savedir, 'save.json')
		if not os.path.exists(self.savepath):
			with open(self.savepath, 'w') as f:
				f.write("{}")
				self.first_time = True
		else:
			self.first_time = False

		with open(self.savepath, 'r') as f:
			self.data = json.load(f)

	def can_audit(self):
		if self.data.get('last_audit') is None: return True

		last_audit = time.localtime(self.data['last_audit'])
		current_time = time.localtime()
		return last_audit.tm_mday != current_time.tm_mday and current_time > last_audit

	def start_journal(self):
		self.data['last_audit'] = int(time.time())
		if self.data.get('journal') is None:
			self.data['journal'] = []
		self.data['journal'].append(dict(date=self.data['last_audit']))

	def end_journal(self, field_response_map):
		audit_time = self.data['last_audit']
		journal = self.data['journal'][-1]
		for k, v in field_response_map.items():
			journal[k] = v
		self.data['journal'][-1] = journal

	def fields(self):
		if self.data.get('fields') is None: self.data['fields'] = {}
		for k, f in self.data['fields'].items():
			yield k, f

	def add_field(self, name, question, qtype):
		"""
		name - The id of the field
		question - The question to ask the user everyday
		qtype - One of: QTYPE
		"""
		if self.data.get('fields') is None: self.data['fields'] = {}
		field = self.data['fields'].get(name, {})
		field['question'] = question
		field['qtype'] = qtype
		self.data['fields'][name] = field
		self.save()
		return self.data['fields'][name]

	def save(self):
		with open(self.savepath, 'w') as f:
			json.dump(self.data, f)

store = Store()
def audit(store: Store):
	if store.can_audit():
		print("[*] [yellow]Starting journal[/yellow]")
		store.start_journal()
		journal_map = dict()

		print("\\[i] [cyan]Baseline.[/cyan]\n")
		for i, (k, field) in enumerate(store.fields()):
			print(f"[green]{i}[/green] - {field['question']}")
			response = console.input(">> ")
			if field['qtype'] == QTYPE.ZERO_TO_ONE:
				journal_map[k] = bool(response)
			elif field['qtype'] == QTYPE.HIGHER_BETTER:
				journal_map[k] = int(response)
			elif field['qtype'] == QTYPE.LOWER_BETTER:
				journal_map[k] = int(response)
			else:
				raise Exception(f"Journal field type {field['qtype']} is invalid")

		store.end_journal(journal_map)
		store.save()
		print()
		print("\\[i] [green]Journal ended[/green]")

@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
	if ctx.invoked_subcommand is None:
		console.print(f"Hello {os.environ['USER']}")
		audit(store)

@main.command()
@click.argument('name')
@click.argument('question')
@click.argument('qtype', type=int)
def add(name, question, qtype):
	print(store.add_field(name, question, qtype))

if __name__ == "__main__":
	main()
