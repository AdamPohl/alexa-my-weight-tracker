from matplotlib import pyplot as plt
import tornado.ioloop
import tornado.web
import pathlib
import boto3

class MainHandler(tornado.web.RequestHandler):

    def post(self):

        try:
            args = self.request.body_args
            filename = str(args['userId']) + '.png'
            bucket = 'weight-tracker-images'
            url = 'https://s3-eu-west-1.amazonaws.com/{}/{}'.format(bucket,
                                                                    filename)
            ExtraArgs = {
                'ACL': 'public-read',
                'ContentType': 'image/png'
                }

            # Generate the graph
            plt.axhline(y=args['targetWeight'], color='blue', linestyle='--')
            plt.plot(args['time'], args['weight'], color='red')
            plt.xticks(args['time'], rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(filename)

            # Upload the file to the S3 bucket, make it public and set tell the
            # bucket that it's an image.
            s3.meta.client.upload_file(filename, bucket, filename, ExtraArgs=ExtraArgs)

            # Delete the local version of the file
            pathlib.Path(filename).unlink()

        except:
            return 'error'

        return url

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
    ])

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()

[95, 94, 93, 92, 91, 91, 92, 90, 89, 88, 87, 86, 85]
