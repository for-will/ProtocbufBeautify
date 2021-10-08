import json

# from enum import Enum

class Node(object):
	
	def __init__(self, typ):
		self._type = typ
		self._text = ''
		self._childs = []

	def NewEnum(name, children, proto3=False):
		node = Node(NodeType.ENUM)
		node._name = name
		node._childs = children
		if proto3:
			if node.min_number(NodeType.ENUM_ENTRY)!=0:
				node._childs.insert(0, Node.NewEnumEntry(name+'_ZERO', 0))
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

	def NewMessageEntry(modifier, field_type, name, number, comm, proto3=False):
		node = Node(NodeType.MESSAGE_ENTRY)
		node._modifier = modifier
		node._field_type = field_type
		node._name = name
		node._number = number
		node._comm = comm
		if proto3 and modifier != 'repeated':
			node._modifier = ''
		return node

	def NewText(text, proto3=False):
		node = Node(NodeType.TEXT)
		if proto3 and text == 'syntax="proto2";':
			node._text = 'syntax="proto3";'
		else:
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

	def renumber(self):
		idx = 1
		for e in self.children:
			if e.type == NodeType.MESSAGE_ENTRY or e.type == NodeType.ENUM_ENTRY:
				e.set_number(idx)
				idx += 1

	def min_number(self, typ):
		l = [x.number for x in self.children if x.type==typ]
		if len(l)==0: return -1
		return min(l)

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


class EnumVal():
	def __init__(self, name, val):
		self._name = name
		self._val = val

	@property
	def name(self):
		return self._name

	@property
	def val(self):
		return self._val

	def __str__(self):
		return self.name

def build_enum(cls):
	for attr in dir(cls):
		v = getattr(cls, attr)
		if type(v) == int:
			setattr(cls, attr, EnumVal(attr, v))

build_enum(NodeType)

def main():
	build_enum(NodeType)
	# n = Node(Node.MESSAGE)
	# n = Node.NewEnum('ReturnCode', [])
	n = Node.NewEnumEntry('Ok', 3, '//okkk')
	print(n)

if __name__ == '__main__':
	main()