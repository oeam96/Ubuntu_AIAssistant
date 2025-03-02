#!/usr/bin/env python3

import sys
import requests
import threading
import gi
import os
import json
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango

class AIAssistant(Gtk.Window):
    def __init__(self):
        super().__init__(title="AI Assistant")
        self.set_border_width(10)
        self.set_default_size(600, 400)
        
        # Apply dark theme
        settings = Gtk.Settings.get_default()
        settings.set_property("gtk-application-prefer-dark-theme", True)
        
        # Apply CSS styling (dark background with default text appearance)
        css_provider = Gtk.CssProvider()
        css = b"""
        window {
            background-color: #2E3436;
        }
        textview {
            font-family: Sans;
            font-size: 12pt;
            color: #000000;
            padding: 10px;
        }
        entry {
            font-size: 12pt;
            padding: 5px;
        }
        button {
            font-size: 12pt;
            padding: 5px;
        }
        """
        css_provider.load_from_data(css)
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(screen, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        # Main vertical box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)

        # Text view for displaying conversation
        self.textview = Gtk.TextView()
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.textview.set_editable(False)
        self.textbuffer = self.textview.get_buffer()
        
        # Create a bold tag for user input
        self.bold_tag = self.textbuffer.create_tag("bold", weight=Pango.Weight.BOLD)
        
        # Scrolled window for text view
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_hexpand(True)
        scrolled_window.set_vexpand(True)
        scrolled_window.add(self.textview)
        vbox.pack_start(scrolled_window, True, True, 0)

        # Entry for user input
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Type your message here...")
        self.entry.connect("activate", self.on_enter)
        vbox.pack_start(self.entry, False, False, 0)

        # Button to send message
        send_button = Gtk.Button(label="Send")
        send_button.connect("clicked", self.on_enter)
        vbox.pack_start(send_button, False, False, 0)

        # Initialize variables to store the offsets for the "Loading..." text
        self.loading_start_offset = None
        self.loading_end_offset = None
        
        self.show_all()

    def append_user_text(self, text):
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert_with_tags(end_iter, text, self.bold_tag)
        mark = self.textbuffer.create_mark(None, self.textbuffer.get_end_iter(), False)
        self.textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)

    def append_text(self, text):
        end_iter = self.textbuffer.get_end_iter()
        self.textbuffer.insert(end_iter, text)
        mark = self.textbuffer.create_mark(None, self.textbuffer.get_end_iter(), False)
        self.textview.scroll_to_mark(mark, 0.0, True, 0.0, 1.0)
        return False

    def on_enter(self, widget):
        user_input = self.entry.get_text().strip()
        if user_input:
            self.entry.set_text("")
            GLib.idle_add(self.append_user_text, f"You: {user_input}\n")
            threading.Thread(target=self.get_response, args=(user_input,)).start()

    def insert_loading_marker(self):
        # Record the starting offset before insertion
        start_offset = self.textbuffer.get_char_count()
        self.textbuffer.insert(self.textbuffer.get_end_iter(), "Loading...")
        # Store the start and end offsets for the "Loading..." text
        self.loading_start_offset = start_offset
        self.loading_end_offset = start_offset + len("Loading...")

    def remove_loading_marker(self):
        if (self.loading_start_offset is not None and 
            self.loading_end_offset is not None and
            self.textbuffer.get_char_count() >= self.loading_end_offset):
            start_iter = self.textbuffer.get_iter_at_offset(self.loading_start_offset)
            end_iter = self.textbuffer.get_iter_at_offset(self.loading_end_offset)
            self.textbuffer.delete(start_iter, end_iter)
            self.loading_start_offset = None
            self.loading_end_offset = None

    def get_response(self, prompt):
        GLib.idle_add(self.append_text, "Assistant: ")
        GLib.idle_add(self.insert_loading_marker)
        
        response_gen = self.call_ollama_api(prompt)
        first_token = True
        for token in response_gen:
            if first_token:
                GLib.idle_add(self.remove_loading_marker)
                first_token = False
            GLib.idle_add(self.append_text, token)
        GLib.idle_add(self.append_text, '\n')

    def call_ollama_api(self, prompt):
        system_prompt = (
            "You are a personal assistant. Your tasks include answering questions, providing advice, "
            "summarizing information, and engaging in thoughtful conversation. "
            "Be precise, helpful, and maintain a friendly tone."
        )
        combined_prompt = f"{system_prompt}\nUser: {prompt}\nAssistant:"
        
        url = "http://localhost:11434/api/generate"
        headers = {'Content-Type': 'application/json'}
        payload = {
            "model": "llama3.1:8b",
            "prompt": combined_prompt,
            "temperature": 0.5,
        }
        try:
            with requests.post(url, json=payload, headers=headers, stream=True) as response:
                if response.status_code == 200:
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8').strip()
                            try:
                                data = json.loads(decoded_line)
                                if data.get('done'):
                                    break
                                token = data.get('response', '')
                                yield token
                            except json.JSONDecodeError:
                                yield decoded_line
                else:
                    yield f"Error: {response.status_code} {response.text}"
        except requests.exceptions.RequestException as e:
            yield f"Exception: {e}"

def main():
    app = AIAssistant()
    app.connect("destroy", Gtk.main_quit)
    Gtk.main()

if __name__ == '__main__':
    main()

