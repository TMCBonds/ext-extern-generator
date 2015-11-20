#!/usr/bin/python

# Written by Daniel Kasierer
# for TMC Bonds

import sys
import subprocess
import re
import json
from pprint import pprint
from ConfigParser import SafeConfigParser
import StringIO
import os

def handleTypes(str):
	hasString = 0
	hasNumber = 0
	retArray = []
	if str is not None:
		str = str.replace("/", "|")
		paramArray = str.split("|")
		for i in range(0, len(paramArray)):
			if paramArray[i] == "*":
				return "*"
			elif "'" in paramArray[i] or '"' in paramArray[i]:
				if hasString == 0:
					retArray.append("string")
					hasString = 1
			elif re.search('\d', paramArray[i]) is not None:
				if hasNumber == 0:
					retArray.append("number")
					hasNumber = 1
			else:
				newItem = paramArray[i]
				if newItem[-3:] == "...":
					newItem = "..." + newItem[:-3]
				elif newItem[-4:] == "[][]":
					newItem = "Array<Array<" + newItem[:-4] + ">>"
				elif newItem[-2:] == "[]":
					newItem = "Array<" + newItem[:-2] + ">"

				# List of Sencha typos to fix
				newItem = newItem.replace("Number", "number")
				newItem = newItem.replace("Boolean", "boolean")
				newItem = newItem.replace("String", "string")
				newItem = newItem.replace("HtmlElement", "HTMLElement")
				newItem = newItem.replace("Ext.grid.column.Rownumberer", "Ext.grid.column.RowNumberer")
				newItem = newItem.replace("Ext.dom.ElementPool", "Ext.dom.UnderlayPool")
				newItem = newItem.replace("Ext.event.EVent", "Ext.event.Event")
				newItem = newItem.replace("Ext.Event", "Ext.event.Event")
				newItem = newItem.replace("Ext.event.Evented", "Ext.Evented")
				newItem = newItem.replace("Ext.data.Result", "Ext.data.ResultSet")
				newItem = newItem.replace("Ext.data.ResultSetSet", "Ext.data.ResultSet")
				newItem = newItem.replace("Ext.list.TreeList", "Ext.list.Tree")
				newItem = newItem.replace("Ext.data.AjaxRequest", "Ext.data.request.Ajax")
				newItem = newItem.replace("Ext.ajax.Request", "Ext.data.request.Ajax")
				newItem = newItem.replace("FocusMoveEvent", "Ext.event.Event")
				newItem = newItem.replace("Mixed", "*")
				newItem = newItem.replace("*Collection", "MixedCollection")
				retArray.append(newItem)
		str = "|".join(retArray)
		return str
	else:
		return None

# Checks against list of Objects not in javascript or Ext
def checkUnknown(str):
	if "Arguments" in str:
		return True
	if "CSSStyleRule" in str:
		return True
	if "CSSStyleSheet" in str:
		return True
	if "|Class" in str or re.search("^Class", str) is not None:
		return True
	if "TextNode" in str:
		return True
	if "Uint8Array" in str:
		return True
	if "XMLElement" in str:
		return True
	if "[type]" in str:
		return True
	if "null" in str:
		return True
	if "type" in str:
		return True
	if "undefined" in str:
		return True
	if "Ext.dom.Element.DISPLAY" in str:
		return True
	if "Ext.dom.Element.OFFSETS" in str:
		return True
	if "Ext.dom.Element.VISIBILITY" in str:
		return True
	if str == "Ext":
		return True
	return False

# fixes variables named after javascript keywords
def fixName(name):
	if name == "class":
		name = "classVar"
	return name

# fixes for specific functions that have been found not to work as intended
# this list is likely incomplete and may be the reason for some compilation issue
def getCustomParams(name, paramName, paramType):
	if name == "fireEvent" and paramName is None:
		return "*"

	if "|..." in paramType:
		paramType = "...*"
	if paramType == "":
		paramType = "*"
	if paramType == "Object" and (name == "isEmpty" or name == "apply" or name == "applyIf"):
		paramType = "(Object|string)="
	if paramType == "Object" and (name == "setY"):
		if paramName == "y":
			paramType = "number"
		else:
			return None
	if paramName == "success" and name == "processResponse":
		paramType ="boolean"
	if name == "isObject" and paramType == "Object":
		paramType = "*"

	if name == "get" and paramName == "returnType":
		return None
	return paramType

# prints out param annotation (or unknown if param has unknown type listed above)
def printParam(memParams, name):
	paramList = ""
	if memParams is not None:
		paramDict = {}
		paramCount = 1
		hasVarParams = False
		varParams = []
		hasOptional = False
		for param in memParams:
			paramName = param.get("name")
			paramName = fixName(paramName)
			paramType = param.get("type")
			paramType = handleTypes(paramType)
			paramOptional = param.get("optional")
			# checking if there is a variable length parameter
			# if so, we will need to make sure there are no
			# parameters following this one (will combine params)
			if paramType is not None and "..." in paramType:
				hasVarParams = True
			if hasVarParams:
				if paramType is not None and not checkUnknown(paramType):
					varParams.append(paramType)
				continue
			if paramName is None:
				paramName = 'var' + str(paramCount)
				paramCount += 1
			while paramName in paramDict:
				paramName = paramName + "a"
			paramDict[paramName] = True
			if paramList == "":
				paramList = paramName
			else:
				paramList += "," + paramName
			if paramType is not None:
				unknown = checkUnknown(paramType)
				paramType = getCustomParams(name, paramName, paramType)
				if paramType is None:
					continue
				if hasOptional or paramOptional is not None:
					hasOptional = True
					paramType = paramType.replace("=", "")
					paramType += "="
				print " * ", ("unknown " if unknown else "@") + "param", "{", paramType, "}", paramName
		if varParams:
			# build variable parameter list to prevent having parameter after
			# closure compiler does not allow parameters after this
			strParams = "|".join(varParams)
			strParams = strParams.replace("...", "")
			strParams = getCustomParams(name, None, strParams)
			strParams = "...(" + strParams + ")"
			print " * ", "@param", "{", strParams, "}", "variableParamsList"
			if paramList == "":
				paramList = "variableParamsList"
			else:
				paramList += "," + "variableParamsList"
	if paramList is None:
		paramList = ""
	return paramList
	
# default core path
corepath = '.'

# see if the config file has a different default path
try:
	config = StringIO.StringIO()
	config.write('[dummysection]\n')
	config.write(open('ExtConfig.properties').read())
	config.seek(0, os.SEEK_SET)

	parser = SafeConfigParser()
	parser.readfp(config)
	configOptions = dict(parser.items("dummysection"))

	corepath = configOptions.get("jsduck_location", ".")
except Exception:
	pass

# for compile issues with extjs
print "/**"
print " *  @fileoverview"
print " *  @suppress {extjsIssues}"
print " */"

# look for jsduck output (json files)
commandstring = "find " + corepath + " | grep '\.json$'"
allFiles = subprocess.check_output(commandstring, shell=True)
allFiles = allFiles.split("\n")
if not allFiles[len(allFiles)-1]:
	del allFiles[len(allFiles)-1]
count = 1
definedTree = {}
tree = {}
for item in allFiles:
	item = item.strip()
	with open(item, "r") as file1:
		data = json.load(file1)
		extends = data.get("extends")
		code_type = data.get("code_type")
		files = data.get("files")
		private = data.get("private")
		requires = data.get("requires")
		name = data.get("name")
		tagname = data.get("tagname")
		singleton = data.get("singleton")
		alternates = data.get("alternateClassNames")
		if name == "Ext.util.Operators":
			continue
		# start namespacing
		nameList = [name]
		nameList.extend(alternates)
		for nameItem in nameList:
			nameTree = nameItem.split(".")
			pos = 1
			if len(nameTree) > 1:
				for i in range(1, len(nameTree) - 1):
					if nameTree[i][0].islower() or nameTree[i] == "DataView":
						pos += 1
			level = 0
			fullPath = []
			for j in range(1, pos):
				treePos = tree
				for path in fullPath:
					treePos = treePos[path]
				fullPath.append(nameTree[j])
				if nameTree[j] not in treePos.keys():
					treePos[nameTree[j]] = {}
		# end namespacing
		
		items = data.get("members")
		constructorParams = None
		for item in items:
			itemParams = item.get("params")
			itemName = item.get("name")
			if itemName == "constructor":
				constructorParams = itemParams
				break

		if files is not None:
			lineNum = files[0].get("linenr")
			lineFile = files[0].get("filename")
		if (code_type == "ext_define" or tagname == 'class') and name != "Ext" and name != "Ext.Function":
			constructor = True
			classDef = "function(config){};"
		else:
			constructor = False
			classDef = "{};"
		
		if extends is not None or constructor or lineNum or lineFile or private or requires:
			print "/**"
			if extends is not None:
				print " * ", "@extends", extends
			constructorParamList = None
			if constructor:
				print " * ", "@constructor"
				if constructorParams is not None and name != "Ext" and name != "Ext.Function":
					constructorParamList = printParam(constructorParams, "")
			if constructorParamList is not None:
				classDef = "function(" + constructorParamList + "){};"
			if lineNum:
				print " * ", "line number:", lineNum
			if lineFile:
				lineFilePath, lineFileName = os.path.split(lineFile)
				print " * ", "file name:", lineFileName
			if private:
				print " * ", "@private"
			if requires:
				print " * ", "requires:", requires
			# for alternate in alternates:
			# 	print " * ", "@template", alternate
			print " */"
		if "." not in name:
			print "var", name, "=", classDef
		else:
			print name, "=", classDef
		for alternate in alternates:
			if alternate == "Ext.chart.CartesianChart":
				continue
			print "/**"
			print " * ", "@extends", "{", name, "}"
			if constructor:
				print " * ", "@constructor"
			if lineNum:
				print " * ", "line number:", lineNum
			if lineFile:
				lineFilePath, lineFileName = os.path.split(lineFile)
				print " * ", "file name:", lineFileName
			print " */"
			
			print alternate, "=", name, ";"
		members = data.get("members")
		for member in members:
			memPriv = member.get("private")
			memProt = member.get("protected")
			memStat = member.get("static")
			memType = member.get("type")
			memTag  = member.get("tagname")
			memParams = member.get("params")
			memDepr = member.get("deprecated")
			memRet  = member.get("return")
			memName = member.get("name")
			paramList = ""
			fullName = name + (".prototype." if (constructor and memStat is None and singleton is None) else ".") + memName
			if fullName in definedTree:
				continue
			else:
				definedTree[fullName] = True
			# list of conditions for skipping object/function/property definition
			if memTag == "cfg" or memTag == "event":
				continue
			if memName == "id" and constructor and memStat is None:
				continue
			if memName == "create" and name == "Ext":
				continue
			if memName == "define" and name == "Ext":
				continue
			if (memName == "animate" and 
				memTag == "property" and 
				name in ("Ext.slider.Multi", "Ext.slider.Single")):
				continue
			if memName == "" or "-" in memName:
				continue
			# end list of skip conditions

			if memTag == "method":
				memType = None
			if memRet is not None:
				retType = memRet.get("type")
			else:
				retType = None
			# if we need to add annotations
			if memPriv or memProt or memStat or memType or retType or memParams:
				print "/**"
				if memProt:
					print " * ", "@protected"
				elif memPriv:
					if name != "Ext.data.reader.Reader" or memName != "onMetaChange":
						print " * ", "@private"
					else:
						print " * ", "@protected"
				if memType:
					memType = handleTypes(memType)
					unknown = checkUnknown(memType)
					print " * ", ("unknown " if unknown else "@") + "type {", memType, "}"
				elif retType:
					retType = handleTypes(retType)
					unknown = checkUnknown(retType)
					if name == "Ext.data.Model":
						retType = getCustomParams(memName, "returnType", retType)
					if retType is not None:
						print " * ", ("unknown " if unknown else "@") + "return {", retType, "}"
				paramList = printParam(memParams, memName)
				if memDepr:
					print " * ", "@deprecated"
				print " */"
			# start namespacing
			nameTree = memName.split(".")
			pos = 0
			if len(nameTree) > 1:
				for i in range(0, len(nameTree)-1):
					if nameTree[i][0].islower() or nameTree[i] == "DataView":
						pos += 1
			level = 0
			fullPath = []
			for j in range(0, pos):
				treePos = tree
				for path in fullPath:
					treePos = treePos[path]
				if j==0:
					nameTreePath = name.replace("Ext.", "") + (".prototype." if (constructor and memStat is None) else ".") + nameTree[j]
				else:
					nameTreePath = nameTree[j]
				fullPath.append(nameTreePath)
				if nameTreePath not in treePos.keys():
					treePos[nameTreePath] = {}
			# end namespacing
			
			if memTag == "method":
				memDef = " = function(" + paramList + "){}"
			else:
				memDef = ""
			print fullName + memDef + ";"

# prints the definitions for classes and namespaces not yet defined
def treePrint(base, tree):
	for treeItem in tree.keys():
		newBase = base + "." + treeItem
		if newBase == "Ext.app":
			print newBase + " = {};"
		else:
			print "/**"
			print " *  @constructor"
			print " *  @param {Object} config"
			print " */"
			print newBase + " = function(config){};"
		treePrint(newBase, tree[treeItem])
# start at Ext and print all remaining definitions
base = 'Ext'
treePrint(base, tree)


