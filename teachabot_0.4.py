from kivy.app import App
from kivy.uix.screenmanager import Screen
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.uix.popup import Popup
from kivy.uix.boxlayout import BoxLayout

from kivmob import KivMob, TestIds
import random


# This class is an improved version of Label
# Kivy does not provide scrollable label, so we need to create one
class ScrollableLabel(ScrollView):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # ScrollView does not allow us to add more than one widget, so we need to trick it
        # by creating a layout and placing two widgets inside it
        # Layout is going to have one collumn and and size_hint_y set to None,
        # so height wo't default to any size (we are going to set it on our own)
        self.layout = GridLayout(cols=1, size_hint_y=None, size_hint_x = 1, height=GridLayout().minimum_height)
        self.add_widget(self.layout)

        # Now we need two wodgets - Label for chat history and 'artificial' widget below
        # so we can scroll to it every new message and keep new messages visible
        # We want to enable markup, so we can set colors for example
        self.chat_history = Label(size_hint_y=None, text_size=(self.width, None), height=Label().texture_size[1],  markup=True)
        self.scroll_to_point = Label()

        # We add them to our layout
        self.layout.add_widget(self.chat_history)
        self.layout.add_widget(self.scroll_to_point)

    # Methos called externally to add new message to the chat history
    def update_chat_history(self, message):

        # First add new line and message itself
        self.chat_history.text += '\n' + message

        # Set layout height to whatever height of chat history text is + 15 pixels
        # (adds a bit of space at teh bottom)
        # Set chat history label to whatever height of chat history text is
        # Set width of chat history text to 98 of the label width (adds small margins)
        self.layout.height = self.chat_history.texture_size[1] + 40
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)

        # As we are updating above, text height, so also label and layout height are going to be bigger
        # than the area we have for this widget. ScrollView is going to add a scroll, but won't
        # scroll to the botton, nor there is a method that can do that.
        # That's why we want additional, empty wodget below whole text - just to be able to scroll to it,
        # so scroll to the bottom of the layout
        self.scroll_to(self.scroll_to_point)

    def update_chat_history_layout(self, _=None):
        # Set layout height to whatever height of chat history text is + 15 pixels
        # (adds a bit of space at the bottom)
        # Set chat history label to whatever height of chat history text is
        # Set width of chat history text to 98 of the label width (adds small margins)
        self.layout.height = self.chat_history.texture_size[1] + 15
        self.chat_history.height = self.chat_history.texture_size[1]
        self.chat_history.text_size = (self.chat_history.width * 0.98, None)
        
        
class ChatPage(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # We are going to use 1 column and 2 rows
        self.cols = 1
        self.rows = 3
        
        #for now, just me as user can use screen manager and shit in future to ask for user ame first
        self.username = 'User'

        #set window to softinput
        Window.softinput_mode = 'pan'

        # First row is going to be occupied by our scrollable label
        # We want it be take 90% of app height
        self.history = ScrollableLabel(height=Window.size[1]*0.8, size_hint_y=None)
        self.add_widget(self.history)

        #add a godd answwr/ bad answer button
        self.good_answer = Button(text='Good Answer')
        #self.good_answer.bind(on_press=self.interpret_button('good'))
        self.good_answer.bind(on_press= lambda *args: self.interpret_button('good'))#, *args))
        
        self.bad_answer = Button(text='Bad Answer')
        #self.bad_answer.bind(on_press=self.interpret_button('bad'))
        self.bad_answer.bind(on_press= lambda *args: self.interpret_button('bad'))#, *args))
        
        #adding the buttons into the line
        middle_line = GridLayout(cols=2)
        middle_line.add_widget(self.good_answer)
        middle_line.add_widget(self.bad_answer)
        #Adding the whole middle line into the main grid
        self.add_widget(middle_line)

        
        # In the second row, we want to have input fields and Send button
        # Input field should take 80% of window width
        # We also want to bind button click to send_message method
        self.new_message = TextInput(width=Window.size[0]*0.8, size_hint_x=None, multiline=False)
        self.send = Button(text="Send")
        self.send.bind(on_press=self.send_message)

        self.help = Button(text='?')
        self.help.bind(on_press=TeachABot().readme)

        # To be able to add 2 widgets into a layout with just one collumn, we use additional layout,
        # add widgets there, then add this layout to main layout as second row
        bottom_line = GridLayout(cols=3)
        bottom_line.add_widget(self.new_message)
        bottom_line.add_widget(self.send)
        bottom_line.add_widget(self.help)
        self.add_widget(bottom_line)

        # To be able to send message on Enter key, we want to listen to keypresses
        Window.bind(on_key_down=self.on_key_down)

        # We also want to focus on our text input field
        # Kivy by default takes focus out out of it once we are sending message
        # The problem here is that 'self.new_message.focus = True' does not work when called directly,
        # so we have to schedule it to be called in one second
        # The other problem is that schedule_once() have no ability to pass any parameters, so we have
        # to create and call a function that takes no parameters
        Clock.schedule_once(self.focus_text_input, 1)

        # And now, as we have out layout ready and everything set, we can start listening for incimmong messages
        # Listening method is going to call a callback method to update chat history with new messages,
        # so we have to start listening for new messages after we create this layout
        #socket_client.start_listening(self.incoming_message, show_error)

        self.bind(size=self.adjust_fields)

        self.history.update_chat_history('[Please click on the "?" to better understand how to use this Bot]')



        #flag to determine whether the input is a question or an answqer to the bot
        #self.question_flag = True        

    # Updates page layout
    def adjust_fields(self, *_):

        # Chat history height - 90%, but at least 50px for bottom new message/send button part
        if Window.size[1] * 0.1 < 50:
            new_height = Window.size[1] - 50
        else:
            new_height = Window.size[1] * 0.8
        self.history.height = new_height

        # New message input width - 80%, but at least 160px for send button
        if Window.size[0] * 0.2 < 160:
            new_width = Window.size[0] - 160
        else:
            new_width = Window.size[0] * 0.8
        self.new_message.width = new_width

        # Update chat history layout
        #self.history.update_chat_history_layout()
        Clock.schedule_once(self.history.update_chat_history_layout, 0.01)

        
    # Gets called on key press
    def on_key_down(self, instance, keyboard, keycode, text, modifiers):

        # But we want to take an action only when Enter key is being pressed, and send a message
        if keycode == 40:
            self.send_message(None)

    # Gets called when either Send button or Enter key is being pressed
    # (kivy passes button object here as well, but we don;t care about it)
    def send_message(self, _):

        # Get message text and clear message input field
        message = self.new_message.text
        self.new_message.text = ''

        # If there is any message - add it to chat history and send to the server
        if message:
            # Our messages - use red color for the name
            self.history.update_chat_history('[color=dd2020]{}: [/color] > {}'.format(self.username, message))
            #HERE WHERE I CHANCGE SATUFF LATER/socket_client.send(message)

            #interprets what t do with the user input
            self.interpret_message(message)
          
        # As mentioned above, we have to shedule for refocusing to input field
        Clock.schedule_once(self.focus_text_input, 0.1)



    #interpret button pressed, good or bad
    def interpret_button(self, button):
        lines = self.history.chat_history.text.split('\n')
        bot_brain = Brain(self.username)

        user_len = len('[color=dd2020]{}: [/color] > '.format(self.username))
        bot_len = len('[color=20dd20]Bot: [/color] > ')

        #the last line will be the bots answer thats good or bad
        #as a safe check, make sure the last line is actually by the bot
        #AND the line before that is by user
        #AND that the bot line isnt the learning/correcting lines
        if 'Bot: ' in lines[-1] and '[Learning...]' not in lines[-1] and '[Correcting...]' not in lines[-1] and 'Bot: ' not in lines[-2]:
        #['Yay you remembered', 'Correct!', 'Your memory is better than mine'] theres a problem with this but i just try/except it    
            #if the good answer button was pressed
            if button == 'good':
                try:
                    key = lines[-2][user_len:] #the question
                    good_answer = lines[-1][bot_len:]
                    #reinforce to the bot that it is a good answer
                    #in practice it add a duplicte entry, so it will say it more ofthen by random
                    bot_brain.update_entry(key, good_answer)

                    prompt = '[Reinforced]'
                    self.history.update_chat_history('{}'.format(prompt))
                except:
                    pass

                

            #if the bad was pressed
            elif button == 'bad':
                try:
                    key = lines[-2][user_len:] #the question that bot answred badly
                    bad_answer = lines[-1][bot_len:]

                    #ask what is the correct response
                    ask = 'What would be the correct response for: ' + key
                    self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', ask))

                except:
                    pass

                
        #special case if the bot asked a question before the user managed to press the button
        elif lines[-1][bot_len:].strip() in list(bot_brain.brain) and '[Learning...]' not in lines[-2] and '[Correcting...]' not in lines[-2] and 'User: ' in lines[-3]:
            if button == 'good':
                try:
                    key = lines[-3][user_len:]
                    good_answer = lines[-2][bot_len:]
                    bot_brain.update_entry(key, good_answer)
                    prompt = '[Reinforced]'
                    self.history.update_chat_history('{}'.format(prompt))
                except:
                    pass

            elif button == 'bad':
                try:
                    key = lines[-3][user_len:] #the question that bot answred badly
                    bad_answer = lines[-2][bot_len:]

                    #ask what is the correct response
                    ask = 'What would be the correct response for: ' + key
                    self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', ask))

                except:
                    pass    
        

        #else just skip it, do nothing
        
        

    #interpret whether is a messagfe a question or an answer to a question by the bot
    def interpret_message(self, message):
        rand_lst = [1,2]
        
        lines = self.history.chat_history.text.split('\n')
        #print(lines)
        bot_brain = Brain(self.username)

        #to skip answering a question
        if message == '/skip':
            answer = '[Skipped]'
            self.history.update_chat_history('{}'.format(answer))

        #to clear and wipe the memory, start new
        elif message == '/wipe':
            answer = '[Memory wiped]'
            bot_brain.wipe_memory()
            
            self.history.update_chat_history('{}'.format(answer))

        #doesnt work
##        elif message == '/clear':
##            answer = '[Clearing chat history]'
##            self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))
##            #clears history, by replacing it with a new one
##            self.history = ScrollableLabel(height=Window.size[1]*0.8, size_hint_y=None)
            
        
        else:
            #to reduce the chance the person is like talking to the bot humnalike
            if message[:4].lower() == 'say ':
                message = message[4:]

            elif message[:7].lower() == 'you say ':
                message = message[7:]

            elif message[:15].lower() == 'you should say ':
                message = message[15:]

            #elif message[].lower() == 'answer ':

            elif message[:17].lower() == 'answer by saying ':
                message = message[17:]

            elif message[:18].lower() == 'you should answer ':
                message = message[18:]

            elif message[:28].lower() == 'you should answer by saying ':
                message = message[28:]

            elif message[:21].lower() == 'you answer by saying ':
                message = message[21:]
                
            elif message[:6].lower() == 'reply ':
                message = message[6:]

            elif message[:17].lower() == 'you should reply ':
                message = message[17:]
                
            elif message[:27].lower() == 'you should reply by saying ':
                message = message[27:]

            elif message[:20].lower() == 'you reply by saying ':
                message = message[20:]


                
            #at the start of program, before theres anything(to stop index error)
            if len(lines) < 3:
                answer = bot_brain.retrieve_entry(message)
                
                if answer == '':#means bot doesnt know the answer
                    #just throw the question back at the person
                    answer = 'How do I answer: ' + message

                #update the entry, no matter what the case                   #its green
                self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))

                
            else:
                #this 2 is to remove the length the unecesarry part of the input
                user_len = len('[color=dd2020]{}: [/color] > '.format(self.username))
                bot_len = len('[color=20dd20]Bot: [/color] > ')

                #if theres this phrase, means its an unknown key, so create entry
                if 'How do I answer: ' in lines[-2]:
                    bot_brain.create_entry(lines[-2][(bot_len+len('How do I answer: ')):], message) #user input was the answer
                    answer = 'I see. [Learning...]'
                    #'ptint'
                    self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))

                    #1 in 3 chance, bot will ask a question back
                    if random.choice(rand_lst) == 1: 
                        answer = bot_brain.ask_question()
                        
                        #update the entry, no matter what the case                   #its green
                        self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))


                #if the message before si this, means the bad answer button was pressed
                elif 'What would be the correct response for: ' in lines[-2]:
                    bot_brain.create_entry(lines[-2][(bot_len+len('What would be the correct response for: ')):], message)
                    answer = 'I understand now. [Correcting...]'
                    self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))


                #check if the last label is A KEY in the brain, besides the YOUR YOU kind means the bot asked a question
                #return something that can make a if n send mesage
                elif lines[-2][bot_len:] in bot_brain.brain:
                    counter = 0
                    key = lines[-2][bot_len:]
                    
                    #CHeck if the line before is by Bot, and contains 'your' in it (or you or are)
                    #cause that means we remember key as 'my' and change the answer from my to your
                    #eg: Bot: What is your name --> Key : what is MY name, Answer : YOUR name is ..  
                    #can run this if its true, thats why if not elif
                    if 'you' in lines[-2] or 'You' in lines[-2]:
                        counter += 1
                        message = message.replace('I ', 'You ', 10)
                        message = message.replace('i ', 'you ', 10)

                        key = key.replace('you ', 'i ', 10)
                        key = key.replace('You ', 'I ', 10)

                        key = key.replace(' you\n', ' i', 10) #end of sentence
                        key = key.replace(' You\n', ' I', 10)

                        
                        #put as a sub condition cause for "they are" dont want to change those ares
                        if 'are' in lines[-2] or 'Are' in lines[-2]:
                            counter += 1
                            message = message.replace('am ', 'are ', 10)
                            message = message.replace('Am ', 'Are ', 10)
                            
                            key = key.replace('are ', 'am ', 10)
                            key = key.replace('Are ', 'Am ', 10)


                    if 'your' in lines[-2] or 'Your' in lines[-2]:
                        counter += 1
                        #the message is the answer by the user
                        message = message.replace('my ', 'your ', 10) #replace my with your for up to 10 occurences
                        message = message.replace('My ', 'Your ', 10) #if theres any

                        #print(key)

                        key = key.replace('your ', 'my ', 10) #same thing but the other way
                        key = key.replace('Your ', 'My ', 10)

                        #print(key)

                    #one or more of the three above was executed, means create entry not update
                    if counter > 0: 
                        counter = 0 #reset
                        bot_brain.create_entry(key, message)
                        #So, when user ask what is My name, it should say YOur name is ...

                        answer = 'I see. [Learning...]'


                    #these are questions that dont need any updatying
                    elif ('my ' in lines[-2]) or ('My ' in lines[-2]) or ('i ' in lines[-2]) or ('I ' in lines[-2]) or ('am ' in lines[-2]) or ('Am ' in lines[-2]):
                        answer = random.choice(['Yay you remembered', 'Correct!', 'Your memory is better than mine'])

                        
                    #or else its a normal entry so just add it as an alternative answwer
                    else:
                        bot_brain.update_entry(lines[-2][bot_len:], message)
                        answer = 'Interesting. [Learning...]'

                    #'print' whatever answer is
                    self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))

                    #then 1 in 3 chance, bot will ask a question back
                    if random.choice(rand_lst) == 1: 
                        answer = bot_brain.ask_question()
                        
                        #update the entry, no matter what the case                   #its green
                        self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))

                
                #otherwise in normal case scenario
                else:
                    answer = bot_brain.retrieve_entry(message)
                    
                    if answer == '':#means bot doesnt know the answer
                        #just throw the question back at the person
                        answer = 'How do I answer: ' + message
                        
                        #update the entry, no matter what the case                   #its green
                        self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))


                    else:
                        #print the message
                        self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))

                        #then 1 in 3 chance, bot will ask a question back
                        if random.choice(rand_lst) == 1: 
                            answer = bot_brain.ask_question()
                            
                            #update the entry, no matter what the case                   #its green
                            self.history.update_chat_history('[color=20dd20]{}[/color] > {}'.format('Bot: ', answer))


    #Sets focus to text input field
    def focus_text_input(self, _):
        self.new_message.focus = True


class Brain:
    def __init__(self, brain_name):
        #maybe some time in the future self.username = str(username)
        self.brain = JsonStore(brain_name + '.json')
        #print(list(self.brain))

    def is_empty(self):
        counter = 0
        for key in self.brain:
            counter += 1
            if counter > 1:
                break #so it doesnt waste time

        if counter > 0:
            return False #its not empty

        else:
            return True #its empty
                

    def wipe_memory(self):
        self.brain.clear()
    
    def create_entry(self, question, answer):
        self.brain.put(question, Answers = [answer])    

    def update_entry(self, question, answer):
        existing_answers = self.brain.get(question)['Answers']
        existing_answers.append(answer)
        updated_answers = existing_answers
        self.brain.put(question, Answers = updated_answers)

    #def delete_entry:
        
    def retrieve_entry(self, question):
        question = question.strip()
        #remove ?!., from the end, cause you and you are the same, but its interpretted differently
        if question[-1] in ['?', '!', '.', ',']:
            #i want the key to still have the punc, just that i dont want to compare the words with punc
            without_punc = question[:-1]
        else:
            without_punc = question

        #make everything lower case, so comparision is the same
        without_punc = without_punc.lower()
            
        words = without_punc.split(' ')#create list of words from question
        #print(words)
        shortlisted = []
        first_round = []
        for key in self.brain:
            #the key will still have the punc, bt i dont want it to get based on it
            if key[-1] in ['?', '!', '.', ',']:
                key_punc = key[:-1]
            else:
                key_punc = key
                
            if key_punc.lower() == question.lower():
                return random.choice(self.brain.get(key)['Answers']) #it will break the method right here already

            else:
                count = 0
                for word in words:                  #these are common words, eg what is your <- thats 3 words
                    if word in key and word.lower() not in ['what', 'who', 'where', 'when', 'why', 'how', 'you', 'your', 'are', 'i', 'am', 'my', 'we', 'they', 'our', 'is', 'us', 'he', 'she']:
                        count += 1
                #if theres even 2 word hit, a logical sentence would probably need at least 3, 1 is abit little
                #i cant find a balance...
                if count > 0:
                    #first round is to eliminate all the sentences just containing common words
                    first_round.append(key)
                    
                    
                #this is to account for the initially excluded common words
                for key in first_round:
                    count2 = 0
                    for word in words:
                        if word in key:
                            count2 += 1

                    #increase the requirement to 3 word hit, cause if theres 2 words and no common words, it probably do have context
                    if count2 > 1:
                        #check the length difference between count and the word,
                        #ifthe difference is too much, its unrealiable to shortlisrtt it
                        difference = abs(len(words) - count2)
                        if difference <= 4: #if a sentence has 10 words, but only just nicely 3 words hit, it shouldnt have the same answer most probably
                            shortlisted.append([key, count2])

        if shortlisted == []:
            return '' #there is no match, nothing to retrieve

        else:
            #checking for the highest num of hit keywords
            highest = 1 #HIGHEST SHOULD START FROM1, CAUSE IT STARTS AT 1
            index = 0
            same_score = []
            for i in range(len(shortlisted)): #each pair being [key, count]
                if shortlisted[i][1] > highest:
                    highest = shortlisted[i][1]
                    index = i

            #This one is to check if there is any SAME scores
            for i in range(len(shortlisted)):
                if shortlisted[i][1] == highest: #here highest will actually be highest already
                    same_score.append(shortlisted[i][0])

            #if theres more than one with exact same number of keywordss matched
            #Choose the key with the closest length to the question 
            if len(same_score) != 0:
                difference = 9999999 #arbitary big number, want to find key with smallert difference in number of words
                question_len = len(words)
                #print(same_score)
                for key in same_score:
                    keywords = key.strip().split(' ')
                    if abs(question_len - len(keywords)) < difference:
                        difference = abs(question_len - len(keywords))
                        desired_key = key
                        #print(desired_key)

                answer = random.choice(self.brain.get(desired_key)['Answers']) #choose one of many possible answer

                
            #no keys with same number of keywords hit
            else:        
                desired_key = shortlisted[index][0]

            answer = random.choice(self.brain.get(desired_key)['Answers'])

            return answer
            
        
    def ask_question(self): #the question is an existing key
        keys = list(self.brain)

        #if there is no keys, eg first run, new brain, then just pass
        if len(keys) > 0:
            return random.choice(list(self.brain))


        
        
class TeachABot(App):
    def readme(self,*args):
        box = BoxLayout(orientation = 'vertical', padding = (10))
        label = Label(text="Thank you for trying out Teach A Bot!\n\n[b]REMEMBER: THIS IS NOT YOUR USUAL CHATBOT[/b]\n This Bot knows NOTHING initially, not even English, or its name, \nThe point of the app is for you to teach it.\nThe bot will sound like it is just repeating what you say at first, as that is all it knows about language initially.\nIt will take at lleast 100 question-answer entries before it becomes even sligthly 'intelligent'.\n\n A few commands you should know:\n\n [b]/skip[/b] : Skips answering a Bot's question\n [b]/wipe[/b] : Wipes the memory of the Bot completely\n[b]Good Answer[/b]: Will reinforce that an answer said y the bot to a question is good\n[b]Bad Answer[/b]: Tells the bot it is a bad answer and it will ask for the suitable answer\n\nHope you enjoy!",
                      halign="center", valign = "middle",
                      height=Window.size[1]*0.7, width=Window.size[0]*0.7,
                      text_size=(Window.size[0]*0.8, Window.size[1]*0.8),
                      markup=True)
##        label.width = label.texture_size[0]
##        label.height = label.texture_size[1]
##        label.texture_update()
##        label.text_size = ()
##        
        box.add_widget(label)

        close_btn = Button(text = "Close", size_hint = (1, 0.1), pos_hint = {'centre_x':1, "bottom":1})
        
        box.add_widget(close_btn)

        popup = Popup(title="How To Use", content = box,
                      size_hint=(0.9, 0.9),
                      auto_dismiss=True)
        close_btn.bind(on_press = popup.dismiss)
        popup.open()
        
    def create_chat_page(self):
        self.chat_page = ChatPage()
        screen = Screen(name = 'Chat')
        screen.add_widget(self.chat_page)
        
        #self.readme()
        
        return screen

    def build(self):
        #Window.size = (500, 800)
        #self.readme()
        self.ads = KivMob(TestIds.APP)
        self.ads.new_banner(TestIds.BANNER, top_pos=True)
        self.ads.request_banner()
        self.ads.show_banner()
        
        return self.create_chat_page()

TeachABot().run()

    
