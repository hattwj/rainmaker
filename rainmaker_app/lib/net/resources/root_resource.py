from base_resource import BaseResource

class RootResource(BaseResource):

    def render_GET(self, request):
        return '<html>Hello, GET world! root located at %r. </html>' \
                % (request.prepath)


