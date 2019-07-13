from oocsi import OOCSI
from NAO_Speak import NAO_Speak  # (file name followed by class name)
import unidecode

#################################
IP = "IP_OF_PEPPER_ROBOT"
text = ""
my_nao = NAO_Speak(IP, 9559)
##################################

def receiveEvent(sender, recipient, event):
    print('from ', sender, ' -> ', event)

    # this will convert unicode string to plain string
    msg = str(event['message'])

    sender = str(sender)

    x, y = sender.split('_')

    if x == 'webclient':
        my_nao.say_text(msg)

if __name__ == "__main__":
    #o = OOCSI('abc', "oocsi.id.tue.nl", callback=receiveEvent)
    o = OOCSI('pepper_receiver', 'oocsi.id.tue.nl')
    o.subscribe('__test123__', receiveEvent)
