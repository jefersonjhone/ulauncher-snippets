# Snippets extension

![snippets usage](./images/snippets.gif)

## Dependencies

To use **{clipboard}** and **{selection}** placeholders, **xclip** is required. You can install it with:

&#96;&#96;&#96;bash
$ sudo apt update
$ sudo apt install xclip
&#96;&#96;&#96;

## Features

Snippets are defined in 3 different types:

- ***text***
- ***dynamic***
- ***templates***

### Text snippets

Text snippets are saved without any processing, they are constants.  
They can be referenced by other template snippets with **{snip:*name_to_your_snippet*}**

`a -> foo`

### Dynamic snippets

Dynamic snippets are saved as expressions and processed when used, applying placeholders, attributes, and modifiers.

`{date} -> 2025-09-04`

### Template snippets

Template snippets are also saved as expressions, but they await a value when used. They can combine *Text snippets* and placeholders, modifiers, and attributes from dynamic snippets.

`{{val|upper}} -> SOMEVALUE`

### Placeholders

The engine currently has **12** placeholders that can be used with native commands.

| Placeholder | Description |
|-------------|-------------|
| **now** | Current date  |
| **today** | Current date only |
| **time** | Current time only |
| **date** | Current date (YYYY-MM-DD) |
| **datetime** | Current date and time |
| **timestamp** | Unix timestamp |
| **uuid** | Random UUID |
| **user** | Current system user |
| **username** | Current username |
| **clipboard** | Current clipboard content (requires xclip) |
| **selection** | Current selection (requires xclip) |
| **hostname** | Current system hostname |

Placeholders can be used inside brackets `{x}` and will be replaced by their value when processed.  
They can also receive modifiers like `upper`, `lower`, etc.

Example:  
`{user|upper} -> USERNAME`

Datetime placeholders can receive *offset* and *format* attributes, for example:  

&#96;&#96;&#96;text
{date offset="+3d" format="%d/%m/%Y"}   -> 07/09/2025
{time offset="+2h -30m" format="%H:%M"} -> 14:30
{datetime format="%Y-%m-%d %H:%M:%S"}   -> 2025-09-04 12:45:00
&#96;&#96;&#96;

### Modifiers

Modifiers are functions that work on strings.  
The engine currently has **15** modifiers.

| Modifier | Description |
|----------|-------------|
| **upper** | Converts to UPPERCASE |
| **lower** | Converts to lowercase |
| **title** | Converts to Title Case |
| **capitalize** | Capitalizes first letter |
| **trim** | Removes whitespace from ends |
| **slug** | Converts to slug format |
| **camel** | Converts to camelCase |
| **snake** | Converts to snake_case |
| **quote** | Wraps in quotes |
| **reverse** | Reverses the string |
| **json** | Converts to JSON string |
| **urlenc** | URL encode |
| **urldec** | URL decode |
| **base64enc** | Base64 encode |
| **base64dec** | Base64 decode |

### Attributes

Currently only datetime placeholders have attributes defined, but it is possible to add helpful attributes to other placeholders in the future.

## Using

### add 
`-> add a simple text snippet`

Every text snippet can be used in a template.

### ads
`-> add a dynamic snippet`

Useful to manipulate date, clipboard, and selection, applying modifiers easily.  
**Every dynamic snippet must start with *!***

### adt 
`-> add a template snippet`

Templates can include text snippets and process them with modifiers.  
Parameters are defined with **{{}}** (named or not).  

- Example:  
  `{{val}} xpto {{val}}` with `val=something;` -> every *{{val}}* is replaced with *something*.  
  If you define `{{}} xpto {{}}` and pass `something`, only the first value is replaced, so you must pass `something1;something2;` to fill correctly.

**Every template snippet must start with *!t***  

It is possible to add a template from a file with a `-f` flag:  
`adt !t_*your_template* -f ~/*path/to/your/template.txt`  

The file must have a `.txt` extension and only needs to contain the template content.

Example:  

&#96;&#96;&#96;txt
{{title|upper}}
## introduction
{{introduction|title}}
## results
{{results}}

{date} {time} by {user} at {snip:email}
&#96;&#96;&#96;

And you type:

&#96;&#96;&#96;bash
s adt !t_headme -f ~/templates/headme.txt
&#96;&#96;&#96;

### del 
`-> delete a snippet`

Deletes any snippet, whatever the type.

### edit
`-> open an external editor to edit a snippet`

By default it opens *gnome-text-editor* because it keeps the process open until the user closes the window.  
This is necessary because a temporary file is generated with the snippet content, and if the editor closes the process early, the tempfile is deleted.

### list [name] [type]
`-> list all snippets filtering by name or type`

### use 
`-> use a template snippet`

Pass values to fill the template. Values are split by `;`.

### x 
`-> execute commands in the engine`

Execute quick commands in the engine, useful to test and speed up conversions.

## Specifications

### Database

Snippets are saved into an SQLite database to allow quick access and good performance.

### Process flow

The processing flow to fill a template is:

&#96;&#96;&#96;
[event - receive the values]
        ↓
[replace {snip:}]
        ↓
[replace {{}} with passed values]
        ↓
[evaluate {placeholders}]
        ↓
[apply attributes (offset, format...)]
        ↓
[apply modifiers]
        ↓
[return the result]
&#96;&#96;&#96;

### Limitations

- **Text editor**: currently only *gnome-text-editor* is supported (other editors are being tested).  
- **Clipboard and selection placeholders**: currently using xclip, which is limited to GNOME environments. Expanding support for Wayland is under testing.  