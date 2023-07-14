import subprocess
import os
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from colorama import init, Fore, Style
from fuzzywuzzy import fuzz, process
from pyfiglet import Figlet
from rich import print
from rich.console import Console
from rich.theme import Theme
from rich.text import Text
from rich.style import StyleType
from rich.syntax import Syntax
import emojis
import spacy

class FolderIcon:
    def __init__(self):
        self.icon_map = {
            "default": emojis.encode(":file_folder:"),
            "home": emojis.encode(":house_with_garden:"),
            "desktop": emojis.encode(":desktop_computer:"),
            "documents": emojis.encode(":page_facing_up:"),
            "downloads": emojis.encode(":arrow_down:"),
        }

    def get_icon(self, folder_name):
        # Remove leading and trailing whitespace, and convert to lowercase
        folder_name = folder_name.strip().lower()

        if folder_name == "":
            return self.icon_map["default"]

        if folder_name in self.icon_map:
            return self.icon_map[folder_name]

        return self.icon_map["default"]


class Shell:
    def __init__(self):
        self.command_history = []
        self.figlet = Figlet()
        self.init_colorama()
        self.init_rich()
        self.cwd = os.getcwd()
        self.folder_icon = FolderIcon()
        self.nlp = spacy.load("en_core_web_sm")

    @staticmethod
    def init_colorama():
        init()

    def init_rich(self):
        theme = Theme({
            "info": "green",
            "warning": "yellow",
            "error": "red",
        })
        self.console = Console(theme=theme)

    def run_command(self, command):
        if command.startswith("cd"):
            self.change_directory(command)
        elif command == "vim":
            self.toggle_vim_mode()
        elif command == "neofetch":
            os.system("neofetch")
        else:
            try:
                process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)

                for line in process.stdout:
                    self.print_output_with_color(line)

            except subprocess.CalledProcessError as e:
                print(f"[error]{e.output}[/error]")
 

    def print_output_with_color(self, line):
        if line.startswith("d"):
            folder_name = line.rstrip()
            icon = self.folder_icon.get_icon(folder_name)
            self.console.print(f"{icon} {folder_name}")
        else:
            self.console.print(line.rstrip())

    def change_directory(self, command):
        args = command.split(" ")
        if len(args) == 1:
            # No directory path provided, change to the home directory
            os.chdir(os.path.expanduser("~"))
        elif len(args) == 2:
            # Change to the specified directory
            dir_path = args[1]
            try:
                os.chdir(dir_path)
            except FileNotFoundError:
                print(f"[error]Directory not found: {dir_path}[/error]")
        else:
            print("[error]Invalid cd command[/error]")

    def auto_correct_command(self, command, command_history):
        best_match, score = process.extractOne(command, command_history)
        threshold = 80

        if score >= threshold:
            confirmation = prompt(f"Did you mean '{best_match}' instead of '{command}'? (y/n) ")
            if confirmation.lower() in ["y", "yes"]:
                return best_match

        return command

    def perform_nlp_task(self, command):
        doc = self.nlp(command)

        # Tokenization
        tokens = [token.text for token in doc]
        self.console.print(f"[info]Tokens: {tokens}[/info]")

        # Part-of-speech tagging
        pos_tags = [(token.text, token.pos_) for token in doc]
        self.console.print(f"[info]Part-of-Speech Tags: {pos_tags}[/info]")

        # Named Entity Recognition
        entities = [(entity.text, entity.label_) for entity in doc.ents]
        self.console.print(f"[info]Entities: {entities}[/info]")

    def get_commands_completer(self):
        class CommandCompleter(Completer):
            def __init__(self, commands):
                self.commands = commands

            def get_completions(self, document, complete_event):
                text_before_cursor = document.text_before_cursor

                for command in self.commands:
                    if command.startswith(text_before_cursor):
                        yield Completion(command, start_position=-len(text_before_cursor))

        return CommandCompleter(self.command_history)

    def run_terminal_emulator(self):
        kb = KeyBindings()

        @kb.add('c-c')
        @kb.add('c-d')
        def _(event):
            event.app.exit()

        session = PromptSession(
            key_bindings=kb,
            history=InMemoryHistory(),
            auto_suggest=AutoSuggestFromHistory(),
            completer=self.get_commands_completer()
        )

        self.console.print(self.figlet.renderText("X-Term"))

        while True:
            self.cwd = os.getcwd()
            prompt_text = f"{self.folder_icon.get_icon('home')} {self.cwd} >>> "
            command_to_run = session.prompt(prompt_text, bottom_toolbar='Press Ctrl+C to exit')

            if command_to_run.lower() == "exit":
                break

            self.command_history.append(command_to_run)
            self.command_history = self.command_history[-5:]

            if command_to_run not in self.command_history:
                corrected_command = self.auto_correct_command(command_to_run, self.command_history)
                if corrected_command != command_to_run:
                    command_to_run = corrected_command

            if command_to_run.startswith("nlp"):
                self.perform_nlp_task(command_to_run)
            else:
                self.run_command(command_to_run)


if __name__ == "__main__":
    shell = Shell()
    shell.run_terminal_emulator()

