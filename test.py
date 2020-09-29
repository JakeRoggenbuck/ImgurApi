from main import Imgur


imgur = Imgur()
if input("Upload? [Y/n]: ").upper() == "Y":
    imgur.upload("test.jpg")

for x in imgur.get_viewable_images():
    print(x["id"], x["link"])

block = input("Block: ")
if block != "":
    imgur.block(block)

delete = input("Delete: ")
if delete != "":
    imgur.delete(delete)
    print(f"Deleted: {delete}")

imgur.view()
