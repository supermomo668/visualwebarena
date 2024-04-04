from abc import ABC, abstractmethod

class Pipeline(ABC):
    @abstractmethod
    def process_image(self, image_path: str):
        pass

    @abstractmethod
    def generate_caption(self, text: str, image_path: str):
        pass
