from base_resource import BaseResource

class SyncPathsResource(BaseResource):

    def show(self, request):
        return '<html>Hello, GET world! I am located at %r. </html>' \
                % (request.prepath)

