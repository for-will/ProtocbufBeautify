import sys
import json

from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

try:
	from node import Node, NodeType
except (ImportError) as e:
	from .node import Node, NodeType

pb_grammar = Grammar(
	r"""
	pb_entries           = (muti_emptyline / emptyline / comment/ enum / message / other)*

	enum                 = edeclare ident lbrace ebody_seq rbrace
	edeclare             = none_or_ws "enum" must_ws_inline
	ebody_seq            = (muti_emptyline / emptyline / comment / eentry)*
	eentry               = none_or_ws ident equal number semi option_comm_line

	message              = mdeclare ident none_or_ws option_comm_line lbrace mbody_seq rbrace	
	mdeclare             = none_or_ws ("message"/"oneof") must_ws_inline
	mbody_seq            = (muti_emptyline / emptyline / comment / enum / message / mentry)*
	mentry               = none_or_ws option_mmodifier ident must_ws_inline ident equal number semi option_comm_line
	option_mmodifier     = mmodifier?
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
		return Node.NewEnum(visited_children[1], visited_children[3])

	def visit_ebody_seq(self, node, visited_children):
		return [x[0] for x in visited_children if x[0] is not None]

	def visit_ebody(self, node, visited_children):
		return visited_children[0]

	def visit_eentry(self, node, visited_children):
		n = len(visited_children)
		_, name, _, number, _, comment = visited_children
		return Node.NewEnumEntry(name, number, comment)

	# visit message
	def visit_message(self, node, visited_children):
		# mdeclare ident none_or_ws option_comm_line lbrace mbody_seq rbrace
		name = visited_children[1]
		comm = visited_children[3]
		entries = visited_children[5]
		oneof = visited_children[0]=='oneof'
		return Node.NewMessage(name, entries, comm, oneof)

	def visit_mdeclare(self, node, visited_children):
		return visited_children[1][0].text

	def visit_mbody_seq(self, node, visited_children):
		return [x[0] for x in visited_children if x[0] is not None]


	def visit_mentry(self, node, visited_children):
		n = len(visited_children)
		_, modifier, field_type, _, name, _, number, _, comment = visited_children
		return Node.NewMessageEntry(modifier, field_type, name, number, comment)

	def visit_option_mmodifier(self, node, visited_children):
		visited_children.append('')
		return visited_children[0]

	def visit_mmodifier(self, node, visited_children):
		return visited_children[1][0].text

	def visit_other(self, node, visited_children):
		return Node.NewText(node.text)

	# visit base element
	def visit_ident(self, node, visited_children):
		return node.text

	def visit_orphan_comm_line(self, node, visited_children):
		return Node.NewCommLine(visited_children[1])

	def visit_comment(self, node, visited_children):
		return visited_children[0]

	def visit_comm_line(self, node, visited_children):
		return node.text.strip()

	def visit_muti_emptyline(self, node, visited_children):
		n = len(visited_children)
		return Node.NewEmpty() if n > 1 else None

	def visit_option_comm_line(self, node, visited_children):
		n = len(visited_children)
		return visited_children[0] if n ==1 else ""

	def visit_number(self, node, visited_children):
		return int(node.text)


def format_enum(st, indent='', assign_num=False):
	entries = st.children
	if assign_num:
		st.renumber()

	maxl = max([len(x.name) for x in entries if x.type==NodeType.ENUM_ENTRY])
	fmt = "%%-%ds = %%d;" % (maxl)
	for x in entries:
		x.build_text(fmt)

	st.fmt_entry_comm(NodeType.ENUM_ENTRY)

	lines = ["enum {} {{".format(st.name)] 
	lines += st.children_lines()
	lines +=  ["}"]
	return "\n".join(lines)

def format_message(st, indent='', assign_num=False):
	entries = st.children

	if assign_num:
		st.renumber()

	modifier_len = max([len(x.modifier) for x in entries if x.type==NodeType.MESSAGE_ENTRY]+[0])
	name_len = max([len(x.name) for x in entries if x.type==NodeType.MESSAGE_ENTRY]+[0])
	type_len = max([len(x.field_type+x.modifier) for x in entries if x.type==NodeType.MESSAGE_ENTRY]+[0])
	if modifier_len>0: type_len = type_len+1
	fmt = "%%-%ds %%-%ds = %%d;" % (type_len, name_len)
	for x in entries:
		if x.type == NodeType.MESSAGE_ENTRY:
			x.build_text(fmt)
		elif x.type == NodeType.COMM_LINE:
			x.build_text()
		elif x.type == NodeType.ENUM:
			x._text = format_enum(x)
		elif x.type == NodeType.MESSAGE:
			x._text = format_message(x)

	st.fmt_entry_comm(NodeType.MESSAGE_ENTRY)
	
	lines = []
	if st.comm != '':
		lines.append(st.comm)

	typ = 'oneof' if st.oneof else 'message'
	lines.append("{} {} {{".format(typ, st.name))
	lines += st.children_lines()
	lines +=  ["}"]
	return "\n".join(lines)
	
def format_proto(source, assign_num=False):
	ast = pb_grammar.parse(source)
	pbv = ProtobufVisitor()
	out_put = pbv.visit(ast)
	
	blocks = []
	for e in out_put:
		t = e.type
		if t == NodeType.MESSAGE:
			blocks.append(format_message(e, '', assign_num))
		elif t == NodeType.ENUM:
			blocks.append(format_enum(e, '', assign_num))
		elif t == NodeType.EMPTY:
			blocks.append('')
		elif t == NodeType.COMM_LINE:
			blocks.append(e.comm)
		elif t == NodeType.TEXT:
			blocks.append(e.text)
		else:
			print(t)

	return "\n".join(blocks)


text = """
//

message TestMessage {
    enum ReturnCode {
        Ok = 10;
        Failed = 11;
    }

    message LogInfo {
        int64  InstallTime = 1;
        string Ip = 2;
        string DeviceModel = 3;
        string OsName = 4;
    }

    ReturnCode return_code = 1;
    LogInfo log_info = 2;
    repeated LogInfo logs = 3;
    string DeviceModel = 4;
    repeated string  OsName = 5;
}
"""

if __name__ == '__main__':
	# help(str.rstrip)
	ast = pb_grammar.parse(text)
	pbv = ProtobufVisitor()
	out_put = pbv.visit(ast)
	print(out_put[2])
	# print(json.dumps(out_put, indent='\t'))

	print(format_proto(text, True))