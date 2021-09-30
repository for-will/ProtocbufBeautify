import sys, os

try:
	from formatter import format_proto
	from auto_number import number_lines
except (ImportError) as e:
	from .formatter import format_proto
	from .auto_number import number_lines

if __name__ == '__main__':
	# print(sys.argv)
	# help(os)
	# print(os.getcwd())
	
	source = sys.argv[1]
	dest = sys.argv[2]
	f = open(source,'r')
	text = f.read()
	f.close()

	# print(text)
	# print(sys.path.append('.'))

	text = format_proto(text, False, True)
	# print(text)
	f = open(dest, 'w')
	f.write(text)
	f.close()