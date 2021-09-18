import sys
import json

# sys.path.append("six")

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

pb_grammar = Grammar(
	r"""
	pb_entries           = (muti_emptyline / emptyline / comment/ enum / message / other)*

	enum                 = edeclare ident lbrace ebody_seq rbrace
	edeclare             = none_or_ws "enum" must_ws_inline
	ebody_seq            = (muti_emptyline / emptyline / comment / eentry)*
	eentry               = none_or_ws ident equal number semi option_comm_line

	message              = mdeclare ident none_or_ws option_comm_line lbrace mbody_seq rbrace	
	mdeclare             = none_or_ws "message" must_ws_inline
	mbody_seq            = (muti_emptyline / emptyline / comment / enum / mentry)*
	mentry               = none_or_ws mmodifier ident must_ws_inline ident equal number semi option_comm_line
	mmodifier            = none_or_ws ("optional"/"repeated"/"required") must_ws_inline

	other                = ~r".*"

	lbrace               = any_ws punctuation_lbrace
	rbrace               = none_or_ws punctuation_rbrace	
	equal                = none_or_ws punctuation_equal none_or_ws
	semi                 = none_or_ws punctuation_semi none_or_ws	

	option_comm_line     = comm_line?
	comment              = orphan_comm_line / comm_line / comm_block
	orphan_comm_line     = ws_seq comm_line
	comm_line            = ~r"//.*"
	comm_block           = comm_block_start comm_block_content comm_block_end
	comm_block_start     = "/*"
	comm_block_content   = (emptyline / comm_block_text)*
	comm_block_text      = (!"*/" ~r".")+
	comm_block_end       = "*/"

	ident                = ~r"[a-zA-Z_][a-zA-Z0-9_]*"
	number               = ~r"\d+"

	none_or_ws           = ~r"[ \t]*"
	must_ws              = ~r"\s+"
	must_ws_inline       = ~r"[ \t]+"
	muti_emptyline       = emptyline+
	emptyline            = ~r"[ \t]*[\r\n]"
	ws                   = ~r"[ \t]"
	ws_seq               = ~r"[ \t]*"
	any_ws               = ~r"\s*"

	punctuation_lbrace   = "{"
	punctuation_rbrace   = "}"
	punctuation_equal    = "="
	punctuation_semi     = ";"
	"""
)

class ProtobufVisitor(NodeVisitor):
	def generic_visit(self, node, visited_children):
		return visited_children or node

	def visit_pb_entries(self, node, visited_children):
		return [x[0] for x in visited_children if x[0] is not None]

	def visit_enum(self, node, visited_children):
		return {"type":"enum", "name":visited_children[1], "entries":visited_children[3]}

	def visit_ebody_seq(self, node, visited_children):
		# print(visited_children)
		return [x[0] for x in visited_children if x[0] is not None]

	def visit_ebody(self, node, visited_children):
		return visited_children[0]

	def visit_eentry(self, node, visited_children):
		n = len(visited_children)
		_, name, _, number, _, comment = visited_children
		entry = {"type":"enum_entry", "name":name, "number":number, "comm":comment}
		return entry

	# visit message
	def visit_message(self, node, visited_children):
		# mdeclare ident none_or_ws option_comm_line lbrace mbody_seq rbrace
		return {
		"type":"message", 
		"name":visited_children[1], 
		"comm":visited_children[3],
		"entries":visited_children[5]
		}

	def visit_mbody_seq(self, node, visited_children):
		return [x[0] for x in visited_children if x[0] is not None]


	def visit_mentry(self, node, visited_children):
		n = len(visited_children)
		_, modifier, field_type, _, name, _, number, _, comment = visited_children
		entry = {
			"type":"message_entry", 
			"modifier":modifier, 
			"field_type":field_type,
			"name":name, 
			"number":number, 
			"comm":comment
		}
		return entry

	def visit_mmodifier(self, node, visited_children):
		return visited_children[1][0].text

	def visit_other(self, node, visited_children):
		# print (node.text)
		return {"type":"text", "text":node.text}

	# visit base element
	def visit_ident(self, node, visited_children):
		return node.text

	def visit_orphan_comm_line(self, node, visited_children):
		return {"type":"comm_line", "comm_line": visited_children[1]}

	def visit_comment(self, node, visited_children):
		# print(node, visited_children)
		return visited_children[0]

	def visit_comm_line(self, node, visited_children):
		return node.text.strip()

	def visit_muti_emptyline(self, node, visited_children):
		n = len(visited_children)
		return {"type":"empty", "text":""} if n > 1 else None

	def visit_option_comm_line(self, node, visited_children):
		n = len(visited_children)
		return visited_children[0] if n ==1 else ""

	def visit_number(self, node, visited_children):
		return int(node.text)



def format_enum(st, indent=''):
	entries = st['entries']
	maxl = max([len(x['name']) for x in entries if x['type']=='enum_entry'])
	fmt = "\t%%-%ds = %%d;" % (maxl)
	for x in st['entries']:
		if x['type'] == 'enum_entry':
			name = x['name']
			number = x['number']
			x['text'] = fmt % (name, number)
		elif x['type'] == 'comm_line':
			x['text'] = '\t' + x['comm_line']


	maxl = max([len(x['text']) for x in entries if x['type']=='enum_entry'])
	fmt = "%%-%ds %%s" % (maxl)
	for x in entries:
		if x['type'] == 'enum_entry':
			text = fmt % (x['text'], x['comm'])
			x['text'] = text.rstrip()

	lines = ["enum {} {{".format(st['name'])] + [x['text'] for x in entries] +  ["}"]
	return "\n".join([indent+x for x in lines])

def format_message(st, indent=''):
	entries = st['entries']
	name_len = max([len(x['name']) for x in entries if x['type']=='message_entry']+[0])
	type_len = max([len(x['field_type']) for x in entries if x['type']=='message_entry']+[0])
	fmt = "\t%%s %%-%ds %%-%ds = %%d;" % (type_len, name_len)
	for x in st['entries']:
		if x['type'] == 'message_entry':
			modifier = x['modifier']
			name = x['name']
			field_type = x['field_type']
			number = x['number']
			x['text'] = fmt % (modifier, field_type, name, number)
		elif x['type'] == 'comm_line':
			x['text'] = '\t' + x['comm_line']
		elif x['type'] == 'enum':
			x['text'] = format_enum(x, indent+'\t')


	maxl = max([len(x['text']) for x in entries if x['type']=='message_entry']+[0])
	fmt = "%%-%ds %%s" % (maxl)
	for x in entries:
		if x['type'] == 'message_entry':
			text = fmt % (x['text'], x['comm'])
			x['text'] = text.rstrip() 

	lines = ["message {} {{".format(st['name'])]
	if st['comm'] != "":
		lines.insert(0, st['comm'])
	lines += [x['text'] for x in entries] +  ["}"]
	return "\n".join(lines)

	
def format_proto(source):
	ast = pb_grammar.parse(source)
	pbv = ProtobufVisitor()
	out_put = pbv.visit(ast)
	
	# print(json.dumps(out_put, ensure_ascii=False, indent='\t'))
	blocks = []
	for e in out_put:
		t = e['type']
		if t == 'message':
			# print(format_message(e))
			# print(e)
			blocks.append(format_message(e))
		elif t == 'enum':
			blocks.append(format_enum(e))
		elif t == 'empty':
			blocks.append("")
		elif t == 'comm_line':
			# print(e)
			blocks.append(e['comm_line'])
		elif t == 'text':
			blocks.append(e['text'])
		else:
			print(t)

	return "\n".join(blocks)


text = """message LootMission {
    enum Status {
        Processing   = 0;
        Finished = 1;
        Rewarded = 2;
    }

    optional int32  Id            = 1; 
    optional Status State        = 2; 
    optional int32  Progress      = 3; // 当前完成数量
    optional int32  CompletedTime = 4; 
}"""

if __name__ == '__main__':
	# help(str.rstrip)
	ast = pb_grammar.parse(text)
	pbv = ProtobufVisitor()
	out_put = pbv.visit(ast)
	print(json.dumps(out_put, indent='\t'))

	print(format_proto(text))