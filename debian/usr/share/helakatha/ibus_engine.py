#!/usr/bin/env python3
# ibus_engine.py
# A native IBus Input Method Engine for HelaKatha.
# This integrates HelaKatha natively into Linux keyboard layouts.

import sys
import gi
gi.require_version('IBus', '1.0')
from gi.repository import IBus, GLib

# Import local transliteration engine
from engine import TransliterationEngine

class HelaKathaEngine(IBus.Engine):
    def __init__(self):
        super().__init__()
        self.engine = TransliterationEngine()
        self.buffer = ""
        
    def do_process_key_event(self, keyval, keycode, state):
        # Mask out system hotkeys (Ctrl/Alt/Super modifier combinations)
        modifiers = state & (IBus.ModifierType.CONTROL_MASK | IBus.ModifierType.ALT_MASK | IBus.ModifierType.SUPER_MASK)
        if modifiers != 0:
            return False # Let system hotkeys pass through

        val_char = IBus.keyval_to_unicode(keyval)
        char = chr(val_char) if val_char else None
        
        # Commit on Space or Enter
        if keyval == IBus.KEY_space or keyval == IBus.KEY_Return:
            if self.buffer:
                candidates = self.engine.get_candidates(self.buffer)
                if candidates:
                    self.commit_text(IBus.Text.new_from_string(candidates[0] + (" " if keyval == IBus.KEY_space else "")))
                self.buffer = ""
                self.update_preedit()
                return True
            return False
            
        # Backspace deletes characters in preedit buffer
        if keyval == IBus.KEY_BackSpace:
            if self.buffer:
                self.buffer = self.buffer[:-1]
                self.update_preedit()
                return True
            return False
            
        # Alphanumeric layout keys
        if char and (char.isalnum() or char in (')', '/', '\\', '-')):
            # Direct candidate numeric selection (1-5)
            if self.buffer and char in ('1', '2', '3', '4', '5'):
                index = int(char) - 1
                candidates = self.engine.get_candidates(self.buffer)
                if index < len(candidates):
                    self.commit_text(IBus.Text.new_from_string(candidates[index]))
                self.buffer = ""
                self.update_preedit()
                return True
                
            self.buffer += char
            self.update_preedit()
            return True
            
        return False
        
    def update_preedit(self):
        if self.buffer:
            candidates = self.engine.get_candidates(self.buffer)
            preedit_text = f"{self.buffer} -> {candidates[0]}"
            text = IBus.Text.new_from_string(preedit_text)
            self.update_preedit_text(text, len(preedit_text), True)
        else:
            self.clear_preedit_text()
            
class HelaKathaComponent:
    def __init__(self):
        self.mainloop = GLib.MainLoop()
        self.bus = IBus.Bus()
        self.factory = IBus.Factory.new(self.bus.get_connection())
        self.factory.add_engine("helakatha-singlish", HelaKathaEngine)
        self.bus.request_name("org.freedesktop.IBus.HelaKatha", 0)
        
    def run(self):
        self.mainloop.run()
        
if __name__ == "__main__":
    IBus.init()
    component = HelaKathaComponent()
    component.run()
