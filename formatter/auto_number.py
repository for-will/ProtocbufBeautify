from parsimonious import NodeVisitor
from parsimonious import Grammar
	

pb_grammar = Grammar(
	r"""
	lines                = (muti_emptyline / emptyline / comment / equal_line / other)*

	equal_line           = equal_left "=" optional_number after_number

	equal_left           = ~r"[^=\n]+"
	after_number         = ~r"[^\n]*"
	other                = ~r".*"
	optional_number      = ~r"[ \t]*\d*"

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

	"""
)

class ProtobufVisitor(NodeVisitor):
	def generic_visit(self, node, visited_children):
		return visited_children or node

	def visit_lines(self, node, visited_children):
		return [x[0] for x in visited_children if x[0] is not None]

	def visit_equal_line(self, node, visited_children):
		
		try:
			n = int(visited_children[2].text)
		except Exception as e:
			n = 1
		# print(n)
		return {
			'type':'number_line', 
			'left':visited_children[0],
			'number':n,
			'right':visited_children[3]
			}

	def visit_equal_left(self, node, visited_children):
		return node.text

	def visit_after_number(self, node, visited_children):
		return node.text

	def visit_other(self, node, visited_children):
		# print (node.text)
		return {"type":"text", "text":node.text}

	# visit base element
	def visit_ident(self, node, visited_children):
		return node.text

	def visit_orphan_comm_line(self, node, visited_children):
		return {"type":"comm_line", "comm_line": node.text}

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


def number_lines(s):
	ast = pb_grammar.parse(s)
	pbv = ProtobufVisitor()
	structure = pbv.visit(ast)
	return assign_line_number(structure)
	# return ''

def assign_line_number(lines):
	idx = -1
	for l in lines:
		if l['type'] == 'number_line':
			if idx == -1:
				idx = l['number']
			l['text'] = l['left'] + "= " + str(idx) + l['right']
			idx = idx+1
		if l['type'] == 'comm_line':
			l['text'] = l['comm_line']

	lines =  [x['text'] for x in lines] 
	return "\n".join(lines)


text = """message DeviceInfo {
    optional string DeviceModel  = 20;  
    // 设备型号
    optional int32  DeviceHeight        =  

    optional int32  DeviceWidth  = ;  //
    optional string OsName       = 4;  // 操作系统
    optional string OsVer        = 5;  // 操作系统版本
   
}
message SdkLoginRs {
    optional ReturnCode ReturnCode      = 10;
    //optional int32      Code            = 2;
    optional int32      SubCode         = 3;
    optional string     UnisdkLoginJson = 4;
    optional string     LoginSessionId  = 5; // 游戏服务器返回的LoginSessionId，用于断线重连
}"""

if __name__ == '__main__':
	# help(str.rstrip)
	ast = pb_grammar.parse(text)
	pbv = ProtobufVisitor()
	out_put = pbv.visit(ast)
	# for l in out_put:
	# 	print(l)
	print(json.dumps(out_put, indent='\t'))
	print(number_lines(text))

	# print(format_proto(text, True))