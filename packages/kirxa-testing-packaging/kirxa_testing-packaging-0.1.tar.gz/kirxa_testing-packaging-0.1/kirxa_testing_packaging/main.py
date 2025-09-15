import matplotlib.pyplot as plt
import random



class RandomPlot:
  def __init__(self, n=10):
    self.number_to_generate = n
    self.values = None

  def generate_random_values(self):
    self.values = [random.random() for x in range(self.number_to_generate)]

  def generate_plot(self):
    if self.values == None:
      print('Run generate_random_values first')
      return None

    else:
      plot=plt.plot(self.values)
      return plot


        