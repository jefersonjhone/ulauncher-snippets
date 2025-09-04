import os
import logging
import sqlite3
from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.CopyToClipboardAction import CopyToClipboardAction
from ulauncher.api.shared.action.DoNothingAction import DoNothingAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.RunScriptAction import RunScriptAction
from engine import PlaceholderEngine

from view import View
from db import DataBase
from manager import Dispatcher


logger = logging.getLogger(__name__)

# Força o cwd para a pasta da extensão
os.chdir(os.path.dirname(os.path.abspath(__file__)))




class SnippetsExtension(Extension):
    def __init__(self):
        super(SnippetsExtension, self).__init__()
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.engine = PlaceholderEngine()
        self.db = DataBase()
        logger.debug("Snippets Extension DataBase Done")



class KeywordQueryEventListener(EventListener):
    # def on_event(self, event, extension):
    #    return search(event, extension)

    def on_event(self, event, extension):

       
        keyword = event.get_keyword() or ""
        logger.debug("KeywordQueryEventListener executing")
        arguments_or_empty: str = event.get_query().get_argument() or ""
        limit_results = 10
        return RenderResultListAction(Dispatcher(arguments_or_empty, extension.db, extension.engine, limit_results, keyword).create().run())
        

   

class ItemEnterEventListener(EventListener):
    def on_event(self, event, extension):
        logger.debug("ItemEnterEventListener executing")
        data = event.get_data()
        if data.get("action") == "delete_snippet":
            extension.db.remove_snippet(data["name"])
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=View.extension_icon,
                    name=f"Snippet '{data['name']}' removido ✅",
                    highlightable = False,
                    on_enter=SetUserQueryAction(data.get("callback"))
                )
            ])
        if data.get("action") == "select_snippet":
            extension.db.update_snippet_usage(data["name"])
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=View.extension_icon,
                    name=f"Snippet '{data['name']}' copiado ✅",
                    on_enter=SetUserQueryAction(data.get("callback") or ""),
                    highlightable = False
                )
            ])
        
        if data.get("action") == "edit_snippet" and data.get("content") and data.get("name") and data.get("type_snippet"):
            import tempfile
            import subprocess

            name = data.get("name")
            content = data.get("content")
            type = data.get("type_snippet")

            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".txt") as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            editor = os.environ.get("EDITOR", "gnome-text-editor")  # fallback para nano
            subprocess.run([editor, tmp_path])
            #proc = subprocess.Popen(["code", tmp_path])
            #proc.wait()
            

            # ler conteúdo atualizado
            with open(tmp_path, 'r') as f:
                updated_content = f.read()

            extension.db.add_snippet(name, updated_content, type)
            os.unlink(tmp_path) 

            return RenderResultListAction([
                ExtensionResultItem(
                    icon=View.extension_icon,
                    name=f"Snippet '{name}' editado ✅",
                    description= updated_content,
                    on_enter=SetUserQueryAction(data.get("callback") or ""),
                    highlightable = False
                )
            ])
        if data.get("action") == "add_snippet" and (data.get("name") and data.get("content") and data.get("type_snippet")):
            extension.db.add_snippet(data["name"], data["content"], data["type_snippet"])
            callback = data.get("callback", "") 
            return RenderResultListAction([
                ExtensionResultItem(
                    icon=View.extension_icon,
                    name=f"Snippet '{data['name']}' adicionado ✅",
                    on_enter=SetUserQueryAction(callback ),
                    description=data["content"],
                    highlightable = False
                )
            ])
        return RenderResultListAction([ExtensionResultItem(icon=View.extension_icon, name=View.NAME, description="Enter: \"[set] <key> <value> | [get] <key>; [unset] | (or just) <key>\"")])






if __name__ == "__main__":
    SnippetsExtension().run()
