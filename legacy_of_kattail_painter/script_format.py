"""Targeted Clausewitz layout; tokens, comments and statement order never change."""
from collections import defaultdict
from pathlib import PurePosixPath
import re

from model import TOKEN, parse, scalar

COMPACT = {'allowed','allowed_to_remove','available','visible','limit','trigger',
           'set_variable','check_variable','set_temp_variable','add_to_variable',
           'multiply_variable','add_to_temp_variable','subtract_from_temp_variable',
           'multiply_temp_variable','divide_temp_variable','add_to_array',
           'spritetype','frameanimatedspritetype'}


def script_path(relative):
    path=str(relative).replace('\\','/')
    return PurePosixPath(path).suffix.lower() in {'.txt','.gfx','.gui','.mod'} and path.startswith(
        ('common/','history/','events/','interface/','portraits/','map/strategicregions/','map/supplyareas/'))


def tokens(text):
    return tuple(m[0] for m in TOKEN.finditer(text))


def indentation(text, position):
    """Actual brace depth, independent of the opening brace's physical column."""
    return sum(1 if m[0]=='{' else -1 if m[0]=='}' else 0 for m in TOKEN.finditer(text[:position]))


def _indexed(nodes,text):
    counts=defaultdict(int);result={}
    for node in nodes:
        discriminator=scalar(text,node.children,'name') if node.children is not None else ''
        key=(node.key,discriminator);index=counts[key];counts[key]+=1
        result[(node.key,discriminator,index)]=node
    return result


def index_nodes(text):
    result={}
    def visit(nodes,path=(),ancestors=()):
        for key,node in _indexed(nodes,text).items():
            address=path+(key,);result[address]=(node,ancestors)
            if node.children is not None:visit(node.children,address,ancestors+(node,))
    visit(parse(text));return result


def changed_paths(before,after):
    """Smallest changed containers; preserve all unrelated source outside them."""
    old=index_nodes(before);new=index_nodes(after);selected=set()
    def visit(path):
        node,parents=new[path];previous=old.get(path)
        if previous and before[previous[0].start:previous[0].end]==after[node.start:node.end]:return
        if node.children is None:
            selected.add(path[:-1] if parents else path);return
        if previous is None or previous[0].children is None:
            selected.add(path);return
        count=len(selected)
        for key in _indexed(node.children,after):visit(path+(key,))
        if len(selected)==count:selected.add(path)
    for key in _indexed(parse(after),after):visit((key,))
    # Inline ancestors must expand too; otherwise a new field still hangs off
    # the middle of an outer definition's opening line.
    expanded=set()
    for address in selected:
        while len(address)>1:
            node,_=new[address];start=after.rfind('\n',0,node.start)+1
            end=after.find('\n',node.end);end=len(after) if end<0 else end
            prefix=after[start:node.start].strip();suffix=after[node.end:end].strip()
            if prefix or suffix and not suffix.startswith('#'):address=address[:-1]
            else:break
        expanded.add(address)
    return {p for p in expanded if not any(p[:i] in expanded for i in range(1,len(p)))}


class Renderer:
    def __init__(self,text):
        self.text=text

    def compact(self,node):
        raw=self.text[node.start:node.end]
        if any(m[0].startswith('#') for m in TOKEN.finditer(raw)):return False
        if node.children is None:return True
        if not node.children:return True
        if all(not n.op and n.children is None for n in node.children):
            return len(' '.join(tokens(raw)))<=120
        return node.key.casefold() in COMPACT and '\n' not in raw and all(n.children is None for n in node.children)

    def gap(self,lines,start,end,depth):
        gap=self.text[start:end]
        for match in TOKEN.finditer(gap):
            if not match[0].startswith('#'):raise ValueError('Unexpected token between script statements')
            at=start+match.start();prefix=self.text[self.text.rfind('\n',0,at)+1:at]
            if prefix.strip() and lines and lines[-1]:lines[-1]+=' '+match[0]
            else:lines.append('\t'*depth+match[0])
        if re.search(r'\n[ \t\r]*\n',gap) and lines and lines[-1]:lines.append('')

    def node(self,node,depth):
        raw=self.text[node.start:node.end];parts=tokens(raw)
        if self.compact(node):return ['\t'*depth+' '.join(parts)]
        if node.children is None:
            # Rare scalar assignments with an interposed comment must retain it.
            lines=[];pending=[]
            for part in parts:
                pending.append(part)
                if part.startswith('#'):lines.append('\t'*depth+' '.join(pending));pending=[]
            if pending:lines.append('\t'*depth+' '.join(pending))
            return lines
        opening=next(m for m in TOKEN.finditer(raw) if m[0]=='{')
        header=tokens(raw[:opening.start()]);lines=[];pending=[]
        for part in (*header,'{'):
            pending.append(part)
            if part.startswith('#'):lines.append('\t'*depth+' '.join(pending));pending=[]
        if pending:lines.append('\t'*depth+' '.join(pending))
        if node.children and all(not n.op and n.children is None for n in node.children) and not any(p.startswith('#') for p in parts):
            row='\t'*(depth+1)
            for child in node.children:
                atom=self.text[child.start:child.end]
                if row.strip() and len(row)+1+len(atom)>120:lines.append(row);row='\t'*(depth+1)
                row+=(' ' if row.strip() else '')+atom
            if row.strip():lines.append(row)
            lines.append('\t'*depth+'}');return lines
        last=node.start+opening.end()
        for child in node.children:
            self.gap(lines,last,child.start,depth+1);lines.extend(self.node(child,depth+1));last=child.end
        self.gap(lines,last,node.end-1,depth+1);lines.append('\t'*depth+'}')
        return lines

    def defective(self,node,depth):
        start=self.text.rfind('\n',0,node.start)+1;prefix=self.text[start:node.start]
        if prefix!='\t'*depth:return True
        if self.compact(node):return False
        if node.children is None:return False
        for child in node.children:
            line_start=self.text.rfind('\n',0,child.start)+1
            if self.text[line_start:child.start]!='\t'*(depth+1):return True
            if self.defective(child,depth+1):return True
        close_start=self.text.rfind('\n',0,node.end-1)+1
        return self.text[close_start:node.end-1]!='\t'*depth


def format_paths(text,paths,only_defective=False):
    indexed=index_nodes(text);renderer=Renderer(text);edits=[]
    paths={p for p in paths if p in indexed}
    paths={p for p in paths if not any(p[:i] in paths for i in range(1,len(p)))}
    roots=[(p,data[0]) for p,data in indexed.items() if len(p)==1]
    groups=[]
    for path in list(paths):
        if len(path)!=1:continue
        node=indexed[path][0];start=text.rfind('\n',0,node.start)+1
        end=text.find('\n',node.end);end=len(text) if end<0 else end
        group={p for p,n in roots if n.start<end and n.end>start}
        if len(group)>1:
            for previous in list(groups):
                if previous&group:group|=previous;groups.remove(previous)
            groups.append(group)
    for group in groups:
        nodes=sorted((indexed[p][0] for p in group),key=lambda n:n.start);lines=[];last=nodes[0].start
        for node in nodes:
            renderer.gap(lines,last,node.start,0);lines.extend(renderer.node(node,0));last=node.end
        start=text.rfind('\n',0,nodes[0].start)+1
        if text[start:nodes[0].start].strip():start=nodes[0].start
        edits.append((start,nodes[-1].end,'\n'.join(lines)));paths-=group
    for path in paths:
        node,parents=indexed[path];depth=len(parents)
        if only_defective and not renderer.defective(node,depth):continue
        start=text.rfind('\n',0,node.start)+1
        if text[start:node.start].strip():start=node.start
        replacement='\n'.join(renderer.node(node,depth))
        edits.append((start,node.end,replacement))
    result=text
    newline='\r\n' if '\r\n' in text else '\n'
    for start,end,replacement in sorted(edits,reverse=True):
        result=result[:start]+replacement.replace('\n',newline)+result[end:]
    if tokens(result)!=tokens(text):raise ValueError('Formatting would change script tokens or comments')
    parse(result)
    return result


def format_changes(relative,before,after):
    if not script_path(relative) or before==after:return after
    return format_paths(after,changed_paths(before,after))
