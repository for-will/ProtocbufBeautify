import json

# from enum import Enum

class Node(object):
	
	def __init__(self, typ):
		self._type = typ
		self._text = ''
		self._childs = []

	def NewEnum(name, children):
		node = Node(NodeType.ENUM)
		node._name = name
		node._childs = children
		return node

	def NewEnumEntry(name, number, comm=''):
		node = Node(NodeType.ENUM_ENTRY)
		node._name = name
		node._number = number
		node._comm = comm
		return node

	def NewMessage(name, children, comm='', oneof=False):
		node = Node(NodeType.MESSAGE)
		node._name = name
		node._childs = children
		node._comm = comm
		node._oneof = oneof
		return node

	def NewMessageEntry(modifier, field_type, name, number, comm):
		node = Node(NodeType.MESSAGE_ENTRY)
		node._modifier = modifier
		node._field_type = field_type
		node._name = name
		node._number = number
		node._comm = comm
		return node

	def NewText(text):
		node = Node(NodeType.TEXT)
		node._text = text
		return node

	def NewCommLine(comm):
		node = Node(NodeType.COMM_LINE)
		node._comm = comm
		return node

	def NewEmpty():
		return Node(NodeType.EMPTY)

	@property
	def text(self):
		return self._text

	@property
	def type(self):		
		return self._type

	@property
	def name(self):
		return self._name

	def set_number(self, v):
		self._number = v

	@property
	def number(self):
		return self._number

	@property
	def modifier(self):
		return self._modifier

	@property
	def field_type(self):
		return self._field_type

	@property
	def comm(self):
		return self._comm

	@property
	def oneof(self):
		return self._oneof

	@property
	def children(self):
		return self._childs

	@property
	def dict(self):
		d = {}
		for kv in self.__dict__.items():
			k = kv[0].lstrip('_')
			d[k] = kv[1]
		d['type'] = d['type'].name
		d['childs'] = [x.dict for x in d['childs']]
		return d

	def build_text(self, fmt=''):
		if self.type == NodeType.ENUM_ENTRY:
			self._text = fmt % (self.name, self.number)
		elif self.type == NodeType.MESSAGE_ENTRY:
			modifier = self.modifier
			name = self.name
			field_type = self.field_type
			number = self.number
			if modifier != '': field_type = modifier + ' ' + field_type
			self._text = fmt % (field_type, name, number)
		elif self.type == NodeType.COMM_LINE:
			self._text = self._comm

	def fmt_entry_comm(self, typ):
		maxl = self.max_child_len(typ)
		fmt = "%%-%ds %%s" % (maxl)
		for e in self.children:
			if e.type == typ:
				text = fmt %(e._text, e._comm)
				e._text = text.rstrip()

	def max_child_len(self, typ):
		return max([len(x.text) for x in self.children if x.type==typ]+[0])

	def children_lines(self):
		if len(self.children) != 0:
			content = '\n'.join([x.text for x in self.children])
			return ['\t'+l if l!='' else '' for l in content.split('\n')]
		else:
			return []

	def to_json(self):
		return json.dumps(self.dict, indent='\t')

	def __str__(self):
		return self.to_json()

	
class NodeType():
	EMPTY         = 0
	MESSAGE       = 1
	MESSAGE_ENTRY = 2
	ENUM          = 3
	ENUM_ENTRY    = 4
	COMM_LINE     = 5
	TEXT          = 6

	@property
	def name(self):
		return 'aaa'

	@property
	def TEXT():
		return 11


def main():
	# n = Node(Node.MESSAGE)
	# n = Node.NewEnum('ReturnCode', [])
	# n = Node.NewEnumEntry('Ok', 3, '//okkk')
	# print(n)
	a = NodeType.TEXT
	# print(help(Enum))

if __name__ == '__main__':
	main()