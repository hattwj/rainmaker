from base_resource import BaseResource

class DiffsResource(BaseResource):

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        return '<html>Hello, GET world! I am located at %r. </html>' \
                % (request.prepath)

