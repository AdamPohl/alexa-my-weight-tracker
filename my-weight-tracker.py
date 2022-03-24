from flask_ask import Ask, statement, question, context
from datetime import datetime
from flask import Flask
# import logging
import boto3


app = Flask(__name__)
ask = Ask(app, '/')
# logging.getLogger("flask_ask").setLevel(logging.DEBUG)

unit_type = ''
target = 0


def database():
    dynamodb = boto3.resource('dynamodb', region_name='eu-west-1')
    table = dynamodb.Table('TrackMyWeightData')
    return table


def display_type():
    displaytype = None

    if "Viewport" in context:
        displaytype = context.Viewport.shape

    return displaytype


@ask.launch
def welcome():
    table = database()
    display = display_type()
    msg = "Hello and welcome to Track My Weight. Well then, I see that you have "

    try:
        user_id = str(context.System.user.userId)

        response = table.get_item(
            Key={
                'userID': user_id
            }
        )

        _ = response['Item']['targetWeight']

        msg = msg + "used this skill before, "
    except Exception:
        msg = msg + """not used this skill before. To start your journey with Track my Weight,
        please give me your target weight or say help to find out more about this skill,"""

    msg = msg + "what would you like to do?"

    render_msg = question(msg)

    if display:
        render_msg = render_msg.display_render(
            backButton="VISIBLE",
            template="BodyTemplate1",
            title="Welcome to Track My Weight",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("TargetIntent")
def target_intent(weight, units):
    global target
    global unit_type
    table = database()
    display = display_type()

    try:
        target = int(weight)
    except Exception:
        return error('Amount')

    try:
        response = table.get_item(
            Key={
                'userID': str(context.System.user.userId)
            }
        )

        unit = response['Item']['units']

        if units == 'stone' and unit == 'Kilograms':
            return error('Units-stone')
        elif units in ['kilograms', 'kilos', 'kg'] and unit == 'Stones':
            return error('Units-kilos')

        table.update_item(
            Key={
                'userID': str(context.System.user.userId)
            },
            UpdateExpression='SET targetWeight = :val1',
            ExpressionAttributeValues={
                ':val1': str(target),
            }
        )

        msg = "Cool, your new target weight has been inputted, have a nice day."

        render_msg = statement(msg)
    except Exception:
        if units == 'stone':
            unit_type = 'Stones'
        elif units in ['kilograms', 'kilos', 'kg']:
            unit_type = 'Kilograms'
        else:
            return error('Units')

        msg = "Thanks, can I now take your starting weight in {}.".format(unit_type)

        render_msg = question(msg)

    if display:
        render_msg = render_msg.display_render(
            backButton="VISIBLE",
            template="BodyTemplate1",
            title="Welcome to Track My Weight",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("NewKiloIntent")
def new_intent(kilo, fraction):
    table = database()
    display = display_type()

    global unit_type
    global target

    if target == 0:
        return error('Target')

    if unit_type != 'Kilograms':
        return error('units-kilo')

    try:
        Kilo = float(kilo)
    except ValueError or TypeError:
        return error('Amount')

    frac = 0.0
    try:
        if len(str(fraction)) == 1:
            frac = float(fraction) / 10
        elif len(str(fraction)) == 2:
            frac = float(fraction) / 100
        elif len(str(fraction)) > 2:
            raise ValueError
    except ValueError or TypeError:
        return error('Amount')

    amount = str(Kilo + frac)

    method = "lose"
    if target > float(amount):
        method = "gain"

    user_id = str(context.System.user.userId)

    item = {
        'userID': user_id,
        'targetWeight': target,
        'method': method,
        'startingWeight': amount,
        'weight': "-",
        'date_started': str(datetime.date(datetime.now())),
        'units': unit_type
    }

    table.put_item(
        Item=item
    )

    msg = "Thanks for starting with Track My Weight, see you soon."

    render_msg = statement(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("UpdateKiloIntent")
def update_intent(kilo, fraction):
    display = display_type()
    table = database()
    frac = 0

    try:
        Kilo = float(kilo)
    except ValueError or TypeError:
        return error('Amount')

    try:
        if len(str(fraction)) == 1:
            frac = float(fraction) / 10
        elif len(str(fraction)) == 2:
            frac = float(fraction) / 100
        elif len(str(fraction)) > 2:
            raise ValueError
    except ValueError or TypeError:
        return error('Amount')

    amount = str(Kilo + frac)

    try:
        user_id = str(context.System.user.userId)

        response = table.get_item(
            Key={
                'userID': user_id
            }
        )
    except Exception:
        return error('Response')

    if response['Item']['units'] == "Stones":
        return error('units-kilos')

    left = "%.2f" % (float(amount) - float(response['Item']['targetWeight']))
    if response['Item']['method'] == "gain":
        left = "%.2f" % (float(response['Item']['targetWeight']) - float(amount))

    table.update_item(
        Key={
            'userID': str(context.System.user.userId)
        },
        UpdateExpression='SET weight = :val1',
        ExpressionAttributeValues={
            ':val1': amount,
        }
    )

    msg = """Cheers for that, at {} kilograms you are now {} Kilograms away from your target. 
    Good luck and thanks for using track my weight""".format(amount, left)
    render_msg = statement(msg)

    if float(left) <= 0:
        msg = """Congratulations, you have hit your target weight of {} Kilograms. Would you like to set a 
        new target weight?""".format(response['Item']['targetWeight'])

        render_msg = question(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("NewStoneIntent")
def new_intent(stone, pounds):
    table = database()
    display = display_type()

    global unit_type
    global target

    if target == 0:
        return error('Target')

    if unit_type != 'Stones':
        return error('units-stone')

    try:
        Stone = float(stone)
    except ValueError or TypeError:
        return error('Amount')

    try:
        Pounds = float(pounds) / 14
    except ValueError or TypeError:
        return error('Amount')

    amount = str(Stone + Pounds)
    user_id = str(context.System.user.userId)

    method = "lose"
    if target > float(amount):
        method = "gain"

    item = {
        'userID': user_id,
        'targetWeight': target,
        'startingWeight': amount,
        'weight': "-",
        'method': method,
        'date_started': str(datetime.date(datetime.now())),
        'units': unit_type
    }

    table.put_item(
        Item=item
    )

    msg = 'Thanks for starting with Track My Weight, see you soon.'

    render_msg = statement(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("UpdateStoneIntent")
def update_intent(stone, pounds):
    display = display_type()
    table = database()

    try:
        Stone = float(stone)
    except ValueError or TypeError:
        return error('Amount')

    try:
        Pounds = float(pounds) / 14
    except ValueError or TypeError:
        return error('Pound')

    amount = str(Stone + Pounds)

    try:
        user_id = str(context.System.user.userId)

        response = table.get_item(
            Key={
                'userID': user_id
            }
        )
    except Exception:
        return error('Response')

    if response['Item']['units'] == "Kilograms":
        return error('units-stone')

    left = "%.2f" % (float(amount) - float(response['Item']['targetWeight']))
    if response['Item']['method'] == "gain":
        left = "%.2f" % (float(response['Item']['targetWeight']) - float(amount))

    table.update_item(
        Key={
            'userID': str(context.System.user.userId)
        },
        UpdateExpression='SET weight = :val1',
        ExpressionAttributeValues={
            ':val1': amount,
        }
    )

    msg = """cheers for that, at {} stone and {} pounds you are now {} stone away from your target. 
    Good luck and thanks for using track my weight""".format(str(Stone), str(Pounds), left)

    render_msg = statement(msg)

    if float(left) <= 0:
        msg = """Congratulations, you have hit your target weight of {} stone. Would you like to set a new 
        target weight?""".format(response['Item']['targetWeight'])

        render_msg = question(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("ProgressIntent")
def progress_intent():
    table = database()
    display = display_type()

    try:
        user_id = str(context.System.user.userId)

        response = table.get_item(
            Key={
                'userID': user_id
            }
        )
    except Exception:
        return error('Response')

    method = "lost"
    lost = "%.2f" % (float(response['Item']['startingWeight']) - float(response['Item']['weight']))
    left = "%.2f" % (float(response['Item']['weight']) - float(response['Item']['targetWeight']))

    if response['Item']['method'] == "gain":
        method = "gained"
        lost = "%.2f" % (float(response['Item']['weight']) - float(response['Item']['startingWeight']))
        left = "%.2f" % (float(response['Item']['targetWeight']) - float(response['Item']['weight']))

    msg = """Well then, since starting your account with Track My Weight on {}, you have {} a total of {} {}. you are 
    currently {} {} away from hitting your target weight of {} {}. Keep going, you got this!""".format(
        response['Item']['date_started'],
        method, lost, response['Item']['units'],
        left, response['Item']['units'],
        response['Item']['targetWeight'],
        response['Item']['units']
    )

    render_msg = statement(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("AMAZON.YesIntent")
def update_intent():
    table = database()
    display = display_type()
    msg = "Cool, can I please take your target weight, in "

    try:
        user_id = str(context.System.user.userId)

        response = table.get_item(
            Key={
                'userID': user_id
            }
        )

        units = response['Item']['units']

        msg = msg + "{}?".format(units)
    except Exception:
        msg = msg + """Kilos or Stones?"""

    render_msg = question(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("AMAZON.HelpIntent")
def help_intent():
    display = display_type()
    msg = """Hi there, with this skill you can keep a track of your weight as
    you work towards your goal. I can tell your progress
    since you started, and when you update your weight I will let you know
    how much further you have to go till you reach that target.  If you measure
    your weight in stone, please give me both stone and pounds, something like
    this: my weight is 12 stone and 3 pounds or my weight is 11 stone and 0
    pounds, if you measure in kilograms please give me your weight like this:
    my weight is 80 point 54 kilograms or my weight is 75 point 0 kilos, please
    keep the number after the point to a maximum of two digits.  To
    start just give me your target weight by saying something like this: My target weight is 75
    kilograms. What would you like to do?"""

    render_msg = question(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("AMAZON.NoIntent")
def no_intent():
    display = display_type()
    msg = 'Goodbye! Thanks for using Track My Weight.'
    render_msg = statement(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("AMAZON.StopIntent")
def stop_intent():
    display = display_type()
    msg = 'Goodbye! Thanks for using Track My Weight.'
    render_msg = statement(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


@ask.intent("AMAZON.CancelIntent")
def cancel_intent():
    display = display_type()
    msg = 'Goodbye! Thanks for using Track My Weight.'
    render_msg = statement(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


def error(option):
    display = display_type()
    msg = ""

    if option == 'Response':
        msg = """Hi there, it doesn't seem as though you have used track my weight, would you like to start?"""
    elif option == 'Target':
        msg = """Hi there, I don't have your target weight which I need to
        before I can put your data into the database"""
    elif option == 'Amount':
        msg = "Your amount was invalid, a number is required. Please try again."
    elif option == 'Units':
        msg = """Hi there, the units you provided are not compatible with this skill, I require either Kilograms, which 
        you could also call Kilos or kg, or Stones. Please give me your target weight again."""
    elif option == 'units-stone':
        msg = """Hi there, you gave me your weight in Stones whilst your previous data entries have been in kilograms, 
        please give me your weight again in kilograms."""
    elif option == 'units-kilos':
        msg = """Hi there, you gave me your weight in Kilograms whilst your previous data entries have been in Stones, 
        please give me your weight again in Stones."""

    render_msg = question(msg)

    if display:
        render_msg = render_msg.display_render(
            template="BodyTemplate1",
            title="Track My Weight",
            backButton="VISIBLE",
            text={
                "primaryText": {
                    "type": "RichText",
                    "text": msg
                }
            }
        )

    return render_msg


if __name__ == '__main__':
    # app.run(debug=True)
    app.run()
