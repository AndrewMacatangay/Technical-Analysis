import matplotlib.pyplot as plt
import matplotlib.image as mpimg

class Image:
    def __init__(self, path):
        self.img = mpimg.imread(path)
        plt.figure(figsize = (20, 10))
        plt.axis("off")
    
    def show(self):
        plt.imshow(self.img)