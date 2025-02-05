from guizero import App, Text, PushButton


ROBOTO = '/usr/share/fonts/truetype/roboto-slab/RobotoSlab-Regular.ttf'
dejavu = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'

def change_message():
    message.value = "You pressed the button!"

app = App(title="Hello world")

message = Text(app, text="Welcome to the Hello world app!", size=20, font=ROBOTO, color="blue")


button = PushButton(app, text="Press me", command=change_message)

app.display()