import sublime
import sublime_plugin

from package_control import sys_path
# from package_control.unicode import unicode_from_os
# from package_control.console_write import console_write

import os
import sys

try:
	from six import text_type
	from parsimonious import NodeVisitor
	
except (ImportError) as e:
	dep_paths = sys_path.generate_dependency_paths(u'ProtocbufBeautify')
	pkg_path = dep_paths['all'].rstrip('all')
	sys_path.add(pkg_path)
	from six import text_type
	from parsimonious import NodeVisitor
	
try:
	from formatter import format_proto
	from auto_number import number_lines
except (ImportError) as e:
	from .formatter import format_proto
	from .auto_number import number_lines


class PbBeautifyCommand(sublime_plugin.TextCommand):
	def run(self, edit, reassign_num=False):
		# self.view.insert(edit, 0, "Hello, World!\n")
		# self.view.insert(edit, 0, "Hello, World!")
		for region in self.view.sel():
			if region.a != region.b:
				sel_content = self.view.substr(region)
				formated = format_proto(sel_content, True)
				self.view.replace(edit, region, formated)
				return
	
		self.reindent_protoc(edit, reassign_num)
		for region in self.view.sel():
			self.view.show(region.a, True, True)
			self.view.show_at_center(region.a)
			break	

	def reindent_protoc(self, edit, reassign_num):
		region = sublime.Region(0, self.view.size())
		view_content = self.view.substr(region)
		formated = format_proto(view_content, reassign_num)
		self.view.replace(edit, region, formated)

	def reindent_enum(self, edit):
		class_list = self.view.find_by_selector("meta.enum.proto")
		class_list.reverse()
		for r in class_list:
			origin = self.view.substr(r)
			formated = format_proto(origin)
			self.view.replace(edit, r, formated)

	def reindent_message(self, edit):
		class_list = self.view.find_by_selector("meta.class.proto")
		class_list.reverse()
		for r in class_list:
			origin = self.view.substr(r)
			formated = format_proto(origin)
			self.view.replace(edit, r, formated)


class AutoNumberLinesCommand(sublime_plugin.TextCommand):
	def run(self, edit):
		for region in self.view.sel():
			if region.a != region.b:
				sel_content = self.view.substr(region)
				formated = number_lines(sel_content)
				self.view.replace(edit, region, formated)
				return
