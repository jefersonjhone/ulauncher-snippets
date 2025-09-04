class View:
        
    extension_icon =  "images/snippet_purple.png"

    snippet_icon_purple = "images/snippet_purple.png"
    snippet_icon_red = "images/snippet_red.png"

    template_icon_purple = "images/template_purple.png"
    template_icon_red = "images/template_red.png"

    search_icon_purple = "images/search_purple.png"
    search_icon_red = "images/search_red.png"

    copy_icon_purple = "images/clipboard_purple.png"
    copy_icon_red = "images/clipboard_red.png"

    NAME = "Snippets"
    actions = [
        {
            "icon": extension_icon,
            "name": "Add new simple text snippet",
            "desc": "add",
            "cmd": "add "
        },
        {
            "icon": search_icon_purple,
            "desc": "list",
            "name": "List all snippets",
            "cmd": "list ",
        },
        {
            "icon": extension_icon,
            "name": "Delete snippet",
            "desc": "del ",
            "cmd": "del ",
        },
        {
            "icon": extension_icon,
            "name": "Add a dinamic snippet",
            "desc": "ads ",
            "cmd": "ads ",
        },
        {
            "icon": template_icon_purple,
            "name": "Add a dinamic template snippet",
            "desc": "adt ",
            "cmd": "adt ",
        },
        {
            "icon": template_icon_purple,
            "name": "Use a dinamic template snippet",
            "desc": "use ",
            "cmd": "use ",
        },
        {
            "icon": extension_icon,
            "name": "Execute a command into snippet engine",
            "desc": "x ",
            "cmd": "x ",
        },
    ]


