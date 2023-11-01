import os
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import NumericProperty
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
import json
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivymd.app import MDApp
LabelBase.register(name="mob_font", fn_regular="mob.ttf")

class SplashScreen(Screen):
    def on_pre_enter(self):
        self.background_music = SoundLoader.load('background.mp3')
        if self.background_music:
            self.background_music.play()

    def __init__(self, **kwargs):
        super(SplashScreen, self).__init__(**kwargs)
        Clock.schedule_once(self.switch_to_contestant, 10)

    def switch_to_contestant(self, dt):
        self.manager.current = "contestant"

class ContestantScreen(Screen):
    def on_pre_enter(self, *args):
        self.current_contestant = 0
        self.update_contestant_details()

    def update_contestant_details(self):
        if 0 <= self.current_contestant < len(app.contestants):
            contestant = app.contestants[self.current_contestant]
            self.ids.contestant_id.text = f"Contestant  {self.current_contestant + 1}"
            self.ids.contestant_name.text = contestant['Name'].upper()
            self.ids.contestant_age.text = f"Age: {contestant['Age']}"
            self.ids.contestant_branch.text = f"Branch: {contestant['Branch']}"
            self.ids.contestant_school.text = f"School: {contestant['School']}"
            self.ids.contestant_class.text = f"Class: {contestant['Class']}"
            self.ids.contestant_career.text = f"Career Choice: {contestant['Choice of Career']}"
            self.ids.contestant_pics.source = contestant['Image']

    def load_next_contestant(self):
        self.current_contestant += 1
        self.update_contestant_details()

    def load_previous_contestant(self):
        self.current_contestant -= 1
        self.update_contestant_details()

    def start_quiz(self):
        self.manager.current = "question"

class CustomButton(Button):
    def __init__(self, **kwargs):
        super(CustomButton, self).__init__(**kwargs)
        self.manager = None  # Reference to the screen manager
    
    def set_manager(self, manager):
        self.manager = manager

    def animate_correct_answer(self):
        self.flash_count = 0
        correct_sound = SoundLoader.load('correct.mp3')
        if correct_sound:
            correct_sound.play()
        self.flash_background_color((0, 1, 0, 1), 10, 0.3)

    def animate_incorrect_answer(self):
        self.flash_count = 0
        incorrect_sound = SoundLoader.load('wrong.wav')
        if incorrect_sound:
            incorrect_sound.play()
        self.flash_background_color((1, 0, 0, 1), 10, 0.3)

    def flash_background_color(self, target_color, flash_count, flash_duration):
        if self.flash_count < flash_count:
            animation = Animation(background_color=target_color, duration=flash_duration) + Animation(background_color=(1, 1, 1, 1), duration=flash_duration)
            animation.start(self)
            self.flash_count += 1
            Clock.schedule_once(lambda dt: self.stop_flash(), flash_duration * 2)

    def stop_flash(self):
        self.flash_count = 0
        Animation.cancel_all(self)

class QuestionScreen(Screen):
    current_question = NumericProperty(0)
    current_contestant = NumericProperty(0)

    def on_pre_enter(self, *args):
        self.current_question = 0
        self.current_contestant = 0
        self.load_question()

    def reset_question_button_color(self):
        # Define your list of question buttons
        button1 = self.ids.option1
        button2 = self.ids.option2
        button3 = self.ids.option3
        question_buttons = [button1, button2, button3]
        for button in question_buttons:
            if isinstance(button, CustomButton):
                button.background_color = (1, 1, 1, 1)

    def load_question(self):
        if 0 <= self.current_question < len(app.questions) and 0 <= self.current_contestant < len(app.scoreboard_data):
            question = app.questions[self.current_question]
            question_text = self.ids.question_text
            option1 = self.ids.option1
            option2 = self.ids.option2
            option3 = self.ids.option3

            question_text.text = question["question"]
            option1.text = question["options"][0]
            option2.text = question["options"][1]
            option3.text = question["options"][2]

            # Set the screen manager reference for the CustomButton instances
            for option in [option1, option2, option3]:
                option.set_manager(self.manager)

            # Update the contestant information
            contestant = app.scoreboard_data[self.current_contestant]
            self.ids.contestant_id.text = f"Contestant: {contestant['name']}"
            self.ids.contestant_score.text = f"Score: {contestant['score']}"

    def check_answer(self, instance):
        self.reset_question_button_color()
        current_question = app.questions[self.current_question]
        selected_option = instance.text
        correct_option = current_question["correct_option"]

        if selected_option == correct_option:
            instance.animate_correct_answer()
            self.update_score(1)  # Correct answer, increment score by 1
        else:
            instance.animate_incorrect_answer()
            self.update_score(0)  # Incorrect answer, no score change

        self.current_question += 1  # Move to the next question

        if self.current_question >= len(app.questions):
            # Move to the next contestant when all questions are answered
            self.current_question = 0
            self.current_contestant += 1
            if self.current_contestant >= len(app.scoreboard_data):
                # All contestants have answered all questions, move to the scoreboard screen
                self.manager.current = "scoreboard"
            else:
                self.load_question()
        else:
            self.load_question()

    def update_score(self, score_change):
        if 0 <= self.current_contestant < len(app.scoreboard_data):
            contestant = app.scoreboard_data[self.current_contestant]
            current_score = contestant.get("score", 0)
            current_score += score_change
            contestant["score"] = current_score  # Update the score in the scoreboard data
            self.save_score()  # Save the updated score

    def save_score(self):
        with open("scoreboard.json", "w") as file:
            json.dump(app.scoreboard_data, file)


# class ScoreboardScreen(Screen):
#     def on_pre_enter(self, *args):
#         self.generate_scoreboard()

#     def generate_scoreboard(self):
#         # Read scores from the scoreboard.json file
#         with open("scoreboard.json") as file:
#             scoreboard_data = json.load(file)

#         # Sort contestants by score in descending order
#         sorted_scoreboard = sorted(scoreboard_data, key=lambda x: x['score'], reverse=True)

#         # Create a layout for the scoreboard
#         scoreboard_layout = GridLayout(cols=2, spacing=10, padding=10, size_hint_y=None)
#         scoreboard_layout.bind(minimum_height=scoreboard_layout.setter('height'))

#         for position, contestant in enumerate(sorted_scoreboard, start=1):
#             name = contestant['name']
#             score = contestant['score']

#             # Create labels to display contestant's name and score
#             name_label = Label(text=f"{position}. {name}", font_name="mob_font", font_size='25sp')
#             score_label = Label(text=f"Score: {score}", font_name="mob_font", font_size='25sp')

#             # Add labels to the scoreboard layout
#             scoreboard_layout.add_widget(name_label)
#             scoreboard_layout.add_widget(score_label)

#         # Create a ScrollView to scroll through the scoreboard
#         scoreboard_scroll = ScrollView(size_hint=(None, None), size=(600, 400), bar_width='10dp')
#         scoreboard_scroll.add_widget(scoreboard_layout)

#         # Add the ScrollView to the Screen
#         self.add_widget(scoreboard_scroll)

class QuizApp(MDApp):
    contestants = []
    current_contestant = 0
    questions = []
    scoreboard_data = []  # Initialize an empty scoreboard data

    def on_start(self):
        with open("contestants.json") as file:
            self.contestants = json.load(file)

        with open("questions.json", 'r', encoding='utf-8') as file:
            self.questions = json.load(file)

        # Create or update the scoreboard JSON file
        self.create_or_update_scoreboard()

        # Load sound effects
        self.correct_sound = SoundLoader.load("correct.wav")
        self.incorrect_sound = SoundLoader.load("incorrect.wav")

    def create_or_update_scoreboard(self):
        # Create the scoreboard JSON file and initialize scores to 0
        scoreboard_data = []
        for contestant in self.contestants:
            scoreboard_data.append({"id": self.contestants.index(contestant), "name": contestant["Name"], "score": 0})

        # Save the scoreboard data to the JSON file (overwriting if it already exists)
        with open("scoreboard.json", "w") as scoreboard_file:
            json.dump(scoreboard_data, scoreboard_file)

    def build(self):
        # Maximize the window when the application starts
        Window.maximize()
        return Builder.load_file("quiz.kv")

if __name__ == "__main__":
    app = QuizApp()
    app.run()
