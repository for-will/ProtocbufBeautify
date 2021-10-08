import sys, os

try:
	from formatter import format_proto
except (ImportError) as e:
	from .formatter import format_proto


def trans(source, dest):
	f = open(source,'r')
	text = f.read()
	f.close()

	text = format_proto(text, False, True)
	f = open(dest, 'w')
	f.write(text)
	f.close()

if __name__ == '__main__':
	if len(sys.argv)==3:		
		source = sys.argv[1]
		dest = sys.argv[2]
		trans(source, dest)
		