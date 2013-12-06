from twisted.internet import defer
from rainmaker_app.db.models import Message

@defer.inlineCallbacks
def post(**kwargs):
    message = yield Message(**kwargs).save()
    if message.errors.isEmpty():
        result['response_code'] = 200
    else:
        result['response'] = 400
        result['error_key'] = [k for message.errors.keys()]
        result['error_val'] = [k for message.errors.keys()]
    defer.returnValue( result ) 

