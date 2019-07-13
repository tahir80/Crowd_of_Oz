from naoqi import ALProxy, ALBroker, ALModule
import argparse

# Global variable to store the TTSEventWatcher module instance
tts_event_watcher = None
memory = None

class TTSEventWatcher(ALModule):
    """ An ALModule to react to the ALTextToSpeech/Status event """

    def __init__(self, ip_robot, port_robot):
        super(TTSEventWatcher, self).__init__("tts_event_watcher")
        global memory
        memory = ALProxy("ALMemory", ip_robot, port_robot)
        self.tts = ALProxy("ALTextToSpeech", ip_robot, port_robot)
        memory.subscribeToEvent("ALTextToSpeech/Status",
                                "tts_event_watcher",  # module instance
                                "on_tts_status")  # callback name

    def on_tts_status(self, key, value, message):
        """ callback for event ALTextToSpeech/Status """
        print "TTS Status value:", value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")
    args = parser.parse_args()

    event_broker = ALBroker("event_broker", "0.0.0.0", 0,
                            args.ip, args.port)
    global tts_event_watcher
    tts_event_watcher = TTSEventWatcher(args.ip, args.port)
    while True:
        raw_input("Watch events be triggered...")
        tts_event_watcher.tts.say("Hello!")
