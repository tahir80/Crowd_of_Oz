from naoqi import ALProxy
class NAO_Speak:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.tts = ALProxy("ALAnimatedSpeech", ip, port)

    def say_text(self, text):
        self.tts.say(text)
