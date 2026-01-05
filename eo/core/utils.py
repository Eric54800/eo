import uuid
import os

class UniqueUploadPath:
    def __init__(self, subfolder):
        self.subfolder = subfolder

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1].lower()
        new_name = f"{uuid.uuid4()}.{ext}"
        return os.path.join(self.subfolder, new_name)

    def deconstruct(self):
        return (
            f"{self.__class__.__module__}.{self.__class__.__name__}",
            [],
            {"subfolder": self.subfolder},
        )
