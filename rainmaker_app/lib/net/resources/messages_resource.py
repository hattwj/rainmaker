from twisted.internet import defer
from rainmaker_app.db.models import Message, Broadcast
from rainmaker_app.lib.net.commands import resource_response, dump_resource_errors

@defer.inlineCallbacks
def post(message, opts):
    result = resource_response()
    message = Message.createOrUpdate( **message )
    yield message.save()
    if not message.errors.isEmpty():
        result['code'] = 400
    else:
        # send message through every open connection except the
        # one we got it from
        yield Broadcast.send( message, opts=opts )
    for err in message.errors:
        result['errors'].append( err + " : " + ','.join(message.errors[err]) )
    defer.returnValue( result )

@defer.inlineCallbacks
def get( server, *pubkeys):
    messages = yield Message.find_many( pubkeys, 'pubkey_str' )
    result = resource_response()
    result['messages'] = []
    for message in messages:
        result['messages'].append( message.to_dict() )
    defer.returnValue( result )

