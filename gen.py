#!/usr/bin/env python

import sys, os, string, markdown, argparse, shutil, json, glob, re
from distutils import dir_util as dirutil

arg_parser = argparse.ArgumentParser(description='Generates html file accroding to directory content');

input_dir = '../content/';
output_dir = '../deploy/';

def parse_args():
	global input_dir, output_dir, clean
	arg_parser.add_argument('--input', help='input directory');
	arg_parser.add_argument('--output', help='output directory');
	arg_parser.add_argument('--clean', help='cleans the output directory');
	args = arg_parser.parse_args();
	if args.input and os.path.isdir(args.input):
		input_dir = args.input;
	if args.output and os.path.isdir(args.output):
		output_dir = args.output;

def translate(txt, dirname):
	try:
		table = open(os.path.join('.', '<table>'), 'r+');
	except:
		print('error opening <table> file. aborting...');
		sys.exit(0);

	href = None
	sections = txt.count('- - -');
	if sections == 1:
		[text, link] = txt.split('- - -');		
	elif sections == 2:
		[text, link, href] = txt.split('- - -');

	text_md = markdown.markdown(text);
	link_md = markdown.markdown(link);

	# revise this - perhaps with a better
	link_md = link_md.replace('data/', dirname + '/');

	out = table.read().replace('[[text_md]]', text_md);
	out = out.replace('[[link_md]]', link_md);
	if href:
		href = href.replace('data/', dirname + '/');
		out = "<a " + href + ">" + out + "</a>";
	return out

def escape_date(dirname):
	return re.sub('^20\d{2}?.', '', dirname)

def emit_img(file, data_dir):
	return '<a href="' + file + '"><img src="' + file + '" /></a>'

def emit_video_mp4(file, data_dir):
	return '<video controls><source src="' + file + '" type="video/mp4"</video>'

def emit_audio(file, data_dir):
	# an '.audio' file is a json file with a list of audio elements
	# which need to be bundles as a type of list in a single <li>
	filename = os.path.join(data_dir, file);
	with open(filename) as f:
		audio = json.loads(f.read())
		out = "<sound>\n"
		for a in audio:
			out += "<track>\n"
			out += "<info>\n"
			out += "<name>" + a["name"] + "</name>\n"			
			#out += "<duration>" + a["length"] + "</duration>\n"
			out += "</info>\n"
			out += "<audio controls preload>\n"
			out += '<source src="' + a["file"] + '" type="audio/' + a["type"] + '">'
			out += "</audio>\n"
			out += "</track>\n"

		out += "</sound>\n"

		return out

	return "to do to do to do"

def default(file, data_dir):
	return None;

content_map = {
	'.png': emit_img,
	'.jpg': emit_img,
	'.m4v': emit_video_mp4,
	'.mov': emit_video_mp4,
	'.audio': emit_audio,
	'.html': default,
	'.txt': default
};

def index_content(dir_name, data_dir, index_txt, desc_txt, template):

	print "	indexing content -- " + dir_name;

	# desc_txt is a markdown file containing description 
	# for the project - no layout applied to it, only md
	desc_md = None
	if os.path.isfile(desc_txt):
		try:
			desc_file = open(desc_txt, 'r+');
			desc_md = markdown.markdown(desc_file.read());
			# transform markdown
		except:
			print "error opening description file: " + desc_txt;
			desc_md = None;
			#return;


	# index_txt is a json file containing one thing:
	# an array of files names or glob patterns
	content_index = None
	if os.path.isfile(index_txt):
		try:
			index_file = open(index_txt, 'r+');
			content_index = json.loads(index_file.read());
		except:
			print "error opening index: " + index_txt;
			content_index = None;
			#return;

	if desc_md == None and content_index == None:
		return;
	
	content = ""

	if desc_md:
		content += "<li>" + "<desc>" + "\n" + desc_md + "</desc>" + "</li>" + "\n";

	if content_index:

		files = [];
		for i in content_index:
			f = os.path.join(data_dir, i);
			if os.path.isfile(f):		
				files.append(i);
			else:
				files += [os.path.basename(a) for a in glob.glob(f)];

		
		for j in files:
			x, ext = os.path.splitext(j);
			if ext in content_map:
				element = content_map[ext](j, data_dir);
				if element:
					content += "<li>" + element + "</li>" + "\n";

	#print content

	html = template.replace('[[content]]', content).replace('[[dir]]', dir_name);

	#print html

	#check if <Project Name>.txt exists (description file)
	f = os.path.join(data_dir, "*.txt");
	txt_files = [a for a in [os.path.basename(a) for a in glob.glob(f)] if a != 'index.txt' and a != 'desc.txt'];
	if len(txt_files) == 1:		
		fn = txt_files[0];
		link = '<li><a href="' + fn + '">' + fn + '</a></li>';
		html = html.replace('<!--[[info]]-->', link);


	try:
		out = open(os.path.join(data_dir, 'index.html'), 'w');
		out.write(html);
		out.close();
	except:
		print('error creating content index output file. aborting...');
		sys.exit(0);



if __name__ == '__main__':

	#fix python markdown utf8 nonsense
	reload(sys);
	sys.setdefaultencoding('utf8');

	parse_args();

	print '1/3 - Configuring';

	# main index template
	try:
		template = open(os.path.join('.', 'index_template.html'), 'r+');
	except:
		print('error opening template file. aborting...');
		sys.exit(0);		

	# images index template
	try:
		content_indx_template = open(os.path.join('.', 'index_apache_template.html'), 'r+');
		content_index_template_str = content_indx_template.read();
	except:
		print('error opening template file. aborting...');
		sys.exit(0);		

	if not os.path.exists(output_dir):
		os.mkdir(output_dir);		

	try:
		out = open(os.path.join(output_dir, 'index.html'), 'w');
	except:
		print('error creating output file. aborting...');
		sys.exit(0);

	print '2/3 - Parsing input';

	dirs = [d for d in os.listdir(input_dir) if not d == '_system' and os.path.isdir(os.path.join(input_dir,d))];

	content = '';

	dirs.sort();	# dirs should be date-named

	for d in reversed(dirs):
		dd = os.path.join(input_dir,d);		
		indx_txt = os.path.join(dd, 'index.txt');
		if os.path.isfile(indx_txt):
			try:
				indx = open(indx_txt, 'r+');
			except:
				print "error opening index: " + indx_txt;
				continue;

			txt = indx.read();
			dirname = os.path.basename(dd);
			newdirname = escape_date(dirname) 		# trim date out of url -- permalink
			content += translate(txt, newdirname);
			content += '\n<br>\n';

			# data dir / content			
			data_dir = os.path.join(dd, 'data');
			if os.path.isdir(data_dir):

				#check if content needs index -- index.txt is a json file
				content_indx_txt = os.path.join(data_dir, 'index.txt');

				#check if there is a description file -- desc.txt is a markdown file
				content_desc_txt = os.path.join(data_dir, 'desc.txt');

				if os.path.isfile(content_indx_txt) or os.path.isfile(content_desc_txt):
					index_content(d, data_dir, content_indx_txt, content_desc_txt, content_index_template_str);				

				
				#copy content
				out_data_dir = os.path.join(output_dir, newdirname);
				try:					
					dirutil.copy_tree(data_dir, out_data_dir);
				except:
					print "error copying " + data_dir + " to " + out_data_dir + ". Continuing."
					continue;

	print '3/3 - Generating ouput';

	html = template.read().replace('[[content]]', content);

	out.write(html);

	style_in = os.path.join('.', '+++');
	style_out = os.path.join(output_dir, '+++');
	try:
		dirutil.copy_tree(style_in, style_out);
	except IOError as err:
		print err;

	template.close();
	content_indx_template.close();
	out.close();

	print 'done.';