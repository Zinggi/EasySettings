#-----------------------------------------------------------------------------------
# Easy Settings
#-----------------------------------------------------------------------------------
#
# This Plug-in helps you with editing the Sublime Text 2 setting files.
# It displays all available settings through auto-completion.
# It also displays the documentation of the just accepted setting.
#
# (c) Florian Zinggeler
#-----------------------------------------------------------------------------------
import sublime
import sublime_plugin
import json
import os


class EasySettings(sublime_plugin.EventListener):
    comments = []
    settings = {}
    b_did_autocomplete = False
    b_helper_panel_on = False
    help_panel_line_number = -1

    def is_setting_file(self, view):
        if view and view.file_name():
            return view.file_name().split('.')[-1] == "sublime-settings"
        return False

    def on_load(self, view):
        self.load_completions(view)

    def on_new(self, view):
        self.load_completions(view)

    def on_activated(self, view):
        self.load_completions(view)

    def load_completions(self, view):
        if self.is_setting_file(view):
            base_name = self.find_base_file(view.file_name().split('\\')[-1])
            self.settings = self.parse_setting(base_name)

    # search for the base settings file
    def find_base_file(self, filename):
        for root, dirs, files in os.walk(sublime.packages_path()):
            if filename in files:
                if os.path.join(root, filename).split('\\')[-2] != "User":
                    print "found: %s" % os.path.join(root, filename)
                    return os.path.join(root, filename)

    # parse the setting file and capture comments
    def parse_setting(self, filename):
        current_comment = ""
        with open(filename) as f:
            content = ""
            for line in f:
                if "//" == line.strip()[:2]:
                    current_comment += line
                else:
                    content += line.split('//')[0]
                    if current_comment != "":
                        current_comment += line.rstrip()
                        self.comments.append(current_comment)
                        current_comment = ""
            # Return json file
            return json.loads(content)

    # gets called when auto-completion pops up.
    def on_query_completions(self, view, prefix, locations):
        if self.is_setting_file(view):
            return self.get_autocomplete_list(prefix)

    # gets called when auto-completion is triggered
    def on_query_context(self, view, key, operator, operand, match_all):
        if self.is_setting_file(view):
            if key == "show_documentation":
                region = view.sel()[0]
                if region.empty():
                    self.b_did_autocomplete = True

    # remove auto completion and insert dynamic snippet instead, just after auto completion
    def on_modified(self, view):
        if self.is_setting_file(view):
            # if the helper panel has just been displayed, save the line number
            if self.b_helper_panel_on:
                self.help_panel_line_number = view.rowcol(view.sel()[0].begin())[0]
                self.b_helper_panel_on = False

            elif self.help_panel_line_number != -1:
                # if we are modifying anything above or below the helper panel line, hide the panel.
                if view.rowcol(view.sel()[0].begin())[0] != self.help_panel_line_number:
                    view.window().run_command("hide_panel", {"panel": "output.settings_documentation_panel"})
                    self.help_panel_line_number = -1

            if self.b_did_autocomplete:
                self.b_did_autocomplete = False
                region_line = view.line(view.sel()[0])
                word = view.substr(region_line).strip()
                view.window().run_command("hide_panel", {"panel": "output.settings_documentation_panel"})
                panel = view.window().get_output_panel('settings_documentation_panel')
                panel_edit = panel.begin_edit()
                panel.insert(panel_edit, panel.size(), self.get_documentation_for(word))
                panel.end_edit(panel_edit)
                panel.show(panel.size())
                view.window().run_command("show_panel", {"panel": "output.settings_documentation_panel"})
                self.b_helper_panel_on = True

    # This will return all settings found in the base settings
    def get_autocomplete_list(self, word):
        autocomplete_list = []

        for s in self.settings:
            autocomplete_list.append((s + "\tsetting", "\"" + s + "\": "))

        return autocomplete_list

    def get_documentation_for(self, word):
        for c in self.comments:
            print c.split("\n")[-1]
            prop = c.split("\n")[-1]
            if word in prop:
                # print c
                c = "\n".join(c.split("\n")[:-1])
                c += self.get_default_as_string(prop.strip().split(':')[0][1:-1])
                return c
        return ""

    def get_default_as_string(self, prop):
        value = self.settings[prop]
        prettyValue = json.dumps({prop: value}, sort_keys=True, indent=4)
        prettyValue = prettyValue[1:-2]
        return prettyValue
