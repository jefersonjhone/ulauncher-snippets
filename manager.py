from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from view import View
from db import DataBase
import re 
import logging


logger = logging.getLogger(__name__)


class DefaultAction:
    @staticmethod
    def run():
        logger.debug("Executing DefaultAction ")
        return[
            ExtensionResultItem(
                icon=View.extension_icon,
                name="Type something...",
                description='Example: hi {user|upper}, today is {now}. Date: {date format="%d/%m/%Y"}, Tomorrow is {date offset="+1d"}',
                highlightable=False,
                on_enter=DoNothingAction(),
            )
            ]
        
class InfoAction:
    def __init__(self, name, description, highlightable=False):
        self.name = name 
        self.description = description
        self.highlightable = highlightable
    def run(self):
        logger.debug("Executing DefaultInfoAction ")
        return[
            ExtensionResultItem(
                icon=View.extension_icon,
                name=self.name,
                description=self.description,
                highlightable=self.highlightable,
                on_enter=DoNothingAction(),
                )
            ]




class AdicionarAction:
    def __init__(self, db: DataBase, engine, name, content, keyword, type="text"):
        self.db = db
        self.engine = engine
        self.name = name
        self.content = content
        self.keyword = keyword
        self.type = type

    def run(self):  
        existing = self.db.get_snippet(self.name)

        callback = f"{self.keyword} list {self.name}"
        if self.type == ("snippet", "template"):
            processed_content = self.engine.expand_text(self.content)
            f"'{self.name}' with '{self.content}' \n'{self.name}' with '{processed_content}' \n "
        else:
            processed_content = f"'{self.name}' with '{self.content}'"
        
        
        if existing:
            desc = f"Update {processed_content}"
        else:
            desc = f"Insert {processed_content}"

        
        logger.debug(desc)

        item = ExtensionResultItem(
            icon=View.extension_icon,
            name=f"{self.name} = {self.content}",
            description=desc,
            highlightable=False,
            on_enter=ExtensionCustomAction(
            {"action": "add_snippet", "name": self.name, "content": self.content, "type_snippet":self.type, "callback":callback},
                keep_app_open=True
            ),
        )

        return [item]


class BuscarAction:
    def __init__(self, name, db: DataBase, engine, limit=10, keyword="", list_menu=True, page=1):
        self.name = name
        self.db = db
        self.engine = engine 
        self.limit = limit
        self.list_menu = list_menu
        self.keyword = keyword
        self.page = page

    def run(self):
        items = []
        results = self.db.list_snippets(self.name, page=self.page, page_size=self.limit)
        if self.list_menu:
            menu = []
            for opt in View.actions:
                if not self.name or self.name in opt["name"].lower() or self.name in opt["cmd"].lower():
                    menu.append(
                    ExtensionResultItem(
                        #compact=True,
                        icon=opt["icon"],
                        name=opt["name"],
                        #description=opt["desc"],
                        on_enter=SetUserQueryAction(f"{self.keyword} {opt['cmd']}"),
                    )
                )
            items.extend(menu)
        
        if results:
            for snippet in results:
                name = snippet.get("NAME")
                content = snippet.get("CONTENT")
                type = snippet.get("TYPE")                
                
                if type == "snippet":
                    rule_processed = self.engine.expand_text(content)
                    processed_content = f"[SNIPPET RULE] {content}\n[SNIPPET RESULT] {rule_processed}"
                else:
                    rule_processed = processed_content = content
                

                if type == "template":
                    on_enter = SetUserQueryAction(f"{self.keyword} use {name} ")
                    icon = View.template_icon_red
                else:
                    on_enter= CopyToClipboardAction(rule_processed)
                    icon = View.copy_icon_purple

                
                item = ExtensionResultItem(
                    icon=icon,
                    name=name,
                    description=processed_content,
                    on_enter = on_enter
                )
                items.append(item)
            if len(results) == self.limit:  
                items.append(
                ExtensionResultItem(
                    icon=View.search_icon_purple,  
                    name="Next page...",
                    description=f"See more results (page {self.page+1})",
                    on_enter=SetUserQueryAction(f"{self.keyword} list {self.name} --p={self.page+1}")
                    )
                )
        else:
            
            if self.name == "":
                title = "It looks like you have nothing stored"
            else:
                title = "No snippet for name: '{}'".format(self.name)
            item = ExtensionResultItem(icon=View.search_icon_red, name=title,  highlightable = False)
            items.append(item)
       
        
        return items

class DeletarAction:
    def __init__(self, db:DataBase, name, keyword):
        self.db = db
        self.name = name 
        self.keyword = keyword
    
    def run(self):
        logger.debug("==== Executing DeleteAction")
        results = self.db.list_snippets(self.name)
        matchs =[]
        for snippet in results:
            name = snippet.get("NAME")
            content = snippet.get("CONTENT")
            type = snippet.get("TYPE")
            if type == "template":
                icon = View.template_icon_red
            else:
                icon = View.snippet_icon_red

            item = ExtensionResultItem(
                icon=icon,
                name="{} = {}".format(name, content),
                description=f"Press enter or click delete '{content}' (value '{content}' )",
                on_enter=ExtensionCustomAction(
                        {"action": "delete_snippet", "name": name, "callback":f"{self.keyword} "}, keep_app_open=True
                    )
            )
            matchs.append(item)
        if not results:
            description = "Snippet '{}' not found ".format(self.name)
            item = ExtensionResultItem(icon=View.search_icon_red, name=View.NAME, description=description, highlightable = False)
            matchs.append(item)
        return matchs


class ExecAction:
    def __init__(self, db:DataBase, query, engine, keyword):
        self.db = db
        self.query = query 
        self.keyword = keyword
        self.engine = engine
    
    def run(self):
        logger.debug("==== Executing DeleteAction")
        try:
            replace_snip = self.fill_snip(self.query)
            expanded_text = self.engine.expand_text(replace_snip)
            return [
                ExtensionResultItem(
                    icon=View.copy_icon_purple,
                    name=expanded_text,
                    highlightable=False,
                    description="Pressione Enter para copiar",
                    on_enter=CopyToClipboardAction(expanded_text),
                    )
                ]
                
        except Exception as e:
            return[
                ExtensionResultItem(
                    icon=View.extension_icon,
                    name=f"Erro ao processar: {str(e)}",
                    description="Verifique a sintaxe dos placeholders",
                    highlightable=False,
                    on_enter=DoNothingAction(),
                )
            ]
        
    def fill_snip(self, text, default=None):
        def find_snippet(name):
            snippet = self.db.get_snippet(name)
            
            if snippet and snippet.get("TYPE") == "text":
                return snippet.get("CONTENT")
            
            return name 
        pattern = re.compile(r"\{snip:(.*?)\}")
        snippet_content = pattern.sub(lambda m: find_snippet(m.group(1)), text)
        return snippet_content


class EditarAction:
    def __init__(self, db:DataBase, name, keyword):
        self.db = db
        self.name = name 
        self.keyword = keyword
    
    def run(self):
        logger.debug("==== Executing EditAction")
        results = self.db.list_snippets(self.name)
        matchs =[]
        for snippet in results:
            name = snippet.get("NAME")
            content = snippet.get("CONTENT")
            type = snippet.get("TYPE")
            if type == "template":
                icon = View.template_icon_red
            else:
                icon = View.snippet_icon_red

            item = ExtensionResultItem(
                icon=icon,
                name="{} = {}".format(name, content),
                description=f"Press enter or click delete '{content}' (value '{content}' )",
                on_enter=ExtensionCustomAction(
                        {"action": "edit_snippet", "name": name, "content":content, "type_snippet":type, "callback":f"{self.keyword} "}, keep_app_open=True
                    )
            )
            matchs.append(item)
        if not results:
            description = "Snippet '{}' not found ".format(self.name)
            item = ExtensionResultItem(icon=View.search_icon_red, name=View.NAME, description=description, highlightable = False)
            matchs.append(item)
        return matchs




class FillTemplateAction:
    def __init__(self, name, values, db, engine, keyword):
        self.name = name
        self.db = db
        self.engine = engine 
        self.keyword = keyword
        self.values = values

    def run(self):
        items = []
        template = self.db.get_snippet(self.name)

        if not template or template.get("TYPE") != "template": 
            if self.name == "":
                description = "It looks like you have nothing stored"
            else:
                description = "No VALUE for KEY: '{}'".format(self.name)
            item = ExtensionResultItem(icon=View.extension_icon, name=View.NAME, description=description,  highlightable = False)
            items.append(item)

            return items
 
        name = template.get("NAME")
        content = template.get("CONTENT")
        type = template.get("TYPE")                
        
        template_filled = self.fill_template(content, self.values)

        rule_processed = self.engine.expand_text(template_filled)
        processed_content = f"[SNIPPET RULE]\n{content}\n[SNIPPET RESULT]\n{rule_processed}"


        chunk_size = 60 
        item = ExtensionResultItem(
            icon=View.copy_icon_red,
            name=name,
            description="\n".join([processed_content[i:i+chunk_size] for i in range(0, len(processed_content), chunk_size)]),
            on_enter=CopyToClipboardAction(rule_processed),
            highlightable = False
        )
        items.append(item)
        return items 
    

    def fill_template(self, snippet_content: str, values: list) -> str:
        user_values_dict = {}
        user_values_list = []

        for value in values:
            if "=" in value:
                key, val = value.split("=" ,1)
                if val:
                    user_values_dict[key.strip()] = val
                else:
                    user_values_list.append(value)
            else:
                user_values_list.append(value)
                

        def fill_template_array(match):
            if user_values_dict.get(match.group(1).strip()):
                return user_values_dict.get(match.group(1).strip())
            else:
                fill_template_array.index += 1
                idx = fill_template_array.index
                return user_values_list[idx] if idx < len(user_values_list) else match.group(0)
        
        def fill_template_array_with_modifiers(match):
            var = match.group('var').strip()
            modifiers = match.group('modifiers')

            if var and var in user_values_dict:
                value = user_values_dict[var]
            else:
                fill_template_array.index += 1
                idx = fill_template_array.index
                value = user_values_list[idx] if idx < len(user_values_list) else match.group(0)

            if modifiers:
                value = '{' +value+ '|' + modifiers + '}'

            return value

        def find_snippet(name, default):
            snippet = self.db.get_snippet(name)
            
            if snippet and snippet.get("TYPE") == "text":
                return snippet.get("CONTENT")
            
            return default

        pattern_snip = re.compile(r"\{snip:(.*?)\}")
        snippet_content = pattern_snip.sub(lambda m: find_snippet(m.group(1), f"<{m.group(1)} não encontrado>"), snippet_content)
        
        fill_template_array.index = -1 

        pattern_var = re.compile(r'\{\{\{?(?P<var>[^|{}]*)\}?(?:\|(?P<modifiers>[^{}]+))?\}\}')

        filled_with_modifiers = pattern_var.sub(fill_template_array_with_modifiers, snippet_content)

        return filled_with_modifiers
        
        



class Dispatcher:
    def __init__(self, query, db, engine, limit, keyword):
        self.query = query
        self.db = db
        self.engine = engine
        self.limit = limit
        self.keyword = keyword
        self.handlers = {
            "add":self.handle_add,
            "ads":self.handle_ads,
            "adt":self.handle_adt,
            "use":self.handle_use,
            "del":self.handle_del,
            "list":self.handle_list,
            "x":self.handle_exe,
            "edit":self.handle_edit
        }

    def create(self):
        query = self.query.strip()
        if not query:
            return BuscarAction(name="", db=self.db, engine=self.engine, limit=self.limit, keyword=self.keyword)
        parts = query.split(" ", 1)
        command = parts[0]
        args = parts[1] if len(parts) > 1 else ""
        handler = self.handlers.get(command)
        
        if handler:
            return handler(args)

        return BuscarAction(query, db=self.db, engine=self.engine, limit=self.limit, keyword=self.keyword)

    def handle_add(self, args):        
        parts = args.split(" ", 1)
        if len(parts) == 2:
            return AdicionarAction(self.db, self.engine, parts[0], parts[1], self.keyword)
        
        return BuscarAction(args, db=self.db, engine=self.engine,limit=self.limit, list_menu=False,keyword= self.keyword)
     
    def handle_ads(self, args):
        parts = args.split(" ", 1)
        if len(parts) == 2:
            name, content = parts
            if not name.startswith("!"):
                return InfoAction(
                    name="Dinamics Snippets must start whith '!' ",
                    description=f"Its must be called '!{name}'"
                    )
            return AdicionarAction(self.db, self.engine, name=parts[0], content=parts[1],keyword=self.keyword, type="snippet")
        return BuscarAction(args, db=self.db, engine=self.engine,limit=self.limit, list_menu=False, keyword=self.keyword)
    
    def handle_adt(self, args):
        parts = args.split(" ", 1)

        if len(parts) == 2:
            name, content = parts
            if not name.startswith("!t"):
                return InfoAction(
                    name="Dinamics templates must start whith '!t' ",
                    description=f"Its must be called '!t{name}'"
                    )
            if content == "-f":
                return InfoAction(
                    name="Add Template from file",
                    description=f"Its must be called '!t{name}'"
                    )
            elif content.startswith("-f "):
                content_parts, filepath = content.split(" ", 1)
                if not filepath.endswith(".txt"):
                    return InfoAction(
                        name=f"filename must be a .txt file :{filepath}",
                        description=f""
                        )
                filecontent = self.get_file_content(filepath)
                return AdicionarAction(self.db,
                            self.engine,
                            name=parts[0],
                            content=f"{filecontent}",
                            keyword=self.keyword,
                            type="template")

            return AdicionarAction(self.db,self.engine, name=parts[0], content=parts[1], keyword=self.keyword, type="template")
        return BuscarAction(args, db=self.db, engine=self.engine,limit=self.limit, list_menu=False, keyword=self.keyword)
    
    def handle_use(self, args):
        if not args :
            return BuscarAction(name=args, db=self.db, engine=self.engine, limit=self.limit, list_menu=False, keyword=self.keyword)
        parts = args.split(" ", 1)
        if len(parts) == 2:
            name, values = parts
            return FillTemplateAction(name, values.split(";") , self.db, self.engine, self.keyword)
        return BuscarAction(name=parts[0], db=self.db, engine=self.engine, limit=self.limit, list_menu=False, keyword=self.keyword)
    
    def handle_del(self, args):
        return DeletarAction(self.db, args, self.keyword)

    def handle_list(self, args):

        page = 1
        if args:
            parts = args.split()
            argu = []
            for arg in parts:
                if arg.startswith("--p="):
                    try:
                        page = int(arg.split("=", 1)[1])
                    except ValueError:
                        ...
                else :
                    argu.append(arg)
            args = " ".join(argu)
        return BuscarAction(name=args, db=self.db, engine=self.engine, limit=self.limit, list_menu=False, keyword=self.keyword, page=page)


    def handle_exe(self, args):
        return ExecAction(self.db, args,  self.engine, self.keyword)
    
    def handle_edit(self, args):
        return EditarAction(self.db, args, self.keyword)
           

    def get_file_content(self, filepath):
        try:
            import os 
            filepath = os.path.expanduser(filepath)
            filepath = os.path.abspath(filepath)
            with open(filepath, 'r') as file:
                return file.read()
        except Exception as e :
            return f"{e}"
    


