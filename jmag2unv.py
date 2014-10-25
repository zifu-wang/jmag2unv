#!/usr/bin/env python


# Jmag2unv
#
# Transfer a Jmag computation result (.plot file) to .unv mesh and field
# Python version 
# v1.2 July 2013
# report all bugs to zifu.wang@outlook.com, thank you!

import os
import math
import string
import fnmatch
import linecache

import pylab
import scipy


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  config
file_plot='Forces_TG12_premier_pas.plot'        # PLOT File from JMAG
out_name='toto'				  	# Output mesh/field name

# What info do you want ?
want_mesh = True
want_analysis_data = True

#if want_analysis_data, which one(s) ?
want_magnetic_field=True
want_magnetic_flux_density=True
want_visu=True					# want a visu file ? (.pos file for GMSH)	
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%  end config

# classes
class Node(object):
	def __init__(self, order=None, ident=None, x=None, y=None, z=None):
		self.order = order
		self.ident = ident
		self.x = x
		self.y = y
		self.z = z

class Element(object):
	def __init__(self, ident=None, n_node=None, mat_type=None, elt_type=None, node=None):
		self.ident = ident
		self.n_node = n_node
		self.mat_type = mat_type
		self.elt_type = elt_type
		self.node = node

class Group(object):
	def __init__(self ):
		self.num = 0
		self.mat_list = []
		self.elt_list = []

class Element_data(object):
	def __init__(self, order=None, elt=None, vector=None):
		self.order = order
		self.elt = elt
		self.vector = vector

class bcolors:
    	HEADER = '\033[95m'
    	OKBLUE = '\033[94m'
    	OKGREEN = '\033[92m'
    	WARNING = '\033[93m'
    	FAIL = '\033[91m'
    	ENDC = '\033[0m'
    	def disable(self):
        	self.HEADER = ''
        	self.OKBLUE = ''
        	self.OKGREEN = ''
        	self.WARNING = ''
        	self.FAIL = ''
        	self.ENDC = ''	
	

#user functions
# convert a string to integer or float if possible
def convert(n):
	try:
        	return int(n)
	except ValueError:
		try:
			return float(n)
		except  ValueError: 
			return n

# convert a Jmag elt to corresponding unv elt
def elt_convert(n):
	elt_jmag2unv=[-1,115,116,111,118,112,113,-1,-1,-1,-1,-1,-1,-1,-1]
	try:
		return elt_jmag2unv[n]
	except IndexError:
		return -1
	
# init
import_node_mode=False
import_element_mode=False
import_control_data_mode=False
import_element_data_control_mode=False
import_element_data_mode=False
import_H_data_mode=False
import_B_data_mode=False
line_indice=0

# let us rock
with open(file_plot, 'r') as inF:
   	for line in inF:
		line_indice=line_indice+1
	   	if '*Node' in line and want_mesh:	
			node_start_line=line_indice
			print '\n+++ Keyword *Node found in line ', line_indice
			line_array=[convert(s) for s in string.split(line)]
			node_num=line_array[0]
			print '    - number of the nodes to be imported  = ', node_num
			import_node_mode=True
			node_list=[]
		elif import_node_mode:
			#print 'import Node in line ', line_indice
			line_array=[convert(s) for s in string.split(line)]
			node_list.append(Node(line_array[0],line_array[1],line_array[2],line_array[3],line_array[4]))
			if line_indice==node_start_line+node_num:
				import_node_mode=False
				print bcolors.OKGREEN + '\t======== done ========\n ' + bcolors.ENDC
	   	elif '*Element' in line and want_mesh:
			element_start_line=line_indice
			print '\n+++ Keyword *Element found in line ', line_indice
			line_array=[convert(s) for s in string.split(line)]
			element_num=line_array[0]
			mat_num=line_array[1]
			group_list=Group()
			print '    - number of the elements to be imported  = ', element_num
			import_element_mode=True
			element_list=[]
		elif import_element_mode:
			#print 'import element in line ', line_indice
			line_array=[convert(s) for s in string.split(line)]
			element_list.append(Element(line_array[0],line_array[1],line_array[2],line_array[3], line_array[4:]))
			if not line_array[2] in group_list.mat_list:
				group_list.num=group_list.num+1
				group_list.mat_list.append(line_array[2])
				group_list.elt_list.append([])
			group_list.elt_list[group_list.mat_list.index(line_array[2])].append(line_array[0])
			if line_indice==element_start_line+element_num:
				import_element_mode=False
				print bcolors.OKGREEN + '\t======== done ========\n ' + bcolors.ENDC
				if not want_analysis_data:
					break
	   	elif '*CONTROL_DATA' in line and want_analysis_data:	
			print '\n+++ Keyword *CONTROL_DATA found in line ', line_indice
			import_control_data_mode=True
		elif import_control_data_mode:
                        line_array=[convert(s) for s in string.split(line)]
			control_step=line_array[0]
			control_value=line_array[1] # time/freq
			print '    - analysis step number   = ', control_step
			print '    - step value (freq if harmonic / time ifnot)   = ', control_value
			import_control_data_mode=False
	   	elif '*MAGNETIC_FLUX_DENSITY' in line and want_magnetic_flux_density:	
			print '\n+++ Keyword *MAGNETIC_FLUX_DENSITY found in line ', line_indice
			import_element_data_control_mode=True
			file_analysis_data='B_'+out_name+'_step_'+str(control_step)+'.unv'
			file_analysis_data_visu='B_'+out_name+'_step_'+str(control_step)+'.pos'
	   	elif '*MAGNETIC_FIELD_VECTOR' in line and want_magnetic_field:	
			print '\n+++ Keyword *MAGNETIC_FIELD_VECTORY found in line ', line_indice
			import_element_data_control_mode=True
			file_analysis_data='H_'+out_name+'_step_'+str(control_step)+'.unv'
			file_analysis_data_visu='H_'+out_name+'_step_'+str(control_step)+'.pos'
		elif import_element_data_control_mode:
			element_data_start_line=line_indice
                        line_array=[convert(s) for s in string.split(line)]
			element_data_num=line_array[0]
			print '    - number of the values to be imported = ', element_data_num
			import_element_data_control_mode=False
			import_element_data_mode=True
			element_data_list=[]
			# out
			outF = open(file_analysis_data, 'w')
			outF.write('    -1\n')
	       		outF.write('  2414\n\n\n\n\n\n\n\n\n')
			# visu
			if want_visu:
				visuF=open(file_analysis_data_visu, 'w')
				visuF.write('General.FastRedraw = 0 ;\n')
				visuF.write('General.Color.Background = White ;\n')
				visuF.write('General.Color.Foreground = White ;\n')
				visuF.write('General.Color.Text = Black ;\n')
				visuF.write("View \"%s_field\" {\n" %(out_name))
		elif import_element_data_mode:
			#print 'import element_data in line ', line_indice
			line_array=[convert(s) for s in string.split(line)]
			element_data_list.append(Element_data(line_array[0],line_array[1],line_array[2:]))
			#out
			outF.write('%10i%10i\n' %(line_array[1],3))
			outF.write('%13.5E%13.5E%13.5E\n' %(line_array[2],line_array[3],line_array[4]))
			#visu
	                if not elt_convert(element_list[line_array[1]-1].elt_type)==-1:
				centre_x=sum(node_list[i-1].x for i in element_list[line_array[1]-1].node)/element_list[line_array[1]-1].n_node
				centre_y=sum(node_list[i-1].y for i in element_list[line_array[1]-1].node)/element_list[line_array[1]-1].n_node
				centre_z=sum(node_list[i-1].z for i in element_list[line_array[1]-1].node)/element_list[line_array[1]-1].n_node
				visuF.write('VP(%13.5E,%13.5E,%13.5E)\n' %(centre_x,centre_y,centre_z))
				visuF.write('{%13.5E,%13.5E,%13.5E};\n' %(line_array[2],line_array[3],line_array[4]))
			if line_indice==element_data_start_line+element_data_num:
				import_element_data_mode=False
				outF.write('    -1\n')
				outF.close()
				visuF.write('};\n')
				visuF.close()
				print bcolors.OKGREEN + '\t======== done ========\n ' + bcolors.ENDC
inF.close()

# Export mesh to unv file
file_mesh_unv=out_name+'_mesh.unv'
if want_mesh:
	outF = open(file_mesh_unv, 'w')
	# node
	outF.write('    -1\n')
	outF.write('  2411\n')
	for i in range(len(node_list)):
		outF.write('%10i%10i%10i%10i\n' %(node_list[i].ident, 0, 0, 11))
	        outF.write('%25.16E%25.16E%25.16E\n' %(node_list[i].x,node_list[i].y,node_list[i].z))
	outF.write('    -1\n')
	# element
	outF.write('    -1\n')
	outF.write('  2412\n')
	for i in range(len(element_list)):
		if not elt_convert(element_list[i].elt_type)==-1:
	        	outF.write('%10i%10i%10i%10i%10i%10i\n' %(element_list[i].ident,elt_convert(element_list[i].elt_type),element_list[i].mat_type,element_list[i].mat_type,4,element_list[i].n_node))
			for j in range(element_list[i].n_node):
				outF.write('%10i' %(element_list[i].node[j]))
			outF.write('\n')
	outF.write('    -1\n')
	# group
	outF.write('    -1\n')
	outF.write('  2467\n')
	for i in range(group_list.num):
		outF.write('%10i%10i%10i%10i%10i%10i%10i%10i\n' %(i, 0, 0, 0, 0, 0, 0, len(group_list.elt_list[i])))
		outF.write('Material_%d\n' %(group_list.mat_list[i]))
		first_insert=True
		for j in range(len(group_list.elt_list[i])):
	        	if first_insert:
	                	outF.write('%10i%10i%10i%10i' %(8, group_list.elt_list[i][j], 0, 0))
	                        first_insert = False
	                else:
	                	outF.write('%10i%10i%10i%10i\n' %(8, group_list.elt_list[i][j], 0, 0))
	                        first_insert = True
        	if not first_insert:
                	outF.write('\n')
	outF.write('    -1\n')
	outF.close()

# end			
os._exit(0)

