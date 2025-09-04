#!/usr/bin/env python3

import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import uuid
import json
import subprocess
import os
from urllib.parse import quote, unquote
import base64
import urllib.parse





class PlaceholderEngine:

  

    def __init__(self, user_variables=None):
        self.placeholder_regex = re.compile(r'\{([^}]+)\}')
        self.attribute_regex = re.compile(r'(\w+)=([^"\s]+|"[^"]*")')
        self.offset_regex = re.compile(r'([+-])(\d+)([ymdwhMs])')
        self.user_variables = user_variables or {}
        self.handlers = {
            "now": self.handle_now,
            "today": self.handle_today,
            "time": self.handle_time,
            "date": self.handle_date,
            "datetime": self.handle_datetime,
            "timestamp": self.handle_timestamp,
            "uuid": self.handle_uuid,
            "user": self.handle_user,
            "username": self.handle_username,
            "clipboard": self.handle_clipboard,
            "selection": self.handle_selection,
            "hostname": self.handle_hostname,
        }

    def expand_text(self, text):
        def replace_match(match):
            expression = match.group(1)
            
            parts = [p.strip() for p in expression.split('|') if p.strip()]

            name_part = parts[0] if parts else ""
            modifiers = parts[1:] if len(parts) > 1 else []

            value, expanded = self.resolve_expression(name_part)
            value, modified =  self.apply_modifiers(value, modifiers)
            expanded = expanded or modified

            return str(value) if expanded else match.group(0) 
        
        
        return self.placeholder_regex.sub(replace_match, text)
    

    def resolve_expression(self, name_part):
        if (name_part.startswith('"') and name_part.endswith('"')) or \
        (name_part.startswith("'") and name_part.endswith("'")):
            return name_part[1:-1], True

        if ' ' in name_part:
            name, attr_str = name_part.split(' ', 1)
            attributes = self.parse_attributes(attr_str)
        else:
            name, attributes = name_part, {}

        value = self.resolve_value(name.strip(), attributes)
        expanded = name in self.handlers  

        return value, expanded

    def resolve_value(self, name, attributes):
        handler = self.handlers.get(name)
        if handler:
            return handler(attributes)
        return f"{name}"



    def parse_attributes(self, attr_str):
        attributes = {}
        for attr_match in self.attribute_regex.finditer(attr_str):
            key = attr_match.group(1)
            value = attr_match.group(2).strip('"')
            attributes[key] = value
        return attributes

    def apply_date_offset(self, base_date, offset_str):
        matches = self.offset_regex.findall(offset_str)
        for sign, amount, unit in matches:
            amount = int(amount)
            if sign == '-':
                amount = -amount
            if unit == 's': 
                base_date += timedelta(seconds=amount)
            elif unit == 'm':
                base_date += timedelta(minutes=amount)
            elif unit == 'h':
                base_date += timedelta(hours=amount)
            elif unit == 'd':
                base_date += timedelta(days=amount)
            elif unit == 'M':
                base_date += relativedelta(months=amount)
            elif unit == 'y':
                base_date += relativedelta(years=amount)

        return base_date
        
    


    def apply_modifiers(self, value, modifiers):
        modified = False
        
        def slug_text(text):
            text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
            return text
        def snake_text(text):
            text = re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_').lower()
            return text
        def camel_text(text):
            words = re.split(r'[^a-zA-Z0-9]+', text)
            text = words[0].lower() + ''.join(word.title() for word in words[1:])
            return text
        def base64dec(text):
            try:
                return base64.b64decode(text.encode('utf-8')).decode('utf-8')
            except Exception as e:
                #__loguer__
                return value
        MODIFIERS = {
            "upper": str.upper,
            "lower": str.lower,
            "title": str.title,
            "capitalize": str.capitalize,
            "trim": str.strip,
            "slug": slug_text,
            "camel":camel_text,
            "snake": snake_text,
            "quote": lambda x: f'"{x}"',
            "reverse":lambda x:x[::-1],
            "json": json.dumps,
            "urlenc": urllib.parse.quote,
            "urldec": urllib.parse.unquote,
            "base64enc": lambda x:base64.b64encode(x.encode('utf-8')).decode('utf-8'),
            "base64dec": base64dec 
            }

        for mod in modifiers:
            modifier = MODIFIERS.get(mod)
            if modifier:
                modified = True
                value = modifier(value)

        return (value, modified)
    
    def handle_now(self, attributes):
        now = datetime.now()
        format_str = attributes.get("format", "%d de %B")
        return now.strftime(format_str)

    def handle_today(self, attributes):
        now = datetime.now()
        format_str = attributes.get("format", "%d/%m/%Y")
        return now.strftime(format_str)

    def handle_time(self, attributes):
        base_time = datetime.now()
        if "offset" in attributes:
            base_time = self.apply_date_offset(base_time, attributes["offset"])
        format_str = attributes.get("format", "%H:%M:%S")
        return base_time.strftime(format_str)

    def handle_date(self, attributes):
        base_date = datetime.now()
        if "offset" in attributes:
            base_date = self.apply_date_offset(base_date, attributes["offset"])
        format_str = attributes.get("format", "%Y-%m-%d")
        return base_date.strftime(format_str)

    def handle_datetime(self, attributes):
        now = datetime.now()
        format_str = attributes.get("format", "%d/%m/%Y %H:%M")
        return now.strftime(format_str)

    def handle_timestamp(self, attributes):
        return str(int(datetime.now().timestamp()))

    def handle_uuid(self, attributes):
        return str(uuid.uuid4())

    def handle_user(self, attributes):
        return os.getlogin()

    def handle_username(self, attributes):
        return os.getenv("USER", "")

    def handle_clipboard(self, attributes):
        try:
            return subprocess.check_output(
                ["xclip", "-selection", "clipboard", "-o"]
            ).decode("utf-8").strip()
        except Exception:
            return ""

    def handle_selection(self, attributes):
        try:
            return subprocess.check_output(
                ["xclip", "-selection", "primary", "-o"]
            ).decode("utf-8").strip()
        except Exception:
            return ""

    def handle_hostname(self, attributes):
        try:
            return subprocess.check_output(["hostname"]).decode("utf-8").strip()
        except Exception:
            return ""