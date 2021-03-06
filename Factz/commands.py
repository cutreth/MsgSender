from Factz.do import sub_exist, add_number, number_exist, add_rating
import re
           
class textCommand:
    def __init__(self, name, display_name, regex_list):
        self.name = name
        self.display_name = display_name
        self.regex_list = regex_list
    def __str__(self):
        return self.display_name
        
commands = [
            textCommand("subscribe",    "Subscribe PoopFactz",  ["subscribe *(.*)", "add *(.*)"]),
            textCommand("unsubscribe",  "Unsubscribe PoopFactz",["unsubscribe *(.*)", "leave *(.*)", "stop *(.*)"]),
            textCommand("source",       "Source",               ["source()", "sauce()"]),
            textCommand("rate",         "Rate {1-5}",           ["rate *(\d*)", "rating *(\d*)", "(\d+)"]),
        ]

def extract_command(text, commands):
    '''
    Loops through the list of commands and looks for the pattern
    "COMMAND [PARAMETERS]" and outputs the first match it finds
    '''
    out = [None, None]
    for command in commands:
        regex_list = command.regex_list
        for reg in regex_list:
            pattern = re.compile(reg, re.IGNORECASE)
            if pattern.match(text):
                parm = pattern.match(text).groups()[0]
                out[0] = command.name
                out[1] = parm if parm != '' else None
                break
    return out
    
def extract_subscription(text):
    '''
    Place older to extract the subscription from a text message
    '''
    return sub_exist("PoopFactz")
    
def subscribe(numObj, subObj):
    '''
    Activate number/subscription in activeSubscription and generate a response
    '''
    numObj.toggle_active(subObj, status=True)
    return "You're now subscribed to " + subObj.name + "."

def unsubscribe(numObj, subObj):
    '''
    Deactivate number/subscription in activeSubscription and generate a response
    '''
    numObj.toggle_active(subObj, status=False)
    return "You're now unsubscribed to " + subObj.name + "."
    
def get_source(numObj):
    '''
    Get the source for the last message and generate a response
    '''
    msgObj = numObj.get_last_message()
    if msgObj is not None:
        return msgObj.source
    else:
        return "You have yet to receive a fact."

def add_user(from_number, message):
    '''
    Add a user to the db and generate a response
    '''
    command, parm = extract_command(message, commands)
    numObj = add_number(from_number)
    subObj = extract_subscription(parm)
    #In future, check that that command == "subscribe"
    numObj.toggle_active(subObj, status=True)
    out = "Welcome to " + subObj.name + "! Your first message is on its way."
    # To do: send last message that was sent for newly subscribed sub?
    return out

def set_rating(numObj, rating):
    '''
    Set the rating and generate a response
    '''
    rate = add_rating(numObj, rating)
    if rate == True:
        out = "Thanks for the rating!"
    elif rate == False:
        out = "You have yet to receive a fact."
    else:
        out = "Please submit a rating 1 through 5."
    return(out)
        
def update_user(message, numObj):
    '''
    Use this for a number already in the db.
    Generate the reply to a text message given the message, list of commands,
    and number object.
    '''
    command, parm = extract_command(message, commands)
    
    subObj = extract_subscription(parm)
    
    if command == "subscribe":
        out = subscribe(numObj, subObj)
    elif command == "unsubscribe":
        out = unsubscribe(numObj, subObj)
    elif command == "source":
        out = get_source(numObj)
    elif command == "rate":
        out = set_rating(numObj, parm)
    else:
        out = "Unknown command. "
        out += "Try one of these: "
        out += ", ".join([str(c) for c in commands])
    return out
    
def gen_reply(from_number, message):
    '''
    High level function to generate a reply to a text
    '''
    numObj = number_exist(from_number)
    if numObj == None:
        reply = add_user(from_number, message)
    else:
        reply = update_user(message, numObj)
    return reply
    