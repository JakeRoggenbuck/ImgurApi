import base64
import fire
import json
from pymongo import MongoClient
import requests
import yaml


class Database:
    def __init__(self, db_name: str, location: str = "localhost", port: int = 27017):
        """Set default location and port"""
        self.db_name = db_name
        self.location = location
        self.port = port
        self.connect()

    def connect(self):
        """Nake client, database, and collection"""
        self.client = MongoClient(self.location, self.port)
        self.database = self.client[self.db_name]
        self.blocked = self.database.blocked
        self.uploaded = self.database.uploaded
        self.deleted = self.database.deleted


class Config:
    def __init__(self, path: str):
        self.path = path
        self.config = self.get_config()
        self.client_id = self.config["client_id"]
        self.client_secret = self.config["client_secret"]

    def get_config(self):
        config_file = open(self.path)
        config = yaml.load(config_file, Loader=yaml.FullLoader)
        return config


class Imgur:
    def __init__(self, name: str = "imgur_image_data"):
        self.db = Database(name)
        self.config = Config("config.yml")
        self.request_headers = {
            "Authorization": f"Client-ID {self.config.client_id}"
        }
        self.url = "https://api.imgur.com/3/image/"

    def get_base64_file(self, path: str):
        """Get image by name and base64 encode it, then return it"""
        file = open(path, 'rb')
        base64_image = base64.b64encode(file.read())
        payload = {'image': base64_image}
        return payload

    def upload(self, path: str) -> dict:
        """Upload an image by path, add it to uploaded database

        Intake a image path, give it to get_base64_file to encode to base64
        the add it to a post request, make the request, if request guess
        throught, add image data json returned from imgur to database"""
        payload = self.get_base64_file(path)
        request = requests.request(
            "POST", self.url,
            headers=self.request_headers,
            data=payload
        )
        if request.status_code == 200:
            data = json.loads(request.text)["data"]
            self.db.uploaded.insert_one(data)
            return data

    def block(self, _id: str):
        """Given an _id, add the name to the blocklist"""
        image = self.db.uploaded.find_one({"id": _id})
        self.db.blocked.insert_one({"id": image["id"]})

    def delete(self, _id: str) -> dict:
        """Check delete key from uploaded images, remove image using request,
        delete from uploaded

        Search image by id from uploaded, then get the deletehash, after that
        send the request and if it returns correctly, delete original image
        document from uploaded collection"""
        image = self.db.uploaded.find_one({"id": _id})
        if image is not None:
            url = f"{self.url}{image['deletehash']}"
            request = requests.request(
                "DELETE",
                url,
                headers=self.request_headers
            )
            if request.status_code == 200:
                self.db.deleted.insert_one(image)
                self.db.uploaded.delete_one({"id": _id})
            return request.text

    def get_viewable_images(self) -> list:
        """Get all the documents in uploaded that do not have a correcsponding
        entry in blocked"""
        images = []
        for image in self.db.uploaded.find({}):
            image_id = image["id"]
            blocked = self.db.blocked.find_one({"id": image_id})
            if blocked is None:
                images.append(image)
        return images

    def view(self):
        """View all uploaded"""
        for x in self.db.uploaded.find():
            print(x)


class ImgurApi(object):
    def __init__(self):
        self.imgur = Imgur()

    def upload(self, filename):
        print(self.imgur.upload(filename))

    def delete(self, id):
        print(self.imgur.delete(id))

    def block(self, id):
        print(self.imgur.delete(id))

    def view_all(self):
        results = self.imgur.get_viewable_images()
        for result in results:
            print(result)

    def view(self):
        self.imgur.view()


def main():
    fire.Fire(ImgurApi)


if __name__ == "__main__":
    main()
