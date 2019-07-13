import qi
import argparse

class HumanTrackedEventWatcher(object):
    """ A class to react to the ALTextToSpeech/Status event """

    def __init__(self, app):
        super(HumanTrackedEventWatcher, self).__init__()
        app.start()
        session = app.session
        self.memory = session.service("ALMemory")
        self.tts = session.service("ALTextToSpeech")
        self.subscriber = self.memory.subscriber("ALTextToSpeech/Status")
        self.subscriber.signal.connect(self.on_tts_status)
        # keep this variable in memory, else the callback will be disconnected

    def on_tts_status(self, value):
        """ callback for event ALTextToSpeech/Status """
        print "TTS Status value:", value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="192.168.1.87",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")
    args = parser.parse_args()

    # Initialize qi framework
    connection_url = "tcp://" + args.ip + ":" + str(args.port)
    app = qi.Application(["HumanTrackedEventWatcher", "--qi-url=" + connection_url])
    tts_event_watcher = HumanTrackedEventWatcher(app)   

    while True:
        raw_input("Watch TTS events be triggered...")
        tts_event_watcher.tts.say("Hello!")
